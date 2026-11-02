# DESIGN — Adendo 001: assinatura delegada com certificado A1 do escritório

Data: 2026-11-02. Decisão explícita do usuário dentro da arquitetura existente (Lovable + serviço
fiscal Python/FastAPI/PostgreSQL). Não altera DEFINE, UX gate nem o Verify Gate; não declara nada concluído.

## Decisão
- O escritório (Atual Assessoria) assina com o **próprio certificado A1** (.pfx/.p12), confirmado pelo usuário.
- O **emitente fiscal** continua sendo a empresa cliente: o CNPJ do prestador na DPS e no Id da DPS é sempre o do cliente.
- A assinatura delegada só é permitida com **resultado de autorização confiável** (outorgante = cliente,
  outorgado = escritório, serviço Receita 00233, ambiente correto, vigente, consultado recentemente).
- Recibo WEB, captura de tela, booleano ou configuração **não** produzem autorização.

## Fontes oficiais citadas pelo usuário
- gov.br/nfse — "Nova funcionalidade possibilita representação e alternância de perfis na NFS-e" (publicado 31/10, disponível 01/11): representação vale para WEB e API; o certificado usado na comunicação e nas assinaturas valida a representação.
- Guia Emissor Público Nacional WEB v1.3, item 11, pp. 126–129.
- Identidade do certificado: DOC-ICP-04 v8.3 (OID 2.16.76.1.3.3 = CNPJ, 14 posições, OCTET STRING ou PrintableString).

## Registro do piloto (somente declaração do usuário, 2026-11-02)
Recibo de representação no **Emissor WEB**: representada/emitente L'OR BLANC GESTORA DE BENS LTDA,
CNPJ 14.168.985/0001-73; representante (escritório) CNPJ 27.532.638/0001-20.
Status: **informativo, não verificado por API**. A captura não comprova ambiente de produção restrita,
acesso via API, datas nem escopo. Estes dados **não** entram em dados de demonstração, fixtures nem emissão automática.

## Implementação
`backend/app/nfse/certificado.py`, `backend/app/nfse/delegacao.py`, `preparar(..., contexto=)` em
`backend/app/nfse/offline.py`, `scripts/inspecionar_certificado.py`, testes `backend/tests/test_certificado.py`.
Provedor oficial de autorização: **não implementado** (contrato não capturado) → bloqueado.
