# UX REVIEW: {FEATURE_NAME}

> Revisão UX/CX depois do Define e antes do Design, baseada na fonte canônica do projeto. Gravar na pasta do SDD, ao lado do DEFINE.

## Metadata

| Atributo | Valor |
|---|---|
| Feature | {FEATURE_NAME} |
| Data | {YYYY-MM-DD} |
| Autor | ux-review |
| DEFINE | {DEFINE_PATH} |
| UX_STANDARD | {UX_STANDARD_PATH} |
| UX_STANDARD Version | {UX_STANDARD_VERSION} |
| Status | Draft / Ready for Design / Blocked for Design |

## UX Summary

{Resumo de 2-4 frases com objetivo da experiência, maior risco e recomendação principal.}

## Sources and Evidence

| Fonte | Papel | Versão/estado | Evidência usada |
|---|---|---|---|
| DEFINE | Requisitos funcionais | {VERSION} | {EVIDENCE} |
| UX_STANDARD | Fonte canônica | {VERSION} | {RULE_IDS} |
| {OPTIONAL_SOURCE} | Contexto adicional | {STATE} | {EVIDENCE} |

## User and Context

| Campo | Valor |
|---|---|
| Usuário principal | {PERSONA_OR_ROLE} |
| Objetivo do usuário | {USER_GOAL} |
| Dor principal | {PAIN} |
| Objetivo de negócio/CX | {BUSINESS_GOAL} |
| Dispositivo/contexto | {DEVICE_CONTEXT} |

## Journey Map

| Etapa | Intenção | Emoção/Risco | Fricção | Necessidade da interface | Recuperação |
|---|---|---|---|---|---|
| Before | {TEXT} | {TEXT} | {TEXT} | {TEXT} | {TEXT} |
| Entry | {TEXT} | {TEXT} | {TEXT} | {TEXT} | {TEXT} |
| Core Action | {TEXT} | {TEXT} | {TEXT} | {TEXT} | {TEXT} |
| Feedback | {TEXT} | {TEXT} | {TEXT} | {TEXT} | {TEXT} |
| Recovery | {TEXT} | {TEXT} | {TEXT} | {TEXT} | {TEXT} |
| Completion | {TEXT} | {TEXT} | {TEXT} | {TEXT} | {TEXT} |
| Follow-up | {TEXT} | {TEXT} | {TEXT} | {TEXT} | {TEXT} |

## Canonical Conformance

| Regra canonica | Status | Evidência | Observação |
|---|---|---|---|
| {UX-ID} | CONFORME / MUST / SHOULD / COULD / WONT / NAO AVALIAVEL | {EVIDENCE} | {NOTE} |

## UX/CX Findings

| Prioridade | Regra canônica | Área | Finding | Evidência | Recomendação |
|---|---|---|---|---|---|
| MUST | {UX-ID} | {AREA} | {RISK} | {EVIDENCE} | {ACTION} |
| SHOULD | {UX-ID} | {AREA} | {OPPORTUNITY} | {EVIDENCE} | {ACTION} |
| COULD | {UX-ID_OR_NA} | {AREA} | {POLISH} | {EVIDENCE} | {ACTION} |
| WONT | {UX-ID_OR_NA} | {AREA} | {EXCLUDED_IDEA} | {EVIDENCE} | {WHY} |

## Universal Principles Check

| ID | Princípio | Status | Evidência/Risco |
|---|---|---|---|
| UX-CORE-001 | Autoexplicativo | CONFORME / MUST / NAO AVALIAVEL | {EVIDENCE} |
| UX-CORE-002 | Estado inequívoco | CONFORME / MUST / NAO AVALIAVEL | {EVIDENCE} |
| UX-CORE-003 | Ação principal evidente | CONFORME / MUST / NAO AVALIAVEL | {EVIDENCE} |
| UX-CORE-004 | Prevenção e recuperação | CONFORME / MUST / NAO AVALIAVEL | {EVIDENCE} |
| UX-CORE-005 | Acessibilidade por padrão | CONFORME / MUST / NAO AVALIAVEL | {EVIDENCE} |
| UX-CORE-006 | Responsividade real | CONFORME / MUST / NAO AVALIAVEL | {EVIDENCE} |
| UX-CORE-007 | Feedback imediato | CONFORME / MUST / NAO AVALIAVEL | {EVIDENCE} |
| UX-CORE-008 | Consistência | CONFORME / SHOULD / MUST / NAO AVALIAVEL | {EVIDENCE} |
| UX-CORE-009 | Sem dark patterns | CONFORME / MUST / NAO AVALIAVEL | {EVIDENCE} |
| UX-CORE-010 | Acabamento completo | CONFORME / MUST / NAO AVALIAVEL | {EVIDENCE} |

## Project North Star Checks

| Regra | Status | Evidência/Risco |
|---|---|---|
| UX-NAV-001 | CONFORME / MUST / SHOULD / NAO AVALIAVEL | Empresa/CNPJ ativo está inequívoco? |
| UX-FORM-002 | CONFORME / MUST / NAO AVALIAVEL | Existe revisão final obrigatória? |
| UX-INT-001 | CONFORME / MUST / NAO AVALIAVEL | Alertas críticos são destacados de forma acionável? |
| UX-STATE-008 | CONFORME / MUST / NAO AVALIAVEL | Rascunho e emissão/transmissão são distintos? |
| UX-A11Y-001 | CONFORME / MUST / NAO AVALIAVEL | Evidência disponível para WCAG 2.2 AA? |
| UX-RESP-001 | CONFORME / SHOULD / MUST / NAO AVALIAVEL | Desktop e celular cumprem os contextos definidos? |

## Visual System Review

Validar somente o sistema definido no `UX_STANDARD.md`. Não introduzir tokens, temas, cores, buckets ou ratios de outro projeto.

| Regra | Papel | Evidência | Status | Recomendação |
|---|---|---|---|---|
| {UX-VIS-ID} | {ROLE} | {EVIDENCE} | {STATUS} | {ACTION} |

## Interaction Requirements

| Regra | Requisito | Motivo | Prioridade |
|---|---|---|---|
| {UX-INT-ID} | {REQUIREMENT} | {WHY} | MUST/SHOULD/COULD |

## Required States

| Estado | Regra canônica | UX requerida | Status |
|---|---|---|---|
| Loading | UX-STATE-001 | Atividade perceptível sem induzir duplo envio | {STATUS} |
| Empty | UX-STATE-002 | Explicar ausência e próximo passo útil | {STATUS} |
| Error | UX-STATE-003 | Linguagem simples, recuperação e detalhe técnico opcional | {STATUS} |
| Success | UX-STATE-004 | Confirmação inequívoca e próximos passos | {STATUS} |
| Partial Data | UX-STATE-005 | Diferenciar parcial de completo e informar impacto | {STATUS} |
| Permission Denied | UX-STATE-006 | Informar bloqueio sem expor dados indevidos | {STATUS} |
| Disabled | UX-STATE-007 | Motivo compreensível quando não óbvio | {STATUS} |

## Content and Copy Guidance

| Regra | Surface | Orientação |
|---|---|---|
| UX-COPY-005 | Primary CTA | Nomear a ação real, como `Emitir NFS-e` |
| UX-COPY-003 | Error Copy | Começar pelo impacto e próximo passo; detalhe técnico depois |
| UX-COPY-006 | Confirmation | Repetir empresa e objeto quando houver risco crítico |
| UX-STATE-002 | Empty State | Explicar ausência e oferecer ação útil |

## Accessibility and Responsiveness

| Regra | Preocupação | Requisito | Evidência/Medição |
|---|---|---|---|
| UX-A11Y-002 / UX-A11Y-003 | Keyboard/Focus | Fluxos principais operáveis por teclado e foco visível | {EVIDENCE} |
| UX-A11Y-005 | Contrast | Verificar WCAG 2.2 AA | {MEASURED_OR_NOT_EVALUABLE} |
| UX-A11Y-004 | Screen Reader/Labels | Rótulos e mensagens associados programaticamente | {EVIDENCE} |
| UX-RESP-003 / UX-RESP-004 | Mobile/Responsive | Consulta e emissão simples completas no celular; críticos não omitidos | {EVIDENCE} |
| UX-A11Y-006 | Non-color cues | Estados e alertas não dependem apenas de cor | {EVIDENCE} |

## Gamification Strategy

Gamification decision: Not recommended because o fluxo principal envolve emissão fiscal e deve priorizar precisão, clareza e prevenção de erro, conforme UX-GAME-001.

## Design Handoff

### UX requirements
- Aplicar apenas regras canônicas relevantes à feature e citar seus IDs.
- Preservar empresa ativa, estado da emissão e próxima ação como elementos inequívocos.
- Incluir revisão final obrigatória nas features de emissão.

### Components likely needed
- Seletor/indicador persistente de empresa para perfil Escritório.
- Formulários progressivos e condicionais.
- Bloco de revisão final.
- Alertas e mensagens com detalhe técnico expansível.
- Estados de loading, empty, error, success, partial data, permission denied e disabled.

### State requirements
- Não confundir rascunho, processando, emitido, erro ou cancelado.

### Copy guidance
- Linguagem humana e objetiva na superfície; detalhe técnico opcional.

### Visual guidance
- Interface clara, moderna, amigável, baixa competição visual e ação principal evidente.

### Accessibility/responsiveness
- Referência WCAG 2.2 AA; desktop principal e celular para consulta/emissão simples.

### Acceptance notes
- [ ] Empresa/CNPJ ativo inequívoco quando aplicável.
- [ ] Campos críticos revisáveis antes da transmissão.
- [ ] Nenhum MUST aberto sem correção ou aceite explícito.
- [ ] Estados essenciais cobertos.
- [ ] Itens não comprovados marcados `NAO AVALIAVEL`.

## Canonical Evolution Proposals

Apenas sugestões. Não editar `UX_STANDARD.md` neste fluxo.

| Regra afetada/nova | Problema observado | Mudança proposta | Motivo | Bloqueia esta feature? |
|---|---|---|---|---|
| {UX-ID_OR_NEW} | {ISSUE} | {PROPOSAL} | {WHY} | Yes/No |

## Gate Outcome

**Resultado:** READY FOR DESIGN / BLOCKED FOR DESIGN

**MUST abertos:** {COUNT}

**MUST aceitos explicitamente como exceção:** {COUNT}

Regra: qualquer MUST não resolvido ou não aceito explicitamente mantém `BLOCKED FOR DESIGN`.

## Open UX Questions

- {QUESTION}

Se nenhuma: `None - ready for Design.`

## Revision History

| Versão | Data | Autor | Mudanças |
|---|---|---|---|
| 1.0 | {YYYY-MM-DD} | ux-review | Initial UX review |

## Next Step

Se `READY FOR DESIGN`: executar o Design usando esta revisão como handoff.

Se `BLOCKED FOR DESIGN`: resolver ou aceitar explicitamente os MUST antes do Design.
