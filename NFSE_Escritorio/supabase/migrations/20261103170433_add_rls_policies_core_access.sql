-- RLS para tabelas centrais consultadas pela API.
-- A identidade é propagada pelo backend em app.user_id.

alter table public.membership enable row level security;
alter table public.company enable row level security;
alter table public.operation_release enable row level security;

drop policy if exists membership_self_select on public.membership;
create policy membership_self_select
on public.membership
for select
to nfse_api
using (
  user_id = current_setting('app.user_id', true)
  and revoked_at is null
);

drop policy if exists company_member_select on public.company;
create policy company_member_select
on public.company
for select
to nfse_api
using (
  exists (
    select 1
    from public.membership m
    where m.company_id = company.id
      and m.user_id = current_setting('app.user_id', true)
      and m.revoked_at is null
  )
);

drop policy if exists operation_release_member_select on public.operation_release;
create policy operation_release_member_select
on public.operation_release
for select
to nfse_api
using (
  exists (
    select 1
    from public.membership m
    where m.company_id = operation_release.company_id
      and m.user_id = current_setting('app.user_id', true)
      and m.revoked_at is null
  )
);
