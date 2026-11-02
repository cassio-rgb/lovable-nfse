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
asyncio.run(main())
