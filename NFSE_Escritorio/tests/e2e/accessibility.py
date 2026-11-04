"""Manifest #38: keyboard and responsive checks using the existing auth E2E fixture.

Run: python tests/e2e/accessibility.py
Only synthetic identities/data. No screenshots, token logs or fiscal operations.
This bounded automated suite does not certify full WCAG conformance.
"""
import asyncio
import re
from pathlib import Path
from playwright.async_api import expect


async def keyboard_to(page, target, limit=80):
    """Reach a control through real Tab presses, without programmatic focus/click."""
    visited = []
    for _ in range(limit):
        visited.append(await page.evaluate("""() => [document.activeElement.tagName,
            document.activeElement.id, document.activeElement.getAttribute('role')]"""))
        if await target.evaluate("el => el === document.activeElement"):
            assert await target.evaluate("""el => {
                const s = getComputedStyle(el);
                return el.matches(':focus-visible') &&
                    ((s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) >= 2) || s.boxShadow !== 'none');
            }"""), "Keyboard focus must have a visible indicator"
            return
        await page.keyboard.press('Tab')
    state = await page.evaluate("""() => ({tag: document.activeElement.tagName,
        id: document.activeElement.id, role: document.activeElement.getAttribute('role')})""")
    raise AssertionError(f'Control not reachable in bounded keyboard navigation: {state}; trail={visited[-20:]}')


async def audit(page):
    """Browser accessibility tree checks, no external analyzer dependency."""
    cdp = await page.context.new_cdp_session(page)
    try:
        tree = await cdp.send('Accessibility.getFullAXTree')
        controls = {'button', 'link', 'textbox', 'combobox', 'checkbox', 'searchbox', 'spinbutton'}
        for node in tree['nodes']:
            if not node.get('ignored') and node.get('role', {}).get('value') in controls:
                assert node.get('name', {}).get('value', '').strip(), 'Unnamed accessible control'
    finally:
        await cdp.detach()
    layout = await page.evaluate("""() => ({overflow: document.documentElement.scrollWidth > innerWidth + 1,
        elements: [...document.querySelectorAll('main *,header *,[role=main] *')].filter(el => el.getBoundingClientRect().right > innerWidth + 1)
            .slice(0, 8).map(el => ({tag: el.tagName, id: el.id, cls: el.className, width: el.getBoundingClientRect().width}))})""")
    assert not layout['overflow'], f'Page horizontal overflow: {layout["elements"]}'
    assert await page.evaluate("""() => [...document.querySelectorAll('[aria-describedby]')].every(el =>
        el.getAttribute('aria-describedby').split(/\\s+/).every(id => document.getElementById(id)))"""), 'Broken accessible description'


async def check_authenticated(page, context, origin, api):
    calls = []
    page.on('request', lambda r: calls.append((r.method, r.url.split('?')[0].split('/v1/')[-1])) if '/v1/' in r.url else None)
    for width, height in [(1280, 900), (390, 844), (320, 740)]:
        if page.url.startswith(origin):
            await page.evaluate("localStorage.removeItem('nfse-imoveis:empresa-ativa:api:u1')")
        await page.set_viewport_size({'width': width, 'height': height})
        # Delayed response proves live loading, then recoverable error semantics.
        released = asyncio.Event()
        async def unavailable(route):
            await released.wait()
            await route.fulfill(status=503, headers={'Access-Control-Allow-Origin': origin,
                'Access-Control-Allow-Credentials': 'true'}, json={'detail': {'mensagem': 'fixture'}})
        await context.route(api + '/v1/sessao', unavailable, times=1)
        await page.goto(origin, wait_until='domcontentloaded')
        await expect(page.get_by_role('status')).to_contain_text('Carregando sessão')
        released.set()
        await expect(page.get_by_role('heading', name='Serviço indisponível')).to_be_focused()
        await audit(page)
        retry = page.get_by_role('button', name='Tentar novamente', exact=True)
        await keyboard_to(page, retry)
        await page.keyboard.press('Enter')
        await expect(page.get_by_role('heading', name='Entrar', exact=True)).to_be_focused()
        email, password = page.get_by_label('E-mail', exact=True), page.get_by_label('Senha', exact=True)
        await keyboard_to(page, email)
        await page.keyboard.type('escritorio@example.test')
        await page.keyboard.press('Tab')
        await expect(password).to_be_focused()
        await page.keyboard.type('errada')
        submit = page.get_by_role('button', name='Entrar', exact=True)
        await keyboard_to(page, submit)
        await page.keyboard.press('Enter')
        await expect(page.get_by_role('alert')).to_be_focused()
        await expect(password).to_have_attribute('aria-describedby', 'login-error')
        await audit(page)
        await keyboard_to(page, password)
        await page.keyboard.type('senha-sintetica')
        await keyboard_to(page, submit)
        await page.keyboard.press('Enter')
        main = page.get_by_role('main')
        await expect(main).to_be_focused()
        await expect(page.get_by_role('heading', name='Empresa A Fictícia', exact=True)).to_be_visible()
        await expect(page.get_by_text('Nenhum rascunho.', exact=False)).to_be_visible()
        await audit(page)
        company = page.get_by_role('combobox', name='Empresa ativa')
        await keyboard_to(page, company)
        await page.keyboard.press('Enter')
        await expect(page.get_by_role('listbox')).to_be_visible()
        await page.keyboard.press('Escape')
        await expect(company).to_be_focused()
        await page.keyboard.press('Enter')
        await expect(page.get_by_role('listbox')).to_be_visible()
        await page.keyboard.press('End')
        await expect(page.get_by_role('option', name=re.compile('Empresa B'))).to_be_focused()
        await page.keyboard.press('Enter')
        await expect(page.get_by_role('heading', name='Empresa B Fictícia', exact=True)).to_be_visible()
        await audit(page)
        # Tab wraps back to the skip link: header can be bypassed without a mouse.
        skip = page.get_by_role('link', name='Ir para o conteúdo principal')
        await keyboard_to(page, skip)
        await page.keyboard.press('Enter')
        await expect(main).to_be_focused()
        history = page.get_by_role('link', name='Histórico', exact=True)
        await keyboard_to(page, history)
        await page.keyboard.press('Enter')
        await expect(main).to_be_focused()
        await expect(page.get_by_role('heading', name='Histórico', exact=True)).to_be_visible()
        await audit(page)
        await page.reload()
        await expect(page.get_by_role('main')).to_be_focused()
        await expect(page.locator('header')).to_contain_text('Empresa B Fictícia')
        await audit(page)
        # Generic denial route: focus and safe recovery remain available.
        await page.goto(origin + '/rascunho/inexistente')
        await expect(page.get_by_role('heading', name='Acesso não disponível')).to_be_focused()
        await audit(page)
        back = page.get_by_role('link', name='Voltar ao contexto autorizado', exact=True)
        await keyboard_to(page, back)
        await page.keyboard.press('Enter')
        await expect(page.get_by_role('heading', name='Empresa B Fictícia', exact=True)).to_be_visible()
        new_draft = page.get_by_role('link', name='Nova NFS-e', exact=True).first
        await keyboard_to(page, new_draft)
        await page.keyboard.press('Enter')
        doc = page.get_by_label('CPF ou CNPJ', exact=True)
        await keyboard_to(page, doc)
        await page.keyboard.type('123')
        advance = page.get_by_role('button', name='Continuar', exact=True)
        await keyboard_to(page, advance)
        await page.keyboard.press('Enter')
        await expect(page.get_by_role('alert')).to_be_focused()
        await expect(doc).to_have_attribute('aria-invalid', 'true')
        await expect(doc).to_have_attribute('aria-describedby', 'doc-erro')
        await keyboard_to(page, doc)
        await page.keyboard.press('ControlOrMeta+A')
        await page.keyboard.type('52998224725')
        await keyboard_to(page, page.get_by_label('Nome ou razão social', exact=True))
        await page.keyboard.type('Tomador Fictício Acessibilidade')
        await keyboard_to(page, advance)
        await page.keyboard.press('Enter')
        await expect(page.get_by_label('Tipo de operação', exact=True)).to_be_focused()
        await audit(page)
        await keyboard_to(page, company)
        await page.keyboard.press('Enter')
        await expect(page.get_by_role('listbox')).to_be_visible()
        await page.keyboard.press('Home')
        await expect(page.get_by_role('option', name=re.compile('Empresa A'))).to_be_focused()
        await page.keyboard.press('Enter')
        dialog = page.get_by_role('alertdialog')
        await expect(dialog).to_be_visible()
        box = await dialog.bounding_box()
        assert box['x'] >= 0 and box['y'] >= 0 and box['x'] + box['width'] <= width + 1 and box['y'] + box['height'] <= height + 1
        await keyboard_to(page, page.get_by_role('button', name='Permanecer', exact=True))
        await page.keyboard.press('Enter')
        await expect(dialog).to_have_count(0)
        await expect(company).to_be_focused()
        await expect(doc).to_have_value('529.982.247-25')
        await keyboard_to(page, page.get_by_role('button', name='Salvar rascunho', exact=True))
        await page.keyboard.press('Enter')
        await expect(page.get_by_text('Rascunho salvo', exact=False).first).to_be_visible()
        await expect(page).to_have_url(re.compile('/rascunho/'))
        await expect(page.get_by_role('main')).to_be_focused()
        await audit(page)
        artifacts = Path('/tmp/browser/accessibility')
        artifacts.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(artifacts / f'{width}-draft.png'), full_page=True)
        close_notice = page.get_by_role('button', name='Fechar notificação', exact=True)
        await keyboard_to(page, close_notice)
        await page.keyboard.press('Enter')
        await expect(close_notice).to_have_count(0)
        logout = page.get_by_role('button', name='Sair', exact=True)
        await keyboard_to(page, logout)
        box = await logout.bounding_box()
        assert box['height'] >= 24 and box['width'] >= 24
        await page.keyboard.press('Enter')
        await expect(page.get_by_role('heading', name='Entrar', exact=True)).to_be_focused()
        assert (await context.request.get(api + '/v1/sessao')).status == 401
        await audit(page)
        print(f'PASS accessibility/responsive {width}x{height}: keyboard, focus, labels, loading/error, company, protected read, reload, denial, logout')
    assert not any('/emissao' in path or '/verificar' in path for _, path in calls)


if __name__ == '__main__':
    from nfse_flow import authenticated
    asyncio.run(authenticated(accessibility=True))
