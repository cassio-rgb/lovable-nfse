# GOVERNANÇA: NFS-e Nacional para Gestoras de Imóveis

**Cobertura: 20 itens — 0 já cobertos integralmente · 9 lacunas · 6 N.A. · 5 na 2ª camada.**

| Feature | Data | Padrão do projeto | DEFINE |
|---|---|---|---|
| Emissão de NFS-e Nacional para Gestoras de Imóveis | 2026-10-31 | Contexto extraído do DEFINE; responsável técnico e guarda ainda não confirmados | DEFINE_NFSE_GESTORAS_IMOVEIS.md, versão 0.9 |

## Parecer executivo

O DEFINE organiza adequadamente o fluxo básico de emissão, a revisão humana e a distinção entre rascunho, rejeição e emissão. Ainda não contém os requisitos e testes negativos necessários para demonstrar integridade documental, rastreabilidade, prevenção de duplicidade e isolamento completo entre empresas.

Recomendação: resolver as lacunas de severidade alta antes de consolidar o Design e planejar as duas lacunas médias de auditoria com decisão explícita. Os itens classificados como segunda camada seguem a classificação do catálogo; isso não significa que foram adiados ou aceitos pelo profissional. G16, em especial, merece ser antecipado como condição para uso de certificado em produção.

Esta é uma revisão documental e técnica, não uma auditoria do sistema implementado ou parecer de incidência tributária. Nenhuma prova foi executada: não há aplicação, schema ou ambiente de teste neste material. Não foram presumidos leiautes oficiais, regras fiscais imobiliárias, prazos legais de guarda ou habilitação dos municípios.

## Triagem e fontes

**Gatilhos encontrados:** valor e operação fiscal (AT-005); lançamento manual/importação (AT-001/AT-002); emissão fiscal e DPS (AT-007/AT-009); CNPJ e autorização (AT-003/AT-012); tomador e credenciais (Constraints).
 
Fontes lidas: DEFINE completo, BRAINSTORM e UX_STANDARD anexados; procedimento, catálogo de 20 itens e modelos da skill sdd-governanca v1.0.0. O bundle anexado não contém GOVERNANCA_PADRAO.md. Não foi localizado padrão de governança na pasta SDD deste trabalho. O UX_STANDARD é referência complementar; não substitui requisito de aceitação no DEFINE.

## Padrão do projeto: contexto conhecido e pendências

| Campo | Contexto de trabalho | Situação |
|---|---|---|
| uso | clientes também, com equipe do escritório | Expresso no DEFINE |
| multi_cnpj | sim, isolamento por empresa em aplicação compartilhada | Multiempresa expresso; desenho físico do banco fica para Design |
| ia_grava_sozinha | não | Technical Context: LLM Prompts = false |
| responsavel_tecnico | nome e CRC a informar | A responsabilidade pelo padrão UX não comprova responsabilidade técnica contábil/fiscal pelo sistema |
| guarda_padrao | a definir por tipo de documento e evento | Não inferir prazo numérico ou regra universal de prescrição |

As cinco informações foram avaliadas; três são recuperáveis do documento. Não se criou padrão canônico como se os dois campos restantes tivessem sido confirmados. Para formalizá-lo, faltam nome/CRC do responsável e política de guarda aprovada. A revisão de recomendações pôde prosseguir com esse contexto.

## Matriz completa do catálogo

| Item | Controle | Veredito | Evidência ou motivo |
|---|---|---|---|
| G01 | Lançamento que não se apaga | lacuna | Aplicação funcional à versão fiscal transmitida; não congela rascunho editável |
| G02 | Partidas dobradas no banco | N.A. | Emissor fiscal sem razão, escrituração ou lançamentos de débito/crédito; “lançamento manual” aqui é entrada de dados para nota |
| G03 | Fechamento de período | N.A. | MVP sem fechamento contábil/fiscal de competência; não introduzir bloqueio mensal de emissão por analogia |
| G04 | Trilha de auditoria do negócio | lacuna | Nenhum AT exige trilha protegida com autoria e conteúdo da mudança |
| G05 | Log forense de segurança | lacuna | Uso por equipe/clientes e certificado; faltam logs de leitura, exportação e uso |
| G06 | Prova de integridade dos logs | lacuna | Ausência de verificação e referência externa |
| G07 | Segregação de funções | lacuna | Revisão humana não exige pessoa distinta; AT-007 permite confirmação pelo preparador |
| G08 | Documento-fonte imutável | lacuna | Importação sem preservação de origem/hash/vínculo |
| G09 | Aritmética exata | lacuna | Não há representação decimal ou arredondamento exigidos |
| G10 | Importação idempotente | lacuna | AT-002 permite importar, sem teste de reimportação |
| G11 | Regra com vigência e memória | 2ª camada | Exigir versão de parâmetros aplicáveis e insumos, sem presumir motor tributário |
| G12 | Conciliação com totais de controle | 2ª camada | Controle de lotes de importação e resultados fiscais, sem integração bancária |
| G13 | Isolamento entre clientes | lacuna | AT-012 cobre Cliente parcialmente; faltam Escritório, arquivos e vínculos cruzados |
| G14 | Retenção e proteção dos dados | 2ª camada | Prazo e tratamento por classe documental não definidos |
| G15 | Backup e restauração testada | 2ª camada | Não há recuperação comprovada nem metas de perda/tempo |
| G16 | Certificado digital e segredos | 2ª camada | Backend separado é positivo, mas faltam cofre/cifra/rotação/log e teste negativo |
| G17 | IA sugere, humano confirma | N.A. | Sem IA em runtime no MVP |
| G18 | Registro da decisão da IA | N.A. | Sem IA em runtime no MVP |
| G19 | Taxa de correção da IA | N.A. | Sem IA em runtime no MVP |
| G20 | Responsabilidade técnica no fechamento com IA | N.A. | Sem IA ou fechamento no MVP; responsável do projeto continua pendente no padrão |

## Lacunas e requisitos propostos

Os textos abaixo são propostas; não são requisitos aprovados ou aplicados. Cada roteiro deve ser executado em ambiente de teste com usuário autorizado e dados de controle válidos. Uma recusa por erro de schema, indisponibilidade ou dado obrigatório ausente não comprova a regra pretendida.

### G01 — Integridade do documento fiscal transmitido · severidade alta

**O que muda no app:** Preservar a versão transmitida da DPS, o documento autorizado e os eventos oficiais; rascunhos continuam editáveis, com histórico.

**Por quê:** Uma edição local não pode reescrever o que foi enviado ou autorizado. Cancelamento ou substituição, quando admitidos pela integração, devem gerar eventos vinculados; não equivalem a apagar a nota. **Base legal:** ainda não confirmada no catálogo — confira na fonte antes de citar.

**Requisito (EARS):** **If** houver tentativa de alterar ou excluir o conteúdo fiscal de uma DPS já transmitida ou de uma NFS-e emitida, **then** the system **shall** recusar a alteração destrutiva, preservar o original e permitir apenas o fluxo de evento oficial aplicável.

**Como provar:** 1. Salvar um rascunho e editar seu valor: alteração permitida com histórico. 2. Transmitir uma DPS de teste e conservar o original. 3. Tentar alterar valor ou excluir o original pela interface e pela API: ambas as ações são recusadas. 4. Registrar um evento oficial suportado: original preservado e evento vinculado.

**Evidência da lacuna:** AT-004, AT-007 e AT-009 distinguem estados, mas não impedem alteração ou exclusão dos dados fiscais após transmissão.

**Decisão:** pendente — aplicar, recusar com motivo ou adiar; nenhuma decisão presumida.

### G04 — Trilha de auditoria do negócio · severidade alta

**O que muda no app:** Registrar ações de criação, edição, revisão, transmissão, retorno e eventos fiscais com empresa, usuário ou serviço identificado, instante UTC, origem, correlação, antes/depois e motivo quando houver mudança ou ação sensível.

**Por quê:** O histórico deve permitir reconstruir a operação sem depender de mensagens da interface ou da memória dos usuários. A escrita da trilha deve ser controlada no backend, atomicamente com as mudanças locais. **Base legal:** o catálogo não aponta base legal para este item — o fundamento técnico vale por si.

**Requisito (EARS):** **If** o cliente tentar inserir diretamente, alterar ou apagar eventos de auditoria, ou concluir uma mudança de negócio sem o correspondente evento de trilha, **then** the system **shall** recusar a operação e preservar a consistência entre o registro e a auditoria.

**Como provar:** 1. Alterar um rascunho com motivo: a ação gera evento com autoria, UTC e antes/depois. 2. Transmitir e receber retorno: cada ação gera seu evento correlacionado. 3. Tentar inserir, editar e excluir diretamente a trilha com credenciais da aplicação: recusado. 4. Simular falha da auditoria numa alteração local: a alteração não é confirmada.

**Evidência da lacuna:** Nenhum AT exige autoria, motivo ou proteção da trilha.

**Decisão:** pendente — aplicar, recusar com motivo ou adiar; nenhuma decisão presumida.

### G05 — Log forense de segurança · severidade média

**O que muda no app:** Manter log separado para acessos, falhas de autenticação, leituras sensíveis, downloads/exportações e uso de certificado, com retenção própria e cópia fora do banco operacional.

**Por quê:** A trilha de alteração não revela quem consultou um documento ou usou um certificado. O log deve registrar metadados suficientes sem gravar senha, chave privada ou conteúdo sensível desnecessário. **Base legal:** o catálogo não aponta base legal para este item — o fundamento técnico vale por si.

**Requisito (EARS):** **If** uma leitura sensível, exportação ou utilização de certificado tentar ocorrer sem geração do evento forense previsto, **then** the system **shall** impedir a conclusão da ação sensível e registrar a falha por canal de contingência definido no Design.

**Como provar:** 1. Consultar um documento sensível: log registra usuário, empresa, objeto e UTC. 2. Exportar ou baixar documento: evento gerado e cópia externa verificável. 3. Usar certificado em teste: evento com identificação do certificado, sem segredo. 4. Simular indisponibilidade do registro obrigatório: ação sensível bloqueada conforme política definida.

**Evidência da lacuna:** AT-012 recusa acesso cruzado, mas não exige registrar a tentativa; não há requisito de log de leitura ou certificado.

**Decisão:** pendente — aplicar, recusar com motivo ou adiar; nenhuma decisão presumida.

### G06 — Verificação de integridade dos logs · severidade média

**O que muda no app:** Encadear hashes dos eventos auditáveis e guardar âncora periódica fora do sistema, com verificador de integridade.

**Por quê:** Impedir edição pelo cliente é diferente de detectar alteração por acesso administrativo. A cadeia precisa de referência externa para permitir detectar reescrita ou truncamento; não torna impossível toda adulteração. **Base legal:** o catálogo não aponta base legal para este item — o fundamento técnico vale por si.

**Requisito (EARS):** **If** a verificação detectar alteração, exclusão, reordenação ou divergência entre a trilha e sua âncora externa, **then** the system **shall** reprovar a integridade, emitir alerta e impedir que o período seja apresentado como íntegro.

**Como provar:** 1. Gerar eventos e publicar âncora externa diária em ambiente de teste: verificação aprovada. 2. Alterar um evento por acesso administrativo controlado: verificação reprovada. 3. Restaurar a amostra e excluir/reordenar um evento: reprovada. 4. Truncar a trilha em trecho já ancorado: divergência detectada. 5. Usar base sem alteração: resultado aprovado.

**Evidência da lacuna:** Não há AT de detecção de adulteração dos logs.

**Decisão:** pendente — aplicar, recusar com motivo ou adiar; nenhuma decisão presumida.

### G07 — Segregação de preparação e aprovação · severidade alta

**O que muda no app:** Se esta recomendação for adotada, separar preparador e aprovador; definir matriz de permissões, ações sujeitas a aprovação e alçadas, inclusive quando exigir duas aprovações.

**Por quê:** A revisão pelo próprio usuário reduz erros, mas não cumpre a segregação do catálogo. Exigir outro aprovador muda a operação do Cliente e precisa de decisão explícita; não deve ser introduzido silenciosamente. **Base legal:** o catálogo não aponta base legal para este item — o fundamento técnico vale por si.

**Requisito (EARS):** **If** o preparador tentar aprovar a própria emissão, um usuário sem alçada tentar aprová-la ou uma emissão acima da alçada tentar seguir sem duas aprovações válidas, **then** the system **shall** recusar a aprovação ou transmissão.

**Como provar:** 1. Preparador A cria um rascunho. 2. A tenta aprová-lo: recusado. 3. B, autorizado e distinto, aprova versão revisada: permitido dentro da alçada. 4. Usuário sem alçada tenta aprovar: recusado. 5. Operação acima da alçada segue com uma única aprovação: transmissão recusada.

**Evidência da lacuna:** AT-005 e AT-007 exigem revisão deliberada, mas admitem que o próprio preparador confirme a emissão.

**Decisão:** pendente — aplicar, recusar com motivo ou adiar; nenhuma decisão presumida.

**Mudança necessária no AT-007 se G07 for aplicado:**

- Antes: “When o usuário confirmar deliberadamente a emissão após a revisão final, o backend shall transmitir a DPS pela integração oficial da NFS-e Nacional”.
- Depois proposto: “When um aprovador autorizado, distinto do preparador, confirmar a versão revisada e as aprovações exigidas pela alçada estiverem completas, o backend shall transmitir exatamente essa versão da DPS pela integração oficial da NFS-e Nacional”.

Alçadas e eventual dupla aprovação precisam ser definidas antes de tornar o AT verificável. Recusar esta recomendação exige registrar o risco de autoaprovação; revisão final pelo próprio emitente não deve ser descrita como segregação.

### G08 — Documento-fonte preservado · severidade alta

**O que muda no app:** Guardar arquivo importado, linha de origem e hash; no lançamento manual, guardar a versão dos dados confirmados e seus anexos quando existirem; preservar DPS, resposta original e eventos vinculados.

**Por quê:** O rascunho precisa apontar para a informação que lhe deu origem. Não se exige criar um anexo inexistente para uma entrada manual: a origem pode ser o formulário versionado e identificado. **Base legal:** o catálogo não aponta base legal para este item — o fundamento técnico vale por si.

**Requisito (EARS):** **If** houver tentativa de substituir o arquivo original, a versão de origem ou o hash de uma origem já vinculada à operação, **then** the system **shall** recusar a substituição e permitir somente nova versão vinculada, preservando a anterior.

**Como provar:** 1. Importar um arquivo e abrir o rascunho correspondente: origem e linha identificáveis. 2. Baixar o original e recalcular SHA-256: coincide. 3. Tentar sobrescrever arquivo ou hash: recusado. 4. Corrigir a origem por nova versão: ambas as versões permanecem rastreáveis. 5. Criar rascunho manual: autoria e versão do formulário preservadas.

**Evidência da lacuna:** AT-002 cria rascunhos por importação; nenhum AT guarda o arquivo original, hash ou vínculo de origem.

**Decisão:** pendente — aplicar, recusar com motivo ou adiar; nenhuma decisão presumida.

### G09 — Aritmética decimal exata · severidade alta

**O que muda no app:** Usar valores decimais exatos de ponta a ponta, definir precisão intermediária e arredondamento; se houver rateio, definir destino do centavo residual.

**Por quê:** Uma coluna decimal no banco não corrige um cálculo previamente feito com ponto flutuante no frontend. A validação deve comparar valor revisado, persistido e serializado para transmissão. **Base legal:** o catálogo não aponta base legal para este item — o fundamento técnico vale por si.

**Requisito (EARS):** **If** um valor não atender à representação decimal, precisão ou regra de arredondamento definida, ou se o total não corresponder aos componentes aplicáveis, **then** the system **shall** recusar a confirmação e transmissão até correção explícita.

**Como provar:** 1. Conferir estrutura do banco e caminho de cálculo: nenhum valor monetário em tipo de ponto flutuante. 2. Processar casos decimais com resultado esperado conhecido: valor persistido e transmitido coincide. 3. Tentar enviar precisão não suportada ou total divergente: recusado sem ajuste silencioso. 4. Se houver rateio, dividir 100,00 por três: soma 100,00 e resíduo segue regra escrita; sem rateio no MVP, registrar este subteste como N.A.

**Evidência da lacuna:** AT-005 e AT-006 não especificam representação, precisão ou arredondamento.

**Decisão:** pendente — aplicar, recusar com motivo ou adiar; nenhuma decisão presumida.

### G10 — Importação idempotente · severidade alta

**O que muda no app:** Reconhecer registros já importados por empresa e identificador estável de origem, com unicidade no backend; não usar apenas coincidência de valor, data e tomador.

**Por quê:** O mesmo arquivo pode ser reenviado ou ter linhas reordenadas. É preciso definir a identidade do registro no layout, para impedir duplicação sem eliminar operações legítimas semelhantes. O hash do arquivo isoladamente não resolve todos esses casos. **Base legal:** o catálogo não aponta base legal para este item — o fundamento técnico vale por si.

**Requisito (EARS):** **If** um registro de origem já importado para a mesma empresa for submetido novamente, inclusive de forma concorrente, **then** the system **shall** impedir novo rascunho equivalente e informar os registros já existentes.

**Como provar:** 1. Importar um lote com identificadores estáveis: N rascunhos. 2. Reimportar: permanecem N. 3. Reordenar o arquivo e importar de novo: permanecem N. 4. Enviar o mesmo registro em duas requisições simultâneas: um único rascunho criado. 5. Importar duas operações legítimas de mesmo valor com identificadores distintos: ambas aceitas.

**Evidência da lacuna:** AT-002 não impede reimportação; AT-008 limita novo envio pelo mesmo fluxo, sem cobrir a importação ou concorrência no backend.

**Decisão:** pendente — aplicar, recusar com motivo ou adiar; nenhuma decisão presumida.

### G13 — Isolamento completo entre empresas · severidade alta

**O que muda no app:** Aplicar isolamento no backend e no armazenamento para Cliente e Escritório, inclusive consultas, mutações, arquivos, eventos e vínculos; empresa ativa não concede permissão por si só.

**Por quê:** Um filtro de tela não impede troca de identificador numa requisição. Os vínculos precisam assegurar que tomador, rascunho, origem, aprovação e documento pertencem à mesma empresa, sem impedir que um operador autorizado atue em várias empresas. **Base legal:** o catálogo não aponta base legal para este item — o fundamento técnico vale por si.

**Requisito (EARS):** **If** um usuário sem autorização tentar ler, criar, alterar, transmitir ou baixar dados de outra empresa, ou vincular objetos de empresas diferentes, **then** the system **shall** recusar a operação sem expor dados da empresa não autorizada.

**Como provar:** 1. Criar empresas A e B, Cliente A e operador do Escritório autorizado somente para A. 2. Ambos tentam acessar B por API, identificador e endereço de arquivo: recusado. 3. Tentar vincular rascunho A a origem ou aprovação B: recusado. 4. Conceder ao operador acesso também a B: operação legítima em B funciona sem misturar A. 5. Revogar acesso a B e repetir com sessão existente: acesso recusado.

**Evidência da lacuna:** AT-012 cobre acesso de Cliente a outra empresa; AT-003 cobre contexto visual, mas faltam testes de vínculos, escrita, documentos e autorização do Escritório.

**Decisão:** pendente — aplicar, recusar com motivo ou adiar; nenhuma decisão presumida.

## Já coberto

Nenhum item do catálogo está integralmente coberto com sua prova negativa. Isso não desconsidera os controles existentes: AT-003, AT-005, AT-006, AT-008 e AT-012 são bons pontos de partida, mas cobrem partes de controles mais amplos.

## N.A.

G02 e G03: ausência de escrituração e fechamento no MVP. G17–G20: ausência de IA em runtime. Caso o escopo passe a incluir essas funções, repetir a análise desses itens.

## 2ª camada — recomendações detalhadas

Esta classificação é do catálogo, não uma decisão de adiamento pelo profissional.

### G11 — Vigência e memória de cálculo · média

**Mudança:** preservar versão da regra/configuração aplicável, parâmetros e insumos da emissão; qualquer alteração futura de parâmetro não reescreve o histórico.

**Fundamento:** o resultado passado precisa ser reconstituído com os dados e parâmetros originais. **Base legal:** o catálogo não aponta base legal para este item — o fundamento técnico vale por si.

**EARS proposto:** **If** uma atualização de regra ou parâmetro tentar sobrescrever a memória de uma emissão anterior, **then** the system **shall** recusar a sobrescrita e preservar a versão histórica.

**Prova:** 1. Emitir teste com configuração V1 e guardar memória. 2. Ativar V2 com outra vigência: V1 continua preservada. 3. Reproduzir o cálculo histórico: mesmo resultado. 4. Tentar sobrescrever a configuração vinculada: recusado.

### G12 — Totais de controle por lote · média

**Mudança:** apresentar quantidade e valores de entrada, rascunhos criados, duplicados, inválidos e resultados oficiais; toda diferença vira pendência.

**Fundamento:** um lote parcialmente processado não pode parecer completo. Esta é conferência de importação/emissão, sem acrescentar conciliação bancária. **Base legal:** o catálogo não aponta base legal para este item — o fundamento técnico vale por si.

**EARS proposto:** **If** houver diferença entre totais de entrada e destinações do lote sem justificativa registrada, **then** the system **shall** impedir que o lote seja marcado como integralmente conferido.

**Prova:** 1. Importar lote com total conhecido: total de entrada preservado. 2. Introduzir rejeição e duplicidade: ambas segregadas nos totais. 3. Tentar concluir sem tratar divergência: recusado. 4. Registrar a pendência e seu responsável: lote aparece com pendência, sem ajuste silencioso de valor.

### G14 — Política de guarda e proteção · média

**Mudança:** definir guarda por documento/evento, bloqueio de eliminação durante a guarda aplicável e tratamento de dados sem destruir a evidência fiscal.

**Fundamento:** “até a prescrição” sozinho não especifica prazo, termo inicial, suspensão da eliminação ou classes de documentos. Pseudonimização deve ser avaliada conforme o tipo de dado; não pode alterar o original fiscal que precisa ser preservado. **Base legal:** ainda não confirmada no catálogo — confira na fonte antes de citar.

**EARS proposto:** **If** um pedido de eliminação atingir documento ainda sujeito à política de guarda validada ou a bloqueio de conservação, **then** the system **shall** recusar a exclusão destrutiva e registrar a decisão e seu fundamento.

**Prova:** 1. Configurar classe documental e prazo de teste aprovado. 2. Solicitar exclusão antes do prazo: recusado e auditado. 3. Acionar bloqueio de conservação: exclusão continua recusada. 4. Após liberação e vencimento, executar procedimento autorizado: preservar apenas o que a política determina e registrar a ação.

### G15 — Recuperação testada · média

**Mudança:** definir backup de banco, arquivos e configurações; testar restauração segregada, com metas de perda de dados e tempo de recuperação.

**Fundamento:** recuperar somente o banco sem os documentos ou vínculos não recupera a operação fiscal. **Base legal:** o catálogo não aponta base legal para este item — o fundamento técnico vale por si.

**EARS proposto:** **If** a restauração não recuperar documentos, vínculos, trilha e estados até o ponto definido, **then** the system **shall** reprovar o teste de recuperação e impedir seu registro como bem-sucedido.

**Prova:** 1. Criar amostra com nota, evento, origem e log. 2. Restaurar backup em ambiente separado: sem transmissão fiscal real. 3. Conferir conteúdo, hashes, vínculos e estados: recuperados. 4. Medir tempo e perda frente às metas: falha reprova. 5. Remover um documento da amostra restaurada: verificação acusa inconsistência.

### G16 — Certificados e segredos · alta

**Mudança:** custodiar certificados e segredos cifrados em serviço adequado, com acesso mínimo, uso registrado, expiração, revogação e rotação.

**Fundamento:** manter a chamada no backend reduz exposição, mas não prova que segredo esteja protegido em código, armazenamento, logs e respostas. Recomendo antecipar este controle antes de conectar certificado real. **Base legal:** o catálogo não aponta base legal para este item — o fundamento técnico vale por si.

**EARS proposto:** **If** um cliente tentar obter o segredo, usar certificado de outra empresa ou executar operação com certificado inválido ou sem autorização vigente, **then** the system **shall** negar o acesso ou uso e registrar o evento sem expor o segredo.

**Prova:** 1. Procurar certificado/senha no código, bundle do frontend e banco em claro: ausentes. 2. Tentar recuperá-los por API com usuário Cliente: recusado. 3. Tentar usar certificado B para empresa A: recusado. 4. Expirar/revogar credencial de teste: uso bloqueado. 5. Rotacionar e realizar operação autorizada: novo uso registrado sem segredo.

## Pendências específicas da feature, além do catálogo

Estas recomendações complementam a revisão; não alteram a contagem dos 20 itens.

### F01 — Resultado desconhecido após timeout · alta

AT-011 trata timeout como erro técnico e oferece nova tentativa, mas não exige resolver se a API aceitou a primeira transmissão. Bloquear o botão no AT-008 não cobre concorrência, várias abas ou reinício do backend.

**Recomendação:** persistir identificador estável da operação e tentativa antes do envio; distinguir rejeição confirmada de resultado ainda desconhecido; consultar/reconciliar o resultado oficial antes de autorizar nova tentativa. Definir no Design o mecanismo compatível com o contrato oficial, sem presumir cabeçalho ou recurso de idempotência da API.

**EARS proposto:** **If** uma tentativa estiver com resultado desconhecido ou houver requisição concorrente para a mesma operação, **then** the system **shall** impedir nova emissão independente, preservar sua identidade e reconciliar o resultado oficial.

**Prova:** 1. Simular API que aceita e perde a resposta. 2. Tentar reenviar em outra aba: nenhuma nova operação independente. 3. Consultar e obter a autorização original: recuperar o mesmo documento. 4. Reiniciar o backend durante a pendência: identidade e bloqueio persistem. 5. Rejeição confirmada segue tratamento distinto.

**AT-011:** precisa ser reescrito, após decisão, para contemplar “resultado desconhecido” e condicionar a tentativa à reconciliação, sem marcar emissão como confirmada apenas por presunção.

### F02 — Revisão vinculada à versão e à empresa · alta

**Recomendação:** vincular a confirmação humana à versão exata revisada, usuário, empresa e conteúdo a transmitir. Alteração de valor, tomador, operação, parâmetro crítico ou empresa invalida a confirmação anterior.

**EARS proposto:** **If** o conteúdo crítico, a empresa ou a versão divergir da revisão confirmada, **then** the system **shall** recusar a transmissão e exigir nova revisão.

**Prova:** 1. Revisar versão V1. 2. Alterar o valor em outra sessão: aprovação de V1 deixa de autorizar a versão nova. 3. Tentar enviar: recusado. 4. Revisar versão nova: envio autorizado apenas para seu conteúdo e empresa.

### F03 — Elegibilidade fiscal e liberação do piloto · alta

O DEFINE acerta ao não equiparar aluguel, venda de imóvel e arrendamento. Falta transformar essa restrição em bloqueio verificável: nem todo recebimento imobiliário deve ser convertido automaticamente em NFS-e.

**Recomendação:** exigir validação técnica explícita das operações admitidas, natureza do valor faturado, parâmetros fiscais, autorização do emitente e aptidão do município/ambiente. Registrar evidência e responsável pela liberação; bloquear operações ainda não validadas. Não se afirma aqui qual dessas operações tem incidência ou qual documento é obrigatório.

**EARS proposto:** **If** a operação, empresa ou configuração municipal/ambiental ainda não tiver validação e liberação registradas, **then** the system **shall** impedir transmissão em produção e indicar a pendência.

**Prova:** 1. Cadastrar operação sem validação: envio bloqueado. 2. Validar uma operação para empresa/ambiente de teste: somente esse contexto fica elegível. 3. Tentar usar a liberação para outra operação ou empresa: recusado. 4. Revogar a liberação: bloqueio restabelecido.

A-002 e A-003 continuam pendentes; A-001 está marcado “yes” sem evidência anexada no DEFINE. Esta revisão não confirma disponibilidade, autenticação ou contrato atual da integração. A validação oficial desses pontos deve preceder a implementação da integração e a liberação operacional.

## Decisões e aplicação no DEFINE

| Situação | Registro |
|---|---|
| Decisões de aplicar | Nenhuma solicitada ou concedida nesta revisão |
| Recusas e riscos aceitos | Nenhum; silêncio não é aceite de risco |
| Adiamentos pelo profissional | Nenhum; segunda camada é classificação do catálogo |
| ATs novos | Nenhum aplicado; propostas estão neste relatório |
| ATs a reescrever se aprovados | AT-007 para G07; AT-011 para F01; complementar AT-005/AT-007 com F02 |
| Clarity Score | 14/15 antes → 14/15 depois; DEFINE não alterado |
| Status original | Needs Clarification, preservado |

O Clarity Score mede clareza e não comprova governança. Não elevar a pontuação apenas por acrescentar recomendações ainda sem decisão ou prova.

A skill exige decisão individual: aplicar, recusar com motivo ou adiar. Como a solicitação atual é revisar e recomendar, as propostas foram entregues sem modificar o DEFINE. Na etapa de incorporação, apresentar uma lacuna por vez; começar por G01, depois controles de duplicidade, auditoria e isolamento. Para cada aplicação, atribuir o próximo AT livre, incluir roteiro de prova, compatibilizar ATs existentes e atualizar o histórico.

## Próximo passo recomendado

1. Formalizar os dois campos pendentes do padrão: responsável técnico com CRC e política de guarda.
2. Decidir individualmente as recomendações, registrando motivo das recusas e alcance dos adiamentos.
3. Incorporar apenas as decisões aprovadas ao DEFINE; resolver a indefinição do Verify Gate no Design/Build.
4. Executar a UX Review específica deste projeto sobre o DEFINE revisado, usando seu UX_STANDARD canônico.
5. Avançar ao SDD Design com regras de autorização, estados, persistência e provas já rastreáveis.

Não foram gerados scripts SQL: ainda não há stack, tabelas ou comando de Verify Gate definidos. Quando existirem, adaptar as provas do catálogo ao schema real, mantendo a inversão dos testes e as guardas de preparação, em ambiente de desenvolvimento ou teste.

---

> No Build, rode a auditoria de schema (`rdd-audita-schema`) sobre a migration: os itens com coluna pós-build preenchida no catálogo têm prova também no SQL. A disponibilidade dessa skill deverá ser verificada nessa fase.
>
> A skill recomenda; o profissional decide e responde.

