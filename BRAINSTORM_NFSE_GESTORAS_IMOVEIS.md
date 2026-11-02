<!--
CANONICAL OUTPUT ASSET — SDD Brainstorm by RDD
Use this file as the structural source of truth for the final Brainstorm.
Replace placeholders in {BRACES}, remove optional sections that do not apply,
and preserve section order/titles unless the user explicitly requests otherwise.
-->

# BRAINSTORM: NFS-e Nacional para Gestoras de Imóveis

> Exploratory session to clarify intent and approach before requirements capture

## Metadata

| Attribute | Value |
|---|---|
| Feature | Emissão de NFS-e Nacional para Gestoras de Imóveis |
| Date | 2026-10-31 |
| Author | brainstorm-agent |
| Status | Handoff Ready |

## Initial Idea

**Raw Input:** "o projeto é criar uma aplicação simples com o lovable para a emissão de NFS-e Nacional para pequenas empresas gestora de imoveis, com recebimentos de alugueis, vendas de imoveis, arrendamento."

**Context Gathered:**
- Objetivo principal: automatizar a emissão de NFS-e no ambiente nacional e transformar essa automação em um serviço oferecido aos clientes.
- Usuários principais do MVP: Cliente e Escritório, com perfis e permissões distintos.
- Modelo de automação: híbrido no uso, porém com emissão oficial via API Nacional desde o início.
- Origem dos dados: híbrida, contemplando lançamento manual, importação Excel/CSV e possibilidade de integrações futuras.
- Municípios iniciais para homologação operacional: Bariri/SP e Pederneiras/SP.
- Critério de sucesso confirmado: emissão via integração oficial, importação/automação dos dados e operação multiusuário/multiempresa com segurança.
- UX canônico já existente no projeto, com revisão final obrigatória antes da emissão, distinção de estados e destaque persistente da empresa ativa.
- Pesquisa oficial realizada no Portal Nacional da NFS-e identificou documentação de produção para APIs do Emissor Público Nacional, APIs do ADN, XSDs, leiautes, anexos de domínio e ambientes separados de produção e produção restrita.
- A documentação oficial atual de produção lista o "Manual de Contribuintes - Emissor Público", "Guia de Utilização das APIs do ADN", esquemas XSD e anexos de leiaute da DPS/NFS-e.
- A página oficial de APIs confirma ambientes separados de produção restrita (homologação/testes) e produção.
- Em 29/10/2026, o Portal Nacional informou que, para competências a partir de 01/11/2026, ME e EPP optantes pelo Simples Nacional devem emitir NFS-e exclusivamente pelo Emissor Nacional, Web ou API.

**Technical Context Observed (for Define):**

| Aspect | Observation | Implication |
|---|---|---|
| Likely Location | Projeto Lovable + backend seguro separado; caminho de repositório não fornecido | O Define deverá separar claramente frontend, backend e integração com a API Nacional |
| Relevant KB Domains | NFS-e Nacional, DPS, API Emissor Público Nacional, autenticação/certificado digital, multiempresa, UX fiscal | Requisitos precisam tratar emissão, consulta, eventos, erros, isolamento de empresas e revisão final |
| IaC Patterns | N/A | Infraestrutura e estratégia de deploy ainda não foram fornecidas; não inferir tecnologia além do Lovable no frontend |

## Discovery Questions & Answers

| # | Question | Answer | Impact |
|---|---|---|---|
| 1 | Qual é o principal problema que você deseja resolver com essa aplicação? | Permitir a automatização da emissão das NFS-e no site nacional e oferecer esse serviço ao cliente | Define o produto como automação operacional com valor comercial para o escritório |
| 2 | Quem será o usuário principal no MVP? | Ambos: Cliente e Escritório | Exige perfis distintos, multiempresa e segregação de contexto |
| 3 | Qual deve ser o nível de automação no MVP? | Híbrida | Algumas operações podem ser mais automatizadas, preservando revisão quando necessária |
| 4 | Qual deve ser a principal origem dos dados que vão gerar as NFS-e? | Híbrido | MVP precisa aceitar lançamento manual e importação; integrações ficam evolutivas |
| 5 | Você tem material que possa ancorar a solução? | Pesquisar no site da NFS-e Nacional os manuais e a API de acesso | A solução foi ancorada na documentação oficial do Sistema Nacional NFS-e |
| 6 | Qual deve ser a abrangência municipal do MVP? | Pederneiras e Bariri | Homologação inicial controlada nesses dois municípios |
| 7 | Como você vai considerar que o MVP deu certo? | Tudo: emissão via integração oficial, importação/automação e operação multiusuário/multiempresa segura | Define o sucesso funcional mínimo da primeira versão |
| 8 | Qual abordagem você confirma? | A — API Nacional nativa desde o início | Elimina RPA do portal como arquitetura principal |
| 9 | Confirma o corte de escopo YAGNI? | Sim | Mantém o MVP enxuto e posterga integrações complexas |
| 10 | O conceito, escopo e componentes representam corretamente o que deseja construir? | Sim | Checkpoint 1 aprovado sem ajustes |
| 11 | Confirma fluxo, tratamento de rejeições e separação frontend/backend? | Sim | Checkpoint 2 aprovado sem ajustes |

## Sample Data Inventory

| Type | Location | Count | Notes |
|---|---|---:|---|
| Input files | N/A | 0 | Nenhuma planilha operacional real foi fornecida nesta fase |
| Output examples | Portal Nacional NFS-e / documentação oficial | múltiplos | Guias, manuais, leiautes e esquemas oficiais serão referência funcional |
| Ground truth | Portal Nacional NFS-e | múltiplos | Documentação oficial de produção, produção restrita e notícia de obrigatoriedade do Simples Nacional |
| Related code | N/A | 0 | Nenhum repositório ou código existente foi fornecido |

**How samples will be used:**
- A documentação oficial da NFS-e Nacional será usada no Define como base para requisitos de integração, leiaute, homologação, retorno de erros, consulta e eventos.
- Os arquivos UX já existentes do projeto serão usados como fonte canônica de experiência e não como fonte de regra fiscal.

## Approaches Explored

### Approach A: API Nacional nativa desde o início — Recommended

**Description:** O Lovable funciona como camada de interface, enquanto um backend seguro integra diretamente com as APIs oficiais da NFS-e Nacional. A aplicação prepara a DPS, valida, apresenta revisão final e transmite pela API oficial.

**Pros:**
- Usa o canal oficial de integração destinado a sistemas próprios/ERPs.
- Evita dependência de automação frágil por navegador.
- Permite evolução para multiempresa, consulta, eventos e integrações futuras.
- É compatível com produção restrita para homologação antes da entrada em produção.

**Cons:**
- Exige backend seguro, autenticação/certificado e aderência a XML/XSD e regras de negócio.
- Exige tratamento disciplinado de rejeições, versionamento de leiautes e mudanças da plataforma nacional.

**Why Recommended:** É a arquitetura mais alinhada ao objetivo de oferecer um serviço confiável e escalável aos clientes, reduzindo dependência da interface Web do portal nacional.

### Approach B: Automação do portal nacional por navegador/RPA

**Description:** A aplicação prepararia os dados e uma automação navegaria no Emissor Nacional Web para preencher e emitir as notas.

**Pros:**
- Pode reduzir o esforço inicial em um protótipo muito simples.

**Cons:**
- Frágil a mudanças de interface, autenticação e comportamento do portal.
- Menor escalabilidade e previsibilidade operacional.
- Duplica uma função já atendida por API oficial.

### Approach C: API oficial com operação assistida e implantação gradual

**Description:** Usar a API oficial desde o início, mas começar com lançamento manual e importação Excel/CSV, evoluindo depois para integrações bancárias e sistemas imobiliários.

**Pros:**
- Reduz risco operacional no MVP.
- Permite validar o processo ponta a ponta em Bariri e Pederneiras.
- Preserva arquitetura para automações mais profundas.

**Cons:**
- Parte da captura de dados continua assistida no início.
- Exige evolução posterior para atingir automação de ponta a ponta.

## Selected Approach

| Attribute | Value |
|---|---|
| Chosen | Approach A — API Nacional nativa desde o início |
| User Confirmation | Confirmado na conversa em 2026-10-31 |
| Reasoning | O usuário quer que a emissão oficial já ocorra via API Nacional, evitando automação de navegador como base do produto |

## Key Decisions Made

| # | Decision | Rationale | Alternative Rejected |
|---|---|---|---|
| 1 | Usar a API oficial da NFS-e Nacional como mecanismo de emissão | Maior robustez, escalabilidade e aderência ao canal oficial | RPA do portal Web |
| 2 | Lovable será a camada de interface | Atende a intenção explícita de construir a aplicação com Lovable | Frontend tradicional fora do Lovable, não explorado |
| 3 | Manter backend seguro separado do frontend | Credenciais, certificados e transmissão fiscal não devem ficar expostos no cliente | Integração fiscal sensível diretamente no frontend |
| 4 | Atender Cliente e Escritório | O serviço precisa funcionar tanto para a empresa quanto para operação multiempresa do escritório | Produto exclusivo para um único perfil |
| 5 | Homologar inicialmente Bariri/SP e Pederneiras/SP | Reduz o risco do MVP e permite validar parâmetros municipais controladamente | Liberação nacional irrestrita no primeiro ciclo |
| 6 | Permitir entrada manual e Excel/CSV no MVP | Entrega valor sem depender de integrações externas desde o início | Integração bancária/imobiliária obrigatória no MVP |
| 7 | Revisão final obrigatória antes da transmissão | Decisão já estabelecida no UX canônico e confirmada no fluxo | Emissão totalmente silenciosa sem revisão |
| 8 | Diferenciar rascunho, validação, transmissão, emitida, rejeitada e erro técnico | Evita confundir salvamento interno com emissão oficial | Estado único ou genérico de processamento |

## Features Removed (YAGNI)

| Feature Suggested | Reason Removed/Deferred | Can Add Later? |
|---|---|---|
| Integração bancária automática | Não é necessária para provar emissão oficial e operação multiempresa no MVP | Yes |
| Integração com sistemas de gestão imobiliária | Depende de fornecedores e contratos ainda não definidos | Yes |
| Conciliação automática de recebimentos | Aumenta complexidade antes de validar emissão ponta a ponta | Yes |
| Emissão totalmente sem intervenção humana | Contraria o estágio inicial de homologação e a revisão crítica definida para o produto | Yes |
| Dashboard financeiro avançado | Não resolve o problema central de emissão no primeiro ciclo | Yes |
| Cobrança/assinatura dentro do sistema | Monetização transacional não é requisito técnico do primeiro MVP | Yes |
| Aplicativo mobile nativo | O UX já prevê web responsiva; app nativo não é necessário agora | Yes |
| Automações complexas por IA | Não são necessárias para o fluxo fiscal básico e aumentariam risco/escopo | Yes |

## Incremental Validations

| Section | Presented | User Feedback | Adjusted? |
|---|---|---|---|
| Checkpoint 1 — conceito, escopo e componentes | Yes | Confirmado como correto | No |
| Checkpoint 2 — fluxo, falhas e dependências | Yes | Confirmado, inclusive tratamento de rejeições e separação frontend/backend | No |

## Suggested Requirements for /define

### Problem Statement (Draft)

Pequenas gestoras de imóveis e o escritório contábil precisam emitir NFS-e Nacional com menos trabalho manual e menor risco operacional, usando uma aplicação simples em Lovable integrada oficialmente à plataforma nacional.

### Target Users (Draft)

| User | Pain Point |
|---|---|
| Cliente da gestora de imóveis | Precisa emitir NFS-e sem depender de navegar e preencher manualmente o portal nacional a cada operação |
| Escritório contábil | Precisa operar emissões de múltiplas empresas com segurança, contexto inequívoco e menor retrabalho |

### Success Criteria (Draft)

- [ ] Emitir NFS-e de empresas de Bariri/SP e Pederneiras/SP por integração oficial com a NFS-e Nacional, sem depender de automação de navegador.
- [ ] Permitir lançamento manual e importação Excel/CSV para gerar rascunhos de emissão.
- [ ] Permitir operação por Cliente e Escritório com perfis distintos e segregação multiempresa.
- [ ] Exigir revisão final dos campos críticos antes da transmissão.
- [ ] Registrar e apresentar claramente estados de rascunho, validação, transmissão, sucesso, rejeição e erro técnico.
- [ ] Exibir rejeições em linguagem acionável, preservando código/detalhe técnico de forma secundária.
- [ ] Homologar o fluxo em ambiente de produção restrita antes de liberar produção.
- [ ] Métricas quantitativas de tempo economizado, taxa de rejeição e volume de emissões: TBD no Define.

### Constraints Identified

- Lovable será usado para a camada de interface.
- Integração fiscal sensível deve ficar em backend seguro.
- A solução deve usar a API oficial da NFS-e Nacional.
- O MVP deve respeitar leiautes, XSDs, regras de negócio e autenticação vigentes na plataforma nacional.
- O MVP operacional será inicialmente homologado para Bariri/SP e Pederneiras/SP.
- O contexto da empresa ativa deve permanecer inequívoco no uso multiempresa.
- Revisão final antes da emissão é obrigatória.
- Regras fiscais específicas por tipo de operação imobiliária não foram definidas nesta fase e não devem ser presumidas.
- A documentação técnica da NFS-e sofre evolução; o Define deve tratar versionamento/compatibilidade como dependência externa.

### Out of Scope (Confirmed)

- Integração bancária automática.
- Integração com sistemas imobiliários de terceiros.
- Conciliação automática de recebimentos.
- Emissão totalmente autônoma sem revisão humana.
- Dashboard financeiro avançado.
- Cobrança ou assinatura dentro do sistema.
- Aplicativo mobile nativo.
- Automações complexas baseadas em IA.

## Session Summary

| Metric | Value |
|---|---:|
| Questions Asked | 11 |
| Approaches Explored | 3 |
| Features Removed (YAGNI) | 8 |
| Validations Completed | 2 |

## Next Step

Execute o **SDD Define by RDD**.
