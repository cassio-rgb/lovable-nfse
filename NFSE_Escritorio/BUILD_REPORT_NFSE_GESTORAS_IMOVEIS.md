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
| Baseline | 0c6cf49b038b56eaec661c1d5b82ba2da7165e13 |
| Repository | cassio-rgb/lovable-nfse; aplicação em NFSE_Escritorio/ |
| Scope desta entrega | Gerar e validar este relatório; nenhuma mudança de produto |

Fontes lidas integralmente na raiz Git (diretório pai desta aplicação): [Brainstorm](../BRAINSTORM_NFSE_GESTORAS_IMOVEIS.md), [Define](../DEFINE_NFSE_GESTORAS_IMOVEIS.md), [Governança](../GOVERNANCA_REVIEW_NFSE_GESTORAS_IMOVEIS.md), [UX Review](../UX_REVIEW_NFSE_GESTORAS_IMOVEIS.md) e [Design](../DESIGN_NFSE_GESTORAS_IMOVEIS.md). Considerados também AGENTS.md, adendo 004, relatórios históricos, código, migrations, testes, scripts e workflows reais. O DEFINE permanece Needs Clarification, o DESIGN permanece Draft e a UX Review permanece BLOCKED FOR DESIGN nos documentos originais; este relatório não modifica esses estados nem presume sua aprovação posterior.

## Mode Selection

Modo sequencial de consolidação e revisão de evidências, sem delegação. O pedido atual autoriza somente o relatório. A infraestrutura já implementada é avaliada como incremento; a completude do produto é avaliada contra todo o manifesto de 47 itens e AT-001 a AT-013. A existência de um arquivo não comprova a entrega integral de seu propósito.

## Summary

A infraestrutura deste incremento está concluída no escopo validado: Supabase Auth, PostgreSQL, RLS, Storage privado e bootstrap seguro da API, com separação dos DSNs da API e do worker. O gate local passou em Linux/Docker; o workflow verify e os checks de Vercel passaram no commit de referência. Isso não conclui o produto exigido pelo Brainstorm/Define/Design.

A interface possui fonte demo explícita e cliente de API, mas falta comprovar e concluir a jornada integrada com login Supabase, troca de sessão, backend durável e documentos reais. A integração fiscal oficial, o cofre, os parâmetros fiscais duráveis e a homologação de Bariri/SP e Pederneiras/SP permanecem pendentes. Produção fiscal continua bloqueada/fail-closed.

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

### File Manifest do Design — 47 itens

Legenda: **Implementado** significa propósito interno comprovado por código/testes disponíveis; não implica homologação fiscal. **Parcial** indica escopo ou prova ainda incompletos. **Fora deste incremento** preserva o trabalho previsto, sem removê-lo do Design. Caminhos abaixo são relativos à aplicação, salvo indicação da raiz Git.

| # | Arquivo previsto → caminho real / evidência | Situação e limite |
|---:|---|---|
| 1 | web/package.json → package.json + bun.lock | Implementado: scaffold Lovable/TanStack, scripts e dependências |
| 2 | web/src/lib/contracts.ts → src/lib/contracts.ts, domain.ts | Implementado: contratos e centavos inteiros; espelho Decimal no backend |
| 3 | web/src/lib/api.ts → src/lib/datasource.ts, confirm.ts | Parcial: cliente com credentials/include e recuperação; jornada autenticada real não comprovada |
| 4 | CompanyContext.tsx → src/components/CompanyContext.tsx | Parcial: empresa, ambiente, guarda de edição e limpeza de cache existem; integração real e todos os cenários de revogação/troca ainda sem prova E2E |
| 5 | StatusPanel.tsx → src/components/StatusPanel.tsx | Parcial: estados e mensagens existem; auditoria acessível e retornos oficiais pendentes |
| 6 | DraftForm.tsx → src/components/DraftForm.tsx | Parcial: formulário e revisão demonstrados; jornada completa com API real pendente |
| 7 | ImportPreview.tsx → src/components/ImportPreview.tsx | Parcial: prévia e confirmação; persistência integral do lote/original e prova integrada pendentes |
| 8 | ReviewPanel.tsx → src/routes/revisao.$id.tsx | Parcial: revisão e confirmação implementadas em rota equivalente; transmissão oficial bloqueada |
| 9 | DocumentResult.tsx → src/routes/operacao.$id.tsx, historico.tsx | Parcial: resultado simulado e link autorizado existem; documento oficial/download integrado não demonstrados |
| 10 | AccessDenied.tsx → src/components/AccessDenied.tsx | Implementado no escopo local: mensagem genérica e retorno; negação também testada na API |
| 11 | NfseWorkspace.tsx → src/components/AppShell.tsx + src/routes/ | Parcial: composição no roteador nativo; entrada autenticada real pendente |
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
| 37 | tests/e2e/nfse.spec.ts → tests/e2e/nfse_flow.py | Parcial: jornada demo passou; não cobre integralmente M01–M05 nem backend durável real |
| 38 | tests/e2e/accessibility.spec.ts | Fora deste incremento: arquivo ausente; auditoria completa de teclado/foco/contraste/mobile não demonstrada |
| 39 | scripts/verify.py | Parcial: local e postgres executáveis; restricted falha fechado e smoke oficial ainda não implementado |
| 40 | deploy/backend.Dockerfile | Parcial: artefato existe; empacotamento/execução completos não validados; comentário referencia worker_main inexistente |
| 41 | deploy/compose.test.yml | Parcial: define db/API, sem serviço worker e sem prova do conjunto isolado previsto; não confundir com contêiner do gate |
| 42 | config/env.example | Implementado como documentação de configuração sem credenciais operacionais |
| 43 | docs/api-contract.md | Parcial: contrato interno existe; seção de estado ainda diz identidade/storage ausentes, divergindo do código atual |
| 44 | docs/nfse-integration-evidence.md | Parcial: evidências offline e bloqueios registrados; spike/smoke oficiais pendentes |
| 45 | docs/runbook.md | Parcial: procedimentos existem; bootstrap descrito está desatualizado e restauração/alertas sem comprovação |
| 46 | docs/pilot-checklist.md | Parcial: checklist criado, itens dos dois municípios não preenchidos com provas oficiais |
| 47 | .github/workflows/verify.yml → ../.github/workflows/verify.yml (raiz Git) | Implementado para CI local/identity/storage; cópia dentro da aplicação é antiga e não é o workflow efetivo |

Itens adicionais rastreados pelos adendos: certificado/delegação A1 offline (001); lançador local em loopback (002); catálogos fiscais e campos de seleção explícita (003); Auth/Storage/runtime/bootstrap (004). Esses incrementos não eliminam as pendências do manifesto original.

## Files Changed

Nesta etapa, somente **BUILD_REPORT_NFSE_GESTORAS_IMOVEIS.md** na pasta da aplicação foi criado. Os arquivos de produto, XSDs, hashes, MANIFEST, especificações e relatórios históricos foram preservados. Existe também relatório homônimo na raiz Git; este novo relatório fica deliberadamente em NFSE_Escritorio/, conforme o repositório de trabalho solicitado, sem sobrescrever o histórico externo.

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
3. BUILD_REPORT.md, docs/api-contract.md e docs/runbook.md ainda descrevem ausência de Auth/Storage ou recusa total do bootstrap, superadas pelo adendo 004 e main.py. Não foram corrigidos nesta etapa restrita ao relatório.
4. Workflow efetivo está na raiz Git; a cópia NFSE_Escritorio/.github/workflows/verify.yml é desatualizada e não define os jobs identity/storage atuais.
5. Worker separado significa segregação de código, DSN e responsabilidade comprovada; ainda não significa serviço contínuo implantado. worker_main.py está ausente.
6. Modelo de importação integral, observabilidade operacional e suíte de acessibilidade estão aquém do propósito completo do Design.

## Verification Results

Evidências históricas são registradas com origem, sem apresentá-las como reexecução em 04/11. A etapa atual só validou documentação/Git e consultou checks em modo leitura.

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
| Frontend/backend autenticados ainda não concluídos | Não fecha jornada operacional do produto | Login Supabase → sessão HttpOnly → API durável → UI/documento, com isolamento e revogação |
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

Próxima ação segura: revisar este relatório e planejar a integração autenticada frontend/backend em homologação, com prova ponta a ponta e fechamento dos itens do manifesto. Manter o adaptador fiscal e produção bloqueados até cofre, contrato/perfil aprovado, parâmetros e smoke oficial. Nenhum commit, push, merge, promoção do PR para Ready for review ou publicação foi realizado nesta etapa.
