# UX STANDARD: NFS-e Nacional para Gestoras de Imóveis

> Fonte canônica de UX do projeto. Versão: 1.0.0. Idioma: Português-BR.

## Metadata

| Campo | Valor |
|---|---|
| Projeto | NFS-e Nacional para Gestoras de Imóveis |
| Versão | 1.0.0 |
| Data | 2026-10-31 |
| Responsável | Cássio Aguiar |
| Status | Approved |
| Local | Pasta do SDD do projeto, ao lado do Define e do Design |
| Modo | Criação |

## Como usar esta fonte canônica

- `DEFINE` define o que a feature precisa fazer.
- Este `UX_STANDARD` define como a experiência deve se comportar.
- `UX_REVIEW_TEMPLATE` define como documentar a revisão.
- A `ux-review` pode sugerir mudanças, mas não altera este arquivo automaticamente.
- Toda regra específica do produto deve preservar os IDs definidos aqui ou receber novo ID versionado.

## Produto e contexto

Aplicação simples, criada no Lovable, para emissão de NFS-e Nacional por pequenas empresas gestoras de imóveis. O produto atende operações como recebimentos de aluguéis, vendas de imóveis e arrendamento, sem presumir que todas tenham o mesmo fluxo fiscal ou os mesmos campos. O sistema deve conduzir o usuário de forma simples, preservar detalhes técnicos para quem precisa deles e reduzir riscos de emissão por empresa, tomador, valor ou operação incorretos.

O produto atende dois contextos de uso: a própria empresa cliente operando suas emissões e a equipe do escritório contábil operando múltiplas empresas. Há três perfis principais: Cliente, Escritório e Administrador.

Materiais existentes de marca, paleta, design system, telas anteriores ou URL de referência: não disponíveis na criação desta versão.

## Usuários e contextos de uso

| Público | Objetivo | Frequência | Nível técnico | Dispositivo/contexto | Risco principal |
|---|---|---|---|---|---|
| Cliente da gestora | Emitir e consultar NFS-e da própria empresa com pouca fricção | Baixa a média | Variável; não pressupor domínio fiscal | Desktop principal; celular para consulta e emissão simples | Erro de tomador, valor, operação ou interpretação de status |
| Escritório contábil | Emitir, revisar e acompanhar NFS-e de várias empresas | Média a alta | Técnico/operacional | Desktop principal | Emitir no CNPJ errado ou perder contexto entre empresas |
| Administrador | Gerenciar acessos, configurações e permissões sensíveis | Eventual | Técnico/administrativo | Desktop principal | Alteração de configuração ou acesso sem contexto e confirmação |

## Referências de experiência

| Referência | Tipo | Observado | Desejado pelo usuário | Decisão canônica |
|---|---|---|---|---|
| ChatGPT | Produto | Interface limpa, conteúdo em primeiro plano, baixa competição visual, ação principal clara | Simplicidade, clareza e fluxo direto | Usar como referência de sensação, sem copiar interface ou marca |
| Identidade própria | Decisão de produto | Não há material visual existente | Visual moderno, amigável, claro e confiável | Construir identidade própria sem aparência de sistema fiscal pesado |

## North Star da experiência

**Emitir a NFS-e correta, pela empresa correta, para o tomador correto e com o valor correto, com o mínimo de carga cognitiva e uma revisão final que torne os riscos visíveis antes do envio.**

A experiência deve ser simples para o cliente e eficiente para o escritório, sem esconder detalhes técnicos necessários. O usuário deve saber sempre em que empresa está, em que estado está a emissão e qual é o próximo passo seguro.

## Princípios universais obrigatórios

| ID | Regra | Como verificar | Severidade-base | Origem | Estado |
|---|---|---|---|---|---|
| UX-CORE-001 | A tarefa principal deve ser compreendida sem manual, tour obrigatório ou tooltip-muleta. | Usuário novo identifica objetivo e próximo passo pela interface. | MUST | Universal | Active |
| UX-CORE-002 | Estados relevantes devem ser inequívocos. | Salvo, pendente, processando, concluído e erro não se confundem. | MUST | Universal | Active |
| UX-CORE-003 | A ação principal deve ser evidente em cada contexto. | Ação primária não compete visualmente com secundárias equivalentes. | MUST | Universal | Active |
| UX-CORE-004 | Erros previsíveis devem ser prevenidos e recuperáveis. | Erros acionáveis oferecem orientação, retry, undo ou alternativa adequada. | MUST | Universal | Active |
| UX-CORE-005 | Acessibilidade deve ser considerada desde o início. | Teclado, foco, labels, contraste, toque e sinais não dependentes apenas de cor são verificáveis. | MUST | Universal | Active |
| UX-CORE-006 | Responsividade deve preservar a tarefa. | Prioridade, ordem de leitura, legibilidade e capacidade de agir sobrevivem à mudança de viewport. | MUST | Universal | Active |
| UX-CORE-007 | Ações relevantes devem produzir feedback perceptível. | Usuário entende que o sistema recebeu, processou ou concluiu a ação. | MUST | Universal | Active |
| UX-CORE-008 | Intenções iguais devem usar padrões consistentes. | Mesma intenção usa linguagem, componente e comportamento equivalentes. | SHOULD | Universal | Active |
| UX-CORE-009 | Dark patterns são proibidos. | Não há consequência escondida, urgência falsa ou fricção deliberada para impedir escolha legítima. | MUST | Universal | Active |
| UX-CORE-010 | Estados de sistema fazem parte da feature. | Loading, empty, error, success, partial data, permission denied e disabled estão definidos quando aplicáveis. | MUST | Universal | Active |

## Princípios específicos do projeto

| ID | Regra | Como verificar | Severidade-base | Origem | Estado |
|---|---|---|---|---|---|
| UX-NAV-001 | O contexto da empresa ativa deve ser inequívoco em toda ação de emissão, revisão e cancelamento. | Cliente entra diretamente na própria empresa; perfil Escritório vê empresa/CNPJ ativo de forma persistente e perceptível. | MUST | Usuário | Active |
| UX-FORM-001 | O fluxo de emissão deve ser híbrido, progressivo e condicional. | Campos básicos aparecem primeiro; detalhes adicionais surgem conforme operação ou expansão deliberada. | MUST | Usuário | Active |
| UX-FORM-002 | A revisão final antes da emissão é obrigatória. | Não existe caminho normal de envio sem tela/etapa de revisão da empresa, tomador, operação, valor e dados críticos. | MUST | Usuário | Active |
| UX-INT-001 | A revisão final deve destacar alertas inteligentes e divergências relevantes sem transformar todo o formulário em estado de alarme. | Alertas críticos aparecem com prioridade visual e explicação acionável na revisão final. | MUST | Usuário | Active |
| UX-STATE-008 | Rascunho e NFS-e emitida/transmitida devem ser visual e semanticamente distintos. | O usuário não consegue confundir conteúdo salvo automaticamente com documento efetivamente enviado. | MUST | Usuário | Active |
| UX-DATA-001 | O histórico deve ser simples por padrão e expansível para uso intensivo. | Colunas essenciais aparecem primeiro; filtros, detalhes e colunas extras ficam acessíveis sob demanda. | SHOULD | Usuário | Active |
| UX-INT-002 | Ações destrutivas devem ter proteção proporcional ao risco. | Descarte simples usa confirmação leve; cancelamento de NFS-e exige confirmação reforçada, contexto e motivo quando aplicável. | MUST | Usuário | Active |
| UX-COPY-001 | A comunicação deve ter linguagem simples na superfície e detalhe técnico expansível. | Mensagem principal é compreensível sem jargão; retorno/código técnico pode ser aberto por quem precisa. | MUST | Usuário | Active |
| UX-RESP-001 | Desktop é o contexto principal; celular deve suportar consulta e emissão simples. | Fluxos simples podem ser concluídos no celular; tarefas complexas preservam clareza sem exigir paridade de densidade. | SHOULD | Usuário | Active |
| UX-A11Y-001 | WCAG 2.2 AA é a referência formal de acessibilidade do projeto. | Revisões verificam contraste, foco, teclado, labels, mensagens, alvos de toque e pistas não dependentes apenas de cor. | MUST | Usuário | Active |

## Hierarquia, densidade e visual

O visual deve ser moderno, amigável, claro e confiável. A interface deve priorizar conteúdo e próxima ação, com baixa competição visual. A aparência não deve remeter a sistemas fiscais antigos ou painéis densos por padrão.

A home deve combinar: ação evidente para `Nova NFS-e`, poucos indicadores realmente úteis e histórico recente. Informação técnica e filtros avançados devem aparecer sob demanda.

### Regras verificáveis

| ID | Regra | Como verificar | Severidade-base | Origem | Estado |
|---|---|---|---|---|---|
| UX-VIS-001 | Cada tela deve ter uma ação principal visualmente dominante. | Há no máximo uma ação primária dominante por contexto; secundárias têm menor peso. | MUST | Referência confirmada | Active |
| UX-VIS-002 | A densidade visual padrão deve ser baixa a moderada. | A primeira leitura não exige varrer tabelas extensas, blocos técnicos ou múltiplos CTAs equivalentes. | SHOULD | Usuário | Active |
| UX-VIS-003 | Alertas críticos devem ser distintos sem usar somente cor. | Alerta crítico combina texto, hierarquia e sinal adicional, como ícone ou rótulo. | MUST | Usuário | Active |
| UX-VIS-004 | A empresa ativa deve possuir destaque persistente e proporcional ao risco. | No perfil Escritório, nome e identificador da empresa aparecem em local consistente durante emissão, revisão e cancelamento. | MUST | Usuário | Active |

## Cor, tokens e temas

Não há paleta, tokens ou tema confirmados nesta versão. Não inventar valores canônicos. O Design poderá propor tokens, mas sua adoção como padrão canônico exige aprovação explícita do responsável.

| ID | Papel semântico | Token/valor | Uso | Contraste/critério | Estado |
|---|---|---|---|---|---|
| UX-VIS-010 | Cor primária | não disponível | Ação principal e marca do produto | Deve atender WCAG 2.2 AA no contexto aplicado | Pending |
| UX-VIS-011 | Cores de estado | não disponível | Sucesso, alerta, erro e informação | Nunca depender apenas de cor para transmitir significado | Pending |

## Tipografia e espaçamento

| ID | Regra | Como verificar | Severidade-base | Estado |
|---|---|---|---|---|
| UX-VIS-020 | Tipografia deve privilegiar leitura rápida e hierarquia clara. | Títulos, rótulos, dados e ajuda são distinguíveis sem excesso de pesos ou tamanhos. | SHOULD | Active |
| UX-VIS-021 | Espaçamento deve separar grupos sem criar telas excessivamente longas. | Campos relacionados aparecem agrupados; seções técnicas são recolhíveis quando possível. | SHOULD | Active |

## Navegação e arquitetura de informação

| ID | Regra | Como verificar | Severidade-base | Estado |
|---|---|---|---|---|
| UX-NAV-002 | A home deve priorizar `Nova NFS-e`, indicadores essenciais e histórico recente. | O usuário identifica imediatamente como iniciar emissão e como retomar/consultar atividade recente. | SHOULD | Active |
| UX-NAV-003 | Cliente não deve precisar selecionar empresa quando só possui acesso à própria empresa. | Login do Cliente entra diretamente no contexto autorizado. | MUST | Active |
| UX-NAV-004 | Escritório deve poder trocar de empresa sem perder a percepção do contexto ativo. | Seletor persistente exibe empresa atual e mudança de contexto produz feedback claro. | MUST | Active |
| UX-NAV-005 | Navegação deve separar emissão, histórico e configurações sem multiplicar níveis desnecessários. | Tarefas frequentes são alcançáveis com poucos passos e rótulos claros. | SHOULD | Active |

## Interação e feedback

| ID | Regra | Como verificar | Severidade-base | Estado |
|---|---|---|---|---|
| UX-INT-003 | Validação durante preenchimento deve ser em tempo real e discreta. | Erros locais aparecem próximos ao campo sem bloquear leitura; problemas críticos ganham destaque na revisão final. | MUST | Active |
| UX-INT-004 | Ações recorrentes devem seguir padrão híbrido. | Ação principal frequente pode ficar visível; ações secundárias ficam em menu contextual. | SHOULD | Active |
| UX-INT-005 | Emissões anteriores devem poder ser reutilizadas quando seguro. | Histórico oferece duplicação/reaproveitamento sem copiar silenciosamente campos críticos sem revisão. | SHOULD | Active |
| UX-INT-006 | Toda transmissão/emissão deve fornecer feedback imediato de processamento. | Após enviar, ação fica protegida contra duplo envio e estado `processando` fica visível. | MUST | Active |
| UX-INT-007 | Ações críticas devem apresentar o objeto e a consequência antes da confirmação. | Cancelamento mostra empresa, nota/documento, consequência e confirmação explícita. | MUST | Active |

## Estados obrigatórios

| ID | Estado | Regra | Como verificar | Severidade-base |
|---|---|---|---|---|
| UX-STATE-001 | Loading | Mostrar atividade sem apagar contexto ou induzir novo envio. | Usuário vê que a ação está em andamento e não precisa repetir o comando. | MUST |
| UX-STATE-002 | Empty | Explicar ausência de dados e oferecer próximo passo útil quando houver. | Histórico vazio orienta `Nova NFS-e`; filtro sem resultado permite limpar/ajustar filtros. | MUST |
| UX-STATE-003 | Error | Explicar em linguagem simples o que ocorreu e como recuperar; detalhe técnico deve ser expansível. | Erro acionável mostra orientação, retry ou alternativa; código técnico não substitui mensagem humana. | MUST |
| UX-STATE-004 | Success | Confirmar conclusão de forma inequívoca e apresentar próximos passos relevantes. | Após emissão, mostrar principais dados e ações como visualizar, baixar, duplicar, emitir outra ou voltar ao histórico. | MUST |
| UX-STATE-005 | Partial Data | Distinguir dados parciais de dados completos e informar impacto. | Interface sinaliza quais informações faltam e se a tarefa pode prosseguir. | MUST |
| UX-STATE-006 | Permission Denied | Informar que a ação não está autorizada sem expor dados de outra empresa ou perfil. | Usuário recebe explicação segura e caminho para retorno/contato adequado. | MUST |
| UX-STATE-007 | Disabled | Explicar por que uma ação está indisponível quando a razão não for óbvia. | Campo/botão desabilitado possui contexto suficiente, ajuda ou condição visível. | SHOULD |

## Formulários e entrada de dados

| ID | Regra | Como verificar | Severidade-base | Estado |
|---|---|---|---|---|
| UX-FORM-003 | Mostrar primeiro empresa, tomador, tipo de operação, valor e descrição quando aplicável ao fluxo. | Primeira camada do formulário contém apenas dados necessários para avançar. | SHOULD | Active |
| UX-FORM-004 | Campos condicionais devem aparecer em função da operação e do contexto, não por preferência estética. | Aluguel, venda de imóvel e arrendamento podem revelar campos distintos quando justificado pelo DEFINE/regra funcional. | MUST | Active |
| UX-FORM-005 | Campos técnicos devem ser expansíveis quando não forem essenciais ao usuário comum. | Usuário comum conclui tarefa sem lidar com códigos desnecessários; escritório pode abrir detalhes. | SHOULD | Active |
| UX-FORM-006 | O sistema deve salvar rascunhos automaticamente quando tecnicamente possível. | Saída acidental, interrupção ou perda de conexão não apaga silenciosamente trabalho já persistido. | SHOULD | Active |
| UX-FORM-007 | Salvamento automático deve ter feedback de estado. | Interface indica `salvando`, `salvo` ou falha de salvamento sem confundir com transmissão oficial. | MUST | Active |
| UX-FORM-008 | A revisão final deve apresentar campos críticos em bloco escaneável. | Empresa/CNPJ, tomador, operação, valor e alertas ficam visíveis sem abrir múltiplos painéis. | MUST | Active |
| UX-FORM-009 | Emissão não pode depender de confirmação implícita. | CTA final possui linguagem inequívoca e exige ação deliberada do usuário. | MUST | Active |

## Tabelas, dashboards e dados

| ID | Regra | Como verificar | Severidade-base | Estado |
|---|---|---|---|---|
| UX-DATA-002 | Indicadores da home devem ser poucos e acionáveis. | Cada indicador responde a uma necessidade real de acompanhamento; métricas decorativas são evitadas. | SHOULD | Active |
| UX-DATA-003 | Histórico deve permitir busca e filtros sem exigir configuração avançada. | Busca simples e filtros essenciais estão disponíveis; filtros avançados são opcionais. | SHOULD | Active |
| UX-DATA-004 | Colunas essenciais devem ser legíveis sem rolagem horizontal excessiva no desktop. | Identificação, tomador, valor, data e status permanecem priorizados conforme a feature. | SHOULD | Active |
| UX-DATA-005 | No celular, tabelas devem se transformar em padrão legível, não apenas encolher. | Cards, linhas empilhadas ou outra adaptação preservam ordem de leitura e ações principais. | MUST | Active |

## Conteúdo, tom de voz e microcopy

| ID | Regra | Como verificar | Severidade-base | Estado |
|---|---|---|---|---|
| UX-COPY-002 | Mensagens devem ser profissionais, humanas e objetivas. | Evitar jargão desnecessário, ironia e linguagem culpabilizadora. | SHOULD | Active |
| UX-COPY-003 | Mensagem de erro deve começar pelo impacto e pelo próximo passo. | O usuário entende o que fazer antes de ler detalhes técnicos. | MUST | Active |
| UX-COPY-004 | Detalhe técnico deve ser opcional e expansível. | Código/retorno do serviço não domina a mensagem principal. | SHOULD | Active |
| UX-COPY-005 | CTAs críticos devem nomear a ação real. | Preferir `Emitir NFS-e`, `Cancelar NFS-e`, `Salvar rascunho` a rótulos vagos como `OK` ou `Continuar`. | MUST | Active |
| UX-COPY-006 | Confirmações devem repetir contexto crítico quando houver risco de empresa/documento errado. | Confirmação de emissão/cancelamento identifica empresa e objeto da ação. | MUST | Active |

## Acessibilidade

| ID | Regra | Como verificar | Severidade-base | Estado |
|---|---|---|---|---|
| UX-A11Y-002 | Fluxos principais devem ser operáveis por teclado. | Ordem de foco segue a leitura e ações essenciais são acionáveis sem mouse. | MUST | Active |
| UX-A11Y-003 | Foco visível deve permanecer perceptível em componentes interativos. | Teste visual mostra foco claro em inputs, botões, links, menus e modais. | MUST | Active |
| UX-A11Y-004 | Campos devem possuir rótulos programáticos e mensagens associadas. | Leitor de tela consegue relacionar campo, instrução e erro. | MUST | Active |
| UX-A11Y-005 | Contraste deve ser verificado contra WCAG 2.2 AA. | Texto, controles e estados críticos atingem critérios aplicáveis; se não medido, marcar `NAO AVALIAVEL`. | MUST | Active |
| UX-A11Y-006 | Significado não pode depender apenas de cor. | Status, alertas e erros possuem texto, ícone, padrão ou outro sinal adicional. | MUST | Active |
| UX-A11Y-007 | Alvos de toque e espaçamento devem suportar uso móvel confortável. | Ações principais não exigem precisão excessiva e não ficam coladas a ações destrutivas. | SHOULD | Active |

## Responsividade

| ID | Regra | Como verificar | Severidade-base | Estado |
|---|---|---|---|---|
| UX-RESP-002 | Desktop é o layout de referência para operação intensiva. | Histórico, filtros e troca de empresa aproveitam a largura sem comprometer legibilidade. | SHOULD | Active |
| UX-RESP-003 | Celular deve suportar consulta e emissão simples de ponta a ponta. | Usuário consegue localizar nota, iniciar emissão simples, revisar e concluir sem zoom ou layout quebrado. | MUST | Active |
| UX-RESP-004 | Fluxos complexos no celular podem reduzir densidade, mas não omitir informação crítica. | Empresa, tomador, valor, operação, estado e alertas permanecem acessíveis. | MUST | Active |
| UX-RESP-005 | Modais e menus devem respeitar viewport pequeno. | Conteúdo crítico não fica inacessível fora da tela e fechamento não depende de hover. | MUST | Active |

## Movimento e microinterações

| ID | Regra | Como verificar | Severidade-base | Estado |
|---|---|---|---|---|
| UX-MOTION-001 | Animações devem ser leves, funcionais e subordinadas à tarefa. | Movimento comunica abertura, carregamento, mudança de estado, sucesso ou erro; não existe animação decorativa intrusiva. | SHOULD | Active |
| UX-MOTION-002 | Movimento não pode atrasar ações críticas nem esconder feedback. | Confirmações e erros são percebidos imediatamente sem esperar animação ornamental. | MUST | Active |
| UX-MOTION-003 | Preferência de redução de movimento deve ser respeitada quando aplicável. | Componentes animados oferecem comportamento reduzido compatível com preferência do sistema. | SHOULD | Active |

## Gamificação

| ID | Regra/decisão | Como verificar | Severidade-base | Estado |
|---|---|---|---|---|
| UX-GAME-001 | Gamificação não é recomendada para o fluxo fiscal principal. | Não existem streaks, urgência artificial, pontuação ou recompensas que incentivem emissão apressada. | WONT | Active |

## Antipadrões proibidos

| ID | Antipadrão | Evidência de violação | Severidade-base |
|---|---|---|---|
| UX-ANTI-001 | Emitir sem revisão final obrigatória | Existe caminho normal de transmissão que ignora a etapa de revisão. | MUST |
| UX-ANTI-002 | Ocultar ou minimizar a empresa ativa em contexto multiempresa | Usuário do Escritório consegue iniciar ou concluir emissão sem perceber claramente o CNPJ/empresa ativa. | MUST |
| UX-ANTI-003 | Usar mensagens técnicas como única explicação de erro | Usuário recebe apenas código/retorno técnico sem impacto e recuperação em linguagem simples. | MUST |
| UX-ANTI-004 | Confundir rascunho com documento emitido | Estado visual ou textual permite interpretar salvamento local como transmissão oficial. | MUST |
| UX-ANTI-005 | Cancelamento com um único clique sem confirmação contextual | Ação crítica pode ser concluída sem confirmação reforçada do objeto e consequência. | MUST |
| UX-ANTI-006 | Copiar emissão anterior sem revisão dos campos críticos | Duplicação permite envio silencioso de empresa, tomador, operação ou valor herdados. | MUST |

## Critérios globais de qualidade

1. O usuário identifica em poucos segundos qual empresa está ativa e qual é a próxima ação principal.
2. Não existe caminho normal de emissão sem revisão final dos campos críticos.
3. Rascunho, processamento, sucesso e erro são estados distintos e compreensíveis.
4. Nenhuma ação crítica depende apenas de cor ou de código técnico para ser compreendida.
5. O histórico permanece simples por padrão e eficiente para uso intensivo.
6. O celular permite consultas e emissões simples sem degradar informação crítica.
7. Toda violação comprovada dos riscos críticos definidos pelo responsável é tratada como `MUST` no gate, salvo regra mais específica.
8. Acessibilidade segue WCAG 2.2 AA como referência formal; itens não medidos não devem ser marcados como conformes.

## Exceções aceitas

Nenhuma exceção aceita na versão 1.0.0.

## Governança

- `UX_STANDARD.md` é a fonte canônica de experiência do projeto.
- Cássio Aguiar é o responsável final pela aprovação e evolução do padrão.
- A `ux-review` pode sugerir mudanças, mas não altera este arquivo automaticamente.
- Toda mudança relevante exige aprovação explícita do responsável.
- IDs não são reutilizados para significados diferentes.
- Regras descontinuadas permanecem rastreáveis no histórico.
- Um `MUST` aceito como exceção continua registrado como violação aceita, não como conformidade.

## Histórico de revisões

| Versão | Data | Responsável | Mudanças |
|---|---|---|---|
| 1.0.0 | 2026-10-31 | Cássio Aguiar | Criação inicial do padrão para NFS-e Nacional de gestoras de imóveis |
