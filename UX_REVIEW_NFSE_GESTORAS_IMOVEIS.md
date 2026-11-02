# UX REVIEW: NFS-e Nacional para Gestoras de Imóveis

> Revisão documental de UX/CX após o Define e antes do Design. Metodologia de Roberto Dias Duarte.

## Metadata

| Atributo | Valor |
|---|---|
| Feature | Emissão de NFS-e Nacional para Gestoras de Imóveis |
| Data | 2026-10-31 |
| Autor | ux-review |
| DEFINE | 06-DEFINE_NFSE_GESTORAS_IMOVEIS.md, versão 0.9 |
| UX_STANDARD | 03-UX_STANDARD-1-.md |
| UX_STANDARD Version | 1.0.0 — Approved |
| Modelo | 02-UX_REVIEW_TEMPLATE-1-.md |
| Procedimento específico | 04-ux-review-nfse-gestoras.zip → ux-review/SKILL.md |
| Status | BLOCKED FOR DESIGN |

## UX Summary

O DEFINE cobre a revisão final, a identificação da empresa e os estados básicos da emissão. Há cinco lacunas documentais bloqueantes nos fluxos de recuperação, importação parcial, mudança de contexto, operação não validada e acesso negado. A recomendação é tornar esses comportamentos verificáveis antes de consolidar o Design; não foi constatado defeito de interface implementada, pois não há telas ou aplicação disponíveis.

## Sources and Evidence

| Fonte | Papel | Versão/estado | Evidência usada |
|---|---|---|---|
| DEFINE | Escopo e aceitação | 0.9; Needs Clarification; 14/15 | AT-001 a AT-013, Goals, Constraints, Assumptions e Out of Scope |
| UX_STANDARD | Fonte canônica | 1.0.0; Approved | Regras UX-CORE, NAV, FORM, INT, STATE, COPY, VIS, DATA, A11Y e RESP |
| UX_REVIEW_TEMPLATE | Estrutura | Anexo sem versão declarada | Seções e gate de saída |
| BRAINSTORM | Intenção e limites | Handoff Ready, 31/10/2026 | Manual + importação, dois perfis operacionais, API oficial, MVP municipal |
| GOVERNANCA_REVIEW | Riscos correlatos | Revisão de 31/10/2026 | F01: resultado desconhecido; F02: elegibilidade; G07: aprovação distinta ainda proposta; G10: reimportação |
| Skill específica no ZIP | Procedimento do projeto | Sem versão declarada | Jornada, riscos críticos, estados e gate |

Leitura integral das fontes textuais acima. O procedimento específico anexado e o padrão deste projeto prevalecem sobre o resumo genérico da skill instalada: não se presume paleta dourada, dois caminhos de emissão ou outro comportamento de projeto diferente.

**Critério de evidência:** CONFORME significa requisito documental coberto, sem validar implementação. MUST indica uma lacuna funcional essencial identificada, com cenário concreto; não comprova falha em software existente. NAO AVALIAVEL indica que a conclusão depende de tela, protótipo, medição ou decisão ainda ausente. Recomendações de governança continuam propostas, sem aceite presumido. Não se valida incidência tributária, contrato atual da API ou habilitação municipal nesta revisão.

## User and Context

| Campo | Valor |
|---|---|
| Usuários | Cliente da própria gestora e Escritório multiempresa |
| Administrador | Previsto no padrão; detalhamento funcional ausente do DEFINE; não acrescentado ao MVP por inferência |
| Objetivo | Preparar, revisar, transmitir e acompanhar a nota da empresa correta |
| Dor | Retrabalho e risco de confundir empresa, tomador, valor, natureza da operação e resultado oficial |
| Negócio/CX | Serviço simples, confiável e recuperável, com suporte acionável |
| Dispositivos | Desktop principal; web no celular para consulta e emissão simples, conforme padrão; app nativo fora do escopo |
| Restrições | Lovable na interface; backend seguro; API oficial; Bariri/SP e Pederneiras/SP como pilotos, sujeitos à validação |

## Journey Map

| Etapa | Intenção | Emoção/Risco | Fricção | Necessidade da interface | Recuperação |
|---|---|---|---|---|---|
| Before | Saber se pode emitir | Insegurança sobre operação e habilitação | Configuração ou regra pendente | Empresa, ambiente e disponibilidade claros | Explicar pendência e encaminhar ao responsável |
| Entry | Entrar na empresa correta | Medo de trocar CNPJ | Seleção desnecessária ou ambígua | Cliente entra na autorizada; Escritório vê seletor persistente | Retornar a contexto autorizado sem revelar terceiros |
| Core Action | Preencher ou importar | Erro de valor/tomador; perda de trabalho | Campos técnicos e linhas inválidas | Formulário progressivo, validação local e prévia de importação | Corrigir campos/linhas preservando dados e origem |
| Feedback | Saber se a ação foi recebida | Confundir salvar com emitir | Estados genéricos | Salvamento separado da transmissão; processamento perceptível | Retomar acompanhamento sem repetir envio |
| Recovery | Resolver rejeição ou timeout | Duplicidade e emissão incerta | Retry indiscriminado | Separar rejeição confirmada de resultado desconhecido | Consultar situação; só permitir tentativa segura após esclarecimento |
| Completion | Confirmar emissão | Falsa conclusão | Retorno técnico sem resultado claro | Confirmação persistente e dados oficiais disponíveis | Se documento não carregar, repetir consulta/download, sem reemitir |
| Follow-up | Consultar ou reaproveitar | Copiar dado antigo ou cancelar errado | Histórico denso e ações ambíguas | Busca simples, status textual e reutilização revisável | Novo rascunho; evento fiscal somente se incluído e confirmado |

## Canonical Conformance

| Regra canônica | Status | Evidência | Observação |
|---|---|---|---|
| UX-NAV-001; UX-VIS-004; UX-ANTI-002 | CONFORME | Goals e Success Criteria; AT-003/005 | Empresa/CNPJ persistente exigido para Escritório; comprovar nas telas |
| UX-FORM-002/008/009; UX-ANTI-001 | CONFORME | AT-005/006/007 | Revisão em bloco e confirmação deliberada antes da transmissão |
| UX-STATE-008; UX-ANTI-004 | CONFORME | AT-004 e Success Criteria | Rascunho salvo distinto de transmitido/emitido |
| UX-INT-006; UX-STATE-001 | CONFORME | AT-008 | Processamento e prevenção de duplo envio pelo mesmo fluxo; retomada permanece em M01 |
| UX-COPY-001/003/004; UX-STATE-003; UX-ANTI-003 | CONFORME | AT-010 | Rejeição de negócio acionável com detalhe secundário; timeout exige M01 |
| UX-CORE-002/004/010 | MUST | AT-011 agrupa falha, timeout e indisponibilidade | M01: não distingue resultado desconhecido de falha confirmada |
| UX-STATE-005 | MUST | AT-002 só descreve registros válidos | M02: faltam resultado misto e recuperação por linha |
| UX-NAV-004; UX-CORE-004/007 | MUST | AT-001/003 preservam vínculo, mas não definem troca durante edição | M03: falta feedback e proteção do trabalho no contexto anterior |
| UX-INT-001; UX-FORM-004 | MUST | Constraints proíbe presumir equivalência fiscal; A-002/003 não validadas | M04: falta experiência para operação/contexto ainda não liberado |
| UX-STATE-006 | MUST | AT-012 exige negar sem expor; não especifica mensagem/retorno | M05: bloqueio seguro está coberto, recuperação da jornada não |
| UX-NAV-003 | NAO AVALIAVEL | Perfis distintos sem fluxo de entrada | Exigir entrada direta do Cliente com uma empresa; não presumir seletor indevido |
| UX-FORM-001; UX-INT-003; UX-VIS-003 | NAO AVALIAVEL | AT-006 prevê bloqueio, sem forma/tempo de apresentação | Formulário progressivo, validação discreta e alerta multimodal a verificar no protótipo |
| UX-INT-002/007; UX-ANTI-005 | NAO AVALIAVEL | Cancelamento citado apenas como “quando aplicável” | Não inferir inclusão; se houver, proteção contextual é obrigatória |
| UX-FORM-006/007 | SHOULD / NAO AVALIAVEL | Autosave não especificado | Recomendar autosave; se adotado, seus estados são obrigatórios |
| UX-STATE-002/004 | SHOULD | Histórico é SHOULD; AT-009 só prevê retorno relevante | Completar vazio, sucesso persistente e próximos passos no Design; sem afirmar implementação incompleta |
| UX-STATE-007 | SHOULD | AT-006/008 exigem bloquear ações | Explicar indisponibilidade; não depender de tooltip em botão inacessível |
| UX-DATA-001/002/003/004; UX-NAV-002/005 | SHOULD | Histórico/reutilização em Goals, sem navegação detalhada | Home enxuta, busca e filtros sob demanda |
| UX-INT-004/005; UX-ANTI-006 | SHOULD / CONFORME | Goal SHOULD proíbe cópia silenciosa de campos críticos; revisão universal | Oferta de reutilização é SHOULD; envio revisado é obrigatório se oferecida |
| UX-FORM-003/005; UX-VIS-002/020/021 | SHOULD | Sem telas | Priorizar básicos, agrupar e expandir detalhes técnicos |
| UX-VIS-001; UX-COPY-005/006 | NAO AVALIAVEL | Ação deliberada prevista, sem CTAs/layout | Validar rótulos e predominância visual |
| UX-A11Y-001 a UX-A11Y-007 | NAO AVALIAVEL | Sem protótipo, DOM ou medições | Não declarar WCAG atendida |
| UX-RESP-001 a UX-RESP-005; UX-DATA-005 | NAO AVALIAVEL | Sem layouts; app nativo excluído | Exclusão de app nativo não exclui web responsiva |
| UX-MOTION-001/002/003 | NAO AVALIAVEL | Sem componentes ou animações | Feedback imediato e redução de movimento a verificar |
| UX-GAME-001 | WONT | Decisão canônica explícita | Sem pontos, streaks ou estímulo a emissão apressada |

## UX/CX Findings

Cada M abaixo conta como um achado bloqueante, mesmo quando abrange várias regras. As correções são propostas e não foram aplicadas ao DEFINE.

| ID / prioridade | Regra canônica | Área | Achado e evidência | Recomendação e prova de aceite proposta |
|---|---|---|---|---|
| M01 — MUST | UX-CORE-002/004/010; UX-STATE-003 | Timeout e retomada | AT-011 registra erro técnico sem resultado desconhecido. Ex.: serviço recebe transmissão, resposta se perde e usuário retorna à tela | Mostrar “Resultado ainda não confirmado”, manter contexto e ação “Verificar situação”. Não oferecer reenvio enquanto houver incerteza. Simular perda de resposta e recarga: manter acompanhamento; se autorização for recuperada, mostrar a mesma nota; se continuar incerto, orientar suporte sem novo envio |
| M02 — MUST | UX-STATE-005; UX-CORE-004/010 | Importação | AT-002 cobre apenas registros válidos. Arquivo misto não tem destino especificado | Prévia por linha com válidas/inválidas/possíveis repetidas, motivo, totais e empresa de destino. Definir política explícita de aceitação parcial ou bloqueio integral; nunca importar parcialmente em silêncio. Demonstrar arquivo misto, correção e reimportação sem perder vínculo nem repetir rascunhos inadvertidamente; nenhuma linha transmite automaticamente |
| M03 — MUST | UX-NAV-004; UX-CORE-004/007 | Troca de empresa e perda de trabalho | Se trocar de empresa com edição não salva ou envio em curso, não há comportamento definido. CNPJ visível sozinho não resolve a transição | Antes de trocar, salvar com confirmação ou oferecer permanecer/descartar deliberadamente; identificar destino e resultado. Transmissão continua vinculada à origem e é retomável. Provar troca com edição, falha de salvamento e envio pendente: nenhum dado migra para outra empresa e nenhum trabalho desaparece silenciosamente |
| M04 — MUST | UX-INT-001; UX-FORM-004; UX-CORE-004 | Operação e elegibilidade | Constraints veda fluxos fiscais presumidos; A-002/003 pendentes; AT-006 só cobre campos inválidos. Falta comportamento para operação sem regra liberada | Apresentar apenas fluxo validado para o contexto; opção não liberada explica pendência e impede emissão. Diferenciar valor recebido e valor a documentar quando a regra validada exigir; não presumir que sejam iguais. Provar aluguel/venda/arrendamento sem configuração validada: transmissão bloqueada com orientação ao responsável; sem afirmar incidência |
| M05 — MUST | UX-STATE-006; UX-CORE-010 | Permissão negada | AT-012 cobre segurança, sem explicação e retorno seguro. Link direto ou permissão revogada pode encerrar a tarefa sem orientação | Mensagem genérica sem confirmar existência/titularidade do documento; ação “Voltar à minha empresa” ou ao contexto autorizado. Provar URL não autorizada e revogação durante edição: nenhum dado protegido visível, explicação e recuperação disponíveis; não sugerir reenviar |
| S01 — SHOULD | UX-NAV-002/005; UX-DATA-001/003 | Entrada e histórico | Ausência de hierarquia/navegação detalhada | Home com “Nova NFS-e”, rascunhos/pendências e histórico recente; filtros avançados sob demanda |
| S02 — SHOULD | UX-FORM-006 | Persistência | Autosave não definido | Propor salvamento automático com estado separado da emissão; não prometer recuperação de texto ainda não persistido |
| S03 — SHOULD | UX-STATE-004; UX-COPY-002 | Conclusão | AT-009 não nomeia próximos passos | Resultado persistente com dados retornados, visualizar/baixar quando disponíveis e voltar ao histórico; erro de download não autoriza reemissão |
| S04 — SHOULD | UX-CORE-008; UX-STATE-007 | Consistência | Sem vocabulário e justificativas uniformes | Um rótulo por estado; explicar botões indisponíveis e próximo passo |
| C01 — COULD | UX-DATA-001 | Operação intensiva | Preferências não especificadas | Considerar guardar filtros por usuário e empresa se não aumentar complexidade |
| W01 — WONT | UX-GAME-001; Out of Scope | Escopo | Fluxo fiscal e MVP enxuto | Sem gamificação, dashboard financeiro avançado, IA ou integrações futuras nesta revisão |

## Universal Principles Check

| ID | Princípio | Status | Evidência/Risco |
|---|---|---|---|
| UX-CORE-001 | Autoexplicativo | NAO AVALIAVEL | Sem protótipo ou observação de usuário |
| UX-CORE-002 | Estado inequívoco | MUST | Estados básicos cobertos; resultado desconhecido ausente, M01 |
| UX-CORE-003 | Ação principal evidente | NAO AVALIAVEL | Sem telas/CTAs |
| UX-CORE-004 | Prevenção e recuperação | MUST | M01 a M04; AT-006/010 cobrem apenas parte da recuperação |
| UX-CORE-005 | Acessibilidade por padrão | NAO AVALIAVEL | Medições e comportamento ainda inexistentes |
| UX-CORE-006 | Responsividade real | NAO AVALIAVEL | Não há evidência de layout quebrado nem de tarefa preservada |
| UX-CORE-007 | Feedback imediato | MUST | AT-008 cobre envio; troca de contexto não definida, M03 |
| UX-CORE-008 | Consistência | SHOULD | Consolidar vocabulário e padrões, S04 |
| UX-CORE-009 | Sem dark patterns | NAO AVALIAVEL | Revisão deliberada prevista; restante depende da interface; nenhuma violação comprovada |
| UX-CORE-010 | Estados completos | MUST | Importação parcial e recuperação por permissão ausentes, M02/M05 |

## Project North Star Checks

| Regra | Status | Evidência/Risco |
|---|---|---|
| UX-NAV-001 | CONFORME | Contexto persistente e bloqueio sem empresa em AT-003/005; transição é M03 |
| UX-FORM-002 | CONFORME | Revisão final obrigatória, AT-005/007 |
| UX-INT-001 | MUST | Operação não validada sem alerta/bloqueio definido, M04 |
| UX-STATE-008 | CONFORME | AT-004 e critério explícito de distinção visual/semântica |
| UX-A11Y-001 | NAO AVALIAVEL | Referência formal conhecida; nenhuma conformidade medida |
| UX-RESP-001 | NAO AVALIAVEL | Contextos definidos no padrão; sem demonstração de uso |

## Visual System Review

| Regra | Papel | Evidência | Status | Recomendação |
|---|---|---|---|---|
| UX-VIS-001/002 | Ação e densidade | Sem telas | NAO AVALIAVEL | Uma ação dominante; poucos indicadores |
| UX-VIS-003/004 | Alertas e empresa | CNPJ persistente exigido; alertas sem visual | CONFORME documental / NAO AVALIAVEL visual | Identificador consistente e alertas com texto e sinal adicional |
| UX-VIS-010/011 | Tokens e estados | Pending no padrão | NAO AVALIAVEL | Design propõe paleta e mede contraste; sem impor preto/dourado por memória |
| UX-VIS-020/021 | Leitura e agrupamento | Sem tipografia ou espaçamento | NAO AVALIAVEL | Hierarquia clara, seções técnicas expansíveis |

## Interaction Requirements

| Regra | Requisito | Motivo | Prioridade |
|---|---|---|---|
| UX-NAV-003/004 | Entrada direta do Cliente autorizado; troca de empresa protegida para Escritório | Evitar seleção redundante e contaminação de contexto | MUST |
| UX-FORM-001/004; UX-INT-003 | Básicos primeiro; condicionais por regra validada; validação próxima ao campo | Reduzir carga sem esconder impedimentos | MUST |
| UX-FORM-002/008/009; UX-INT-001 | Revisão escaneável, alertas e CTA explícito; mudança crítica após revisão exige nova conferência | Manter decisão sobre a versão efetivamente enviada | MUST |
| UX-INT-006; UX-CORE-004 | Processamento imediato; retomada/consulta em resultado desconhecido | Evitar repetição insegura | MUST |
| UX-INT-002/007 | Descarte contextual; cancelamento com documento, empresa, consequência e motivo quando exigido | Proteção proporcional se essas ações forem incluídas | MUST condicional |
| UX-INT-005 | Reutilização cria novo rascunho e volta à revisão | Não reaproveitar confirmação antiga | SHOULD; revisão é MUST se houver reutilização |

## Required States

| Estado | Regra | UX requerida | Status documental |
|---|---|---|---|
| Loading | UX-STATE-001 | Manter empresa/documento, indicar envio e proteger ação | CONFORME AT-008; recuperação em M01 |
| Empty | UX-STATE-002 | Histórico vazio: iniciar; busca vazia: ajustar/limpar filtros | SHOULD, detalhar se histórico incluído |
| Error | UX-STATE-003 | Separar rejeição de negócio, falha local e resultado desconhecido | Rejeição CONFORME; M01 MUST |
| Success | UX-STATE-004 | Confirmar apenas com retorno oficial; exibir identificação disponível e próximos passos | AT-009 parcial; S03 SHOULD |
| Partial Data | UX-STATE-005 | Informar linhas/campos pendentes e impacto no prosseguimento | M02 MUST |
| Permission Denied | UX-STATE-006 | Explicação segura e retorno autorizado | AT-012 cobre sigilo; M05 MUST |
| Disabled | UX-STATE-007 | Explicar motivo e condição de liberação | S04 SHOULD |
| Rascunho | UX-STATE-008 | “Rascunho — não emitido” | CONFORME AT-004 |
| Salvando / salvo / falha | UX-FORM-007 | Estado de persistência independente do fiscal | NAO AVALIAVEL; obrigatório se autosave adotado |
| Resultado desconhecido | UX-CORE-002/004 | “Verificar situação”, sem conclusão ou reenvio presumidos | M01 MUST |
| Cancelamento | UX-INT-002/007 | Separar pedido em andamento e evento confirmado | NAO AVALIAVEL; escopo a confirmar |

## Content and Copy Guidance

Textos propostos, sujeitos à aplicação dos requisitos:

| Regra | Superfície | Copy proposta |
|---|---|---|
| UX-COPY-005 | Ações sequenciais | “Revisar NFS-e” → “Emitir NFS-e”; não usar “OK” como autorização fiscal |
| UX-COPY-006 | Revisão | “Emitir pela empresa [nome] — CNPJ [número], para [tomador], no valor de R$ [valor]?”; operação e demais críticos visíveis |
| UX-STATE-008 | Rascunho | “Rascunho salvo. A NFS-e ainda não foi emitida.” |
| UX-INT-006 | Envio | “Transmissão em andamento. Acompanhe o resultado aqui.” |
| UX-CORE-002/004 | Timeout | “Ainda não foi possível confirmar o resultado. Verifique a situação antes de tentar novamente.” / “Verificar situação” |
| UX-COPY-003 | Rejeição | “[Dado] precisa ser corrigido. Revise o campo indicado antes de emitir.” / “Ver detalhes técnicos” |
| UX-STATE-005 | Importação | “[X] linhas válidas e [Y] com pendências. Revise o resultado antes de criar os rascunhos.” |
| UX-STATE-006 | Acesso negado | “Não foi possível acessar este conteúdo com sua permissão atual.” / “Voltar à minha empresa” |
| UX-STATE-002 | Vazio | “Você ainda não tem NFS-e neste histórico.” / “Nova NFS-e”; busca: “Nenhum resultado com estes filtros.” |
| UX-STATE-004 | Sucesso | “NFS-e emitida” somente com confirmação oficial; identificação retornada e ação de consulta |
| UX-INT-001 | Indisponibilidade | “Esta operação ainda não está liberada para esta empresa. Solicite a revisão da configuração ao responsável.” |

## Accessibility and Responsiveness

| Regra | Preocupação | Requisito para Design/Build | Evidência/medição |
|---|---|---|---|
| UX-A11Y-002/003 | Teclado/foco | Ordem lógica, foco visível, navegação completa; restaurar foco ao fechar modal | NAO AVALIAVEL |
| UX-A11Y-004 | Rótulos e erros | Labels programáticos; ajuda/erro associados; resumo navegável de pendências | NAO AVALIAVEL |
| UX-A11Y-005 | Contraste | Medir texto, controles, foco e estados contra critérios aplicáveis da WCAG 2.2 AA | NAO AVALIAVEL; paleta não definida |
| UX-A11Y-006 | Cor | Status e alertas com texto e sinal adicional; não depender só de cor | NAO AVALIAVEL |
| UX-CORE-007; UX-A11Y-001 | Retorno perceptível | Atualizações de salvamento/envio anunciadas por tecnologia assistiva sem mover foco arbitrariamente | NAO AVALIAVEL |
| UX-A11Y-007; UX-RESP-005 | Toque e modais | Ações acessíveis sem hover, sem sobreposição e com conteúdo crítico alcançável | NAO AVALIAVEL |
| UX-RESP-003/004; UX-DATA-005 | Celular | Completar emissão simples; histórico em padrão legível; preservar CNPJ, tomador, operação, valor e alertas | NAO AVALIAVEL |
| UX-RESP-002 | Desktop | Operação intensiva com filtros e troca de empresa sem perder legibilidade | NAO AVALIAVEL |
| UX-MOTION-002/003 | Movimento | Feedback não espera animação; respeitar redução de movimento quando aplicável | NAO AVALIAVEL |

Verificação futura proposta: executar criação → revisão → envio → consulta por teclado, leitor de tela e celular; provocar rejeição, timeout, importação parcial e permissão negada. Anexar resultados e medições. Nenhum desses testes foi executado nesta revisão documental.

## Gamification Strategy

Não recomendada, conforme UX-GAME-001. Indicadores de etapa e feedback de conclusão servem à orientação; não premiar velocidade ou volume de emissão.

## Design Handoff

### UX requirements

Preservar o que já está definido em AT-003/004/005/006/007/008/009/010/012. Resolver M01–M05 com comportamento e aceitação verificáveis. Não transformar propostas de governança em regras aprovadas: segundo aprovador, logs, integridade e retenção dependem do fluxo de decisão próprio.

### Components likely needed

- Indicador de empresa para Cliente; seletor persistente para Escritório; identificação inequívoca do ambiente de teste/produção.
- Home enxuta, formulário progressivo, campos condicionais e blocos técnicos expansíveis.
- Prévia de importação com linhas, pendências, totais e destino; não pressupor emissão em lote.
- Revisão final com empresa, tomador, operação, valor, dados críticos e alertas.
- Indicador de salvamento se adotado; acompanhamento de transmissão, resultado desconhecido e consulta de situação.
- Resultado persistente; histórico simples com filtros; mensagem de acesso negado e recuperação.
- Confirmações de descarte e de eventos fiscais apenas conforme escopo definido.

### State requirements

Usar a matriz Required States. Atualizar estado fiscal somente segundo evidência oficial; o retorno do salvamento local não confirma emissão. Preservar vínculo do documento com sua empresa ao trocar contexto.

### Copy guidance

Aplicar as propostas acima com dados efetivos. Mensagens principais explicam impacto e próximo passo; detalhes técnicos são secundários. Nunca prometer “não foi emitida” se o retorno permanece desconhecido.

### Visual guidance

Interface clara, moderna, amigável, densidade baixa/moderada e ação principal dominante. Não há tokens aprovados; propostas visuais não alteram o padrão automaticamente.

### Accessibility/responsiveness

Usar a matriz de acessibilidade. Desktop principal e web móvel para consulta/emissão simples, sem adicionar aplicativo nativo. Conformidade visual/técnica permanece pendente de evidência.

### Acceptance notes

- [ ] M01: resposta perdida/recarga mantém resultado desconhecido até consulta; não oferece reenvio inseguro.
- [ ] M02: arquivo misto informa resultado por linha, política de parcialidade e recuperação; reimportação não repete rascunhos inadvertidamente.
- [ ] M03: troca de empresa com edição/falha/envio pendente preserva origem, trabalho e feedback.
- [ ] M04: operação/contexto não liberado bloqueia transmissão e explica pendência, sem presumir tratamento fiscal.
- [ ] M05: acesso negado permite retorno autorizado sem exposição ou confirmação de dados de terceiros.
- [ ] Toda entrada, inclusive importação/reutilização, passa por revisão atual antes de emitir.
- [ ] Sucesso depende de confirmação oficial; falha de consulta/download não produz reemissão.
- [ ] Evidenciar teclado, foco, rótulos, contraste, sinais adicionais e emissão simples no celular no protótipo/Build.

Os critérios são propostas de complemento; não receberam IDs AT novos nem foram incorporados ao DEFINE nesta revisão.

## Canonical Evolution Proposals

| Regra afetada/nova | Problema | Mudança proposta | Motivo | Bloqueia esta feature? |
|---|---|---|---|---|
| UX-STATE: possível novo ID | Resultado desconhecido sem regra específica | Em evolução futura, explicitar estado após timeout e prioridade de consulta sobre reenvio | Dar nome canônico a um caso já coberto por prevenção/clareza | O comportamento M01 bloqueia; criar novo ID não |
| UX-STATE-005 / UX-FORM: possível novo ID | Importação mista não detalhada no padrão | Padronizar prévia, totais, erros por linha e retomada | Reutilizar o padrão em outras importações | Resolver M02 basta; evolução não obrigatória |

Somente sugestões para ux-review-builder em modo Evolução. UX_STANDARD preservado.

## Gate Outcome

**Resultado: BLOCKED FOR DESIGN.**

**MUST abertos: 5 — M01 a M05.**

**MUST aceitos explicitamente como exceção: 0.**

O gate avalia a especificação documental. Não significa reprovação visual ou falha de um produto implementado. Conforme a skill específica anexada (`ux-review/SKILL.md`, seção “Determinar o resultado do gate”): “Com MUST não resolvido: BLOCKED FOR DESIGN.” A revisão está concluída; o bloqueio se aplica à passagem de fase.

Acessibilidade e responsividade sem evidência ficam NAO AVALIAVEL; isso não foi convertido automaticamente em violação ou aprovação. O Verify Gate executável ainda indefinido no DEFINE é pendência distinta e não foi contado entre os cinco achados UX.

## Open UX Questions

1. Na importação mista, criar só rascunhos válidos após confirmação explícita ou bloquear o arquivo inteiro? Recomenda-se prévia e aceitação parcial deliberada, com identificação das pendências.
2. Como identificar a linha de origem e apresentar possíveis repetições na reimportação? Não usar apenas igualdade de tomador/valor para afirmar duplicidade.
3. Quais operações estarão validadas/liberadas por empresa e contexto piloto, e quem resolverá pendências? A revisão não escolhe o tratamento fiscal.
4. Cancelamento faz parte deste MVP? Até definição, não considerar funcionalidade aprovada; se incluída, exigir fluxo contextual reforçado.
5. Será exigido aprovador distinto do preparador? G07 é recomendação de governança pendente; não assumir bloqueio por segunda pessoa nesta UX.
6. Adotar autosave? Recomendado; qualquer política escolhida deve resolver a perda silenciosa de trabalho em M03.

Estas são decisões para incorporar ao fluxo, não pedidos de aprovação para concluir a revisão.

## Revision History

| Versão | Data | Autor | Mudanças |
|---|---|---|---|
| 1.0 | 2026-10-31 | ux-review | Revisão documental inicial com padrão específico, jornada, cinco lacunas bloqueantes e handoff; fontes preservadas |

## Next Step

Incorporar ao DEFINE os comportamentos de M01–M05, compatibilizando AT-002, AT-011 e os demais critérios afetados; registrar decisões pendentes e reaplicar o gate. Sem MUST aberto, avançar ao Design com este handoff. Nesta entrega, DEFINE e UX_STANDARD não foram alterados e nenhuma exceção foi aceita.
