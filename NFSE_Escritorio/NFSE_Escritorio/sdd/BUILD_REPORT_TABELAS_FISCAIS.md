# BUILD REPORT: Catálogos fiscais NFS-e — incremento local

> Consulta e seleção de tabelas oficiais anexadas; não é liberação de emissão fiscal.

## Metadata

| Attribute | Value |
|---|---|
| **Feature** | Catálogos NBS, serviço nacional, CST, cClassTrib e cIndOp |
| **Date** | 2026-11-02 |
| **Author** | SDD Build by RDD |
| **BRAINSTORM** | BRAINSTORM_NFSE_GESTORAS_IMOVEIS.md |
| **DEFINE** | DEFINE_NFSE_GESTORAS_IMOVEIS.md |
| **DESIGN** | DESIGN_NFSE_GESTORAS_IMOVEIS.md + sdd/design-addendum-003-tabelas-fiscais.md |
| **Status** | Blocked |
| **Base Lovable** | 2920cd4219b76b9bbfbc7bf8c291bcf5e317fa06 |
| **Distribuição** | Incremento local verificado; sem novo commit Lovable |

## Mode Selection

| Signal | Observation |
|---|---|
| Manifest files | Adendo 003; integração TS/Python e fontes compartilhadas |
| Cross-file coupling | High: contratos, hash, rascunhos, revisão e armazenamento |
| Security surface | Revisão e guardas existentes; nenhuma liberação de transmissão |
| LLM prompt items | None |
| Independent volume | Baixo; implementação sequencial |
| Context-rot risk | Moderado; adendo e manifesto para rastreabilidade |
| Runtime capabilities | Execução local disponível; continuação Lovable falhou |

**Recommendation:** default, para preservar coerência dos contratos.

**User decision:** continuação autorizada pelo “ok” após descrição da integração, mantendo execução sequencial da sessão. Sem novo modo ou arquitetura.

**Pre-build review:** Not available. Análise de fontes no Lovable não é revisão externa formal de código.

## Summary

| Metric | Value |
|---|---|
| **Tasks Completed** | Implementação do incremento local e testes concluídos; sincronização/UX visual pendentes |
| **Files Created/Modified** | Relação abaixo e manifesto de distribuição |
| **Files Deleted** | 0 |
| **Verification Commands Run** | Testes frontend/backend, lint, typecheck, builds, extrator, comparação independente e HTTP |
| **Verify Gate** | Blocked: clarificação do gate original e integração oficial |
| **Execution Mode** | default |

São 338 serviços, 918 registros NBS com padrão completo (917 descritos selecionáveis e um marcador sem descrição bloqueado), 173 cClassTrib (73 NFS-e; 12 CST), 40 indOp (28 NFS-e) e 1609 linhas de correlações. Códigos preservados como texto; espaços externos removidos. Fontes XLSX copiadas sem alterações, SHA256 no JSON. cClassTrib sem versão declarada: não inventar data de vigência.

Campos pesquisáveis por código/descrição, seleção explícita, nenhum código preenchido por inferência. Troca de CST limpa classe. Rascunhos incompletos podem ser salvos e importados; revisão exige códigos válidos. Seleções participam de hash, versão e snapshot; revisões antigas sem catálogo são inválidas. JSON PostgreSQL é preservado por asdict/DadosRascunho, sem migração. Anexo VIII só referência, não valida combinação nem escolhe enquadramento.

## Task Execution

| # | Manifest ID | Task | Executor | Status | Verification | Evidence |
|---|---|---|---|---|---|---|
| 1 | 1–3 | Fontes e extração reproduzível | direct | Complete | gerar_catalogos.py --check | Conteúdo confere integralmente |
| 2 | 4–10 | Campos, busca e revisão | direct | Complete | npm test; tsc | 23/23 testes; exit 0 |
| 3 | 11–15 | Contrato Python, hash, API e JSON PG | direct | Complete | unittest discover | 140 executados: 129 aprovados, 11 skip |
| 4 | 16–23 | Testes e compatibilidade de build | direct | Complete | lint/build | exit 0; limitações abaixo |
| 5 | 19,24 | Relatório e distribuição | direct | Complete | validador e ZIP | Validar estrutura e manifesto ao empacotar |

## Files Changed

| File | Action | Verified |
|---|---|---|
| `backend/app/api.py` | Modify | Sim |
| `backend/app/catalogos.py` | Create | Sim |
| `backend/app/domain/models.py` | Modify | Sim |
| `backend/app/reviews.py` | Modify | Sim |
| `backend/tests/fixtures/official/catalogos/anexo_b-nbs2-lista_servico_nacional-snnfse-v1-01-20260122.xlsx` | Create | Sim |
| `backend/tests/fixtures/official/catalogos/anexo_viii-tabela-correlacao-v01-02-00-20261026.xlsx` | Create | Sim |
| `backend/tests/fixtures/official/catalogos/anexovii-indop_ibscbs_v1-03-00-nt009.xlsx` | Create | Sim |
| `backend/tests/fixtures/official/catalogos/classificacao_tributaria.xlsx` | Create | Sim |
| `backend/tests/helpers.py` | Modify | Sim |
| `backend/tests/test_api.py` | Modify | Sim |
| `backend/tests/test_catalogos.py` | Create | Sim |
| `deploy/backend.Dockerfile` | Modify | Sim |
| `scripts/gerar_catalogos.py` | Create | Sim |
| `scripts/verify.py` | Modify | Sim |
| `sdd/design-addendum-003-tabelas-fiscais.md` | Create | Sim |
| `shared/catalogos-fiscais.json` | Create | Sim |
| `src/components/CatalogFields.tsx` | Create | Sim |
| `src/components/DraftForm.tsx` | Modify | Sim |
| `src/lib/catalogos.ts` | Create | Sim |
| `src/lib/contracts.ts` | Modify | Sim |
| `src/lib/datasource.ts` | Modify | Sim |
| `src/lib/domain.ts` | Modify | Sim |
| `src/routes/revisao.$id.tsx` | Modify | Sim |
| `src/test/catalog-fields.test.tsx` | Create | Sim |
| `src/test/catalogos.test.ts` | Create | Sim |
| `src/test/domain.test.ts` | Modify | Sim |
| `vite.config.ts` | Modify | Sim |

backend/app/pg.py não exigiu alteração: serialização existente já armazena campos adicionados ao dataclass no JSON. Testado roundtrip antigo/novo, sem afirmar teste PostgreSQL real.

## Drift Detected

| Task | Drift | Decision | Action |
|---|---|---|---|
| NBS | Contagem inicial 821 ignorava espaços externos | Corrigir leitura sem alterar fonte | 918 após trim; marcador sem descrição não selecionável |
| Execução | Lovable retornou INVALID_ARGUMENT em três tentativas de continuação | Manter trabalho autorizado no código local | ZIP local; editor não sincronizado |
| Build | process.env.NFSE_BUILD_PROFILE conflita com noPropertyAccessFromIndexSignature | Correção mínima | Acesso com colchetes em vite.config.ts |
| Container | Backend copia apenas seu diretório | Preservar consulta no Docker existente | COPY do mesmo JSON e fallback de localização; imagem não executada |

## Verification Results

### Incremental Verification

| Task | Command / Method | Result | Evidence |
|---|---|---|---|
| Fontes | python3 scripts/gerar_catalogos.py --check | Pass | JSON reproduzido integralmente |
| Independência | Leitura separada dos XLSX e expansão apenas de intervalos mesclados | Pass | Todos serviços, NBS, classes e 1609 linhas comparados |
| Frontend | npm test | Pass | 6 arquivos, 23 testes |
| Backend | python -m unittest discover -s tests -t . em backend | Pass com skips explícitos | 140 casos, 129 aprovados, 11 ignorados |
| Tipos | npx tsc --noEmit | Pass | exit 0 |
| Lint novo | npx eslint nos quatro novos arquivos TS/TSX | Pass | exit 0, incluindo Prettier |
| Lint existente | npx eslint nos arquivos existentes alterados, prettier/prettier off | Pass | exit 0; formatação histórica não reescrita |
| Build local | NFSE_BUILD_PROFILE=local-node npm run build | Pass | .output-local/server/index.mjs |
| Build padrão | npm run build | Pass | Perfil Cloudflare preservado; sem deploy |
| HTTP | Iniciar build local e GET / e /nova na porta temporária 4518 | Pass | HTTP 200 nas duas páginas; processo encerrado |

Ambiente de verificação: Linux, Node 24.22.1, Python 3.12. Dependências frontend instaladas com npm sem criar lockfile; bun.lock e package.json originais preservados. Versão efetiva Vitest 4.1.12 dentro da faixa existente. Instalação Bun/Windows deste incremento não foi executada aqui; usa lançador já existente no computador do usuário.

### Verify Gate

| Attribute | Value |
|---|---|
| **Kind** | smoke |
| **Command / Method** | DEFINE original contém comando NEEDS CLARIFICATION, sem smoke executável definido |
| **Exit / Result** | 5 (classificação do bloqueio; não é saída de comando executado) |
| **Status** | Clarification pending |
| **Evidence** | Gate original não pode ser substituído pelos testes do incremento; nenhuma emissão oficial realizada |

### Manual UX Receipt

Pendente. Testes de interação jsdom aprovados, sem aprovação humana ou validação visual completa no Windows.

### Complementary Checks

| Check | Status | Evidence |
|---|---|---|
| Lint/typecheck | Pass | Verificações acima |
| Build local e padrão | Pass | Sem publicação |
| Interação de busca e seleção | Pass | Testes DOM; pesquisa não seleciona; troca de CST limpa classe |
| Navegador visual | Not run | Playwright não tinha Chromium; download retornou arquivo inválido. Nenhuma captura apresentada como prova |
| PostgreSQL/assinatura | Skip | 9 casos PG dependem de banco; 2 de xmlsec1; sem alterações em assinatura |
| Docker | Not run | Só compatibilidade de empacotamento do JSON; sem build/deploy de imagem |

## Acceptance Test Verification

| ID | Scenario | Status | Evidence |
|---|---|---|---|
| CAT-001 | Fontes completas, padding e mesclas reais | Pass | Contagens, SHA e comparação independente |
| CAT-002 | Busca e escolha explícita, sem inferência | Pass | Testes DOM e pesquisa sem acento |
| CAT-003 | Aplicabilidade NFS-e e par CST/classe | Pass | Casos TS/Python de rejeição |
| CAT-004 | Salvar incompleto e bloquear revisão | Pass | Demo, domínio Python; testes API regressivos |
| CAT-005 | Hash muda com cada campo e revisão antiga inválida | Pass | Casos TS/Python |
| CAT-006 | Persistência e revisão com descrições | Pass | Demo localStorage, API/Pydantic, JSON PG e resumo DOM |
| AT-007/009/010/013 | Smoke oficial e homologação municipal | Blocked | Integração nacional permanece fechada |
| UX visual | Tela real no Windows | Pending | Conferir após instalar |

## Advisor Ledger

None — no formal external review was executed. Checklist React aplicado diretamente: hooks fora de condicionais, labels com useId, opções de select nativas, erro associado, nenhuma requisição fiscal no componente ou escolha por efeito.

## Issues Encountered

| Issue | Resolution | Impact |
|---|---|---|
| Fixtures antigas não tinham códigos | Acrescentar seleções explícitas somente nas fixtures de revisão | Não altera rascunhos reais ou importações |
| Marcador NBS sem descrição | Preservar na fonte e bloquear seleção | Não inventar significado |
| Navegador ausente | Registrar limitação | Revisão visual humana pendente |
| Lovable indisponível para continuação | Distribuir incremento local | Sem alegação de novo commit/preview atualizado |

## Deviations from Design

Arquitetura mantida. Extensão aprovada registrada no adendo 003 antes das alterações. Sem perfis por empresa, atualização automática de tabelas, cálculo de imposto ou adaptação do transmissor nacional.

## Blockers

| Blocker | Required Action | Owner |
|---|---|---|
| Verify Gate original indefinido e emissão oficial não homologada | Fechar critérios e integração antes de emissão real | Responsável técnico/fiscal |
| Editor Lovable ainda no commit base | Sincronizar incremento quando integração voltar a aceitar mensagens | Responsável técnico |
| UX visual Windows pendente | Instalar cópia e conferir formulário/revisão | Usuário |

## Final Status

### Overall: BLOCKED

Incremento local implementado e verificações descritas aprovadas. BLOQUEIO global mantido para emissão real, encerramento do ciclo SDD e sincronização Lovable. Pacote de demonstração pode ser revisado e instalado localmente, preservando a mesma origem do navegador para os rascunhos. Nenhuma transmissão fiscal ou publicação foi executada.
