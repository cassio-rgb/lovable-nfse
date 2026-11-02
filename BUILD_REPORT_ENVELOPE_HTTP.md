# BUILD REPORT: Envelope HTTP da NFS-e Nacional — offline

## Metadata

| Attribute | Value |
|---|---|
| **Feature** | Preparação de mensagens JSON e leitura offline de respostas SEFIN |
| **Date** | 2026-11-02 |
| **Author** | SDD Build by RDD |
| **BRAINSTORM** | BRAINSTORM_NFSE_GESTORAS_IMOVEIS.md |
| **DEFINE** | DEFINE_NFSE_GESTORAS_IMOVEIS.md |
| **DESIGN** | DESIGN_NFSE_GESTORAS_IMOVEIS.md + adendo 004 |
| **Status** | Blocked |

## Mode Selection

| Signal | Observation |
|---|---|
| Manifest files | Adendo 004, contrato, cliente e testes |
| Cross-file coupling | Médio, codec separado do domínio fiscal |
| Security surface | XML/JSON não confiáveis, descompactação e correlação de identidade |
| LLM prompt items | None |
| Independent volume | Baixo |
| Context-rot risk | Baixo |
| Runtime capabilities | Execução sequencial local; Lovable não sincronizado |

**Recommendation:** default para manter os bloqueios e contratos existentes.

**User decision:** continuação autorizada por “prosseguir” e fornecimento da captura Swagger solicitada; sem nova arquitetura ou modo.

**Pre-build review:** Not available; nenhuma revisão externa formal.

## Summary

| Metric | Value |
|---|---|
| **Tasks Completed** | Preparação e parsing offline concluídos; transporte real não liberado |
| **Files Created** | 5 incluindo este relatório/adendo/fixture/codec/testes |
| **Files Modified** | 5: cliente, teste existente, runner, preflight e evidências |
| **Files Deleted** | 0 |
| **Verification Commands Run** | 2 suítes de unittest (11 novos e 48 casos relevantes) e compilação |
| **Verify Gate** | Clarification pending |
| **Execution Mode** | default |

A captura Swagger 2.0 traz 8 rotas e 10 definições. O envelope dpsXmlGZipB64 usa XML UTF-8/GZip/Base64. GET DPS retorna chave; POST 201 e GET NFS-e contêm XML compactado. idDps (sucesso) e idDPS (erro) preservados. Fonte fornecida pelo usuário, não captura TLS independente deste ambiente. A data de exemplo do Swagger não é uma emissão.

## Task Execution

| # | Manifest ID | Task | Executor | Status | Verification | Evidence |
|---|---|---|---|---|---|---|
| 1 | 1 | Extrair captura e registrar SHA256 | direct | Complete | Parse JSON e teste de fonte | 8 rotas, 10 definições |
| 2 | 2,3 | Implementar codec e testes adversariais | direct | Complete | unittest tests.test_envelope | 11/11 |
| 3 | 7,8 | Integrar apenas preparação JSON ao cliente | direct | Complete | unittest tests.test_contract | Bloqueios, TLS e allowlist preservados |
| 4 | 4–6,9 | Runner, diagnóstico, evidências e relatório | direct | Complete | unittest tests.test_preflight; validador | 48 casos relevantes, exit 0; estrutura do relatório validada |

## Files Changed

| File | Action | Verified |
|---|---|---|
| backend/tests/fixtures/official/swagger-sefin-restrita-captura-20261102.json | Create | SHA256 |
| backend/app/nfse/envelope.py | Create | Testes |
| backend/tests/test_envelope.py | Create | Executado |
| backend/app/nfse/client.py | Modify | Testes do cliente |
| backend/tests/test_contract.py | Modify | Executado |
| scripts/verify.py | Modify | Suíte adicionada |
| scripts/preflight.py | Modify | Testes |
| docs/nfse-integration-evidence.md | Modify | Histórico preservado e nova seção |
| sdd/design-addendum-004-envelope-http.md | Create | Manifest anterior ao código |
| sdd/BUILD_REPORT_ENVELOPE_HTTP.md | Create | Validador estrutural |

## Drift Detected

Captura declara schemes=http, TLS legado e basePath=/SefinNacional; URL de documentação usa /API/SefinNacional. Nenhum downgrade ou alteração de rota. HTTPS e TLS >=1.2 mantidos; rota efetiva não confirmada. XMLDSIG genérico não informa algoritmo vigente. O JSON descreve o contrato, não comprova autorização por procuração. Esses itens bloqueiam somente o transporte real; codec isolado pode ser verificado sem eles.

## Verification Results

### Incremental Verification

| Task | Command / Method | Result | Evidence |
|---|---|---|---|
| Codec | python3 -m unittest tests.test_envelope -v em backend | Pass | 11 novos casos |
| Regressão pertinente | python3 -m unittest tests.test_envelope tests.test_contract tests.test_preflight -v em backend | Pass | 48/48, sem skips |
| Compilação | python3 -m compileall -q backend/app/nfse scripts/preflight.py scripts/verify.py | Pass | Exit 0 |
| Estrutura do relatório | validate_build_report.py | Pass | Exit 0 |

Casos: roundtrip determinístico; nomes de campos conferidos com a captura; XML hostil, Base64 inválido, GZip expansivo/truncado/concatenado; JSON excessivo, inválido e chaves repetidas; ambiente e identidade divergentes; 201 informativo sem validação fiscal; 500 e status ambíguos indeterminados; 404 sem decisão de reenvio. submit/lookup continuam lançando AdaptadorFiscalBloqueado. Conteúdos XML e chave omitidos no repr. Nenhum I/O de rede, leitura de certificado ou alteração de estado nos testes.

### Verify Gate

| Attribute | Value |
|---|---|
| **Kind** | smoke |
| **Command / Method** | DEFINE original ainda contém comando NEEDS CLARIFICATION |
| **Exit / Result** | 5: classificação de bloqueio, não saída de comando executado |
| **Status** | Clarification pending |
| **Evidence** | Nenhum smoke oficial pode ser substituído pelo codec offline |

### Manual UX Receipt

N/A: incremento sem UI; não representa aprovação de UX ou emissão no Windows.

### Complementary Checks

Compilação e testes relevantes descritos acima. Frontend inalterado, sem repetir build/testes TS. Suite completa de backend, PostgreSQL, mTLS e smoke oficial não executados neste incremento.

## Acceptance Test Verification

| ID | Scenario | Status | Evidence |
|---|---|---|---|
| HTTP-001 | Corpo com dpsXmlGZipB64 e compactação correta | Pass | Roundtrip e preparação do cliente |
| HTTP-002 | Parser limitado e entradas hostis recusadas | Pass | Testes adversariais |
| HTTP-003 | Ambiente, DPS e chave correlacionados | Pass | Casos de divergência |
| HTTP-004 | Nenhum envio ou marcação de emitida | Pass | Resultado informativo e cliente bloqueado |
| AT-007 | Envio oficial | Blocked | Dependências reais abaixo |

## Advisor Ledger

None — no formal external review was executed.

## Issues Encountered

A captura resolve nomes/formato dos envelopes, mas não rota efetiva, algoritmo de assinatura ou autorização delegada. Preservado status parcial em vez de declarar integração completa. JSON com example não é recibo. Fonte e hash preservados em fixture.

## Deviations from Design

Nenhuma mudança arquitetural. Extensão de contrato registrada no adendo antes das alterações. Não alterar worker, assinatura, dados fiscais ou regras de liberação.

## Blockers

| Blocker | Required Action | Owner |
|---|---|---|
| Rota efetiva restrita | Evidência oficial e conexão mTLS controlada | Responsável técnico |
| Perfil criptográfico e certificado autorizado | Confirmar algoritmo vigente, cadeia, revogação e autorização | Responsável técnico/fiscal |
| Serviço local real incompleto | Conectar identidade, cofre e armazenamento durável | Responsável técnico |
| Smoke e Verify Gate global | Homologar sem simulador e fechar critérios | Responsável técnico/fiscal |
| Sincronização Lovable | Incorporar código quando integração estiver disponível | Responsável técnico |

## Final Status

### Overall: BLOCKED

Preparação e processamento offline implementados e testados. A instalação do usuário continua em demonstração. Não houve envio ao governo, autorização por procuração validada, publicação ou alegação de prontidão fiscal. O codec não retorna FiscalResult; 201 exige validação adicional de XML/XSD, assinatura, identidade e snapshot antes de qualquer aceitação de domínio.
