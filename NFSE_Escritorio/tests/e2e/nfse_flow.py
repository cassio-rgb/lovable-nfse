import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
S=Path("/tmp/browser/flow/s");S.mkdir(parents=True,exist_ok=True)
CSV="""id_origem;tomador_documento;tomador_nome;operacao;competencia;valor;descricao
A1;529.982.247-25;Maria;locacao;11/2026;100,00;Administração nov
A2;529.982.247-25;João;locacao;11/2026;200,00;Administração nov
A3;000;Inválido;locacao;11/2026;50,00;Administração nov
A1;529.982.247-25;Maria;locacao;11/2026;100,00;Administração nov
"""
Path("/tmp/browser/flow/mix.csv").write_text(CSV)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(headless=True);c=await b.new_context(viewport={"width":1280,"height":1800});pg=await c.new_page()
    errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
    await pg.goto("http://localhost:8080/");await pg.wait_for_timeout(2500)
    await pg.screenshot(path=str(S/"1home.png"))
    await pg.get_by_role("link",name="Nova NFS-e").first.click();await pg.wait_for_timeout(800)
    await pg.fill("#doc","52998224725");await pg.fill("#nome","Maria Fictícia")
    await pg.get_by_role("button",name="Continuar").click()
    await pg.select_option("#op","locacao");await pg.fill("#comp","2026-11")
    await pg.get_by_role("button",name="Continuar").click()
    # Códigos fiscais exigem escolha humana explícita; o E2E seleciona fixtures válidas.
    await pg.get_by_role("combobox", name="Serviço nacional").select_option("010101")
    await pg.get_by_role("combobox", name="NBS").select_option("1.0101.11.00")
    await pg.get_by_role("combobox", name="CST IBS/CBS").select_option("000")
    await pg.get_by_role("combobox", name="cClassTrib").select_option("000001")
    await pg.get_by_role("combobox", name="Indicador da operação").select_option("010101")
    await pg.fill("#valor","1.250,00");await pg.fill("#desc","Taxa de administração de locação")
    await pg.screenshot(path=str(S/"2form.png"))
    await pg.get_by_role("button",name="Salvar e revisar").click();await pg.wait_for_timeout(1500)
    print("review url",pg.url)
    await pg.get_by_label("Conferi").click()
    await pg.get_by_label("Resposta perdida").check()
    await pg.screenshot(path=str(S/"3review.png"))
    await pg.get_by_role("button",name="Executar simulação de envio").click();await pg.wait_for_timeout(5000)
    await pg.screenshot(path=str(S/"4op.png"))
    print("has resend?", await pg.get_by_role("button",name="Executar simulação").count())
    await pg.get_by_role("button",name="Verificar situação (simulação)").click();await pg.wait_for_timeout(1500)
    print("after verify:", (await pg.locator("main").inner_text())[:200])
    await pg.goto("http://localhost:8080/importar");await pg.wait_for_timeout(4000)
    await pg.set_input_files("#arq","/tmp/browser/flow/mix.csv")
    await pg.get_by_role("button",name="Analisar arquivo").click();await pg.wait_for_timeout(800)
    await pg.screenshot(path=str(S/"5prev.png"))
    await pg.get_by_role("button",name="Criar 2 rascunho(s)").click();await pg.wait_for_timeout(800)
    await pg.get_by_role("button",name="Analisar arquivo").click() if False else None
    await pg.set_input_files("#arq","/tmp/browser/flow/mix.csv")
    await pg.get_by_role("button",name="Analisar arquivo").click();await pg.wait_for_timeout(800)
    print("reimport:", await pg.get_by_role("button",name="Criar 0 rascunho(s)").count())
    # dirty switch
    await pg.goto("http://localhost:8080/nova");await pg.wait_for_timeout(1200)
    await pg.fill("#doc","123")
    await pg.get_by_label("Empresa ativa").click();await pg.get_by_role("option",name="Gestora Exemplo").click();await pg.wait_for_timeout(500)
    await pg.screenshot(path=str(S/"6switch.png"))
    await pg.get_by_role("button",name="Permanecer").click()
    print("doc kept:", await pg.input_value("#doc"))
    await pg.goto("http://localhost:8080/rascunho/inexistente");await pg.wait_for_timeout(1200)
    print("denied:", await pg.get_by_text("Conteúdo indisponível").count())
    print("errors",errs)
    await b.close()
# O modo autenticado usa o mesmo contrato FastAPI e verificador JWT do produto.
# Somente provedor, chaves, vínculos e armazenamento são fixtures locais de teste.
async def authenticated(accessibility=False):
    import ipaddress
    import json
    import os
    import ssl
    import subprocess
    import sys
    import tempfile
    import threading
    import time
    import urllib.request
    from datetime import datetime, timedelta, timezone
    from types import SimpleNamespace

    import jwt
    import uvicorn
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    from playwright.async_api import expect

    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "backend"))
    from app.api import ApiSettings, Deps, create_app
    from app.auth import Company, CompanyDirectory, MembershipStore, SupabaseIdentityVerifier
    from app.documents import MemoryStorage
    from app.eligibility import ReleaseRegistry
    from app.repository import MemoryRepository

    origin, api, issuer = "http://localhost:8081", "https://localhost:8443", "https://auth.example.test/auth/v1"
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.now(timezone.utc)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost teste sintetico")])
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
        .serial_number(x509.random_serial_number()).not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=1)).add_extension(x509.SubjectAlternativeName([
            x509.DNSName("localhost"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), critical=False).sign(key, hashes.SHA256()))
    class Jwks:
        def get_signing_key_from_jwt(self, token):
            return SimpleNamespace(key=key.public_key())
    def token(user="u1", expired=False):
        return jwt.encode({"sub": user, "iss": issuer, "aud": "authenticated", "role": "authenticated",
            "is_anonymous": False, "exp": int(time.time()) + (-60 if expired else 3600),
            "app_metadata": {"papel": "escritorio" if user == "u1" else "cliente"},
            "user_metadata": {"papel": "escritorio"}}, key, algorithm="RS256")
    repo, members, companies = MemoryRepository(), MembershipStore(), CompanyDirectory()
    for cid in ("A", "B", "C"):
        companies.add(Company(cid, f"Empresa {cid} Fictícia", "11222333000181", "Bariri/SP"))
    for cid in ("A", "B"):
        members.grant("u1", cid, {"ler", "editar"})
    members.grant("u2", "B", {"ler", "editar"})
    app = create_app(Deps(ApiSettings("test", (origin,)), repo, members, companies,
        ReleaseRegistry(), MemoryStorage(), SupabaseIdentityVerifier(issuer, "authenticated", Jwks())))
    requests = []
    @app.middleware("http")
    async def trace(request, call_next):
        requests.append((request.method, request.url.path, bool(request.headers.get("authorization"))))
        return await call_next(request)

    with tempfile.TemporaryDirectory(prefix="nfse-auth-e2e-") as temp:
        folder = Path(temp)
        certfile, keyfile = folder / "tls.pem", folder / "tls.key"
        certfile.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        keyfile.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8443,
            ssl_keyfile=str(keyfile), ssl_certfile=str(certfile), log_level="error"))
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        env = {**os.environ, "VITE_NFSE_API_URL": api, "VITE_SUPABASE_URL": "https://auth.example.test",
               "VITE_SUPABASE_PUBLISHABLE_KEY": "sb_publishable_fixture_not_a_real_key"}
        with (folder / "vite.log").open("w") as log:
            frontend = subprocess.Popen(["bun", "run", "dev", "--host", "127.0.0.1", "--port", "8081"], cwd=root, env=env, stdout=log, stderr=log, start_new_session=True)
            try:
                for _ in range(100):
                    try:
                        await asyncio.to_thread(urllib.request.urlopen, origin, None, 1)
                        if server.started:
                            break
                    except OSError:
                        pass
                    await asyncio.sleep(0.2)
                else:
                    raise AssertionError((folder / "vite.log").read_text()[-3000:])
                async with async_playwright() as playwright:
                    browser = await playwright.chromium.launch(headless=True)
                    context = await browser.new_context(ignore_https_errors=True)
                    page = await context.new_page()
                    errors = []
                    page.on("pageerror", lambda e: errors.append(str(e)))
                    async def provider(route):
                        headers = {"Access-Control-Allow-Origin": origin, "Access-Control-Allow-Headers": "*"}
                        if route.request.method == "OPTIONS":
                            return await route.fulfill(status=204, headers=headers)
                        if "/token?" in route.request.url:
                            credentials = route.request.post_data_json
                            if credentials.get("password") != "senha-sintetica":
                                return await route.fulfill(status=400, headers=headers, json={"error": "invalid_grant"})
                            user = "u2" if credentials.get("email") == "cliente@example.test" else "u1"
                            return await route.fulfill(headers=headers, json={"access_token": token(user), "refresh_token": "fixture-refresh",
                                "token_type": "bearer", "expires_in": 3600, "user": {"id": user, "aud": "authenticated", "email": credentials["email"], "app_metadata": {}, "user_metadata": {}}})
                        if "/logout" in route.request.url:
                            return await route.fulfill(status=204, headers=headers)
                        raise AssertionError("Chamada inesperada ao provedor")
                    await context.route("https://auth.example.test/**", provider)
                    if accessibility:
                        from accessibility import check_authenticated
                        await check_authenticated(page, context, origin, api)
                        await browser.close()
                        return
                    async def login(email="escritorio@example.test", password="senha-sintetica"):
                        await page.get_by_label("E-mail", exact=True).fill(email)
                        await page.get_by_label("Senha", exact=True).fill(password)
                        await page.get_by_role("button", name="Entrar", exact=True).click()
                    release_session = asyncio.Event()
                    async def unavailable(route):
                        await release_session.wait()
                        await route.fulfill(status=503, headers={"Access-Control-Allow-Origin": origin, "Access-Control-Allow-Credentials": "true"}, json={"detail": {"mensagem": "indisponível"}})
                    await context.route(api + "/v1/sessao", unavailable, times=1)
                    await page.goto(origin, wait_until="domcontentloaded")
                    await expect(page.get_by_text("Carregando sessão…", exact=True)).to_be_visible()
                    release_session.set()
                    await expect(page.get_by_role("heading", name="Serviço indisponível", exact=True)).to_be_visible()
                    await expect(page.get_by_text("Demonstração — sem emissão fiscal")).to_have_count(0)
                    await page.get_by_role("button", name="Tentar novamente", exact=True).click()
                    await expect(page.get_by_role("heading", name="Entrar", exact=True)).to_be_visible()
                    # Preferência forjada não concede membership nem seleciona empresa C.
                    await page.evaluate("localStorage.setItem('nfse-imoveis:empresa-ativa:api:u1', 'C')")
                    await login(password="errada")
                    await expect(page.get_by_role("alert")).to_contain_text("Não foi possível entrar")
                    await login()
                    await expect(page.get_by_role("heading", name="Empresa A Fictícia", exact=True)).to_be_visible()
                    await expect(page.get_by_text("Demonstração — sem emissão fiscal")).to_have_count(0)
                    cookie = next(c for c in await context.cookies(api) if c["name"] == "session")
                    assert cookie["httpOnly"] and cookie["secure"] and cookie["sameSite"] == "None"
                    assert "session=" not in await page.evaluate("document.cookie")
                    assert not any("auth-token" in x for x in await page.evaluate("Object.keys(localStorage)"))
                    assert "fixture-refresh" not in await page.evaluate("JSON.stringify(localStorage)")
                    await page.reload()
                    await expect(page.get_by_role("heading", name="Empresa A Fictícia", exact=True)).to_be_visible()
                    await page.get_by_label("Empresa ativa", exact=True).click()
                    await expect(page.get_by_role("option", name="Empresa C")).to_have_count(0)
                    await page.get_by_role("option", name="Empresa B").click()
                    await expect(page.get_by_role("heading", name="Empresa B Fictícia", exact=True)).to_be_visible()
                    unauthorized = await context.request.get(api + "/v1/empresas/C/rascunhos")
                    assert unauthorized.status == 404 and "Empresa C" not in await unauthorized.text()
                    # Salvar rascunho via UI autenticada nunca cria job nem tentativa fiscal.
                    await page.get_by_role("link", name="Nova NFS-e").first.click()
                    await page.fill("#doc", "52998224725")
                    await page.fill("#nome", "Tomador somente B")
                    await page.get_by_role("button", name="Continuar", exact=True).click()
                    await page.select_option("#op", "locacao")
                    await page.fill("#comp", "2026-11")
                    await page.get_by_role("button", name="Continuar", exact=True).click()
                    await page.get_by_role("button", name="Salvar rascunho", exact=True).click()
                    await expect(page.get_by_text("Rascunho salvo", exact=False).first).to_be_visible()
                    drafts = await context.request.get(api + "/v1/empresas/B/rascunhos")
                    assert len(await drafts.json()) == 1
                    assert await (await context.request.get(api + "/v1/empresas/A/rascunhos")).json() == []
                    # Expiração real do JWT: o backend rejeita assinatura temporalmente inválida.
                    await context.add_cookies([{**{k: cookie[k] for k in ("name", "value", "domain", "path", "secure", "httpOnly", "sameSite")}, "value": token(expired=True)}])
                    await page.goto(origin + "/historico")
                    await expect(page.get_by_role("heading", name="Entrar", exact=True)).to_be_visible()
                    await expect(page.get_by_text("Tomador somente B")).to_have_count(0)
                    await login()
                    await expect(page.get_by_role("button", name="Sair", exact=True)).to_be_visible()
                    # 403 explícito na UI (injeção de erro de transporte, não contrato novo).
                    async def forbidden(route):
                        await route.fulfill(status=403, headers={"Access-Control-Allow-Origin": origin, "Access-Control-Allow-Credentials": "true"}, json={"detail": {"mensagem": "Origem não autorizada"}})
                    await context.route(api + "/v1/empresas/*/rascunhos", forbidden)
                    await page.get_by_role("link", name="Início", exact=True).click()
                    await expect(page.get_by_role("heading", name="Acesso não disponível", exact=True)).to_be_visible()
                    await context.unroute(api + "/v1/empresas/*/rascunhos", forbidden)
                    await page.get_by_role("link", name="Voltar ao contexto autorizado").click()
                    await expect(page.get_by_role("button", name="Sair", exact=True)).to_be_visible()
                    # Revogação no mesmo cookie não concede acesso pela seleção da UI.
                    members.revoke("u1", "B")
                    await page.reload()
                    await expect(page.get_by_role("heading", name="Empresa A Fictícia", exact=True)).to_be_visible()
                    assert (await context.request.get(api + "/v1/empresas/B/rascunhos")).status == 404
                    async def fail_logout(route):
                        await route.fulfill(status=503, headers={"Access-Control-Allow-Origin": origin, "Access-Control-Allow-Credentials": "true"})
                    await context.route(api + "/v1/auth/session", fail_logout, times=1)
                    await page.get_by_role("button", name="Sair", exact=True).click()
                    await expect(page.get_by_role("alert")).to_contain_text("Não foi possível encerrar a sessão")
                    await expect(page.get_by_role("heading", name="Empresa A Fictícia", exact=True)).to_have_count(0)
                    assert (await context.request.get(api + "/v1/sessao")).status == 200
                    await page.get_by_role("button", name="Tentar sair novamente", exact=True).click()
                    await expect(page.get_by_role("heading", name="Entrar", exact=True)).to_be_visible()
                    assert (await context.request.get(api + "/v1/sessao")).status == 401
                    await login(email="cliente@example.test")
                    await expect(page.get_by_role("heading", name="Empresa B Fictícia", exact=True)).to_be_visible()
                    await expect(page.get_by_label("Empresa ativa", exact=True)).to_have_count(0)
                    assert (await (await context.request.get(api + "/v1/sessao")).json())["papel"] == "cliente"
                    assert (await context.request.get(api + "/v1/empresas/A/rascunhos")).status == 404
                    assert all(not auth or (method, path) == ("POST", "/v1/auth/session") for method, path, auth in requests)
                    assert not any("/emissao" in path or "/verificar" in path for _, path, _ in requests)
                    assert errors == [], errors
                    await browser.close()
                    print("PASS auth E2E: login SDK + JWT/JWKS FastAPI, loading/503, cookie seguro, reload, memberships/preferência forjada, troca, rascunho, 401/403, revogação e logout/falha; zero emissão fiscal")
            finally:
                import signal
                os.killpg(frontend.pid, signal.SIGTERM)
                frontend.wait(timeout=15)
                server.should_exit = True
                thread.join(timeout=10)

if __name__ == "__main__":
    import sys
    async def standard():
        await main()
        await authenticated(accessibility=True)
    asyncio.run(authenticated() if "--auth" in sys.argv else standard())
