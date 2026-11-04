# BUILD REPORT: NFS-e Nacional para Gestoras de Imóveis

## Metadata

| Attribute | Value |
|---|---|
| Feature | LOVABLE NFSe — Gestoras de Imóveis |
| Date | 2026-11-04 |
| Author | Codex — consolidação documental baseada em código e evidências |
| Status | In Progress |
| Overall | IN PROGRESS |
| Branch | feat/supabase-infra |
| Baseline | 81af5478a7291ec3e8baa78a4d2c5c248fed6e9e — incremento autenticado sobre o fechamento documental; histórico de CI em 0c6cf49 preservado |
| Repository | cassio-rgb/lovable-nfse; aplicação em NFSE_Escritorio/ |
| Scope desta entrega | Integração autenticada frontend/backend, sem emissão fiscal real |

Fontes lidas integralmente na raiz Git (diretório pai desta aplicação): [Brainstorm](../BRAINSTORM_NFSE_GESTORAS_IMOVEIS.md), [Define](../DEFINE_NFSE_GESTORAS_IMOVEIS.md), [Governança](../GOVERNANCA_REVIEW_NFSE_GESTORAS_IMOVEIS.md), [UX Review](../UX_REVIEW_NFSE_GESTORAS_IMOVEIS.md) e [Design](../DESIGN_NFSE_GESTORAS_IMOVEIS.md). Considerados também AGENTS.md, adendo 004, relatórios históricos, código, migrations, testes, scripts e workflows reais. O DEFINE permanece Needs Clarification, o DESIGN permanece Draft e a UX Review permanece BLOCKED FOR DESIGN nos documentos originais; este relatório não modifica esses estados nem presume sua aprovação posterior.

## Mode Selection

Modo sequencial/default, sem delegação. O fechamento documental anterior permanece histórico; o incremento atual autoriza apenas a integração autenticada nos paths do manifesto remapeado, seus testes e este relatório. A infraestrutura já implementada é avaliada como incremento; a completude do produto é avaliada contra todo o manifesto de 47 itens e AT-001 a AT-013. A existência de um arquivo não comprova a entrega integral de seu propósito.

## Summary

A infraestrutura deste incremento está concluída no escopo validado: Supabase Auth, PostgreSQL, RLS, Storage privado e bootstrap seguro da API, com separação dos DSNs da API e do worker. O gate local passou em Linux/Docker; o workflow verify e os checks de Vercel passaram no commit de referência. Isso não conclui o produto exigido pelo Brainstorm/Define/Design.

A interface agora implementa login Supabase na superfície de entrada existente, troca de JWT pelo cookie do backend, leitura de /v1/sessao, contexto autorizado e logout/expiração. O E2E autenticado comprova essa integração com a FastAPI e seu verificador JWT, usando provedor e dados sintéticos. As provas de API e frontend de leitura com Supabase hospedado e PostgreSQL durável passaram após a correção pontual do contexto RLS. O isolamento hospedado com segunda empresa não foi executado por ausência de fixture segura; documentos e emissão fiscais reais continuam pendentes. A fonte demo continua explícita nos fluxos não integrados/configurados. A integração fiscal oficial, o cofre, os parâmetros fiscais duráveis e a homologação de Bariri/SP e Pederneiras/SP permanecem pendentes. Produção fiscal continua bloqueada/fail-closed.

O Brainstorm exige emissão oficial, importação e operação multiempresa segura como sucesso conjunto. O DEFINE exige transmissão e retornos oficiais, além da preparação local. O DESIGN adiciona recuperação de incerteza, contexto protegido, acessibilidade e operação durável. Testes simulados e infraestrutura verde atendem partes desse conjunto, sem substituir o smoke oficial.

## Task Execution

| Trabalho | Evidência | Situação |
|---|---|---|
| Domínio, revisão, idempotência e isolamento | backend/app/domain/, reviews.py, emissions.py, repository.py, pg.py; testes correspondentes | Implementados e testados no escopo interno |
| Identidade e sessão da API | backend/app/auth.py, api.py; tests/test_auth.py e test_api.py | Implementados; integração completa do login no frontend pendente |
| Storage privado | backend/app/documents.py, config.py, test_storage.py; adendo 004 | Implementado; bucket nfse-documentos privado confirmado no incremento |
| Bootstrap seguro | backend/app/main.py; test_main_bootstrap.py | API monta dependências duráveis; não carrega A1 nem inicia worker fiscal |
| Runtime segregado | worker.create_worker_repository; test_runtime_config.py | DSNs separados implementados; serviço contínuo do worker ainda não comprovado |
| RLS nas consultas de sessão | 0731650 e migration 20261103170433_add_rls_policies_core_access.sql | Contexto app.user_id e policies centrais implementados |
| Assinatura independente | 3e36851; tests/test_interop.py | Compatibilidade entre mensagens xmlsec1 corrigida, sem dispensar verificação |
| CLI e lockfile | 3a8d684; package.json e bun.lock | Supabase 3.0.0 resolvido pelo Bun; instalação congelada validada em Linux |
| Preservação dos XSDs | 0c6cf49; .gitattributes | Bytes originais preservados; hashes/MANIFEST não ajustados para mascarar falha |
| Relatório atual | Este arquivo | Consolidação documental; sem reexecução do produto nesta etapa |

### Incremento 2026-11-04 — integração autenticada (baseline 81af547)

Antes de editar, foram identificados e apresentados os itens #1, #3, #4, #11, #17/#30, #34/#37 e #42/#43. A adaptação de paths segue o scaffold já mapeado neste relatório. Alterações reais: package.json/bun.lock (#1), datasource.ts (#3), CompanyContext.tsx (#4), AppShell.tsx (#11), tests/e2e/nfse_flow.py (#37), config/env.example (#42), docs/api-contract.md (#43) e este relatório, solicitado explicitamente. #17/#30 e os testes de #34 foram inspecionados/executados, sem mudança de backend.

Implementado e verificado neste recorte:

- SDK oficial @supabase/supabase-js 2.118.0, versão exata e bun.lock atualizado; sem package-lock.json. Importação dinâmica no login, sem inicializar autenticação compartilhada no SSR.
- Entrada por e-mail/senha na superfície SourceFallback existente. Nenhuma nova rota /login nem novo endpoint, schema ou payload. O redirect legado /v1/auth/login não é usado por esse fluxo.
- POST /v1/auth/session recebe Bearer somente na troca; GET /v1/sessao e as chamadas normais usam credentials/include. DELETE /v1/auth/session confirma logout. Cookie HttpOnly/Secure/SameSite=None preservado pelo backend inalterado.
- UI obtém usuário, papel, empresas e liberações da resposta do backend. Nenhuma autorização por JWT decodificado ou user_metadata; app_metadata.papel continua verificado no servidor. RLS e app.user_id não foram alterados.
- Preferência de empresa separada por usuário/modo e validada contra memberships recebidas. Cancelamento/limpeza de caches, barreira antes de renderizar outra sessão e remontagem das telas ao mudar usuário/empresa evitam reutilização do contexto anterior.
- 401 remove contexto e pede login; 403/404 exibem negação genérica com recuperação. Loading e indisponibilidade têm estados explícitos; nenhuma falha ativa demo automaticamente. Logout sem confirmação mantém dados ocultos e oferece repetir a saída.
- Tokens do provedor somente em memória, sem auto-refresh/persistência. Após a troca o SDK encerra sua sessão local; o JWT no cookie continua sujeito a exp, validado pelo backend. Expiração exige novo login. Não se promete revogação global de todos os tokens/dispositivos.

**Itens concluídos neste recorte:** cliente de sessão autenticada de #3; obtenção de identidade/memberships e propagação de contexto em #4; entrada/logout/estados em #11; prova autenticada local de #37; configuração pública/documentação em #42/#43. Isso não conclui os propósitos integrais de #4/#11/#37 ou os ATs fiscais e a UX Review.

Limite da evidência: o E2E usa navegador Chromium e API FastAPI reais em HTTPS, SupabaseIdentityVerifier com assinatura/iss/aud/exp reais e JWKS sintético injetado. Provedor Supabase, chaves TLS/JWT, memberships e armazenamento são fixtures locais (APP_ENV=test). Não há conta Supabase hospedada nem PostgreSQL real nessa jornada. Não houve alteração de API/schema/arquitetura fora do Design, emissão fiscal, certificado A1 ou acesso ao Storage de documentos. O único certificado criado pelo teste é TLS sintético temporário.

### File Manifest do Design — 47 itens

Legenda: **Implementado** significa propósito interno comprovado por código/testes disponíveis; não implica homologação fiscal. **Parcial** indica escopo ou prova ainda incompletos. **Fora deste incremento** preserva o trabalho previsto, sem removê-lo do Design. Caminhos abaixo são relativos à aplicação, salvo indicação da raiz Git.

| # | Arquivo previsto → caminho real / evidência | Situação e limite |
|---:|---|---|
| 1 | web/package.json → package.json + bun.lock | Implementado: scaffold Lovable/TanStack, scripts e dependências |
| 2 | web/src/lib/contracts.ts → src/lib/contracts.ts, domain.ts | Implementado: contratos e centavos inteiros; espelho Decimal no backend |
| 3 | web/src/lib/api.ts → src/lib/datasource.ts, confirm.ts | Implementado no recorte autenticado: login, troca/logout, cookie e erros; E2E FastAPI com provedor sintético PASS. Validação no ambiente hospedado continua pendente |
| 4 | CompanyContext.tsx → src/components/CompanyContext.tsx | Parcial: contexto autenticado, memberships, troca, expiração e limpeza de cache com E2E local PASS; prova hospedada e cobertura integral de M03 pendentes |
| 5 | StatusPanel.tsx → src/components/StatusPanel.tsx | Parcial: estados e mensagens existem; auditoria acessível e retornos oficiais pendentes |
| 6 | DraftForm.tsx → src/components/DraftForm.tsx | Parcial: formulário e revisão demonstrados; jornada completa com API real pendente |
| 7 | ImportPreview.tsx → src/components/ImportPreview.tsx | Parcial: prévia e confirmação; persistência integral do lote/original e prova integrada pendentes |
| 8 | ReviewPanel.tsx → src/routes/revisao.$id.tsx | Parcial: revisão e confirmação implementadas em rota equivalente; transmissão oficial bloqueada |
| 9 | DocumentResult.tsx → src/routes/operacao.$id.tsx, historico.tsx | Parcial: resultado simulado e link autorizado existem; documento oficial/download integrado não demonstrados |
| 10 | AccessDenied.tsx → src/components/AccessDenied.tsx | Implementado no escopo local: mensagem genérica e retorno; negação também testada na API |
| 11 | NfseWorkspace.tsx → src/components/AppShell.tsx + src/routes/ | Parcial: entrada autenticada e logout integrados na superfície existente, sem nova rota; jornada hospedada e restante do produto pendentes |
| 12 | web/src/styles/nfse.css → src/styles.css | Parcial: estilos/tokens responsivos presentes; contraste e tarefa móvel completa sem prova |
| 13 | backend/pyproject.toml | Implementado: dependências e descoberta de pacotes app* |
| 14 | backend/app/config.py | Implementado: validação e DSNs segregados; ausência de configuração não vira fallback fiscal |
| 15 | backend/app/domain/models.py | Implementado: Decimal, estados e invariantes testados |
| 16 | backend/app/domain/transitions.py | Implementado: transições e conflitos internos testados |
| 17 | backend/app/auth.py | Implementado no backend: JWT/JWKS, issuer/audience/exp e papel confiável; frontend integrado ainda pendente |
| 18 | backend/db/001_initial.sql | Implementado como schema operacional; modelo completo de lotes/fontes do Design ainda não demonstrado |
| 19 | backend/db/002_isolation.sql + supabase/migrations/20261103170433_add_rls_policies_core_access.sql | Implementado: roles, RLS e isolamento; não equivale a auditoria integral de governança |
| 20 | backend/app/repository.py + backend/app/pg.py | Implementado: contrato Tx e persistência durável; memória somente teste |
| 21 | backend/app/imports.py | Parcial: CSV/XLSX, prévia e idempotência implementados; lote/prévia/original persistidos conforme todo o Design sem comprovação integral |
| 22 | backend/app/reviews.py | Implementado: revisão vinculada a versão/hash e invalidação |
| 23 | backend/app/eligibility.py | Implementado como bloqueio/liberação contextual; liberações reais dos pilotos pendentes |
| 24 | backend/app/ports.py | Implementado como contratos; cofre e FiscalParameters ainda sem adaptadores duráveis completos |
| 25 | backend/app/documents.py | Implementado como adaptador privado com integridade/autorização; ciclo documental fiscal completo pendente |
| 26 | backend/app/nfse/client.py | Parcial: allowlist/transporte e bloqueio; submit/lookup oficiais não implementados para operar |
| 27 | backend/app/nfse/xml.py + dps.py, signing.py, secure_xml.py, offline.py, schemas/ | Parcial: XML/assinatura offline e XSD testados; perfil aprovado e spike completo pendentes |
| 28 | backend/app/emissions.py | Implementado no escopo interno: comando atômico, identidade, revisão e idempotência testados |
| 29 | backend/app/worker.py | Parcial: claim, lease, fence, recuperação e DSN próprio; loop/entrypoint operacional e fiscal real pendentes |
| 30 | backend/app/api.py + main.py | Implementado: endpoints e bootstrap com infraestrutura durável; não demonstra jornada browser/API real completa |
| 31 | backend/app/observability.py | Parcial: logs UTC e correlação/redação; métricas, alertas, destinos e trilha forense completa não comprovados |
| 32 | backend/tests/test_domain.py | Implementado: testes locais do domínio |
| 33 | backend/tests/test_imports.py + test_pg.py | Implementado para casos internos existentes; não comprova preservação integral da origem |
| 34 | backend/tests/test_isolation.py + test_api.py, test_pg.py | Implementado para isolamento/revogação internos; não encerra G13 integralmente |
| 35 | backend/tests/test_emissions.py + test_pg.py | Implementado para resposta perdida, crash/fence e concorrência simulados; smoke externo separado |
| 36 | backend/tests/test_contract.py + test_interop.py | Parcial: contratos XML e assinatura offline cobertos; interpretação do HTTP oficial sem fixture validada |
| 37 | tests/e2e/nfse.spec.ts → tests/e2e/nfse_flow.py | Parcial: jornada demo e modo --auth passaram; autenticação/JWT/cookie/isolamento/erros locais cobertos, sem provar Supabase hospedado/PG durável nem M01–M05 integrais |
| 38 | tests/e2e/accessibility.spec.ts | Fora deste incremento: arquivo ausente; auditoria completa de teclado/foco/contraste/mobile não demonstrada |
| 39 | scripts/verify.py | Parcial: local e postgres executáveis; restricted falha fechado e smoke oficial ainda não implementado |
| 40 | deploy/backend.Dockerfile | Parcial: artefato existe; empacotamento/execução completos não validados; comentário referencia worker_main inexistente |
| 41 | deploy/compose.test.yml | Parcial: define db/API, sem serviço worker e sem prova do conjunto isolado previsto; não confundir com contêiner do gate |
| 42 | config/env.example | Implementado como documentação de configuração sem credenciais operacionais |
| 43 | docs/api-contract.md | Implementado no recorte interno: seção de bootstrap corrigida e contratos de sessão existentes documentados; sem novo contrato HTTP |
| 44 | docs/nfse-integration-evidence.md | Parcial: evidências offline e bloqueios registrados; spike/smoke oficiais pendentes |
| 45 | docs/runbook.md | Parcial: procedimentos existem; bootstrap descrito está desatualizado e restauração/alertas sem comprovação |
| 46 | docs/pilot-checklist.md | Parcial: checklist criado, itens dos dois municípios não preenchidos com provas oficiais |
| 47 | .github/workflows/verify.yml → ../.github/workflows/verify.yml (raiz Git) | Implementado para CI local/identity/storage; cópia dentro da aplicação é antiga e não é o workflow efetivo |

Itens adicionais rastreados pelos adendos: certificado/delegação A1 offline (001); lançador local em loopback (002); catálogos fiscais e campos de seleção explícita (003); Auth/Storage/runtime/bootstrap (004). Esses incrementos não eliminam as pendências do manifesto original.

## Files Changed

Neste recorte de correção: backend/app/api.py (ordem de contexto), backend/tests/test_api.py (regressão de autorização/contexto) e este BUILD_REPORT. As nove mudanças locais anteriores foram preservadas. Nenhum frontend de produto foi modificado nesta correção.

No fechamento documental anterior foi criado somente este relatório. No incremento autenticado atual foram alterados exatamente nove paths: package.json, bun.lock, src/lib/datasource.ts, src/components/CompanyContext.tsx, src/components/AppShell.tsx, tests/e2e/nfse_flow.py, config/env.example, docs/api-contract.md e BUILD_REPORT_NFSE_GESTORAS_IMOVEIS.md. Backend de produto, schema, RLS, XSDs, hashes, MANIFEST e cliente fiscal permaneceram intactos. Existe também relatório homônimo na raiz Git; este novo relatório fica deliberadamente em NFSE_Escritorio/, conforme o repositório de trabalho solicitado, sem sobrescrever o histórico externo.

Mudanças históricas relevantes já commitadas, apenas documentadas aqui:

| Commit | Conteúdo |
|---|---|
| 0731650 | Propagação de contexto RLS nas consultas de sessão |
| 3e36851 | Compatibilidade das mensagens do xmlsec1 entre versões |
| 3a8d684 | CLI Supabase, bun.lock, policies centrais e ignores |
| 0c6cf49 | .gitattributes com *.xsd -text e preservação dos bytes originais dos 20 XSDs |

O diff de 0c6cf49 mostra alterações de finais de linha; não representa autorização para editar regras dos esquemas. O SHA-256 staged de CNC_v1.00.xsd informado na correção foi 7032188bb6f137d52b16512583b739a361e6b1434c42cb539a29b8efa32f8321. Nenhum hash foi recalculado ou substituído nesta etapa.

## Drift Detected

1. Caminhos web/ propostos foram adaptados ao scaffold: datasource.ts substitui api.ts; revisão e resultado são rotas; E2E é Python/Playwright. Adaptação de organização, não dispensa funcional.
2. DEFINE mantém comando smoke indefinido e DESIGN mantém Draft. scripts/verify.py concretiza o gate local; isso não atualiza formalmente o aceite fiscal do DEFINE.
3. BUILD_REPORT.md e docs/runbook.md ainda contêm descrições antigas de ausência de infraestrutura/recusa do bootstrap. docs/api-contract.md foi atualizado no incremento autenticado, no path #43 previsto. As fontes históricas restantes não foram alteradas.
4. Workflow efetivo está na raiz Git; a cópia NFSE_Escritorio/.github/workflows/verify.yml é desatualizada e não define os jobs identity/storage atuais.
5. Worker separado significa segregação de código, DSN e responsabilidade comprovada; ainda não significa serviço contínuo implantado. worker_main.py está ausente.
6. Modelo de importação integral, observabilidade operacional e suíte de acessibilidade estão aquém do propósito completo do Design.

## Verification Results

Evidências históricas são registradas com origem, sem apresentá-las como reexecução em 04/11. Isso descreve o fechamento documental anterior. O incremento autenticado executou os checks locais abaixo; não executou novo GitHub Actions nem deploy.

### Correção pontual do contexto RLS em allow() — 2026-11-04

**Escopo e compatibilidade:** execução sequencial/default sobre HEAD 81af547. Em backend/app/api.py, current_user_id.set(p.user_id) passa a ocorrer imediatamente após principal(request), antes de members.require. Segue o padrão de /v1/sessao e dos adaptadores PgDatabase/PG transacionais existentes (PostgresRepository.tx no código atual). Nenhum contrato HTTP, schema, policy, migration, frontend ou cliente fiscal foi alterado neste recorte. app_metadata.papel continua sendo a fonte do papel.

**ContextVar:** handlers síncronos executam no contexto copiado pelo AnyIO; handlers assíncronos têm contexto da task da requisição. Os adaptadores PostgreSQL aplicam set_config com is_local=true e fecham a conexão ao final. A revisão não identificou risco material que justifique uma solução arquitetural maior. A regressão alterna usuários/empresas, testa negações e logout e confirma que o contexto do chamador permanece intacto. Não se afirma que esse teste sozinho prove toda situação possível de concorrência.

**Regressão reproduzida:** antes da correção, tests.test_api.RlsAuthorization falhou na primeira leitura autorizada: a consulta recebeu caller-context em vez de u1. Depois da correção passou, com consulta de membership verificando a identidade antes de autorizar. O roteiro usa POST /v1/auth/session para criar o cookie real do contrato e comprovar sua remoção no logout.

| Verificação executada neste recorte | Resultado |
|---|---|
| Auth, API, isolamento, configuração segregada e bootstrap | 36 testes PASS |
| Autorização de empresa A/B, alternância de usuários e revogação | PASS; empresa autorizada 200, sem membership/permissão 404 genérico, conforme M05 |
| Sessão ausente/encerrada e proteção CSRF | PASS; 401 sem sessão e 403 para mutação sem Origin/header, preservando contratos |
| Verify Gate Linux/Docker: python scripts/verify.py --mode local | PASS: 145 Python, 23 Vitest, typecheck, build e E2E |
| E2E autenticado adicional: python tests/e2e/nfse_flow.py --auth | PASS: login sintético/JWT, loading/503, cookie, reload, memberships, rascunho, 401/403, revogação e logout |

A execução canônica do gate ocorreu em nfse-verify-20261103, com Bash e xmlsec1 disponíveis. Não há novo resultado de GitHub Actions para estas mudanças não commitadas. O E2E padrão usa emissão simulada; nenhuma emissão fiscal real ocorreu.

**Prova hospedada após a correção:** Auth PASS; cookie/API PASS; PostgreSQL durável PASS; RLS/membership PASS; logout PASS. Login PostgreSQL efetivo da API: nfse_api_login; worker: nfse_worker_login (somente conectividade). Ambos sem superuser/bypassrls. /v1/sessao confirmou usuário 802954e5-87c3-478f-883c-53029c061f57, papel escritorio e empresa 5a94b88b-458d-4b20-90ec-cac7c28eec24. Cookie HttpOnly/Secure/SameSite=None confirmado. Duas leituras protegidas de rascunhos retornaram 200; segunda leitura de sessão preservou o resultado. DELETE /v1/auth/session retornou 204 e leituras de sessão/rascunhos posteriores retornaram 401. A sessão Auth usada nessa prova API foi encerrada com scope=local.

Isolamento hospedado contra segunda empresa: INCONCLUSIVE, por ausência de fixture hospedada segura; nenhuma empresa/membership foi criada. O isolamento entre empresas tem cobertura local, sem substituir essa lacuna hospedada.

O primeiro roteiro de frontend deste recorte parou por buscar um combobox inexistente na apresentação de empresa única, que usa texto no cabeçalho. Isso é uma falha do roteiro, não evidência de defeito no produto. A repetição com localização correta passou: login pelo SDK contra Supabase hospedado, empresa autorizada e ativa no cabeçalho, GET protegido de rascunhos 200 observado pelo navegador, reload, logout pela UI e GET /v1/sessao 401 após a saída. Chromium confiou somente na chave do certificado TLS local efêmero; o TLS do Supabase continuou validado normalmente. Loading/503 e demais estados negativos foram comprovados pelo E2E sintético adicional, sem alegar nova indução de falha no serviço hospedado.

| Classificação final desta repetição | Resultado |
|---|---|
| Auth hospedado | PASS |
| Cookie/API | PASS |
| PostgreSQL durável | PASS |
| RLS/membership | PASS |
| Isolamento contra segunda empresa hospedada | INCONCLUSIVE — ausência de fixture segura |
| Logout | PASS |
| Frontend hospedado no fluxo de leitura deste incremento | PASS |

**Prontidão:** o incremento autenticado está pronto para revisão do diff e commit autorizado no seu recorte, com a limitação de isolamento hospedado acima declarada. Não é conclusão de todo o produto nem autorização de produção. Nenhum commit foi criado.

Configuração e credenciais foram lidas dos arquivos locais ignorados e mantidas em memória; nenhuma senha, DSN, chave ou token foi registrado. A API local TLS usou o bootstrap durável real na porta 8001, produção desabilitada e apenas leituras de dados. Nenhum upload, job, worker fiscal, submit ou lookup foi executado. O auxiliar ignorado de validação não integra o produto nem o diff versionável.

Os registros abaixo são históricos; a falha de ordem de contexto neles descrita foi corrigida e sua leitura protegida foi validada neste recorte. O Build geral permanece **IN PROGRESS**.

### Validação HTTP real com Storage configurado — 2026-11-04

Rodada posterior às evidências abaixo. Usados .env.homologacao.local e o arquivo externo nfse-s3.txt indicado pelo operador, somente em memória. Os dois campos STORAGE_S3_ACCESS_KEY_ID e STORAGE_S3_SECRET_ACCESS_KEY foram extraídos de rótulos inequívocos; nenhum valor foi exibido, copiado para logs ou versionado. Endpoint, região e bucket não secretos foram fornecidos pelo operador. Arquivos de credenciais e código não foram alterados.

Bootstrap real app.main:app: **PASS**, com PostgreSQL/Auth/Storage duráveis configurados. Apenas a API foi iniciada em 127.0.0.1:8001, com TLS local temporário para preservar o cookie Secure. O cliente S3 foi apenas inicializado; nenhum objeto foi lido, enviado ou alterado. A origem local foi configurada somente na memória desse processo, sem alteração de arquivo. NFSE_PRODUCTION_ENABLED=false e produção restrita foram conferidos. Worker e jobs não foram iniciados.

| Prova | Resultado | Evidência efetivamente executada |
|---|---|---|
| Auth hospedado | PASS | Novo login protegido; verificação real de assinatura/exp/iss/aud/sub e app_metadata.papel pelo SupabaseIdentityVerifier. Usuário esperado confirmado; sem service_role ou autorização por user_metadata |
| Cookie/API | PASS — endpoints de sessão | POST /v1/auth/session → 204; Set-Cookie confirmado HttpOnly=true, Secure=true, SameSite=None. GET /v1/sessao → 200, usuario/papel/empresa esperados. Segunda chamada com o mesmo cookie → 200 e mesmo conteúdo |
| PostgreSQL durável | PASS | API montada com as dependências reais de app.main e DATABASE_URL hospedada. Usuário e empresa retornados pela API real; logins segregados/TLS já comprovados na rodada anterior, sem credencial privilegiada ou memória substituta |
| RLS/membership | FAIL na integração de leitura protegida; políticas diretas PASS | GET /v1/empresas/5a94b88b-458d-4b20-90ec-cac7c28eec24/rascunhos → 404 para o usuário autorizado. Consulta read-only confirmou vínculo ativo e permissão ler. A ordem de aplicação de app.user_id em allow() está incorreta, conforme reprodução descrita abaixo |
| Isolamento contra segunda empresa | INCONCLUSIVE | Sem fixture hospedada segura confirmada; não foram criadas/alteradas empresas ou memberships. A negação de dados sem contexto permanece comprovada pelas leituras anteriores |
| Logout | PASS — API | DELETE /v1/auth/session → 204; chamada posterior GET /v1/sessao → 401. Sessão Auth própria do teste também encerrada com scope=local, HTTP 204, sem logout global |
| Frontend hospedado | INCONCLUSIVE — jornada completa não aprovada | Navegador usando Supabase hospedado e API local real realizou troca 204 e /v1/sessao 200; o roteiro interrompeu na verificação de empresa antes de comprovar reload/logout completos. Erro do roteiro/ambiente não foi tratado como defeito comprovado da UI. Há, independentemente, o 404 funcional confirmado no endpoint protegido |

Confirmação da resposta HTTP de /v1/sessao: usuario=802954e5-87c3-478f-883c-53029c061f57; papel=escritorio; lista autorizada contém empresa=5a94b88b-458d-4b20-90ec-cac7c28eec24. Apenas correspondências booleanas foram impressas durante a prova; token, DSN, senha, chaves e demais dados da resposta não foram expostos.

**Falha funcional nova, reproduzida sem alteração de código/dados:**

1. A leitura protegida de rascunhos retorna 404, apesar de /v1/sessao listar a empresa autorizada.
2. Com nfse_api_login e transação READ ONLY, a membership esperada existe, revoked_at é nulo e permissions contém ler.
3. PgMemberships.require executado com current_user_id ausente recusa esse mesmo vínculo; com current_user_id esperado, autoriza.
4. backend/app/api.py, função allow(), chama members.require antes de current_user_id.set(p.user_id). Como PgMemberships._q define app.user_id a partir desse contexto, a primeira consulta de autorização ocorre sem identidade visível ao RLS.

Conclusão: as políticas RLS estão protegendo os dados corretamente; existe uma falha de propagação de contexto no backend nas rotas que usam allow(). A correção precisa preceder a aprovação da navegação autenticada completa. Não foi feita nesta etapa, que proíbe alterar código. A prova passou a distinguir explicitamente sessão/autenticação de acesso autorizado aos dados; o 404 não foi ocultado para obter PASS geral.

Limites do frontend: o primeiro roteiro em Chromium interrompeu na etapa de verificação da empresa e não comprova o fluxo completo. Foram preservadas somente as evidências observadas (401 inicial, troca de sessão 204 e /v1/sessao 200), sem promover login/empresa ativa/reload/logout/estados a PASS integral. O endpoint protegido já tem falha real independente do roteiro; não se prosseguiu para ações fiscais nem para alteração de produto.

Encerramento: API local parada e grupo de processos frontend desta prova encerrado após identificação de cwd/porta/URL de teste. Certificado TLS sintético temporário limpo; não se usou certificado A1. Nenhuma chamada a NationalNfseClient.submit/lookup, nenhuma emissão, job, upload, DDL/DML de correção ou alteração de usuário/app_metadata/membership/RLS ocorreu. Somente a sessão Auth criada pelo teste foi encerrada com escopo local.

**Prontidão para commit como incremento homologado: pendente.** Auth, sessão, cookie, PostgreSQL e logout reais passaram, mas a falha de contexto nas leituras protegidas impede aprovar a integração completa. Próxima ação segura: obter autorização explícita para corrigir pontualmente allow(), adicionar prova de regressão com RLS efetivo e repetir leitura protegida/frontend. Não modificar policies, usuários ou dados para mascarar o erro. **Build geral: IN PROGRESS.** Sem commit/push/merge/alteração de PR.

### Validação hospedada com configuração local — 2026-11-04

Nova rodada, posterior ao registro inconclusivo abaixo. HEAD 81af547 e as nove mudanças locais anteriores preservados. `.env.homologacao.local` foi confirmado como ignorado pela regra `*.local`, lido somente na memória dos processos e não alterado/versionado. Nenhum valor do arquivo, senha, token completo, DSN ou chave foi exibido nos logs. A senha foi fornecida pelo operador na entrada protegida do Windows; não foi solicitada no chat nem persistida.

| Prova | Resultado | Evidência efetivamente executada |
|---|---|---|
| Auth hospedado | PASS | Login real usando apenas publishable key no projeto nxgdpfhhhplnifzatneb. SupabaseIdentityVerifier do produto verificou assinatura e exp por JWKS real; iss esperado, aud=authenticated, sub=802954e5-87c3-478f-883c-53029c061f57, app_metadata.papel=escritorio e papel normalizado=escritorio confirmados. user_metadata não foi usado para autorizar |
| Cookie/API | INCONCLUSIVE | Bootstrap existente app.main tentado, mas config.load recusou iniciar pela ausência das cinco variáveis STORAGE_* obrigatórias. POST /v1/auth/session, Set-Cookie e GET /v1/sessao não foram executados contra a configuração hospedada; nenhum substituto fictício foi usado |
| PostgreSQL durável | PASS | Conexões reais ao projeto esperado pela configuração, TLS ativo, DATABASE_URL com current_user=session_user=nfse_api_login; WORKER_DATABASE_URL com current_user=session_user=nfse_worker_login. Nenhum login é superuser/BYPASSRLS; ambos pertencem aos respectivos papéis segregados |
| RLS/membership | PASS — leitura direta/adaptadores | RLS habilitado e row_security_active=true para company, membership e operation_release no login nfse_api_login, que não é dono dessas tabelas. Sem contexto: zero empresas; com app.user_id esperado: membership ativa e empresa 5a94b88b-458d-4b20-90ec-cac7c28eec24 visíveis, somente essa empresa retornada; removendo contexto: zero empresas novamente |
| Isolamento | INCONCLUSIVE — segunda empresa | Negação sem contexto comprovada, mas nenhuma segunda empresa fora da membership foi confirmada como fixture segura. Não se usou conta privilegiada para descobrir dados ocultos, nem se criou empresa/membership |
| Logout | INCONCLUSIVE — cookie da API | Sem API iniciada, DELETE /v1/auth/session e 401 posterior não foram executados. Separadamente, a sessão Supabase Auth criada para o teste foi encerrada com HTTP 204 e scope=local; isso não substitui a prova do logout da API e não fez logout global |
| Frontend hospedado | INCONCLUSIVE | Sem backend real inicializado, não foi concluído login/empresa ativa/reload/logout/loading/erro da UI contra a cadeia hospedada. As provas sintéticas anteriores não foram promovidas a PASS hospedado |

Detalhes da execução e limites:

- API: login efetivo **nfse_api_login**, membro de nfse_api, sem superuser e sem BYPASSRLS. Worker: login efetivo **nfse_worker_login**, membro de nfse_worker, sem superuser e sem BYPASSRLS. A prova do worker se limitou à conexão e SELECT de identidade/permissões; nenhum processamento ou job foi iniciado.
- As provas de conexão/RLS usaram transações explicitamente READ ONLY, confirmado no servidor. Uma tentativa inicial com opção de conexão não tornou read_only efetivo; isso foi corrigido no procedimento de teste com BEGIN READ ONLY explícito, sem mudar configuração ou dados do banco. Mesmo a tentativa inicial só executou SELECTs de diagnóstico.
- Além das consultas diretas, os métodos reais PgMemberships.empresas, PgCompanies.get e PgReleases.for_company foram executados com current_user_id esperado. Membership, empresa e leitura de liberações foram confirmadas pelo PostgreSQL hospedado, sem MemoryRepository. Os adaptadores abrem as transações padrão do produto, mas nesta prova foram chamados somente seus métodos de leitura; nenhum DDL/DML foi executado.
- A propagação de app.user_id foi comprovada nas transações e nos adaptadores usados pelo produto. **Não foi comprovada via requisição HTTP nesta rodada**, pois a FastAPI não subiu. `/v1/sessao` não retornou resposta nesta validação: usuário confirmado por Auth e empresa por SQL/adaptadores não equivalem a confirmar a serialização HTTP.
- Valores ausentes exigidos por backend/app/config.py: STORAGE_S3_ENDPOINT, STORAGE_S3_REGION, STORAGE_S3_ACCESS_KEY_ID, STORAGE_S3_SECRET_ACCESS_KEY e STORAGE_CONTAINER. Os nomes foram informados, nunca valores. Não foram inventadas credenciais, relaxadas guardas, usados adaptadores fictícios ou alterado o arquivo protegido. Foi solicitada apenas a indicação de outra configuração local segura já existente.
- NFSE_PRODUCTION_ENABLED=false foi conferido no processo; ambiente esperado de produção restrita preservado. Nenhuma chamada a NationalNfseClient.submit/lookup, tentativa de emissão fiscal, alteração de dados, RLS, usuários, app_metadata, memberships ou XSD/MANIFEST ocorreu. Não foi usado service_role, postgres ou outro superuser.
- A única sessão Auth real criada nesta rodada foi encerrada com escopo local e seu token descartado da memória ao fim do processo. Não se alteraram outras sessões da conta. O teste de cookie/API ainda é uma pendência distinta.

**Prontidão para commit:** evidências locais e Auth/PG/RLS reais agora disponíveis; validação integrada de cookie/API e frontend ainda incompleta por configuração de Storage ausente. Não encerrar o incremento como homologado integralmente nem declarar Build completo. Próxima ação segura: fornecer por mecanismo local seguro adicional a configuração de Storage já existente, sem publicar valores e sem alterar código ou o arquivo protegido, e repetir as provas HTTP/frontend.

**Build geral: IN PROGRESS.** Nesta rodada somente este relatório foi atualizado; nenhuma mudança de produto, commit, push, merge, PR ou produção foi realizada.

### Validação hospedada de homologação — 2026-11-04

Etapa somente de inspeção e provas de autenticação/leitura. HEAD conferido: 81af547; as nove mudanças locais do incremento anterior foram preservadas. Nenhum código, banco, usuário, app_metadata, empresa, membership, RLS, schema, XSD, hash ou MANIFEST foi alterado nesta etapa. Não houve emissão fiscal, deploy, alteração de PR, commit ou push.

Projeto solicitado: nxgdpfhhhplnifzatneb. Issuer esperado: https://nxgdpfhhhplnifzatneb.supabase.co/auth/v1. Usuário e empresa informados pelo solicitante, **não confirmados por consulta hospedada nesta etapa**: 802954e5-87c3-478f-883c-53029c061f57 e 5a94b88b-458d-4b20-90ec-cac7c28eec24. Papel esperado: escritorio em app_metadata.papel. Configuração fiscal requerida: producao_restrita, produção desabilitada; não se afirma ter verificado runtime remoto sem acesso.

Evidências novas efetivamente obtidas:

- GET HTTPS do JWKS público do projeto, `/auth/v1/.well-known/jwks.json`: HTTP 200, um JWK ES256, validação TLS normal. Não foram impressos tokens, credenciais nem conteúdo das chaves. Isso comprova disponibilidade pública, não autenticação ou claims de usuário.
- Inventário dos nomes de variáveis nos processos PowerShell/Python, ambientes persistidos de usuário/máquina e contêiner nfse-verify-20261103: nenhuma variável pertinente de credencial/DSN disponível nesses locais. Busca direcionada de configuração no projeto/diretório pai, backend/config/.nfse-local encontrou apenas config/env.example, sem .env operacional utilizável. Valores sensíveis não foram impressos. A ausência é limitada aos locais inspecionados, sem presumir ausência em outros cofres externos.
- Nenhum listener de backend NFSe identificado nas portas locais verificadas no host (8000/8001/8080/8081/8443/8444). O contêiner de verificação anterior não tem variáveis de credenciais hospedadas e não foi apresentado como backend hospedado.
- Consulta opcional de metadados pelo conector Supabase sem evidência utilizável. Não se consultou SQL administrativo/service role/conta postgres para contornar a falta de credenciais segregadas.

| Prova obrigatória | Resultado | Evidência / impedimento |
|---|---|---|
| Auth hospedado | INCONCLUSIVE | Sem credencial utilizável do usuário existente. Nenhum token real obtido; iss/aud/exp/sub/app_metadata.papel não validados em JWT hospedado. JWKS 200 é apenas evidência complementar |
| Cookie/API | INCONCLUSIVE | Sem token real nem configuração utilizável do backend. POST /v1/auth/session e GET /v1/sessao não executados com o projeto hospedado |
| PostgreSQL durável | INCONCLUSIVE | DSNs segregados indisponíveis nos locais inspecionados. Não houve conexão ao banco hospedado nem prova da origem dos dados da API |
| RLS/membership | INCONCLUSIVE | Nenhuma consulta hospedada com nfse_api/contexto app.user_id; membership/revoked_at/empresa informados permanecem sem confirmação nesta etapa |
| Isolamento | INCONCLUSIVE | Não executado por ausência de fixture hospedada segura confirmada e de sessão/conexão para identificá-la. Não se afirma que inexista outra empresa; nenhuma foi criada/alterada |
| Logout | INCONCLUSIVE | Nenhuma sessão hospedada de teste aberta; DELETE /v1/auth/session e 401 posterior não executados com token real. Nenhuma outra sessão invalidada |
| Frontend hospedado | INCONCLUSIVE | Login, empresa ativa, reload, logout e loading/erro contra Supabase/PG reais não executados sem credenciais/configuração. O E2E sintético anterior não foi convertido em PASS hospedado |

Aplicada a parada somente às provas dependentes de credencial ausente. Não foram solicitados secrets no terminal/chat, inventadas credenciais ou tentadas senhas. Nenhum privilégio que burle RLS foi usado. Falta de credencial é bloqueio de ambiente, sem demonstrar falha funcional.

**Prontidão para commit:** implementação e evidências locais anteriores preservadas, mas a homologação hospedada solicitada permanece inconclusiva. Não fechar/commitar como integração hospedada validada antes de executar essas provas. **Build geral: IN PROGRESS**, sem mudança de status.

Próxima ação segura: disponibilizar a configuração existente de homologação ao processo por mecanismo local seguro, sem colar valores no terminal/log/chat; então repetir A–F em leitura/sessão, com credencial do usuário de teste, publishable key e DSNs segregados. Produção e transmissão fiscal permanecem bloqueadas.

### Evidências executadas no incremento autenticado

| Comando / check (Linux/Docker) | Resultado | Evidência local |
|---|---|---|
| python -m unittest tests.test_auth tests.test_api tests.test_isolation tests.test_runtime_config tests.test_main_bootstrap -v (cwd backend) | PASS — 35 testes | .nfse-local/verify/auth-unit-api.log |
| bunx tsc --noEmit | PASS — após implementação e após redução de diff de formatação | Saída do terminal, exit 0 |
| bunx vitest run | PASS — 23 testes / 6 arquivos | .nfse-local/verify/auth-vitest.log |
| python tests/e2e/nfse_flow.py --auth | PASS | .nfse-local/verify/auth-e2e-final.log |
| python scripts/verify.py --mode local | PASS — Python/API 144, Vitest 23, typecheck, build e E2E demo | .nfse-local/verify/auth-gate-local.log |
| bun install --frozen-lockfile --no-progress | PASS, sem mudanças | Terminal Linux; 612 pacotes no lockfile |
| ESLint nos três arquivos frontend alterados | 0 erros; 1 warning react-refresh/only-export-components | .nfse-local/verify/auth-eslint.log; arquivo já reúne hook/contexto e componente |

O E2E --auth comprova: loading, indisponibilidade 503 sem demo automática, credencial inválida, login SDK, cookie seguro e inacessível ao JavaScript, ausência de token/refresh token persistido, recarga, preferência de empresa forjada recusada, listagem e seleção autorizadas, rascunho criado via UI só em B, empresa C sem membership recusada, JWT temporalmente expirado → 401, 403 explícito → UI genérica, revogação com cookie existente, falha de logout sem falso sucesso, logout confirmado e segundo usuário sem acesso à empresa anterior. Papel cliente prevalece mesmo com user_metadata.papel forjado. Não houve requisição de confirmação/transmissão/verificação fiscal.

O gate padrão continua contendo E2E demo; --auth é check adicional explícito documentado, não foi incluído silenciosamente na matriz do workflow. Os 23 Vitest são a regressão existente; os cenários novos deste recorte foram adicionados ao E2E no path #37, sem criar paths de testes não previstos. O gate completo não substitui a prova hospedada nem o smoke oficial.

Histórico anterior, preservado:

| Verificação | Resultado | Origem / limite |
|---|---|---|
| Python unit + API | PASS — 144 testes | Linux/Docker; .nfse-local/verify/gate-linux-final.log; sem substituir smoke oficial |
| Vitest | PASS — 23 testes | Linux/Docker, execução anterior confirmada |
| Typecheck | PASS | Mesmo gate |
| Build frontend | PASS | Mesmo gate; build não é publicação |
| E2E | PASS | Jornada demo, errors []; não prova Auth/Storage reais ponta a ponta |
| API/Auth/Storage/bootstrap focados | PASS — 37 testes | Execução anterior desta sessão de Build, antes da correção final de CI |
| Integridade/construção fiscal focadas | PASS — 10 testes | Execução anterior local; não contradiz normalização posteriormente observada no Git/CI |
| tests.test_contract.Esquemas | PASS — 2 testes | Evidência fornecida da correção 0c6cf49; não reexecutada nesta etapa |
| bun install --frozen-lockfile | PASS no Linux | Lockfile com Supabase 3.0.0, sem mudanças na confirmação anterior |
| Instalação Bun nativa Windows | FAIL — EPERM | Links de executáveis; inclusive copyfile/instalação vazia; sem resolução nativa comprovada |
| verify / local, identity, storage | PASS | GitHub Actions do SHA exato, consultado nesta etapa |
| Vercel | PASS | Status de deployment do SHA exato; não é homologação fiscal |
| PostgreSQL isolado — modo postgres | Não reexecutado neste fechamento | test_pg.py existe e há histórico em BUILD_REPORT.md; não incluído nos 144 do modo local |
| Smoke fiscal — modo restricted | Pendente/bloqueado | Script mantém NOT RUN/falha mesmo com configuração, até integração oficial |

[Workflow verify SUCCESS — execução 41710185536](https://github.com/cassio-rgb/lovable-nfse/actions/runs/41710185536), commit 0c6cf49b038b56eaec661c1d5b82ba2da7165e13. Jobs consultados: [local](https://github.com/cassio-rgb/lovable-nfse/actions/runs/41710185536/job/126175907130), [identity](https://github.com/cassio-rgb/lovable-nfse/actions/runs/41710185536/job/126175906499), [storage](https://github.com/cassio-rgb/lovable-nfse/actions/runs/41710185536/job/126175906876). [Vercel SUCCESS](https://vercel.com/cassio77/lovable-nfse/C8Fmu2JefP4HgUNPVvDgxNeWPjV4) também confirmado por consulta ao status do commit.

## Verify Gate

**Evidências canônicas do gate de software local: Linux/Docker e GitHub Actions.** Windows/Bash sem ambiente compatível não é usado como diagnóstico de falha funcional.

Comando real: `python scripts/verify.py --mode local`. Exige Python/dependências, Bun/bunx, Bash para os testes de guardas, xmlsec1 independente e servidor em localhost:8080 com Playwright/Chromium. Cada FAIL ou NOT RUN provoca exit 1. Nenhuma exigência foi removida para obter aprovação.

No Docker foi usada a imagem nfse-verify-local:20261103, com Bun 1.4.4 e xmlsec1 real. No CI efetivo há instalação de xmlsec1, dependências Python e Chromium, instalação Bun e servidor de desenvolvimento em loopback antes do gate.

Resultado local: **PASS, exit 0**. Resultado do aceite fiscal global: **PENDENTE**. O DEFINE original define kind: smoke, ainda com comando a esclarecer; o DESIGN exige smoke oficial restrito. `python scripts/verify.py --mode restricted` permanece fail-closed, sem simulador como substituto. CI verde não encerra AT-007/009/010/011/013 oficiais.

## Complementary Checks

Incremento autenticado: git diff --check executado com PASS; package-lock.json ausente; diff vazio em backend/app, backend/db, supabase e .gitattributes. Revisão React aplicada a hooks, campos rotulados, estados anunciados e cache. SDK importado somente ao entrar. Estrutura do relatório e status Git serão conferidos no fechamento.

- Leitura do Git confirmou branch feat/supabase-infra, HEAD 0c6cf49 e árvore limpa antes deste relatório.
- Histórico e estatística dos quatro commits relevantes foram inspecionados; .gitattributes contém `*.xsd -text`.
- Consultas somente leitura: `gh run list`, check-runs e status do commit via `gh api`; nenhum PR/deployment alterado.
- Código, testes, migrations, manifest de 47 itens e checklist dos pilotos foram confrontados; existência foi separada de completude.
- Validação estrutural deste relatório: 15 seções canônicas na ordem, 47 itens do manifesto e 13 ATs, estados conservadores e ausência de placeholders de template.
- `git diff --check` executado no fechamento: PASS (exit 0). Como o relatório é novo/untracked, também foi verificado diretamente quanto a espaços finais e newline final.
- `git status --short` executado no fechamento para comprovar alteração documental isolada.
- Não foram repetidos testes de produto nem executados modes postgres/restricted nesta etapa documental.

## Acceptance Test Verification

**Parcial** significa que há implementação/prova interna, mas falta a evidência integrada ou oficial necessária para fechar integralmente o AT. **Pendente oficial** não pode ser convertido em PASS por simulador.

| AT | Situação | Evidência e falta para aceite integral |
|---|---|---|
| AT-001 | Parcial | DraftForm, CompanyContext, API e test_api.Drafts; provar criação com usuário real no contexto autorizado ponta a ponta |
| AT-002 | Parcial | test_imports, test_api.Imports e E2E demo; confirmar jornada real XLSX/CSV, origem e comportamento completo de lote |
| AT-003 | Parcial | Contexto de empresa e autorização no servidor; provar toda jornada integrada sem contexto e impedir emissão real |
| AT-004 | Parcial | Textos de rascunho/demo e estados de domínio testados; falta prova de todos os fluxos do produto integrado |
| AT-005 | Parcial | Rota de revisão, hash/versão e E2E demo; completar prova com dados e parâmetros reais validados |
| AT-006 | Parcial | Validações server-side e eligibility bloqueiam; parâmetros fiscais reais/liberações dos pilotos pendentes |
| AT-007 | Pendente oficial | Comando interno testado; submit oficial bloqueado; não houve transmissão oficial comprovada |
| AT-008 | Parcial | Idempotência, fence, testes de crash/concorrência e UI demo; falta jornada integrada de transmissão real |
| AT-009 | Pendente oficial | Resultado aceito apenas simulado; faltam retorno e documento oficial preservados |
| AT-010 | Pendente oficial | Rejeição simulada e detalhe técnico existem; catálogo/interpretação de rejeição oficial e smoke pendentes |
| AT-011 | Parcial; smoke oficial pendente | Incerteza e consulta simuladas, sem reenvio; formalizar refinamento do DEFINE e validar falha/consulta no contrato oficial |
| AT-012 | Parcial | Testes de isolamento/API/Storage e RLS; completar browser/API/arquivos com sessão real e revogação |
| AT-013 | Pendente oficial | Liberação contextual implementada; checklist sem evidências dos dois municípios, A-002/A-003 não encerradas |

M01 possui recuperação simulada; M02 possui prévia/idempotência; M03 possui guarda de troca; M04 possui elegibilidade; M05 possui negação genérica. Isso constitui implementação parcial das soluções propostas, sem fechamento formal da UX Review. Faltam cobertura integral dos cenários de falha, incorporação autorizada ao DEFINE e reaplicação da revisão. Acessibilidade, contraste, teclado, leitor de tela e emissão simples no celular continuam sem prova completa; não se declara WCAG atendida.

## Advisor Ledger

No incremento autenticado foram usadas as skills Supabase e React Best Practices para SDK/segurança e revisão dos componentes; nenhuma revisão externa ou delegação foi executada. Consultados [signInWithPassword](https://supabase.com/docs/reference/javascript/auth-signinwithpassword), [signOut](https://supabase.com/docs/reference/javascript/auth-signout) e changelog oficial antes da implementação. TLS moderno exigido; mudanças de SAML/self-hosted não alteram o login por senha hospedado deste recorte.

| Entrada | Natureza | Tratamento |
|---|---|---|
| GOVERNANCA_REVIEW de 31/10 | Revisão documental, não auditoria do produto | Recomendações preservadas; nenhuma aprovação individual presumida |
| UX_REVIEW v1.0 | Revisão documental com M01–M05 abertos | Soluções técnicas mapeadas; gate formal original preservado |
| rdd-audita-schema | Recomendada pela governança; não disponível no catálogo desta sessão | Não executada; sem declaração de auditoria concluída |
| Revisão externa do Build atual | Nenhuma executada nesta etapa | CI não equivale a aprovação humana ou auditoria fiscal |

G01/G08 têm mecanismos parciais de snapshot/artefatos; G09/G10 têm Decimal/centavos e unicidade; G13 tem autorização e RLS. Não se declara nenhum desses controles integralmente aprovado pelo profissional com base somente na sobreposição técnica. G04/G05/G06, G07, retenção G14, backup/restauração G15 e custódia completa G16 permanecem sem fechamento comprovado. G02/G03 e G17–G20 seguem N.A. no escopo documental original, sem razão/fechamento contábil ou IA em runtime.

## Issues Encountered

| Problema | Evidência / causa comprovada | Resolução e risco residual |
|---|---|---|
| Bun EPERM no Windows | Falha ao criar links de executáveis em node_modules/.bin, inclusive backend copyfile e instalação vazia; processo anterior ficou sem progresso | Instalação limpa Linux/Docker validada; causa específica da recusa Windows ainda não isolada. Backup npm preservado; não declarar instalação Windows corrigida |
| Bash no Windows | 4 falhas ambientais na seleção de 144; WSL sem /bin/bash | Execução Linux resolve ambiente; não classificadas como defeito funcional |
| xmlsec1 ausente no Windows | 2 testes independentes pulados; gate recusava aprovação | Linux/CI fornecem binário real obrigatório; nenhum skip tratado como PASS |
| Mensagem xmlsec1 entre versões | Retorno 0 e assinatura válida, mas teste exigia apenas Verification status: OK; versão 1.2.41 imprime OK | 3e36851 aceita linhas exatas de sucesso das duas versões; mantém retorno zero e negativos de adulteração/certificado errado |
| CRLF/LF dos XSDs | Git normalizava bytes para LF; checkout local anterior não revelava necessariamente a divergência presente no índice/CI | 0c6cf49 adiciona *.xsd -text e preserva bytes originais; não altera contrato/schema para passar teste |
| CI anterior com hash divergente | Integridade baseada em bytes recusou XSD normalizado | Testes Esquemas: 2 OK na correção; CI seguinte completamente verde; MANIFEST não foi reescrito para aceitar bytes incorretos |
| Contexto RLS ausente nas consultas de sessão | Policies dependem de app.user_id por transação | 0731650 propaga contexto; migration adiciona SELECT para membership/company/operation_release no papel nfse_api |
| Documentação histórica desatualizada | Runbook/contrato ainda descrevem bloqueio total do bootstrap | Drift registrado; atualização fica para etapa autorizada posterior |

## Deviations from Design

Adaptações justificadas: scaffold TanStack existente preservado; caminhos web/ remapeados; testes unittest e E2E Python/Playwright em vez de arquivos .spec.ts propostos; fornecedores concretizados pelo adendo 004; bootstrap da API permitido sem cofre porque a API não transmite, conforme decisão registrada. API e worker continuam separados em responsabilidade e DSN.

Lacunas ainda abertas, sem reclassificar como redução de requisito: integração frontend/backend real; storage de origem/lotes e contrato integral da prévia; worker operacional; alertas/métricas; acessibilidade; cofre e autorização de assinatura delegada confiável; parâmetros fiscais duráveis; envelope HTTP/perfil de assinatura aprovados e smoke dos pilotos. O protocolo Vault existe, mas isso não implementa um cofre.

A1 não vai ao frontend nem ao Storage comum. Certificado de escritório não substitui silenciosamente o emitente cliente; assinatura delegada depende de autorização confiável. Os testes offline não autorizam transmissão. O defeito oficial da série do XSD de produção, registrado nas evidências, continua bloqueante para esse perfil, sem alteração do esquema.

## Blockers

| Bloqueador / pendência | Efeito | Próxima evidência necessária |
|---|---|---|
| Validação autenticada no ambiente hospedado | Auth/API/PG durável, leitura protegida e jornada UI de leitura PASS; isolamento com segunda fixture pendente | Obter fixture segura de segunda empresa em etapa autorizada, sem criar dados nesta prova |
| Cofre, cadeia/revogação e autorização delegada | Impede uso fiscal real do A1 | Provedor confiável, acesso mínimo e testes negativos sem exposição de segredo |
| Parâmetros fiscais por contexto | Impede liberar operações reais | Cadastro durável e validação por responsável fiscal |
| Contrato HTTP e perfil cripto oficial | Mantém submit/lookup bloqueados | Spike documentado com contrato vigente e testes de interpretação |
| Pilotos Bariri/Pederneiras | Impede fechar ATs smoke e liberar produção | Habilitação e recibos/retornos oficiais de ambos os contextos |
| Acessibilidade e completude do manifesto | Impede declarar todo o Build completo | Suíte/provas de tarefa e fechamento das lacunas itemizadas |
| Governança e alinhamento documental | Impede fechamento formal integral | Decisões individuais, responsável/CRC, guarda, recuperação e atualização autorizada de critérios |
| Bun Windows | Limita ambiente nativo | Diagnóstico da recusa de links; Linux/Docker segue alternativa validada |

Esses bloqueios recaem sobre partes da entrega e a ativação fiscal. O trabalho de produto pode continuar em incremento autorizado; por isso o status global requerido é In Progress, não uma conclusão artificial nem impossibilidade total de avançar.

## Final Status

Status: In Progress

Overall: IN PROGRESS

Infraestrutura deste incremento: concluída e validada no escopo descrito. Gate local Linux/Docker e CI no commit 0c6cf49: PASS. Produto completo do DEFINE/DESIGN: não concluído; manifesto e ATs oficiais ainda possuem pendências.

Incremento autenticado: implementação e gate local PASS; Auth, API, PostgreSQL durável e leitura protegida hospedados PASS após correção de allow(). Frontend hospedado de leitura, reload e logout PASS. Isolamento hospedado com segunda empresa permanece INCONCLUSIVE por ausência de fixture segura. O incremento está pronto para revisão e commit somente mediante autorização, com essa limitação explícita. Próxima ação segura: revisar o diff e obter autorização de commit, sem emissão fiscal. O restante do manifesto e dos ATs continua pendente. Manter o adaptador fiscal e produção bloqueados até cofre, contrato/perfil aprovado, parâmetros e smoke oficial. Nenhum commit, push, merge, promoção do PR para Ready for review ou publicação foi realizado nesta etapa.
