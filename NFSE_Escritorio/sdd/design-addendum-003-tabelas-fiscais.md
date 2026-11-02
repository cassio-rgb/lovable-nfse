# Adendo 003 — Catálogos fiscais de consulta

2026-11-02. Incremento autorizado pelo usuário após entrega das quatro planilhas. Modo sequencial, continuação do Build. Sem LLM. Arquitetura e bloqueio de transmissão real preservados. Lovable analisou fontes, mas chamadas de continuação retornaram INVALID_ARGUMENT; execução local, sincronização pendente.

## Contrato e aceite

Catálogo único JSON gerado de fontes imutáveis, com hashes SHA256. Serviço nacional de seis dígitos (338), NBS com padrão detalhado e espaços externos removidos (918 registros; 917 com descrição selecionáveis, marcador 9.9999.99.99 sem descrição preservado apenas na fonte), cClassTrib (173; 73 NFS-e), CST correspondente e indOp (40; 28 NFS-e). Não inferir vigência ou homologação do download. Nenhum cálculo de imposto ou liberação de emissão.

Seleção opcional no armazenamento do rascunho; obrigatória na revisão deste fluxo. Importação legada cria rascunhos incompletos sem preencher códigos. Canonical legado preservado para deduplicação quando seleção ausente; revisão legada sem seleção é inválida. Seleção presente participa integralmente do hash; fonte desconhecida, código inexistente, indicador não NFS-e e par CST/cClassTrib incoerente bloqueiam revisão. Validação espelhada TS/Python. PostgreSQL mantém seleção no JSON existente, sem migração.

Anexo VIII somente consulta, com expansão de células mescladas limitada a seus intervalos, linha de origem preservada. Nenhuma propagação global de células vazias, nenhuma escolha automática ou validação obrigatória por correlação. Fonte preliminar, não regra fiscal.

## File Manifest

1. scripts/gerar_catalogos.py: extrator reproduzível offline, openpyxl só na regeneração.
2. backend/tests/fixtures/official/catalogos/*: quatro fontes originais.
3. shared/catalogos-fiscais.json: catálogo com metadados e proveniência.
4. src/lib/catalogos.ts: pesquisa e validação para UX.
5. src/lib/contracts.ts: seleção opcional no contrato.
6. src/lib/domain.ts: hash/revisão/status com catálogo.
7. src/lib/datasource.ts: bloqueio de revisão incompleta.
8. src/components/CatalogFields.tsx: busca explícita e revisão dos códigos.
9. src/components/DraftForm.tsx: integração no formulário.
10. src/routes/revisao.$id.tsx: códigos na revisão final.
11. backend/app/catalogos.py: validação autoritativa Python.
12. backend/app/domain/models.py: seleção e hash.
13. backend/app/api.py: entrada tipada e saída persistente.
14. backend/app/reviews.py: exigir catálogo válido na revisão e invalidar antigas.
15. backend/app/pg.py: roundtrip JSON.
16. src/test/catalogos.test.ts e src/test/catalog-fields.test.tsx: testes de dados/UX.
17. backend/tests/test_catalogos.py: testes de domínio/fontes/revisão.
18. vite.config.ts: acesso indexado a variável de ambiente para typecheck.
19. sdd/BUILD_REPORT_TABELAS_FISCAIS.md: evidências e bloqueios.

20. src/test/domain.test.ts e backend/tests/helpers.py: seleções explícitas nas fixtures existentes de revisão.

21. backend/tests/test_api.py: seleção explícita na fixture de revisão da API.
22. scripts/verify.py: registrar nova suíte no runner local existente.

23. deploy/backend.Dockerfile: incluir o mesmo catálogo JSON na imagem existente (sem build/deploy de imagem nesta entrega).

24. ATUALIZACAO_TABELAS_MANIFEST.json e LEIA_ATUALIZACAO_TABELAS.txt: manifesto de distribuição e instruções Windows, gerados ao empacotar.

## Verificação

Comparar catálogos com as quatro fontes, testar pesquisa e escolha, hashes e roundtrip, salvar incompleto/rejeitar revisão, carregar legados. Executar testes TS/Python relevantes, typecheck e build local. Verify Gate original continua em clarificação (5); não declarar sistema fiscal completo. Sem revisão externa formal disponível. Teste humano Windows após instalação permanece pendente.
