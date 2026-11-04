# Contrato interno — serviço fiscal

Base: `VITE_NFSE_API_URL` (frontend). **CSRF:** toda mutação (POST/PUT/DELETE) exige `Origin` na allowlist e `X-Requested-With: nfse-imoveis`; sem isso, 403. Respostas: `Cache-Control: private, no-store`. Sessão em cookie HttpOnly `session` emitido após login no provedor de identidade (`GET /v1/auth/login?retorno=`); requisições com `credentials: include`. CORS restrito à origem do app.

| Método | Caminho | Corpo | Retorno / erros |
|---|---|---|---|
| GET | /v1/sessao | — | usuário, papel, empresas autorizadas, liberações · 401 |
| GET | /v1/empresas/{e}/rascunhos | — | rascunhos não enviados |
| POST | /v1/empresas/{e}/rascunhos | dados, origem | rascunho v1 |
| PUT | /v1/empresas/{e}/rascunhos/{id} | versao_esperada, dados | nova versão · 409 conflito |
| DELETE | /v1/empresas/{e}/rascunhos/{id} | — | 204 · 423 se enviado |
| POST | /v1/empresas/{e}/importacoes/analisar | multipart `arquivo` (.csv/.xlsx) | prévia por linha com totais, calculada no servidor · 422 |
| GET | /v1/empresas/{e}/importacoes/origens | — | mapa sistema\|id_origem → conteúdo |
| POST | /v1/empresas/{e}/importacoes/confirmar | linhas selecionadas | criados/ignorados (atômico) |
| POST | /v1/empresas/{e}/rascunhos/{id}/revisao | versao | rascunho com revisão (hash) · 409 · 422 |
| POST | /v1/empresas/{e}/rascunhos/{id}/emissao | revisao_id, versao, ambiente, confirmacao_humana; header Idempotency-Key | 202 operação; repetição devolve a mesma · 409 · 423 bloqueio |
| GET | /v1/empresas/{e}/emissoes?rascunho_id=&versao= | — | lista/filtra; usada para recuperar a operação após resposta perdida |
| GET | /v1/empresas/{e}/emissoes/{id} | — | estado persistido; leitura não reenvia |
| POST | /v1/empresas/{e}/emissoes/{id}/verificar | — | agenda consulta pela identidade DPS; nunca cria emissão |
| GET | /v1/empresas/{e}/emissoes/{id}/documento | — | download autorizado |

Acesso a outra empresa: 404 genérico `Conteúdo indisponível`. Valores: string decimal canônica. A chave idempotente é interna; não se presume equivalente na API Nacional.

## Idempotência e resposta perdida
- Chave do cliente: `emissao:{empresa}:{rascunho}:v{versao}:{ambiente}:{hash revisado}`, estável depois de recarregar a página.
- Servidor: chave escopada por empresa e ligada à impressão digital (empresa, rascunho, versão, ambiente, hash). Mesma chave com outro conteúdo ou ambiente → 409. Chave nova para o mesmo rascunho, versão e ambiente → mesma operação. Com resultado desconhecido → 423.
- Cliente: falha de rede, timeout ou 5xx na confirmação = **resultado desconhecido**. O botão "Verificar situação" consulta `GET /emissoes?rascunho_id&versao`; só se nada for encontrado repete o POST com a mesma chave (idempotente).

## Estado da implementação
Todas as rotas acima estão em `backend/app/api.py` (`create_app(deps)`), testadas com TestClient em memória (`tests/test_api.py`) e com PostgreSQL efêmero (`tests/test_pg.py::PgApi`).
- Persistência durável: `app/pg.py` (`PostgresRepository`, `PgMemberships`, `PgCompanies`, `PgReleases`) sobre `backend/db/001_initial.sql` + `002_isolation.sql`.
- Identidade: `SupabaseIdentityVerifier` verifica JWT/JWKS; `POST /v1/auth/session` cria o cookie e `DELETE /v1/auth/session` o exclui. Storage privado: `SupabaseS3Storage`. `app.main:app` monta as dependências duráveis, sem carregar certificado ou iniciar worker. Cofre, processo/loop operacional do worker e adaptador fiscal oficial continuam pendentes/bloqueados.
- A prévia de importação no modo API vem de `POST /importacoes/analisar`; a confirmação reclassifica as linhas no servidor.


## Entrada autenticada do frontend

A superfície de entrada existente (`SourceFallback` em `AppShell`) autentica por e-mail/senha no Supabase Auth com o SDK oficial. Não cria usuários nem decide permissões. Configuração pública: `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY` e `VITE_NFSE_API_URL`. Somente chave `sb_publishable_` é aceita; service role, chaves secretas e credenciais S3 nunca pertencem ao frontend.

Contratos já existentes, sem novas rotas ou payloads:

| Método | Endpoint | Uso |
|---|---|---|
| POST | /v1/auth/session | `Authorization: Bearer <access_token>`; cria cookie HttpOnly/Secure/SameSite=None; resposta 204 |
| GET | /v1/sessao | Lê usuário, papel, empresas e liberações autorizadas pelo backend; resposta 200 ou 401 |
| DELETE | /v1/auth/session | Exclui cookie; resposta 204; ausência de confirmação não é apresentada como saída concluída |

As chamadas ao serviço continuam exclusivamente em `src/lib/datasource.ts`, com `credentials: include`; mutações mantêm `X-Requested-With: nfse-imoveis`. O JWT é enviado como Bearer somente na troca de sessão. A UI não lê o cookie e não decodifica JWT para conceder autorização; usa o papel devolvido pelo backend, que preserva `app_metadata.papel` e desconsidera `user_metadata`.

Tokens do provedor não são persistidos no browser nem renovados em segundo plano neste incremento. Após a troca, o SDK encerra sua sessão local; a validade do access token no cookie continua limitada por `exp`, verificado pelo backend a cada requisição. Ao expirar, exige-se novo login. O logout da aplicação exclui esse cookie; não promete revogar todos os access tokens já emitidos em outros dispositivos.

401 limpa o contexto/cache e abre a entrada novamente. 403/404 usam mensagem genérica de acesso indisponível e retorno ao contexto autorizado; nenhuma resposta de erro ativa demo automaticamente. A demonstração segue explícita quando não há URL de API ou é escolhida deliberadamente após indisponibilidade. A seleção de empresa valida a lista de `/v1/sessao`; não concede membership. Preferências são separadas por usuário/modo, e caches são descartados ao trocar empresa, perder acesso ou sair.

HTTPS e origens permitidas no backend são requisitos de integração real; a política do cookie não foi relaxada. Bloqueio de cookies entre sites pelo navegador pode impedir a sessão: a UI permanece sem acesso, sem recorrer a Bearer em todas as chamadas ou armazenamento inseguro. O fluxo de entrada atual não usa o redirect legado `GET /v1/auth/login`; nenhuma nova rota `/login` foi criada.

Prova automatizada: `python tests/e2e/nfse_flow.py --auth`, em Linux. Usa API FastAPI e verificador JWT do produto com TLS/chaves, memberships, storage/repositório e provedor sintéticos de teste. Não comprova login numa conta Supabase hospedada nem persistência PostgreSQL nessa jornada; essa validação de ambiente continua separada.
