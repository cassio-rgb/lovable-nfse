# BUILD REPORT: NFS-e Nacional para Gestoras de Imóveis

| Atributo | Valor |
|---|---|
| Data | 2026-10-31 (incremento 6: guia de ativação e preflight somente leitura) |
| Base | DEFINE v0.9, DESIGN v0.9 (Draft) — execução default/sequencial autorizada |
| Status | **BLOQUEADO / Build parcial — SDD NÃO completo**. Faltam identidade/storage/cofre/infra reais, contrato HTTP e perfil cripto oficiais, smoke em homologação e Verify Gate do DEFINE |

## Arquitetura
Frontend Lovable (TanStack Start) + serviço fiscal Python/FastAPI em `backend/` com PostgreSQL. Runtime e hospedagem do serviço são separados e **não provisionados**. Sem `VITE_NFSE_API_URL`, o app abre em demonstração explícita.

## Incremento 3 — entregue
1. **Contrato de persistência** `Tx` (`backend/app/repository.py`): todos os serviços (rascunhos, revisão, importação, emissão, worker, API) usam `with repo.tx() as t`. `MemoryRepository` (`durable=False`) fica só para testes.
2. **PostgreSQL durável** (`backend/app/pg.py`): `PostgresRepository`, `PgMemberships`, `PgCompanies`, `PgReleases`, com SQL parametrizado (psycopg 3) e uma transação por operação. Esquema normalizado reescrito: ids uuid, `timestamptz`, FKs compostas `(company_id, id)`, FK diferida draft→emission, `UNIQUE` de idempotência, versão e origem de importação, `dps_sequence` por UPSERT atômico, job com `fence`, RLS por `app.user_id` (`nfse_api`), políticas do worker, `GRANT USAGE` no schema e trigger de imutabilidade.
3. **Concorrência:** confirmação trava a linha do rascunho (`FOR UPDATE`). Corrida de unicidade → `UniqueRace` → repete e devolve a operação existente. Importação concorrente decidida por `ON CONFLICT DO NOTHING`.
4. **Worker:** claim com `FOR UPDATE SKIP LOCKED`, lease e fencing token. Tentativa registrada antes da chamada externa; nenhuma transação aberta durante HTTP. Lease perdido → `consultar` + `resultado_desconhecido`. Worker antigo → `stale`, não sobrescreve.
5. **Importação no modo API:** a prévia vem de `POST /importacoes/analisar` (`previaDaApi`). A demonstração continua local. O servidor reclassifica na confirmação.
6. **`scripts/verify.py`:** modos `local` / `postgres` / `restricted`. Qualquer check FAIL ou NOT RUN dá exit 1. `scripts/pg_ephemeral.sh` sobe e derruba um PostgreSQL local temporário.
7. `__pycache__`/`.pyc` removidos e ignorados no `.gitignore`. `app/main.py` instancia as classes PostgreSQL e recusa iniciar por falta de identidade, storage e cofre.

## Incremento 6 — preparação para homologação (baseline 078dd4f)
Arquivos: `docs/ativacao-homologacao.md` (etapas 1–8, responsáveis, evidências, checklist sem segredos), `scripts/preflight.py` (somente leitura, stdlib, `--json`, exit 1 se não pronto), `backend/tests/test_preflight.py` (4 testes: sem vazamento de valores/URLs, presença ≠ validação, test/demo recusados, produção recusada), `scripts/verify.py` (inclui test_preflight). `python3 scripts/verify.py --mode local` → exit 0: 87 testes Python (0 skip), vitest 16/16, typecheck, build, e2e PASS. Status geral: **BLOQUEADO**. Serviço fiscal inalterado: `app.main` continua recusando iniciar; adaptador HTTP continua bloqueado.

Comando: `env -i PATH="$PATH" python3 scripts/preflight.py`
```
[ausente               ] config/APP_ENV: obrigatória
[ausente               ] config/NFSE_ENVIRONMENT: obrigatória
[ok                    ] config/NFSE_PRODUCTION_ENABLED: desabilitada
[ausente               ] config/IDENTITY_ISSUER: emissor do provedor de identidade
[ausente               ] config/IDENTITY_AUDIENCE: audiência esperada nos tokens
[ausente               ] config/DATABASE_URL: papel nfse_api, nunca superusuário
[ausente               ] config/WORKER_DATABASE_URL: papel do worker separado do API
[ausente               ] config/CERTIFICATE_REFERENCE: referência no cofre, nunca o arquivo
[ausente               ] config/CORS_ORIGINS: origens permitidas do frontend
[ausente               ] adaptadores/verificador_identidade: não implementado/conectado; app.main recusa iniciar
[ausente               ] adaptadores/storage_privado_duravel: não implementado/conectado; app.main recusa iniciar
[ausente               ] adaptadores/cofre_certificados: não implementado/conectado; app.main recusa iniciar
[ausente               ] adaptadores/parametros_fiscais_duraveis: cadastro explícito por empresa/operação não implementado
[bloqueado             ] adaptadores/adaptador_http_oficial: contrato HTTP oficial não capturado; submit/lookup falham fechados
[bloqueado             ] adaptadores/perfil_cripto_aprovado: nenhum perfil com fonte oficial vigente
[bloqueado             ] adaptadores/xsd_producao_serie: TSSerieDPS do XSD de produção v1.01 não aceita série real
[bloqueado             ] adaptadores/smoke_producao_restrita: não executado; depende de todos os itens acima e de certificado autorizado

RESULTADO: NÃO PRONTO (BLOQUEADO) — preflight não valida provedores nem transmite.
exit=1
```

## Incremento 5b — correções da revisão independente (3f48422)
1. Tipo de inscrição no Id: CNPJ = `2` (regra oficial E0004, anexo I linha 151), validado contra o texto do anexo vendorizado como fixture.
2. Parser: somente UTF-8 estrito, mais recusa pós-parse de DTD/entidades. Casos hostis UTF-16/UTF-32 (LE/BE/BOM) e defesa pós-parse testada com a varredura textual desativada.
3. C14N de subárvore corrigida (cópia destacada; defeito do libxml2 2.14.6). Verificação independente com xmlsec1 1.3.7 obrigatória em `verify.py --mode local` (resolvida via PATH, `XMLSEC1` ou `nix build nixpkgs#xmlsec`; ausente = FAIL). signxml 5.2.0 incompatível neste libxml2; não usado. Dependências fixadas: `lxml>=6.0,<6.2` (testado 6.0.2 e 6.1.3), `cryptography>=50,<51` (50.0.2).
4. `verificar` aplica tpAmb/Id além do XSD; `numero_reservado` exige o prefixo exato da empresa/ambiente.

| Comando | Exit | Resultado |
|---|---|---|
| `python3 scripts/verify.py --mode local` | 0 | python-unit+api **83 pass, 0 skip** (contract 33, interop 2 via xmlsec1); vitest **16/16**; typecheck, build, e2e PASS |
| `pg_ephemeral.sh start` + `verify.py --mode postgres` + `stop` | 0 | **9/9 PASS** |

## Incremento 5 — XML fiscal offline (baseline 84a67ca)
Entregue: XSD oficiais vendorizados com manifest/hashes; parser seguro; `EntradaDPS`/`ParametrosFiscais` tipados; builder determinístico validado por XSD por perfil; Id oficial a partir do número persistido; XMLDSIG com verificação anti-wrapping e perfis versionados não aprovados; allowlist exata de URL/transporte endurecido; `offline.preparar` ligado ao snapshot imutável sem mudar estado; CNPJ/CPF com letras recusado (Python + TS). Detalhes e achados (incluindo o defeito da série no XSD de produção) em `docs/nfse-integration-evidence.md`.

Arquivos: `backend/app/nfse/{secure_xml,dps,signing,client,offline,xml}.py`, `backend/app/nfse/schemas/**` (+`MANIFEST.json`), `backend/app/ports.py` (`FiscalParameters`), `backend/app/repository.py` (`numero_reservado`), `backend/app/domain/models.py`, `src/lib/domain.ts`, `backend/tests/test_contract.py` (reescrito, 27 testes, sem skip de XSD), `src/test/domain.test.ts`, `backend/pyproject.toml`, `scripts/verify.py`, `docs/nfse-integration-evidence.md`, `AGENTS.md`.

| Comando | Exit | Resultado |
|---|---|---|
| `pip install lxml cryptography` | 0 | lxml 6.0.2, cryptography 50.0.2 |
| `curl` OpenAPI restrita/produção (1 tentativa) | — | 403 / 403 → envelope HTTP pendente |
| `python3 -m unittest tests.test_contract` | 0 | **27/27 pass, 0 skip** |
| `python3 scripts/verify.py --mode local` | 0 | python-unit+api **75 pass, 0 skip**; vitest **16/16**; typecheck, build, e2e PASS |
| `scripts/pg_ephemeral.sh start` + `verify.py --mode postgres` + `stop` | 0 | **9/9 PASS** |
| `verify.py --mode restricted` | não executado | sem credenciais; nenhuma DPS transmitida |

## Verificações executadas (incremento 4 — guardas dos helpers de teste)
Mudanças: `scripts/pg_ephemeral.sh` só aceita `/tmp/nfse-pg-test[-sufixo]` canônico (recusa `/`, `/tmp`, symlink, relativo, fora de `/tmp`), cria marcador `.nfse-pg-test-owner` e recusa diretório preexistente sem ele antes de qualquer `rm`; dados em `<dir>/data`. Não edita mais /etc/passwd ou /etc/group: como root usa `PG_EPHEMERAL_USER` existente (padrão `nobody`) ou sai com exit 2. `backend/tests/pg_guard.py` exige dbname `nfse_test`/`nfse_test_<sufixo>`, host unix socket/loopback e `NFSE_PG_ALLOW_SCHEMA_RESET=nfse_test_reset_public`, checados antes de importar psycopg/conectar. `backend/tests/test_guards.py` (9 testes) cobre os guardas sem conexão nem `rm` perigoso; incluído no modo local.

| Comando | Exit | Resultado |
|---|---|---|
| `python3 scripts/verify.py --mode local` | 0 | python-unit+api PASS (**51 testes: 50 pass, 1 skip** XSD), vitest 15/15, typecheck, build, e2e PASS |
| `PG_EPHEMERAL_USER=pgtest scripts/pg_ephemeral.sh start` + `TEST_DATABASE_URL=… NFSE_PG_ALLOW_SCHEMA_RESET=nfse_test_reset_public python3 scripts/verify.py --mode postgres` | 0 | **9/9 PASS** (banco efêmero; `pgtest` já existia no ambiente, não foi criado) |
| mesmo URL sem a flag | ≠0 | `UnsafeTestDatabase` antes de conectar |
| dbname `protest` com flag | ≠0 | `UnsafeTestDatabase` antes de conectar |
| `python3 scripts/verify.py --mode postgres` sem URL | 1 | NOT RUN, declarado |
| `scripts/pg_ephemeral.sh stop` | 0 | diretório removido |

Verify Gate do DEFINE e smoke oficial continuam pendentes; SDD não completo.

## Verificações executadas (incremento 3)
| Comando | Exit | Resultado |
|---|---|---|
| `python -m pip install "psycopg[binary]"` | 0 | psycopg 3.3.6 |
| `python3 scripts/verify.py --mode local` | 0 | python-unit+api PASS (**42 testes: 41 pass, 1 skip** XSD oficial), vitest PASS (**15/15**), typecheck PASS, build PASS, e2e PASS |
| `TEST_DATABASE_URL=$(scripts/pg_ephemeral.sh start) python3 scripts/verify.py --mode postgres` | 0 | **9/9 PASS** no PostgreSQL 17.9 efêmero |
| `python3 scripts/verify.py --mode postgres` sem URL | 1 | NOT RUN, declarado |
| `python3 scripts/verify.py --mode restricted` | 1 | NOT RUN (sem credenciais oficiais) |

Os testes PostgreSQL cobrem:
- dados persistem entre instâncias do repositório;
- invalidação da revisão;
- 8 confirmações concorrentes → 1 emissão e 1 job;
- 6 reservas de DPS concorrentes → identidades únicas;
- mesma chave com outro conteúdo → conflito;
- 5 importações concorrentes → 1 rascunho;
- worker com `SKIP LOCKED`, fencing e recuperação por consulta (0 novos POSTs, 1 tentativa);
- trigger de imutabilidade;
- RLS (`nfse_api` só vê a própria empresa e nada sem `app.user_id`);
- API completa sobre PostgreSQL (sessão, idempotência, uuid malformado → 404/[], empresa cruzada, revogação).

## Mapa do manifest → caminhos reais
| # | Manifest | Real |
|---|---|---|
| 1–12 | web/* | package.json, src/lib/{contracts,domain,imports,import-file,datasource,confirm}.ts, src/components/*, src/routes/*, src/styles.css |
| 18–19 | backend/db/*.sql | idem (reescritos) |
| 20 | backend/app/repository.py | repository.py (contrato + memória de teste) **+ app/pg.py** (durável) |
| 13–36 | demais backend/** | idem (+ app/main.py, tests/helpers.py, tests/test_api.py, **tests/test_pg.py**) |
| 37–38 | tests/e2e/*.spec.ts | tests/e2e/nfse_flow.py |
| 39–41 | scripts/verify.py, deploy/* | idem (+ **scripts/pg_ephemeral.sh**) |
| 42–47 | config, docs, CI | idem |

## Pendências reais
1. **Verify Gate do DEFINE:** candidato `scripts/verify.py --mode local` + `--mode postgres`; o DEFINE não foi editado.
2. **Smoke oficial** AT-007/009/010/013 e spike; adaptador `nfse/client.py` bloqueado (envelope HTTP e perfil cripto não confirmados; OpenAPI 403). DPS offline implementada para produção restrita; produção bloqueada pelo defeito de série no XSD v1.01. `dps_identity` interna persiste o nDPS; o Id oficial é derivado.
3. **Infraestrutura:** provedor de identidade (verificador e cookie), storage privado durável, cofre, hospedagem, processo do worker (loop/agendamento), pool de conexões, banco gerenciado. CI (`.github/workflows/verify.yml`) não executado nem atualizado para o modo postgres.
4. Liberações e pilotos, governança G01–G14, retenção e backup.
5. `sdd/`: textos integrais das especificações ainda não colados.

## Incremento 2026-11-02 — prontidão do certificado A1 delegado (baseline 6159b1f)
**Status geral: BLOQUEADO.** Nada transmitido, publicado ou provisionado; `main.py` e `submit/lookup` continuam fail-closed.

Arquivos: `backend/app/nfse/certificado.py` (novo), `backend/app/nfse/delegacao.py` (novo), `backend/app/nfse/offline.py`
(parâmetro `contexto`), `scripts/inspecionar_certificado.py` (novo), `backend/tests/test_certificado.py` (novo, 15 testes),
`scripts/verify.py` (inclui `tests.test_certificado`), `sdd/design-addendum-001-delegacao-a1.md` (novo),
`docs/ativacao-homologacao.md`, `docs/nfse-integration-evidence.md`.

Comandos executados:
- `curl` OpenAPI oficial (1 tentativa): produção restrita 403, produção 403.
- `APP_ENV=test python -m unittest tests.test_certificado` → 15/15 OK.
- `XMLSEC1=…/xmlsec-1.3.7/bin/xmlsec1 APP_ENV=test python -m unittest <PY_LOCAL + test_certificado>` → **102 testes OK, 0 skips**
  (cryptography 50.0.2, lxml 6.0.2).
- `python scripts/preflight.py` → exit 1 (BLOQUEADO, esperado).
- Frontend não alterado: Vitest/typecheck/build/E2E não reexecutados nesta etapa. PostgreSQL não reexecutado (sem mudança de storage).

Cobertos: senha errada, expirado, ainda não válido, sem chave, EC e RSA 1024, CNPJ ambíguo, certificado ambíguo, tamanho,
DER estrito, CN não usado, provedor ausente/revogado/inexistente/outra empresa/outro outorgado/ambiente/serviço/expirado/
desatualizado, recibo WEB ≠ autorização, provedor sintético fora de teste, DPS mantém emitente cliente, reuso entre empresas,
sem vazamento em repr/pickle/CLI (senha, CNPJ, serial, caminho), CLI sem escrita e sem senha por argumento.

Bloqueios restantes: provedor oficial de autorização (representação) via API; cadeia ICP/revogação; cofre do A1; identidade;
storage privado; hospedagem/gateway; contrato HTTP e algoritmo oficiais; parâmetros fiscais do piloto; smoke em produção restrita;
Verify Gate do DEFINE.

## Incremento 2026-11-02b — inicialização LOCAL no escritório (baseline 6c2d426)
Decisão do usuário registrada em `sdd/design-addendum-002-escritorio-local.md` (local, Windows, sem hospedagem externa, sem recursos gerenciais).

**Arquivos:** `vite.config.ts` (perfil opt-in `NFSE_BUILD_PROFILE=local-node` → Nitro `node-server`, saída `.output-local/`), `scripts/escritorio.py`, `scripts/escritorio.cmd`, `backend/tests/test_escritorio.py`, `scripts/verify.py` (inclui o teste), `docs/instalacao-escritorio-windows.md`, `docs/ativacao-homologacao.md`, `AGENTS.md`, `.gitignore`, `sdd/design-addendum-002-escritorio-local.md`.

**Framework:** @lovable.dev/vite-tanstack-config 2.26.5, @tanstack/react-start 1.168.60, nitro 3.0.260603-beta, vite 8.1.5. O wrapper força `cloudflare-module` quando detecta sandbox (`LOVABLE_SANDBOX`/`DEV_SERVER__PROJECT_PATH`); o lançador remove essas variáveis apenas no processo de build local.

**Verificações executadas (Linux sandbox, Node 22.23, Python 3.13):**
| Check | Resultado |
|---|---|
| `python3 scripts/escritorio.py construir --modo demo` | exit 0; `.output-local/nitro.json` preset `node-server` |
| `python3 scripts/escritorio.py iniciar` | exit 0; HTTP 200 em http://127.0.0.1:4517/ (artefato `node server/index.mjs`, não Vite dev/preview) |
| Playwright no artefato | aviso "Demonstração — sem emissão fiscal" visível (1) |
| segundo `iniciar` | exit 3, recusado (já rodando) |
| porta ocupada por outro processo | exit 3, "Nada foi encerrado"; processo alheio intacto |
| `parar` / `estado` | exit 0 / exit 1 "Parado."; HTTP sem resposta depois |
| `construir --modo api` sem prontidão | exit 3, explicação em português; nada construído |
| `npx vite build` padrão | exit 0, preset `cloudflare-module` (Preview Lovable inalterado) |
| `python3 -m unittest tests.test_escritorio` | 12/12 OK |
| Regressão Python (11 módulos locais) | 114 executados, 108 OK, 6 skips ambientais (4 guardas que exigem usuário/PG, 2 interop sem binário `xmlsec1` neste sandbox reiniciado) |
| Vitest | 16/16 |
| `python3 scripts/preflight.py` | NÃO PRONTO (BLOQUEADO), como esperado |

**Limitações de SO:** nada executado em Windows. `escritorio.cmd`, `tasklist`/`taskkill /PID` e `CREATE_NEW_PROCESS_GROUP` não testados. No Linux, logo após `parar` a porta pode ficar em TIME_WAIT e ser recusada por alguns segundos (falha segura).

**Status global: BLOQUEADO.** LAN bloqueada (sem login real/TLS); `app.main`, submit/lookup fail-closed; faltam identidade, storage durável, cofre A1, contrato HTTP/algoritmo oficial, parâmetros fiscais do piloto, smoke restrito e Verify Gate do DEFINE.

## Incremento 2026-11-02c — correções da revisão do lançador local (888b3a9)
- **Instalação:** repositório só rastreia `bun.lock` (sem `package-lock.json`). Guia passa a usar `bun install --frozen-lockfile`. Executado em diretório limpo (`git archive HEAD` → `/tmp/fresh`, Bun 1.4.4, Linux): exit 0, 526 pacotes. Não executado em Windows.
- **Propriedade do processo:** estado grava `identidade` = executável + linha de comando + horário de criação (Linux `/proc/<pid>/exe|cmdline|stat`; Windows `Get-CimInstance Win32_Process`, somente leitura). `parar` reconsulta imediatamente antes; diferença, PID inexistente ou consulta indisponível ⇒ não encerra (falha de consulta ⇒ recusa e mantém registro). Estado com forma exata (PID int > 0, não bool; porta; host loopback; modo demo/api; identidade com 3 campos); inválido ⇒ recusa. `nonce` removido. Windows encerra só `taskkill /PID <verificado> /F` (sem `/T`, sem nome/porta).
- **Versões:** engines instalados: vite 8.1.5 e nitro `^20.19.0 || >=22.12.0`, @tanstack/react-start `>=22.12.0` ⇒ mínimo Node 22.12 (recomendado 22/24 LTS), Python 3.12; exigidos em `construir` e `iniciar`.
- **Ambiente:** execução descarta `HOST`, `PORT` e todo `NITRO_*` herdados antes de definir loopback; manifesto do build exige `modo` ∈ {demo, api} e `perfil=local-node`, senão recusa.
- **Testes:** `python3 -m unittest tests.test_escritorio` 24/24 OK (Windows CIM simulado: ok/inexistente/falhas; PID reusado por outro node; criação diferente; consulta falhou; 9 estados inválidos; dono normal; env; manifesto; versão), nenhum kill real nos unitários; `tests.test_preflight` OK. Ciclo real Linux `iniciar`/`estado`/`parar` exit 0/0/0, depois `estado` exit 1. Sem rebuild completo.
- **Status global:** BLOQUEADO. Apenas demo/loopback; LAN e emissão fiscal bloqueadas; nada verificado em Windows.

## Incremento 2026-11-02d — consistência de mensagens do lançador (só texto)
- `scripts/escritorio.py`: erro de Node ausente em `node_exe()` passou a dizer "Node.js 22.12 ou superior (24 é aceito…)"; `verificar` e `construir` com dependências ausentes agora indicam exatamente `bun install --frozen-lockfile`. Nenhuma menção a `npm ci` nem a "Node 20 LTS" resta no lançador (a doc continua explicando para não usar `npm ci`).
- Sem mudança de comportamento, sem rebuild, sem testes novos. `python3 -m unittest tests.test_escritorio` 24/24 OK.
- **Status global:** inalterado — BLOQUEADO.
