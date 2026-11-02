<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

## Project rules
- Fiscal logic lives in the separate Python service under `backend/` (FastAPI + PostgreSQL); never reimplement it as TypeScript server functions — architecture fixed by DESIGN Decision 1/2.
- Frontend talks to the fiscal service only via `src/lib/datasource.ts` (`VITE_NFSE_API_URL`); without it, the explicit demo source runs with fictitious data only.
- Domain rules (money as integer cents/Decimal, review hash/version, no resend on unknown result) are mirrored in `src/lib/domain.ts` and `backend/app/domain/`; change both and their tests together.
- Fiscal services access storage only through the `Tx` contract in `backend/app/repository.py` (`with repo.tx() as t`); `MemoryRepository` is test-only and `app/pg.py` is the durable implementation — keep both in sync and covered by `tests/test_api.py` and `tests/test_pg.py`.
- Worker writes are fenced by `job.fence`; never hold a DB transaction across an external fiscal HTTP call.
- Official XSDs are vendored unmodified under `backend/app/nfse/schemas/` and loaded only via `secure_xml.load_schema` (manifest hash check, no network/DTD); never edit them to make XML pass — record defects in `docs/nfse-integration-evidence.md`.
- Crypto profiles in `backend/app/nfse/signing.py` keep "can sign" separate from "approved"; only an officially sourced profile may set `permite_transmissao`, and the live adapter stays fail-closed until the HTTP contract is captured.
- Delegated signing (office A1 for a client emitter) requires `delegacao.contexto_assinatura` with a trusted authorization provider; WEB receipts/config never authorize, and the DPS emitter stays the client — prevents silent identity substitution.
- Office-local deployment uses the opt-in `NFSE_BUILD_PROFILE=local-node` Nitro preset driven by `scripts/escritorio.py`; the default build stays Cloudflare for the Lovable preview, and the launcher binds loopback only (LAN blocked until real auth + TLS) — see sdd/design-addendum-002.
