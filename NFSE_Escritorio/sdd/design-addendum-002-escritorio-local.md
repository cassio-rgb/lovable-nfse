# Design Addendum 002 — Implantação local no escritório (2026-11-02)

**Origem:** decisão do usuário (Cassio Aguiar Filho, Atual Assessoria) em 2026-11-02, baseline 6c2d426.
Os documentos originais (Brainstorm/Define/Design) permanecem históricos e não foram reescritos.

## Decisão do usuário
- Agora: somente colaboradores do escritório, em computadores do escritório. Clientes online: fase futura separada.
- Emissão SIMPLES; não construir sistema gerencial de controle de emissões.
- Sem hospedagem externa. Computador principal: Windows 10/11.

## Consequências de arquitetura
| Item | Antes (DESIGN) | Agora |
|---|---|---|
| Hospedagem | serviço Python em container + PostgreSQL gerenciado (pendente) | frontend (Node) e serviço Python rodam no computador principal do escritório; hospedagem externa adiada |
| Frontend | build Cloudflare do Lovable | build Cloudflare continua padrão do Preview; perfil opt-in `NFSE_BUILD_PROFILE=local-node` gera `.output-local/` (Nitro `node-server`) |
| Acesso | internet | somente loopback `127.0.0.1`. LAN BLOQUEADA até login real + TLS |
| Escopo | — | mantém mínimo durável: identidade da emissão, estado, resposta oficial, idempotência, revisão/confirmação, isolamento por empresa. Sem novos recursos gerenciais; nada do histórico existente é removido |
| Python/FastAPI/PostgreSQL | proposta | preservados; PostgreSQL local é uma opção futura de etapa 2 (não instalado aqui) |

Inalterados: `app.main` fail-closed (identidade/storage/cofre), submit/lookup fail-closed, perfil criptográfico não aprovado, smoke do DEFINE bloqueado. A1 fica no computador principal, fora do navegador e do repositório.

## Manifest deste adendo
| Arquivo | Função |
|---|---|
| `vite.config.ts` | perfil opt-in `local-node` (mesmo plugin Nitro, sem duplicar) |
| `scripts/escritorio.py` | lançador: verificar/construir/iniciar/estado/parar; loopback, porta, PID próprio, API bloqueada |
| `scripts/escritorio.cmd` | atalho Windows (não altera política de execução) |
| `backend/tests/test_escritorio.py` | testes das guardas |
| `docs/instalacao-escritorio-windows.md` | guia simples em português |
| `.gitignore` | ignora `.output-local`, `.nfse-local` |

## Fora deste adendo (próximas fases)
Login real dos colaboradores; cofre local do A1; PostgreSQL local e backup; LAN com TLS; acesso de clientes online (exige hospedagem + autenticação).
