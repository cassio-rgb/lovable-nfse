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
- **Não conectado:** provedor de identidade (verificador e emissão do cookie `session`), storage privado durável (só `MemoryStorage`, de teste), cofre, processo/loop do worker e adaptador fiscal oficial (bloqueado). `app.main:app` recusa iniciar enquanto faltarem.
- A prévia de importação no modo API vem de `POST /importacoes/analisar`; a confirmação reclassifica as linhas no servidor.
