# DEFINE: NFS-e Nacional para Gestoras de Imóveis

> Aplicação web em Lovable para emissão de NFS-e Nacional por Cliente e Escritório, com integração oficial via API, operação multiempresa e revisão obrigatória antes da transmissão.

## Metadata

| Attribute | Value |
|---|---|
| **Feature** | Emissão de NFS-e Nacional para Gestoras de Imóveis |
| **Date** | 2026-10-31 |
| **Author** | SDD Define by RDD |
| **Status** | Needs Clarification |
| **Clarity Score** | 14/15 |

---

## Problem Statement

Pequenas empresas gestoras de imóveis e o escritório contábil precisam reduzir o trabalho manual e o risco operacional na emissão de NFS-e Nacional. A solução deve permitir preparar, revisar, transmitir e acompanhar emissões por integração oficial, sem depender de automação de navegador e preservando o contexto correto da empresa em operação multiempresa.

---

## Target Users

| User | Role | Pain Point |
|---|---|---|
| Cliente | Usuário da própria gestora de imóveis | Precisa emitir e consultar NFS-e sem preencher manualmente o portal nacional a cada operação e sem lidar com complexidade técnica desnecessária |
| Escritório | Operador contábil multiempresa | Precisa preparar, revisar, emitir e acompanhar NFS-e de várias empresas sem risco de atuar no CNPJ errado e com menor retrabalho operacional |

---

## Goals

| Priority | Goal |
|---|---|
| **MUST** | Emitir NFS-e por integração oficial com a NFS-e Nacional, usando backend seguro e sem RPA do portal web como mecanismo principal |
| **MUST** | Suportar Cliente e Escritório com perfis distintos, isolamento por empresa e contexto da empresa ativa inequívoco |
| **MUST** | Exigir revisão final da empresa, tomador, operação, valor e demais dados críticos antes de qualquer transmissão |
| **MUST** | Suportar lançamento manual e importação Excel/CSV para criação de rascunhos de emissão |
| **MUST** | Tratar e exibir estados de rascunho, validação, transmissão, emissão, rejeição e erro técnico de forma distinta |
| **MUST** | Homologar inicialmente o fluxo para Bariri/SP e Pederneiras/SP em ambiente de produção restrita antes da liberação em produção |
| **SHOULD** | Permitir consulta de histórico e reutilização segura de dados anteriores sem copiar silenciosamente campos críticos |
| **COULD** | Preparar pontos de extensão para futuras integrações bancárias e sistemas imobiliários sem implementá-las no MVP |

---

## Success Criteria

- [ ] 100% dos caminhos normais de emissão passam por revisão final explícita antes da transmissão à API Nacional.
- [ ] O sistema permite criar rascunho por lançamento manual e por importação Excel/CSV.
- [ ] Um usuário Cliente acessa somente a empresa autorizada, e um usuário Escritório visualiza de forma persistente a empresa/CNPJ ativo durante preparação, revisão, emissão e cancelamento quando aplicável.
- [ ] O fluxo de homologação consegue transmitir emissões válidas de Bariri/SP e Pederneiras/SP em produção restrita e distinguir sucesso de rejeição.
- [ ] Toda rejeição recebida da integração é apresentada com mensagem acionável em linguagem simples e detalhe técnico secundário disponível.
- [ ] O sistema impede duplo envio perceptível durante uma transmissão em andamento e mantém estado de processamento até resposta ou falha controlada.
- [ ] Rascunho salvo e NFS-e efetivamente emitida permanecem semanticamente e visualmente distintos em todos os fluxos do MVP.

---

## Acceptance Tests

| ID | Pattern | Criterion (EARS) | Gate (`kind`) |
|---|---|---|---|
| AT-001 | Event-driven | **When** um usuário autorizado iniciar uma nova emissão, o sistema **shall** criar ou abrir um rascunho associado à empresa ativa correta | test |
| AT-002 | Event-driven | **When** um arquivo Excel/CSV suportado for importado com registros válidos, o sistema **shall** criar rascunhos de emissão correspondentes sem transmitir automaticamente à API Nacional | test |
| AT-003 | Unwanted | **If** um usuário Escritório tentar concluir uma emissão sem contexto de empresa ativa inequívoco, **then** o sistema **shall** bloquear a transmissão e exigir seleção/confirmação da empresa | test |
| AT-004 | State-driven | **While** uma NFS-e estiver em rascunho, o sistema **shall** apresentá-la como não transmitida e não emitida | test |
| AT-005 | Event-driven | **When** o usuário avançar para revisão final, o sistema **shall** exibir empresa/CNPJ, tomador, tipo de operação, valor e demais dados críticos necessários à emissão em bloco revisável | test |
| AT-006 | Unwanted | **If** houver campo obrigatório ausente ou validação crítica inválida, **then** o sistema **shall** impedir a transmissão e indicar o ponto a corrigir | test |
| AT-007 | Event-driven | **When** o usuário confirmar deliberadamente a emissão após a revisão final, o backend **shall** transmitir a DPS pela integração oficial da NFS-e Nacional | smoke |
| AT-008 | State-driven | **While** uma transmissão estiver em andamento, o sistema **shall** indicar estado de processamento e impedir novo envio equivalente pelo mesmo fluxo | test |
| AT-009 | Event-driven | **When** a API Nacional retornar emissão aceita, o sistema **shall** registrar o resultado como emitido e disponibilizar os dados de retorno relevantes ao usuário | smoke |
| AT-010 | Unwanted | **If** a API Nacional retornar rejeição de negócio, **then** o sistema **shall** registrar estado de rejeição, apresentar orientação acionável e manter o detalhe técnico acessível de forma secundária | smoke |
| AT-011 | Unwanted | **If** ocorrer falha técnica, timeout ou indisponibilidade na integração, **then** o sistema **shall** registrar erro técnico sem marcar a NFS-e como emitida e oferecer caminho seguro para nova tentativa quando aplicável | smoke |
| AT-012 | Unwanted | **If** um usuário Cliente tentar acessar dados de outra empresa, **then** o sistema **shall** negar o acesso sem expor informações da empresa não autorizada | test |
| AT-013 | Event-driven | **When** o fluxo for executado em produção restrita para empresa homologada de Bariri/SP ou Pederneiras/SP, o sistema **shall** usar a configuração e os parâmetros válidos do ambiente e município correspondentes | smoke |

---

## Clarifications

### Session 2026-10-31

- [x] (Done signal / Verify Gate) Existe projeto/repositório com comando real de teste? → Não; o projeto começará do zero no Design/Build. Integrado em Verify Gate, Technical Context e Status.

---

## Verify Gate

```yaml
verify_gate:
  kind: smoke
  cmd: "[NEEDS CLARIFICATION: definir no Design/Build o comando real de smoke test do projeto após criação do repositório]"
  pass_when: "exit 0"
  threshold: "—"
  manual_fallback: "—"
```

---

## Out of Scope

- Automação do portal nacional por navegador/RPA como arquitetura principal.
- Integração bancária automática.
- Integração com sistemas de gestão imobiliária de terceiros.
- Conciliação automática de recebimentos.
- Emissão totalmente autônoma sem revisão humana.
- Dashboard financeiro avançado.
- Cobrança ou assinatura dentro do sistema.
- Aplicativo mobile nativo.
- Automações complexas baseadas em IA.
- Definição de regra fiscal específica para cada natureza de operação imobiliária não sustentada pela documentação ou por requisitos posteriores.

---

## Constraints

| Type | Constraint | Impact |
|---|---|---|
| Technical | Frontend em Lovable | A experiência de usuário será construída no Lovable; decisões detalhadas de stack ficam para Design |
| Technical | Integração fiscal em backend seguro separado | Certificados, credenciais, assinatura e chamadas sensíveis não podem depender do frontend cliente |
| Technical | Uso da API oficial da NFS-e Nacional | A solução deve acompanhar contratos, leiautes, XSDs, regras de negócio, autenticação e versionamento oficiais |
| Technical | Produção restrita antes de produção | Fluxos devem ser homologados antes da liberação operacional |
| Scope | Municípios iniciais: Bariri/SP e Pederneiras/SP | O MVP não assume cobertura nacional irrestrita |
| UX | Revisão final obrigatória | Não pode existir caminho normal de transmissão sem conferência explícita dos dados críticos |
| UX | Multiempresa com contexto inequívoco | Operação pelo Escritório deve preservar empresa/CNPJ ativo de forma persistente |
| Timeline | N/A | Prazo não foi definido nesta fase |
| Resource | N/A | Equipe, orçamento e capacidade não foram definidos nesta fase |
| Other | Regras fiscais imobiliárias não presumidas | Aluguel, venda de imóvel e arrendamento não devem ser tratados como fluxos fiscais idênticos sem regra funcional/fiscal validada |

---

## Technical Context

| Aspect | Value | Notes |
|---|---|---|
| **Deployment Location** | Frontend Lovable + backend seguro TBD | Não há repositório, stack de backend ou infraestrutura definidos ainda |
| **KB Domains** | NFS-e Nacional, DPS, API Emissor Público Nacional, autenticação/certificado, multiempresa, UX fiscal | Documentação oficial e UX canônico são fontes relevantes para Design |
| **IaC Impact** | TBD | O projeto começará do zero; recursos de infraestrutura serão definidos no Design |
| **LLM Prompts** | false | O MVP não utiliza chatbot, agente, RAG, classificação ou geração por LLM em runtime |

---

## Assumptions

| ID | Assumption | If Wrong, Impact | Validated? |
|---|---|---|---|
| A-001 | A API Nacional continuará sendo o canal oficial de integração aplicável ao escopo do MVP | A arquitetura de integração precisará ser revista | yes |
| A-002 | As empresas piloto poderão ser credenciadas/autorizadas para operar no ambiente necessário da NFS-e Nacional | Homologação e produção ficam bloqueadas | no |
| A-003 | Bariri/SP e Pederneiras/SP estarão aptos ao fluxo nacional necessário para as empresas piloto e operações selecionadas | Pode ser necessário adaptar escopo municipal ou fluxo | no |
| A-004 | Os arquivos Excel/CSV de entrada terão layout definido pelo próprio produto ou por importador configurável no MVP | O mecanismo de importação precisará de regra adicional | no |

---

## Clarity Score Breakdown

| Element | Score (0-3) | Notes |
|---|---:|---|
| Problem | 3 | Dor, usuários afetados e resultado pretendido estão claros |
| Users | 3 | Cliente e Escritório possuem papéis e riscos distintos definidos |
| Goals | 3 | Objetivos do MVP e prioridades estão suficientemente delimitados |
| Success | 3 | Critérios são observáveis e verificáveis sem inventar métricas de desempenho não fornecidas |
| Scope | 2 | Escopo funcional está claro, mas o Verify Gate executável depende da criação do repositório no Design/Build |
| **Total** | **14/15** | |

Minimum to proceed: **12/15**.

---

## Open Questions

- Definir o comando real de teste/smoke do projeto após a criação do repositório e da stack no Design. Esta questão é bloqueante apenas para fechar formalmente o Verify Gate automatizado; não altera o escopo funcional definido acima.

---

## Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 0.9 | 2026-10-31 | SDD Define by RDD | Initial draft; funcionalmente definido, aguardando comando real do Verify Gate |
