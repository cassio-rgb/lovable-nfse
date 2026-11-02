# Evidências da integração NFS-e Nacional — OFFLINE parcial; transmissão BLOQUEADA

Atualizado 2026-10-31. Downloads feitos neste ambiente; hashes recalculados e conferidos com os informados pela pesquisa.

| Item | Fonte | Versão/data | SHA-256 | Situação |
|---|---|---|---|---|
| XSD produção | `.../documentacao-atual/nfse-esquemas_xsd-v1-01-20260209.zip` | v1.01, 2026-02-09 (subpasta `Schemas/1.01`) | `e7935cbd9470527c6cc32984c1b2263e614183bf0139ce2733eaaed2de9a8072` | Vendorizado em `backend/app/nfse/schemas/producao_v1_01_20260209/` |
| XSD produção restrita | `.../producao-restrita/esquemas_prod_restrita_20261020.zip` | 2026-10-20 | `25fdcecc651a67a216496ab10d7566631e6ed10f721e37d62c7845dadb0ea267` | Vendorizado em `backend/app/nfse/schemas/producao_restrita_20261020/` |
| Anexo I leiaute (restrita) | `.../anexo_i-sefin_adn-dps_nfse-snnfse_prodrest-v1-01-20261020.xlsx` | 2026-10-20 | `72b05981c8882cdd807f3acf901b669465360f9cf1b9d9e235ac4363dacfb2d8` | Vendorizado como fixture em `backend/tests/fixtures/official/`; regra E0004 (aba "RN DPS_NFS-e 1.01", linha 151) lida pelo teste |
| Manual contribuintes v1.2 (out/2025) | `.../manual-contribuintes-emissor-publico-api-sistema-nacional-nfs-e-v1-2-out2025.pdf` | v1.2 | — | Rotas POST /nfse, GET /nfse/{chave}, GET/HEAD /dps/{id} (via pesquisa) |
| OpenAPI produção restrita | `https://sefin.producaorestrita.nfse.gov.br/API/SefinNacional/docs/index` | — | — | **HTTP 403** (nova tentativa 2026-10-31) — envelope não verificado |
| OpenAPI produção | `https://sefin.nfse.gov.br/SefinNacional/docs/index` | — | — | **HTTP 403** — envelope não verificado |
| Algoritmo de assinatura vigente | XSD atuais não fixam; manual 2022 (RSA-SHA1) arquivado | — | — | **Não confirmado** |

Hash de cada `.xsd` em `backend/app/nfse/schemas/MANIFEST.json` (verificado antes de carregar).

## Achados
1. **Restrita exige `finNFSe`** (após `cMotivoEmisTI`, antes de `chNFSeRej`; enum `0`); produção não tem o elemento.
2. **Restrita aceita CNPJ alfanumérico** (`[0-9A-Z]{14}`, Id com tipo `2`); produção só numérico. O app **recusa** CNPJ/CPF com letras (Python e TS), sem remover caracteres.
3. **Defeito no XSD de produção v1.01:** `TSSerieDPS` = `^0{0,4}\d{1,5}$`. Em XSD, `^` e `$` são literais, então nenhuma série real valida. O esquema oficial não foi alterado; o perfil de produção fica bloqueado para construção (teste `test_producao_schema_serie_defect_blocks_build`). A restrita usa `[0-9]{1,4}|[0-8][0-9]{4}`.
4. O `xmldsig-core-schema.xsd` de produção tem DOCTYPE com DTD externo; carregado com `load_dtd=False`, `no_network=True`, sem buscar nada.

5. **Correção (revisão 3f48422):** a regra E0004 define tipo de inscrição 1 = CPF e **2 = CNPJ**. O Id usava `1` para CNPJ (o XSD aceitava, a regra rejeitaria). Agora usa `2`; o teste lê o texto da regra no anexo oficial.
6. **C14N do libxml2 2.14.6** (empacotado no lxml 6.0.2 e 6.1.3): canonicalizar uma subárvore in-place, quando o default namespace redefine o do ancestral, gera `xmlns=""` espúrio. Num caso mínimo dá `C14NError`. O assinador anterior era coerente só consigo mesmo e falhava fora dele. Correção: canonicalizar uma cópia destacada, que preserva os namespaces em escopo. **Verificação independente** com `xmlsec1` 1.3.7 (libxmlsec/OpenSSL, libxml2 2.15.1, nixpkgs) em `tests/test_interop.py`: SHA-256 e SHA-1 dão OK; valor alterado e certificado de confiança errado falham. O signxml 5.2.0 continua falhando neste ambiente porque usa a mesma C14N defeituosa do lxml; não é usado como evidência.
7. O parser recusava DOCTYPE só por varredura de bytes, e UTF-16/32 escapava. Agora aceita **somente UTF-8 estrito** (sem BOM UTF-16/32, sem NUL, declaração só UTF-8) e, **após o parse**, recusa `docinfo.doctype`/DTD e qualquer nó de entidade.
8. `verificar(..., ambiente)` passou a exigir também `tpAmb` do ambiente (E0006) e Id coerente (E0004), mesmo com assinatura válida. A preparação offline exige que a identidade persistida pertença exatamente à empresa/ambiente da emissão (prefixo + número), sem mutação nem nova reserva.

## Implementado (offline)
- `secure_xml.py`: limite 512 KiB, recusa DOCTYPE/ENTITY, parser sem rede/DTD/entidades; esquemas só com arquivos do manifest e hash conferido (resolver de allowlist).
- `dps.py`: entrada tipada (`EntradaDPS`, `ParametrosFiscais`), `dCompet` como data completa, regime/códigos/município explícitos, Id `DPS`+mun7+`2`(CNPJ, regra E0004)+CNPJ14+série5+número15, builder determinístico na ordem do `TCInfDPS`, validação XSD por perfil e coerência Id/tpAmb.
- `signing.py`: XMLDSIG envelopado com referência exata `#Id`, C14N 1.0, perfis versionados (`xmldsig-rsa-sha256-c14n10` = `nao_confirmado`; `...sha1...-legado` = `legado_nao_vigente`). `permite_transmissao` é falso para todos. A verificação recusa Id duplicado, wrapping, assinatura fora do lugar, transform, algoritmo ou certificado diferentes e conteúdo alterado.
- `client.py`: allowlist exata (https, host exato e sensível a caixa, porta 443, caminho por regex completa e método), sem `%`, `\`, `@`, query, fragmento ou `..`. Destino deve ser o do ambiente. Sem redirect, TLS sempre verificado, POST nunca repetido, timeouts limitados, interface mTLS. `submit`/`lookup` falham com motivo exato.
- `offline.py`: artefato a partir do snapshot imutável e da identidade reservada (`nDPS` = número persistido). Confere CNPJ da empresa, competência e ambiente; não muda estado; `transmissivel=False`.

## Pendente para liberar transmissão
Contrato HTTP oficial (OpenAPI), perfil criptográfico vigente confirmado, correção/confirmação do XSD de produção (série), certificado autorizado via cofre, cadastro durável de `ParametrosFiscais` por responsável fiscal, identidade/storage/infra, smoke em produção restrita (emissão válida, rejeição, consulta pela DPS) e Verify Gate do DEFINE.

## 2026-11-02 — A1 PKCS#12 e assinatura delegada (offline)
- OpenAPI oficial: 1 tentativa, produção restrita e produção → HTTP 403. Envelope HTTP e algoritmo continuam **não verificados**.
- Identidade do certificado: DOC-ICP-04 v8.3 (PDF gov.br/iti, sha256 `0603dbb47ea9f1928a5e6f72168a2f6dfe1ad2796b394aa6ad6ac92282a9c9a8`),
  item 7.1.2.2 (otherName em OCTET STRING ou PRINTABLE STRING; zeros quando indisponível) e Anexo I
  (OID 2.16.76.1.3.3 = CNPJ em 14 posições). Parser DER estrito e limitado em `app/nfse/certificado.py`. CN/nome de arquivo nunca usados.
- `carregar_a1`: verifica só estrutura local (chave↔certificado, RSA ≥ 2048, X.509 v3, validade, ambiguidade). Cadeia ICP,
  revogação e autorização governamental ficam `nao_verificado`.
- `contexto_assinatura`: delegação exige provedor confiável e resultado vigente para outorgante/outorgado/serviço 00233/ambiente;
  `ProvedorAutorizacaoAusente` bloqueia; provedor sintético só com `APP_ENV=test`; recibo WEB é ignorado na decisão.
- `preparar(..., contexto=)`: DPS mantém CNPJ do cliente; recusa certificado de terceiro sem contexto, contexto de outra empresa/ambiente
  ou outro certificado. Artefato continua `transmissivel=False`.
- Recibo WEB do piloto registrado apenas como declaração do usuário (ver adendo de DESIGN); não usado em código, fixtures ou demo.
