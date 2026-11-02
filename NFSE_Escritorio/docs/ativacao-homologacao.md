# Ativação em homologação (produção restrita) — passo a passo

Situação em 2026-10-31: **BLOQUEADO**. Este guia não autoriza implantação, publicação nem transmissão.
Nenhuma etapa pede chave, senha ou certificado no chat; segredos ficam somente no cofre do provedor escolhido.

## Por que só configurar variáveis não basta
`backend/app/main.py` valida a configuração e depois **recusa iniciar**, porque ainda não existem
os adaptadores reais de **identidade** (verificação de sessão e emissão de cookie), **storage privado
durável** e **cofre de certificados**. Preencher `.env` não muda isso; é preciso implementar e conectar
esses adaptadores (etapa 3). O adaptador fiscal HTTP também continua bloqueado (etapa 5).

O **Preview do frontend é só demonstração** (dados fictícios, aviso "Demonstração — sem emissão fiscal").
`VITE_NFSE_API_URL` só deve ser definido depois que o serviço fiscal real estiver acessível e aprovado
nas etapas 3–4. Antes disso, apontá-lo para qualquer endereço só gera erro de acesso.

## Verificação rápida (somente leitura)
```
python3 scripts/preflight.py          # texto
python3 scripts/preflight.py --json   # máquina
```
Não importa `app.main`, não acessa rede/banco/cofre, não imprime valores. Exit 0 só quando tudo
estiver `ok`; hoje sai com **1**. `presente_nao_validado` = variável existe, **não** que o provedor funciona.
`APP_ENV=test`/`demo` é recusado: memória/demo nunca contam como prontidão.

## Etapas

| # | Etapa | Responsável | Evidência de conclusão |
|---|---|---|---|
| 1 | **Demonstração.** Percorrer no Preview: nova NFS-e, importação CSV/XLSX, revisão, histórico, resultado desconhecido (só "verificar situação"), troca de empresa. | Usuário | Observações anotadas; nenhuma ação apresentada como emissão oficial |
| 2 | **Inventário de infraestrutura (sem segredos).** Responder o checklist abaixo; escolher onde roda o serviço Python (decisão 2026-11-02: computador principal do escritório; hospedagem externa adiada — ver sdd/design-addendum-002), PostgreSQL (local ou gerenciado), provedor de identidade, storage privado e cofre. | Usuário decide; implementador registra | Respostas do checklist; decisão registrada no DESIGN |
| 3 | **Adaptadores reais.** Implementar `IdentityVerifier` (iss/aud/exp/assinatura), `Storage` privado durável e `Vault` para o provedor escolhido; conectar em `app.main`; testes de contrato. | Implementador | `preflight` mostra os três como `presente_nao_validado`; testes passam; `app.main` inicia só com eles |
| 4 | **Banco.** Aplicar `backend/db/001_initial.sql` e `002_isolation.sql` num banco de homologação dedicado; papéis separados para API (`nfse_api`) e worker, sem superusuário. **Nunca** rodar `tests/test_pg.py`, `scripts/pg_ephemeral.sh` ou qualquer reset de schema contra banco real (os guardas já recusam). | Implementador; usuário provê o banco | Registro das migrações aplicadas e das permissões por papel |
| 5 | **Contrato oficial.** Capturar o OpenAPI oficial (hoje 403/503) com URL, data e SHA-256; confirmar envelope HTTP e algoritmo de assinatura em fonte oficial vigente; tratar o defeito de série do XSD de produção com a fonte oficial. | Implementador (pesquisa); usuário pode abrir canal com o suporte oficial | `docs/nfse-integration-evidence.md` atualizado; perfil cripto aprovado com fonte; adaptador HTTP implementado contra o contrato |
| 6 | **Certificado e parâmetros fiscais.** Certificado autorizado guardado só no cofre (referência em `CERTIFICATE_REFERENCE`); responsável fiscal cadastra para cada empresa/operação: município, série, regime, códigos de tributação. Nada inferido. | Usuário/responsável fiscal | Referência do cofre existe; parâmetros revisados por responsável |
| 7 | **Smoke em produção restrita.** `python3 scripts/verify.py --mode restricted`: emissão válida, rejeição de negócio, resultado desconhecido seguido de consulta pela DPS (sem reenvio), isolamento entre empresas, sem duplicidade; XML/DANFSe somente se o contrato oficial suportar. | Implementador executa; usuário acompanha | Saída do smoke e evidências anexadas ao BUILD_REPORT |
| 8 | **Produção.** Só depois de revisar as evidências das etapas 1–7, corrigir o XSD/perfil de produção e cumprir o Verify Gate do DEFINE. | Usuário aprova | Aprovação registrada; nada é ativado automaticamente |

## Checklist para responder (somente sim/não ou nome do provedor — nunca credenciais)
- [x] Onde roda o serviço Python? **Decidido: computador principal Windows do escritório** (hospedagem externa só na fase de clientes online).
- [ ] Há PostgreSQL gerenciado disponível para homologação, separado de produção? Qual?
- [ ] Qual provedor de identidade será usado para login dos usuários (Cliente/Escritório)?
- [ ] Qual storage privado guardará XML/documentos?
- [ ] Qual cofre guardará o certificado? Quem tem acesso administrativo?
- [ ] Existe certificado autorizado para produção restrita? (sim/não — não enviar o arquivo)
- [ ] Quem é o responsável fiscal que cadastra os parâmetros de Bariri/SP e Pederneiras/SP?
- [ ] Há contato com o suporte oficial da NFS-e Nacional para obter o contrato da API?

## Bloqueios atuais (saída real do preflight, 2026-10-31, ambiente vazio)
Ver `BUILD_REPORT.md`, incremento 6. Resumo: configuração ausente; identidade, storage, cofre e
parâmetros fiscais duráveis ausentes; adaptador HTTP oficial, perfil criptográfico aprovado, XSD de
produção (série) e smoke em produção restrita bloqueados.

## Adendo 2026-11-02 — certificado A1 do escritório e procuração

**Situação: BLOQUEADO.** Ver `sdd/design-addendum-001-delegacao-a1.md`.

- **Quem emite:** a empresa cliente (CNPJ do prestador na DPS). **Quem assina:** o escritório, com o próprio certificado A1.
- **Certificado:** o usuário confirmou que é A1 (.pfx/.p12). Ele nunca é enviado pelo chat nem colocado no repositório.
- **Procuração:** o usuário informou que o Emissor WEB mostra a representação (cliente piloto L'OR BLANC GESTORA DE BENS LTDA,
  CNPJ 14.168.985/0001-73; escritório CNPJ 27.532.638/0001-20; recibo de 2026-11-02). Status: **declaração do usuário,
  não verificada por API**. A tela não comprova acesso pela API, ambiente de produção restrita, datas nem escopo.
- **API com procuração:** NÃO TESTADA (documentação OpenAPI oficial respondeu 403 em 2026-11-02).

### Como conferir o certificado no seu próprio computador (opcional, somente leitura)
1. Tenha Python 3 e o pacote `cryptography` instalados (`python3 -m pip install "cryptography>=50,<51"`).
2. Na pasta do projeto, rode: `python3 scripts/inspecionar_certificado.py CAMINHO/DO/certificado.pfx`
3. Digite a senha quando for pedida (ela não aparece na tela). Não coloque a senha no comando.
4. O resultado mostra só estrutura, validade e o CNPJ mascarado. Ele sempre termina em **NÃO PRONTO**, porque não verifica
   cadeia ICP-Brasil, revogação, procuração no governo nem API.
5. Não envie o arquivo, a senha nem a saída completa para ninguém pelo chat. O programa não usa internet e não grava arquivos.

### O que ainda falta para usar a procuração na emissão
- Provedor confiável de **consulta de autorização** (contrato oficial da API de representação ainda não capturado).
- Verificação de **cadeia ICP-Brasil e revogação** no ambiente real.
- **Cofre** para guardar o A1 e a senha, identidade, storage, hospedagem e contrato HTTP/algoritmo de assinatura (etapas 3–5).
- Parâmetros fiscais explícitos do cliente piloto (etapa 6) e smoke em produção restrita com representação (etapa 7).

## Adendo 2026-11-02 — implantação local no escritório
Hospedagem externa deixou de ser obrigatória: a implantação atual é local (ver `sdd/design-addendum-002-escritorio-local.md` e `docs/instalacao-escritorio-windows.md`). As etapas 3–8 continuam necessárias, executadas no computador principal. Acesso em rede local segue bloqueado até login real e TLS; clientes online exigirão hospedagem e autenticação em fase própria.
