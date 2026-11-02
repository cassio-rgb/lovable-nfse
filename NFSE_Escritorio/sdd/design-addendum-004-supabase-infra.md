# Design Addendum 004 — Supabase/Vercel para infraestrutura de homologação

**Data:** 2026-11-02  
**Feature:** NFS-e Nacional para Gestoras de Imóveis  
**Status:** Aprovado para implementação incremental em homologação

## Decisão

Concretizar os provedores que estavam pendentes no Design original:

- Frontend: Vercel, a partir do repositório GitHub `cassio-rgb/lovable-nfse`.
- Identidade: Supabase Auth.
- PostgreSQL: Supabase Postgres, projeto dedicado de homologação.
- Storage privado: Supabase Storage, bucket privado `nfse-documentos`.
- Backend fiscal: FastAPI separado do frontend; publicação somente após os adaptadores reais exigidos pelo preflight.
- Ambiente fiscal: `producao_restrita`; produção continua desabilitada.

## Identidade e sessão

O frontend autentica o usuário no Supabase Auth. O access token JWT é enviado ao backend somente para criação/renovação da sessão do serviço fiscal.

O backend:

1. valida assinatura pelo JWKS oficial do issuer Supabase;
2. valida `iss`, `aud`, `exp` e `sub`;
3. exige `role=authenticated` e rejeita sessão anônima;
4. lê o papel de aplicação somente de `app_metadata.papel`;
5. nunca usa `user_metadata` para autorização;
6. grava o JWT validado em cookie `session` com `HttpOnly`, `Secure` e `SameSite=None`;
7. continua revalidando `membership` por empresa em cada operação.

Issuer esperado: `https://<project-ref>.supabase.co/auth/v1`.  
Audience inicial: `authenticated`.

A URL JWKS é derivada do issuer: `<issuer>/.well-known/jwks.json`.

## Banco

Os papéis de permissão permanecem `nfse_api` e `nfse_worker`, ambos `NOLOGIN`.

Usuários de conexão separados:

- `nfse_api_login` herda `nfse_api`;
- `nfse_worker_login` herda `nfse_worker`;
- nenhum é superusuário.

`DATABASE_URL` e `WORKER_DATABASE_URL` são segredos de runtime e nunca entram no repositório.

## Storage

O bucket `nfse-documentos` permanece privado. Não haverá política pública. O navegador não recebe acesso irrestrito ao bucket; documentos fiscais serão mediados pelo backend após autorização por empresa.

A implementação do adaptador Storage é tarefa posterior deste mesmo incremento e continua bloqueando o bootstrap real até existir.

## Certificado

Nenhuma mudança nesta etapa. O A1 e sua senha não vão para GitHub, frontend nem bucket de documentos. `CERTIFICATE_REFERENCE` só será definido quando existir cofre real.

## Impacto no Design original

Este addendum apenas resolve fornecedores antes marcados como “a confirmar”. Não altera:

- revisão humana obrigatória antes da transmissão;
- isolamento multiempresa;
- idempotência;
- tratamento de resultado desconhecido;
- bloqueio de produção;
- necessidade de contrato oficial e smoke em produção restrita.

## Evidência

- Supabase Security Advisor após migrations: 0 errors, 0 warnings.
- Supabase Auth Email habilitado, auto-signup desabilitado para homologação.
- Bucket `nfse-documentos` criado como privado.
- Frontend publicado na Vercel em modo demonstração.
- Branch de implementação: `feat/supabase-infra`.

## Próxima implementação

1. `SupabaseIdentityVerifier` e ponte de sessão segura.
2. Adaptador Supabase Storage.
3. Cofre do certificado.
4. Parâmetros fiscais duráveis.
5. Contrato HTTP/assinatura e smoke restrito.

## Delta de File Manifest — Storage Supabase

A concretização do Storage usa o protocolo S3 compatível do Supabase, com credenciais próprias de Storage mantidas somente em runtime.

Arquivos afetados/adicionados:

- `backend/app/documents.py`: adicionar `SupabaseS3Storage` durável.
- `backend/app/config.py`: adicionar endpoint, região, access key, secret key e bucket.
- `backend/app/main.py`: conectar o adaptador Storage real sem remover o bloqueio do cofre.
- `backend/pyproject.toml`: adicionar cliente S3 `boto3`.
- `config/env.example`: documentar somente nomes/exemplos não sensíveis.
- `scripts/preflight.py`: verificar presença da configuração e reconhecer o adaptador.
- `backend/tests/test_storage.py`: novo teste unitário com cliente S3 falso; sem rede e sem segredo.
- `.github/workflows/verify.yml`: job focado de Storage.

As credenciais S3 não entram no GitHub, no frontend ou no banco. O bucket continua privado e sem política pública.



## Delta de File Manifest — Runtime segregado do Worker

Decisão aprovada pelo usuário em 2026-11-02 após validação real das duas conexões PostgreSQL no smoke de infraestrutura.

Objetivo: tornar efetiva em runtime a segregação já definida entre API e Worker, sem habilitar transmissão fiscal.

Arquivos afetados/adicionados:

- `backend/app/config.py`: adicionar `worker_database_url` ao `Settings` e exigir `WORKER_DATABASE_URL`.
- `backend/app/worker.py`: adicionar bootstrap explícito do repositório do worker usando somente `WORKER_DATABASE_URL`; manter o adaptador fiscal bloqueado.
- `backend/tests/test_runtime_config.py`: validar que API e Worker recebem DSNs distintos e que o bootstrap do worker usa exclusivamente o DSN do worker.
- `config/env.example`: manter a documentação dos dois DSNs separados; sem segredos.
- `scripts/preflight.py`: manter a verificação de presença de `WORKER_DATABASE_URL`; nenhuma alteração de semântica necessária nesta etapa.

Restrições:
- o Worker não pode reutilizar `DATABASE_URL`;
- nenhum fallback entre os dois DSNs;
- nenhum segredo entra no repositório;
- nenhuma chamada à API Nacional é habilitada;
- certificado A1 e cofre permanecem fora desta etapa;
- `NFSE_ENVIRONMENT=producao_restrita` e `NFSE_PRODUCTION_ENABLED=false` permanecem obrigatórios para homologação.
