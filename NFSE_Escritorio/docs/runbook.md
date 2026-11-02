# Runbook — serviço fiscal

**Hospedagem e runtime são separados do Lovable e não estão provisionados.** `uvicorn app.main:app` recusa iniciar até que identidade, storage privado e cofre estejam conectados.

## Verificação
| Objetivo | Comando | Requisitos |
|---|---|---|
| Local completo | `python scripts/verify.py --mode local` | Python com fastapi, httpx, python-multipart, openpyxl, playwright; bun; preview em :8080 |
| PostgreSQL | `export TEST_DATABASE_URL=$(scripts/pg_ephemeral.sh start)` → `NFSE_PG_ALLOW_SCHEMA_RESET=nfse_test_reset_public python scripts/verify.py --mode postgres` → `scripts/pg_ephemeral.sh stop` | initdb/pg_ctl/psql locais; dbname exato `nfse_test` ou `nfse_test_<sufixo>`, host unix socket/loopback, flag de reset com valor exato (os testes recriam `public`). Diretório só `/tmp/nfse-pg-test[-sufixo]` com marcador de ownership; como root usa usuário não privilegiado existente (`PG_EPHEMERAL_USER`, padrão `nobody`) ou falha — nunca edita /etc/passwd |
| Smoke oficial | `python scripts/verify.py --mode restricted` | Credenciais e liberações reais; hoje sempre falha (adaptador bloqueado) |

Cada modo termina com exit 1 se algum check ficar como FAIL ou NOT RUN.

## Banco
- Migrações: `backend/db/001_initial.sql`, depois `002_isolation.sql` (roles `nfse_api`/`nfse_worker`, RLS, trigger de imutabilidade).
- A API deve conectar com um login membro de `nfse_api` (nunca dono das tabelas nem superusuário); o RLS usa `app.user_id`, definido por transação.
- O worker usa `nfse_worker`. Pool de conexões ainda não existe: uma conexão por transação.

## Resultado desconhecido
1. Não reenviar. Localizar a operação pelo código de atendimento e pela identidade DPS.
2. O job `consultar` faz as consultas; esgotadas as tentativas, permanece desconhecido e vai para o responsável técnico.
3. Consulta manual no portal oficial pela DPS; registrar evidência antes de qualquer ação.

## Job travado / lease expirado
`worker.claim` incrementa `job.fence`. Se `tentativas > 0`, converte em `consultar` e marca a emissão como `resultado_desconhecido`. O worker antigo recebe `stale` e não grava resultado.

## Credencial/certificado indisponível
Envio bloqueado. XML/assinatura só offline (`backend/app/nfse/offline.py`, testes em `tests/test_contract.py`); artefato nunca é NFS-e. Cofre não conectado; nunca enviar certificado por chat ou e-mail.

## Revogação de acesso
`UPDATE membership SET revoked_at = now() ...` (ou `PgMemberships.revoke`). A próxima requisição recebe 404 genérico.

## Restauração
Política de backup e retenção pendente de decisão de governança.
