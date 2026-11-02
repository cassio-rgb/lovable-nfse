# BUILD REPORT: NFS-e Nacional para Gestoras de Imóveis

> Atualização de 31/10/2026: geração, validação e assinatura local da DPS implementadas; transmissão fiscal oficial ainda bloqueada.

## Metadata

| Attribute | Value |
|---|---|
| **Feature** | NFS-e Nacional para Gestoras de Imóveis |
| **Date** | 2026-10-31 |
| **Author** | SDD Build by RDD |
| **BRAINSTORM** | BRAINSTORM_NFSE_GESTORAS_IMOVEIS.md |
| **DEFINE** | DEFINE_NFSE_GESTORAS_IMOVEIS.md v0.9 |
| **DESIGN** | DESIGN_NFSE_GESTORAS_IMOVEIS.md v0.9 Draft |
| **Status** | Blocked |
| Projeto | NFS-e Imóveis |
| Project ID | ab6fb1ff-c777-428e-8b45-6712a008425d |
| Base deste incremento | 84a67caecd14da4ed0886972d12e03caf18069d3 |
| Primeiro incremento fiscal | 3f48422d093dde8f1ea8002fb5103faa078e51cf |
| Commit fiscal inspecionado | 078dd4fcee24af9e929527b46e7d03a379f0e034 |
| Commit de preparação inspecionado | 6159b1f39d772147be481760b592bebac66f69a7 |
| Arquitetura | Frontend Lovable; serviço separado Python/FastAPI/PostgreSQL |
| Publicação | Não publicada |
| LLM Prompts | false |

[Abrir projeto no Lovable](https://lovable.dev/projects/ab6fb1ff-c777-428e-8b45-6712a008425d)

## Mode Selection

**Recommendation:** default, em incrementos sequenciais no projeto existente, preservando a arquitetura aprovada.

**User decision:** modo confirmado anteriormente; pedido “proseguir para o proximo passo” autorizou o incremento. Nenhuma nova confirmação foi necessária.

Manifest de Design: 47 itens, com dependências entre empresa, revisão, idempotência, jobs e integração. Não houve revisão externa formal nem delegação para subagentes. O conector Lovable foi usado conforme pedido explícito do usuário.

## Summary

| Metric | Value |
|---|---|
| **Tasks Completed** | Preparação fiscal offline e correção dos achados independentes |
| **Files Created** | 25 caminhos retornados pelo diff incremental |
| **Files Modified** | 14 caminhos retornados pelo diff incremental |
| **Verify Gate** | Blocked: smoke oficial não executado; comando canônico do DEFINE pendente |
| **Execution Mode** | default |
| Testes Python independentes | 83 casos: 81 aprovados, 2 ignorados por ausência do CLI xmlsec1 |
| Prova criptográfica independente adicional | Python xmlsec 1.3.18 / libxmlsec 1.3.13: dois perfis verificam; adulteração e certificado incorreto recusados |
| Testes no Lovable | 83 Python sem skips; 16 frontend; tipos, build, E2E; PostgreSQL 9/9 |
| Produção fiscal | Não habilitada |

A fase anterior entregou API interna, repositório PostgreSQL, controle de acesso, importação e recuperação segura de confirmação. Este incremento substitui os stubs de XML por construção determinística de DPS, validação dos XSD oficiais e assinatura XMLDSIG testável localmente.

O resultado é uma biblioteca fiscal offline; não constitui emissão pela API nacional. O frontend continua com demonstração explícita quando não existe serviço configurado. O serviço Python ainda exige identidade, storage, cofre e infraestrutura reais.

## Task Execution

| Task | Manifest equivalente | Status | Evidence |
|---|---|---|---|
| Fixar esquemas oficiais por ambiente | 24–27, 40–41 | Implementado | Dois perfis, manifest e SHA-256 |
| Construir DPS com parâmetros explícitos | 24–27 | Implementado no escopo offline | Data completa, códigos fiscais, regime e município obrigatórios |
| Assinar e verificar localmente | 24–27, 32–39 | Implementado no escopo offline | Certificados sintéticos; verificação independente libxmlsec |
| Corrigir identidade CNPJ | Integração e testes | Corrigido | Regra E0004 lida do XLSX oficial: tipo 1 CPF, tipo 2 CNPJ |
| Rejeitar XML hostil | Integração e testes | Implementado | Tamanho limitado, UTF-8 estrito, sem DTD/entidades |
| Preparar transporte | 24–27 | Parcial | URL exata, TLS, sem redirect ou POST automático repetido |
| Vincular artefato ao snapshot | 23–29 | Implementado offline | Valor/competência/CNPJ/ambiente; sem mudança de estado |
| Transmitir e consultar API oficial | 24–27, 40–41 | Blocked | Envelope e algoritmo vigente não confirmados |
| Homologar municípios piloto | Aceite final | Blocked | Sem smoke autorizado/configurado em produção restrita |

Parâmetros fiscais ausentes não são inferidos da descrição do serviço. Competência mensal não é convertida automaticamente em dia 1. IBS/CBS, substituição e cancelamento não foram acrescentados como regras presumidas. O builder cobre um subconjunto de emissão normal; operações que exigirem campos adicionais permanecem pendentes de implementação/validação.

## Files Changed

Diff incremental inspecionado da base 84a67ca ao commit 078dd4f. O inventário abaixo é o retornado pelo conector, não substitui o manifest integral do Design.

| File | Action | Verification |
|---|---|---|
| `AGENTS.md` | Modify | Inspeção de fonte/diff; testes por componente |
| `BUILD_REPORT.md` | Modify | Inspeção de fonte/diff; testes por componente |
| `backend/app/domain/models.py` | Modify | Inspeção de fonte/diff; testes por componente |
| `backend/app/nfse/client.py` | Modify | Inspeção de fonte/diff; testes por componente |
| `backend/app/nfse/dps.py` | Create | Inspeção de fonte/diff; testes por componente |
| `backend/app/nfse/offline.py` | Create | Inspeção de fonte/diff; testes por componente |
| `backend/app/nfse/schemas/MANIFEST.json` | Create | Inspeção de fonte/diff; testes por componente |
| `backend/app/nfse/schemas/producao_restrita_20261020/CNC_v1.00.xsd` | Create | Inspeção de fonte/diff; testes por componente |
| `backend/app/nfse/schemas/producao_restrita_20261020/DPS_v1.01.xsd` | Create | Inspeção de fonte/diff; testes por componente |
| `backend/app/nfse/schemas/producao_restrita_20261020/NFSe_v1.01.xsd` | Create | Inspeção de fonte/diff; testes por componente |
| `backend/app/nfse/schemas/producao_restrita_20261020/evento_v1.01.xsd` | Create | Inspeção de fonte/diff; testes por componente |
| `backend/app/nfse/schemas/producao_restrita_20261020/pedRegEvento_v1.01.xsd` | Create | Inspeção de fonte/diff; testes por componente |
| `backend/app/nfse/schemas/producao_restrita_20261020/tiposCnc_v1.00.xsd` | Create | Inspeção de fonte/diff; testes por componente |
| `backend/app/nfse/schemas/producao_restrita_20261020/tiposEventos_v1.01.xsd` | Create | Inspeção de fonte/diff; testes por componente |
| `backend/app/nfse/schemas/producao_restrita_20261020/tiposSimples_v1.01.xsd` | Create | Inspeção de fonte/diff; testes por componente |
| `backend/app/nfse/schemas/producao_restrita_20261020/xmldsig-core-schema.xsd` | Create | Inspeção de fonte/diff; testes por componente |
| `backend/app/nfse/schemas/producao_v1_01_20260209/CNC_v1.00.xsd` | Create | Inspeção de fonte/diff; testes por componente |
| `backend/app/nfse/schemas/producao_v1_01_20260209/DPS_v1.01.xsd` | Create | Inspeção de fonte/diff; testes por componente |
| `backend/app/nfse/schemas/producao_v1_01_20260209/NFSe_v1.01.xsd` | Create | Inspeção de fonte/diff; testes por componente |
| `backend/app/nfse/schemas/producao_v1_01_20260209/evento_v1.01.xsd` | Create | Inspeção de fonte/diff; testes por componente |
| `backend/app/nfse/schemas/producao_v1_01_20260209/pedRegEvento_v1.01.xsd` | Create | Inspeção de fonte/diff; testes por componente |
| `backend/app/nfse/schemas/producao_v1_01_20260209/tiposCnc_v1.00.xsd` | Create | Inspeção de fonte/diff; testes por componente |
| `backend/app/nfse/schemas/producao_v1_01_20260209/tiposEventos_v1.01.xsd` | Create | Inspeção de fonte/diff; testes por componente |
| `backend/app/nfse/schemas/producao_v1_01_20260209/tiposSimples_v1.01.xsd` | Create | Inspeção de fonte/diff; testes por componente |
| `backend/app/nfse/schemas/producao_v1_01_20260209/xmldsig-core-schema.xsd` | Create | Inspeção de fonte/diff; testes por componente |
| `backend/app/nfse/secure_xml.py` | Create | Inspeção de fonte/diff; testes por componente |
| `backend/app/nfse/signing.py` | Create | Inspeção de fonte/diff; testes por componente |
| `backend/app/nfse/xml.py` | Modify | Inspeção de fonte/diff; testes por componente |
| `backend/app/ports.py` | Modify | Inspeção de fonte/diff; testes por componente |
| `backend/app/repository.py` | Modify | Inspeção de fonte/diff; testes por componente |
| `backend/pyproject.toml` | Modify | Inspeção de fonte/diff; testes por componente |
| `backend/tests/fixtures/official/anexo_i-sefin_adn-dps_nfse-snnfse_prodrest-v1-01-20261020.xlsx` | Create | Inspeção de fonte/diff; testes por componente |
| `backend/tests/test_contract.py` | Modify | Inspeção de fonte/diff; testes por componente |
| `backend/tests/test_interop.py` | Create | Inspeção de fonte/diff; testes por componente |
| `docs/nfse-integration-evidence.md` | Modify | Inspeção de fonte/diff; testes por componente |
| `docs/runbook.md` | Modify | Inspeção de fonte/diff; testes por componente |
| `scripts/verify.py` | Modify | Inspeção de fonte/diff; testes por componente |
| `src/lib/domain.ts` | Modify | Inspeção de fonte/diff; testes por componente |
| `src/test/domain.test.ts` | Modify | Inspeção de fonte/diff; testes por componente |

Os testes independentes usaram o backend anterior mais todas as fontes Python alteradas destes commits. Os esquemas e o XLSX foram copiados dos downloads oficiais independentes; os hashes conferiram com o manifest. Não se alterou código de produção para fazer os testes passarem na cópia.

## Drift Detected

| Drift | Decision | Action |
|---|---|---|
| Scaffold TanStack difere dos caminhos conceituais web/ | Adaptação técnica já prevista | Manter equivalentes nativos |
| Dois leiautes oficiais distintos | Não usar o mesmo XSD para ambos | Perfis separados por ambiente/versão |
| Série do XSD de produção não aceita série numérica no validador | Não modificar esquema oficial | Registrar incompatibilidade e bloquear perfil |
| XMLDSIG anterior passava apenas no verificador próprio | Exigir interoperabilidade | Corrigir C14N e testar libxmlsec independente |
| Identidade CNPJ aceitável pelo XSD, mas divergente da RN | Corrigir regra de negócio | Tipo 2 para CNPJ, teste contra fonte oficial |
| Integração HTTP oficial não capturada | Não inventar contrato | Transmissão e consulta continuam bloqueadas |

A identidade interna ainda usa prefixo de empresa com oito caracteres. Não foi demonstrada migração para vínculo integral nem congelamento durável de todos os parâmetros fiscais do ID oficial. Antes de transmissão real, fixar esses parâmetros na operação e provar que retentativas/consultas reutilizam exatamente a mesma identidade e bytes.

## Verification Results

### Incremental Verification

| Check | Method | Result |
|---|---|---|
| Baseline anterior | Sete suítes unittest | 51 casos: 50 aprovados, 1 skip |
| Primeiro incremento XML | Mesmas suítes com novos testes fiscais | 75/75 independentes |
| Incremento corrigido final | Oito suítes unittest | 83 casos: 81 aprovados, 2 skips; exit 0 |
| XMLDSIG independente adicional | Python xmlsec 1.3.18, libxmlsec 1.3.13 | SHA-256 e SHA-1 verificam; valor alterado e certificado errado falham; exit 0 |
| XMLDSIG CLI no Lovable | xmlsec1 1.3.7 | Dois testes aprovados; incluídos nos 83 sem skips |
| Frontend no Lovable | Vitest | 16/16 aprovados |
| Tipos, build e E2E no Lovable | Runner local | Aprovados, conforme receipt |
| PostgreSQL no Lovable | Banco temporário | 9/9 aprovados |
| Smoke nacional | Não executado | Blocked |

Comando independente final, em checkout temporário:

```bash
python -m unittest tests.test_domain tests.test_imports tests.test_isolation tests.test_emissions tests.test_contract tests.test_api tests.test_guards tests.test_interop -q
```

Resultado: Ran 83 tests; OK (skipped=2). Os dois skips são os testes CLI xmlsec1, ausente neste ambiente. A verificação adicional com o binding Python de libxmlsec foi executada separadamente e não foi contada como execução desses dois testes CLI.

Ambiente independente: Python 3.12, lxml 6.1.3, cryptography 50.0.2. A tentativa inicial com SignXML 5.2.0 identificou falha de interoperabilidade/canonicalização. A correção foi comprovada via libxmlsec; não se apresenta SignXML como prova verde.

Casos cobertos: XSD por ambiente, hashes, ordem de elementos, ID E0004, tpAmb, competência completa, recusa de CNPJ alfanumérico sem remoção silenciosa, alteração de valor/assinatura, certificado errado, wrapping/ID duplicado, DTD UTF-16/32, limites de XML e ataques de URL.

Os resultados de frontend, CLI e PostgreSQL são receipts do Lovable, separados da execução independente. Não foi possível repetir o servidor PostgreSQL temporário neste ambiente. A prévia externa anteriormente respondeu 401; não há aceite visual humano independente.

### Verify Gate

| Attribute | Value |
|---|---|
| **Kind** | smoke |
| **Command / Method** | O DEFINE ainda contém marcador de clarificação; smoke oficial não executado |
| **Exit / Result** | 5 — classificação de protocolo, não exit de comando executado |
| **Status** | Clarification pending |
| **Evidence** | Testes locais e criptográficos não substituem homologação da API nacional |

O runner local exige CLI de verificação independente; modo postgres exige banco dedicado e guardas de reset. Modo restricted permanece bloqueado sem contrato/credenciais. Não houve emissão real.

### Manual UX Receipt

N/A. Nenhum aceite humano formal de UX/acessibilidade foi coletado. E2E de demonstração não certifica integralmente o UX_STANDARD.

### Complementary Checks

As proteções anteriores permanecem: revisão por hash/versão, isolamento de empresa, origem/CSRF, idempotência, recuperação de resposta incerta por consulta e fencing de jobs. Nenhum teste desta etapa habilitou transmissão.

## Acceptance Test Verification

| ID | Scenario | Status | Evidence |
|---|---|---|---|
| AT-001 | Rascunho da empresa correta | Pass local/API | Regressão |
| AT-002 | Importar sem transmitir | Pass local/API | Regressão |
| AT-003 | Empresa obrigatória | Parcial | API isolada; aceite visual pendente |
| AT-004 | Rascunho distinto de emissão | Pass na demonstração | Labels/E2E reportado |
| AT-005 | Revisão dos dados críticos | Pass local | Versão/hash |
| AT-006 | Dados/eligibilidade bloqueiam envio | Pass local/API | Validação e parâmetros explícitos |
| AT-007 | Transmitir API oficial | Blocked | Contrato, certificado e infraestrutura |
| AT-008 | Impedir duplicidade | Pass nos testes locais | Idempotência/concorrência anterior |
| AT-009 | Aceite fiscal oficial | Blocked | Sem autorização nacional nesta execução |
| AT-010 | Rejeição fiscal oficial | Blocked | Testes offline não validam catálogo nacional |
| AT-011 | Timeout e recuperação | Pass local | Consulta e fencing |
| AT-012 | Dados de outra empresa | Pass local | API/RLS anteriores |
| AT-013 | Pilotos Bariri/Pederneiras | Blocked | Sem homologação |

## Advisor Ledger

None — nenhuma revisão externa formal. A inspeção independente encontrou e levou à correção do tipo CNPJ, DTD em UTF-16, interoperabilidade XMLDSIG e verificação de ambiente/ID.

## Issues Encountered

| Issue | Resolution | Impact |
|---|---|---|
| Swagger oficial inacessível | Registrar 503 na pesquisa e 403 no ambiente Lovable | Contrato HTTP não comprovado; sem afirmar indisponibilidade geral do serviço |
| XSD de produção: série com âncoras literais | Manter arquivo oficial intacto e teste reproduzível | Perfil de produção bloqueado neste validador |
| Assinatura passava no próprio verificador | C14N com cópia destacada e libxmlsec independente | Interoperabilidade offline comprovada nos perfis testados |
| Tipo de inscrição invertido | Regra E0004 oficial aplicada | ID CNPJ corrigido |
| DTD com codificação alternativa | UTF-8 estrito e checagem pós-parse | Casos hostis recusados |
| Sem binário xmlsec1 local | Distinguir dois skips e executar binding libxmlsec separadamente | Sem contagem inflada de testes |

## Deviations from Design

| Deviation | User Decision | Reason | Impact |
|---|---|---|---|
| Novos módulos dps, secure_xml, signing e offline | Concretização do Build autorizado | Separar construção, parsing e criptografia | Não altera stack |
| Perfis criptográficos testáveis, sem aprovação vigente | Não é redução de escopo aprovada | Evidência oficial insuficiente | Nenhum perfil libera transmissão |
| Serviço ainda sem implantação | Não é corte aprovado | Dependências reais ausentes | Build integral continua bloqueado |

## Blockers

| Blocker | Required Action | Owner |
|---|---|---|
| Contrato HTTP oficial | Capturar OpenAPI vigente e validar envelopes/respostas/erros | Executor técnico |
| Algoritmo vigente | Confirmar perfil criptográfico com fonte oficial atual | Técnico/responsável fiscal |
| XSD de produção | Confirmar versão compatível ou orientação oficial para série | Técnico/fornecedor nacional |
| Perfil fiscal por empresa | Cadastrar e validar códigos, regime, datas e campos exigidos pela operação | Responsável fiscal |
| Identidade e bytes imutáveis | Consolidar vínculo integral e parâmetros fiscais duráveis por operação | Executor técnico |
| Infraestrutura | Configurar identidade, storage privado, cofre, banco e hospedagem/worker | Responsável técnico |
| Certificado autorizado | Configurar por mecanismo seguro, sem envio pelo chat | Responsável autorizado |
| Homologação municipal | Smoke em produção restrita para Bariri/Pederneiras | Fiscal/técnico |
| Verify Gate do DEFINE | Fixar comando e evidência real de aceite | Responsável do projeto |
| Governança/retensão/recuperação | Concluir decisões e provar backup/restauração | Responsável do projeto |
| CI/manifest/UX | Consolidar fontes, pipeline e aceite formal | Executor/responsável |

## Preparação de ativação — incremento posterior

Pedido: “avançar e passe o passo a passo para prosseguir”. O usuário informou que ainda não tem hospedagem/banco contratados para esta aplicação. Nenhum provedor foi escolhido ou contratado automaticamente.

Commit: 6159b1f39d772147be481760b592bebac66f69a7.

| Arquivo | Resultado |
|---|---|
| docs/ativacao-homologacao.md | Oito etapas, responsáveis, evidências e checklist sem credenciais |
| scripts/preflight.py | Diagnóstico estático somente leitura, sem rede/banco; texto ou JSON; configuração presente nunca equivale a validação |
| backend/tests/test_preflight.py | Quatro testes independentes aprovados, exit 0 |
| scripts/verify.py | Runner inclui os novos testes |
| BUILD_REPORT.md | Receipt da execução no Lovable |

Verificação independente: python -m unittest tests.test_preflight -v, quatro testes aprovados. Execução python3 scripts/preflight.py: exit 1 esperado, NÃO PRONTO. Adaptadores de identidade, storage e cofre ausentes; parâmetros duráveis ausentes; contrato HTTP/cripto/XSD/smoke bloqueados. Nenhuma variável sensível foi exibida.

Receipt do Lovable para este incremento: 87 testes Python sem skips, 16 frontend, tipos, build e E2E aprovados. Não se afirma repetição independente de toda a suíte de 87 casos neste incremento.

Limite do preflight: é um inventário estático conservador, não uma prova de conectividade, implantação, segurança ou homologação. Ele não libera emissão.

Próxima decisão do usuário: escolher hospedagem para API Python/worker/PostgreSQL. Após essa decisão, fechar também identidade, armazenamento privado e cofre e implementar os adaptadores antes de tentar ativar o serviço. Custos e credenciais não foram assumidos.

## Certificado A1 e representação — 02/11/2026

Pedido do usuário: prosseguir com o certificado do escritório e a procuração já concedida. Tipo confirmado nesta execução: A1 (.pfx/.p12).

| Informação | Evidência / limite |
|---|---|
| Piloto | L'OR BLANC GESTORA DE BENS LTDA, CNPJ 14.168.985/0001-73 |
| Representante | Escritório, CNPJ 27.532.638/0001-20 |
| Acesso WEB | Captura fornecida pelo usuário mostra perfil representado e identificação do representante |
| Certificado real | Não recebido, aberto ou usado nesta execução |
| Acesso pela API | NÃO TESTADO; WEB não prova autorização na API nem no ambiente restrito |
| Commit inspecionado | 6c2d4268201577f5fb7baf6578a793df1983ce20 |
| Publicação/transmissão | Não realizadas |

Implementado no mesmo projeto, preservando o serviço Python separado:
- backend/app/nfse/certificado.py: carregamento PKCS#12 por bytes injetados; senha ocultada em repr e bloqueio de pickle; RSA 2048+, chave correspondente, validade, X.509 v3 e identidade SAN por OID ICP-Brasil 2.16.76.1.3.3. Cadeia ICP, revogação e autorização governamental permanecem não verificadas.
- backend/app/nfse/delegacao.py: contexto distingue emitente e signatário; resultado de autorização por outorgante/outorgado/serviço 00233/ambiente e tempo da consulta. Provedor oficial ausente bloqueia. Recibo WEB é informativo e não autoriza envio. Não se afirma que exista endpoint governamental autônomo para consultar procurações; a implementação real deverá seguir o contrato oficial de representação.
- backend/app/nfse/offline.py: integra contexto de assinatura, recusa terceiro identificado sem contexto e reuso entre empresas/ambientes; mantém CNPJ do cliente na DPS. O artefato continua sempre não transmissível.
- scripts/inspecionar_certificado.py: inspeção local somente leitura, senha por getpass, sem rede e sem gravação de dados. Resultado sempre NÃO PRONTO/API NÃO TESTADA; não é teste oficial.
- backend/tests/test_certificado.py: 15 novos testes com certificados sintéticos.
- scripts/verify.py: inclui testes novos.
- sdd/design-addendum-001-delegacao-a1.md, docs/ativacao-homologacao.md, docs/nfse-integration-evidence.md, BUILD_REPORT.md e AGENTS.md: decisões/evidências atualizadas.
- .lovable/north-star/north-star.md: gerado pelo ambiente Lovable; não representa validação fiscal das operações imobiliárias.

Verificações independentes, usando cópia do backend já verificado mais as fontes alteradas:
1. APP_ENV=test python -m unittest tests.test_certificado -v: 15/15 aprovados, exit 0.
2. APP_ENV=test python -m unittest tests.test_domain tests.test_imports tests.test_isolation tests.test_emissions tests.test_contract tests.test_api tests.test_guards tests.test_interop tests.test_preflight tests.test_certificado -q: 102 casos, 100 aprovados e 2 ignorados por ausência do CLI xmlsec1, exit 0.
3. python3 scripts/preflight.py: exit 1 esperado, NÃO PRONTO. Identidade/storage/cofre/parâmetros duráveis ausentes; contrato HTTP, cripto, XSD de produção e smoke bloqueados. Esse diagnóstico estático não foi ampliado para classificar toda a nova delegação.
4. Receipt do Lovable: 102 Python aprovados sem skips, com xmlsec1 disponível. Frontend e PostgreSQL não reexecutados nesta etapa, pois não foram alterados.

Ambiente independente: Python 3.12, cryptography 50.0.2, lxml 6.1.1, dependências API instaladas em ambiente temporário de verificação. Não foram usados certificados reais ou dados fiscais reais em testes.

Fontes: comunicado oficial de representação publicado em 31/10/2026 e Guia WEB v1.3, item 11. Reconsulta em 02/11/2026 manteve confirmação de acesso por representação. Swagger não capturado: recuperação web de produção inacessível e restrita 502; no Lovable, tentativa única retornou 403 em ambos. Isso descreve os ambientes de consulta, não prova indisponibilidade geral das APIs.

Limites: o provedor de autorização e o cofre continuam sem implementação real. A verificação estrutural de um PKCS#12 e o contexto offline não são validação ICP-Brasil, autorização oficial ou permissão para transmitir. É necessário fixar o contrato real e integrar a validação governamental, revogação, cadeia, armazenamento, infraestrutura e parâmetros fiscais antes do smoke restrito.

O modo default já autorizado foi mantido. Sem runtime LLM, sem revisão externa formal. O Verify Gate do DEFINE segue em clarificação pendente (classificação 5), e os ATs fiscais oficiais permanecem bloqueados.

## Final Status

### Overall: BLOCKED

- [x] Incremento offline implementado e inspecionado.
- [x] Testes independentes registrados com limites explícitos.
- [x] Achados críticos desta revisão corrigidos.
- [ ] Contrato e assinatura vigentes homologados.
- [ ] Infraestrutura e certificado configurados.
- [ ] Verify Gate e testes fiscais oficiais aprovados.
- [ ] Build integral concluído.

**Resultado:** biblioteca de preparação/validação/assinatura da DPS disponível no projeto; aplicação não publicada, sem transmissão de DPS e sem liberação para emissão fiscal real.

