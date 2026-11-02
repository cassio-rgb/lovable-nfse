#!/usr/bin/env python3
"""Lançador LOCAL do escritório (sdd/design-addendum-002-escritorio-local.md).

Somente biblioteca padrão. Não instala nada, não altera registro/firewall/política de execução,
não abre portas no roteador, não cria serviço global e nunca imprime valores de configuração.

  python scripts/escritorio.py verificar          pré-requisitos e configuração (sem segredos)
  python scripts/escritorio.py construir [--modo demo|api]
  python scripts/escritorio.py iniciar   [--porta N] [--abrir] [--host 127.0.0.1]
  python scripts/escritorio.py estado
  python scripts/escritorio.py parar              encerra SOMENTE o processo iniciado por este lançador

Escopo atual: apenas loopback (127.0.0.1). Uso em rede local (LAN) está BLOQUEADO até existir
identidade real e TLS. Modo api exige preflight do serviço fiscal aprovado; sem ele o lançador para
com explicação — nunca cai silenciosamente para demonstração nem usa repositório em memória.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".output-local"
ENTRY = OUT / "server" / "index.mjs"
BUILD_INFO = OUT / "nfse-build.json"
STATE_DIR = ROOT / ".nfse-local"
STATE = STATE_DIR / "frontend.json"
LOG = STATE_DIR / "frontend.log"
DEFAULT_PORT = 4517
LOOPBACK = {"127.0.0.1", "localhost", "::1"}
SANDBOX_VARS = ("LOVABLE_SANDBOX", "DEV_SERVER__PROJECT_PATH", "NITRO_PRESET", "SERVER_PRESET", "LOVABLE_NITRO_PRESET")
MIN_NODE = (22, 12, 0)  # engines de vite 8 / @tanstack/react-start: >=22.12
MIN_PY = (3, 12)
MODOS = ("demo", "api")
PS_QUERY = ("$p = Get-CimInstance -ClassName Win32_Process -Filter 'ProcessId={pid}'; "
            "if ($p) {{ [pscustomobject]@{{exe=$p.ExecutablePath; cmd=$p.CommandLine; "
            "criado=$p.CreationDate.ToUniversalTime().ToString('o')}} | ConvertTo-Json -Compress }}")

MSG_API_BLOQUEADA = (
    "Modo API BLOQUEADO: o serviço fiscal local ainda não pode operar.\n"
    "Faltam, conforme o preflight: identidade real de usuários, armazenamento durável privado,\n"
    "cofre do certificado A1, contrato HTTP oficial e algoritmo de assinatura aprovados.\n"
    "Nada foi iniciado. Use '--modo demo' (dados fictícios, sem emissão fiscal) ou conclua\n"
    "as etapas de docs/ativacao-homologacao.md. O lançador não usa modo demonstração no lugar da API."
)


class Recusa(Exception):
    """Condição que impede a operação; mensagem em português, sem segredos."""


# ---------------------------------------------------------------- guardas puras (testáveis)

def validar_host(host: str) -> str:
    h = host.strip().lower()
    if h not in LOOPBACK:
        try:
            ok = ipaddress.ip_address(h).is_loopback
        except ValueError:
            ok = False
        if not ok:
            raise Recusa(f"Endereço '{host}' recusado: acesso pela rede local (LAN) está BLOQUEADO "
                         "até existir login real e TLS. Use 127.0.0.1.")
    return "127.0.0.1" if h == "localhost" else h


def validar_porta(porta: int) -> int:
    if not (1024 <= porta <= 65535):
        raise Recusa(f"Porta {porta} fora do intervalo permitido (1024–65535).")
    return porta


def porta_livre(host: str, porta: int) -> bool:
    fam = socket.AF_INET6 if ":" in host else socket.AF_INET
    with socket.socket(fam, socket.SOCK_STREAM) as s:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            s.bind((host, porta))
        except OSError:
            return False
    return True


def validar_api_url(url: str) -> None:
    """A API do modo local também precisa ficar no próprio computador (loopback)."""
    p = urllib.parse.urlsplit(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        raise Recusa("VITE_NFSE_API_URL inválida (esperado http(s)://127.0.0.1:<porta>).")
    if p.username or p.password:
        raise Recusa("VITE_NFSE_API_URL não pode conter usuário/senha.")
    validar_host(p.hostname)


def env_construcao(base: dict[str, str], modo: str) -> dict[str, str]:
    env = {k: v for k, v in base.items() if k not in SANDBOX_VARS}
    env["NFSE_BUILD_PROFILE"] = "local-node"
    if modo == "demo":
        env["VITE_NFSE_API_URL"] = ""  # sobrepõe qualquer .env: demonstração explícita
    return env


def rodar_preflight(env: dict[str, str]) -> int:
    return subprocess.call([sys.executable, str(ROOT / "scripts" / "preflight.py")], cwd=ROOT, env=env,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def exigir_api_pronta(env: dict[str, str], preflight=rodar_preflight) -> None:
    url = env.get("VITE_NFSE_API_URL", "")
    if not url:
        raise Recusa("Modo API pedido, mas VITE_NFSE_API_URL não está definida.\n" + MSG_API_BLOQUEADA)
    validar_api_url(url)
    if preflight(env) != 0:
        raise Recusa(MSG_API_BLOQUEADA)


# ---------------------------------------------------------------- utilidades

def node_exe() -> str:
    n = shutil.which("node")
    if not n:
        raise Recusa("Node.js não encontrado no PATH. Instale Node.js 22.12 ou superior (24 é aceito; não é instalado automaticamente).")
    return n


def versao(cmd: list[str]) -> tuple[int, ...] | None:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=15).stdout.strip().lstrip("v")
        return tuple(int(x) for x in out.split(".")[:3])
    except Exception:
        return None


def ler_json(p: Path) -> dict | None:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


class ConsultaIndisponivel(Exception):
    """Não foi possível consultar a identidade do processo; nunca encerrar nesse caso."""


def consultar_processo(pid: int, sistema: str | None = None, run=subprocess.run) -> dict | None:
    """Identidade somente leitura: executável, linha de comando e horário de criação.
    Retorna None se o PID não existe; levanta ConsultaIndisponivel se não dá para saber."""
    sistema = sistema or os.name
    if sistema == "nt":
        try:
            r = run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", PS_QUERY.format(pid=pid)],
                    capture_output=True, text=True, timeout=20)
        except (OSError, subprocess.SubprocessError) as e:
            raise ConsultaIndisponivel("consulta CIM indisponível") from e
        if r.returncode != 0:
            raise ConsultaIndisponivel("consulta CIM falhou")
        if not r.stdout.strip():
            return None
        try:
            d = json.loads(r.stdout)
        except ValueError as e:
            raise ConsultaIndisponivel("resposta CIM ilegível") from e
        if not all(isinstance(d.get(k), str) and d.get(k) for k in ("exe", "cmd", "criado")):
            raise ConsultaIndisponivel("resposta CIM incompleta")
        return {"exe": d["exe"], "cmd": d["cmd"], "criado": d["criado"]}
    base = Path(f"/proc/{pid}")
    if not Path("/proc/self").exists():
        raise ConsultaIndisponivel("/proc indisponível")
    try:
        exe = os.readlink(base / "exe")
        argv = (base / "cmdline").read_bytes().rstrip(b"\0").split(b"\0")
        stat = (base / "stat").read_text()
        criado = stat[stat.rindex(")") + 2:].split()[19]  # campo 22: starttime
    except FileNotFoundError:
        return None
    except (OSError, ValueError, IndexError) as e:
        raise ConsultaIndisponivel("leitura de /proc falhou") from e
    return {"exe": exe, "cmd": json.dumps([a.decode(errors="replace") for a in argv]), "criado": criado}


def validar_estado(st) -> dict:
    """Arquivo de estado precisa ter forma exata; qualquer desvio = recusa (fail-closed)."""
    if not isinstance(st, dict):
        raise Recusa("Arquivo de estado inválido; nada foi encerrado. Confira manualmente.")
    pid, porta, ident = st.get("pid"), st.get("porta"), st.get("identidade")
    ok = (type(pid) is int and pid > 0 and type(porta) is int and 1024 <= porta <= 65535
          and st.get("host") in ("127.0.0.1", "::1") and st.get("modo") in MODOS and isinstance(ident, dict)
          and set(ident) == {"exe", "cmd", "criado"} and all(isinstance(v, str) and v for v in ident.values()))
    if not ok:
        raise Recusa(f"Arquivo de estado {STATE} inválido; nada foi encerrado. Confira manualmente e apague-o.")
    return st


def e_nosso(st: dict, consulta=consultar_processo) -> bool:
    """True só se PID atual tem exatamente o executável, a linha de comando e a criação gravados."""
    atual = consulta(st["pid"])
    return atual is not None and atual == st["identidade"]


def exigir_versoes() -> None:
    if sys.version_info[:2] < MIN_PY:
        raise Recusa(f"Python {MIN_PY[0]}.{MIN_PY[1]} ou superior é necessário.")
    nv = versao([node_exe(), "--version"])
    if not nv or nv < MIN_NODE:
        raise Recusa("Node.js 22.12 ou superior é necessário (exigência do Vite 8). Atualize manualmente.")


def ler_build_modo() -> str:
    info = ler_json(BUILD_INFO)
    modo = info.get("modo") if isinstance(info, dict) else None
    if not ENTRY.exists() or modo not in MODOS or info.get("perfil") != "local-node":
        raise Recusa("Build local ausente ou com manifesto inválido. Rode 'construir' novamente.")
    return modo


def env_execucao(base: dict[str, str], host: str, porta: int) -> dict[str, str]:
    env = {k: v for k, v in base.items()
           if k not in SANDBOX_VARS and k not in ("HOST", "PORT") and not k.startswith("NITRO_")}
    env.update(HOST=host, PORT=str(porta), NITRO_HOST=host, NITRO_PORT=str(porta), NODE_ENV="production")
    return env


def estado_ativo() -> dict | None:
    """Estado válido de um processo ainda nosso; None se não há registro."""
    if not STATE.exists():
        return None
    st = validar_estado(ler_json(STATE))
    try:
        return st if e_nosso(st) else None
    except ConsultaIndisponivel:
        raise Recusa("Não foi possível confirmar a identidade do processo registrado; nada foi feito.")


def http_pronto(url: str, timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status == 200 and "text/html" in r.headers.get("content-type", "")
    except (urllib.error.URLError, OSError):
        return False


# ---------------------------------------------------------------- comandos

def cmd_verificar(_a) -> int:
    linhas, ok = [], True
    py = sys.version_info[:2]
    linhas.append(("python", py >= MIN_PY, f"{py[0]}.{py[1]} (mínimo {MIN_PY[0]}.{MIN_PY[1]})"))
    n = shutil.which("node")
    nv = versao([n, "--version"]) if n else None
    linhas.append(("node", bool(nv and nv >= MIN_NODE), f"{'.'.join(map(str, nv)) if nv else 'ausente'} (mínimo 22.12)"))
    linhas.append(("dependências do projeto", (ROOT / "node_modules" / "vite").exists(),
                   "node_modules presente" if (ROOT / "node_modules" / "vite").exists() else "rode 'bun install --frozen-lockfile' manualmente"))
    linhas.append(("build local", ENTRY.exists(), "construído" if ENTRY.exists() else "rode 'construir'"))
    info = ler_json(BUILD_INFO) or {}
    for nome, passou, det in linhas:
        ok &= passou
        print(f"[{'OK' if passou else 'FALTA':<5}] {nome}: {det}")
    print(f"[INFO ] modo do build: {info.get('modo', 'nenhum')}")
    print(f"[INFO ] VITE_NFSE_API_URL: {'definida (não validada)' if os.environ.get('VITE_NFSE_API_URL') else 'não definida → demonstração'}")
    print("[BLOQ ] rede local (LAN): bloqueada até login real e TLS")
    print("[BLOQ ] emissão fiscal: bloqueada (ver scripts/preflight.py)")
    return 0 if ok else 1


def cmd_construir(a) -> int:
    if not (ROOT / "node_modules" / "vite").exists():
        raise Recusa("Dependências ausentes. Rode 'bun install --frozen-lockfile' manualmente antes.")
    exigir_versoes()
    env = env_construcao(dict(os.environ), a.modo)
    if a.modo == "api":
        exigir_api_pronta(env)
    if estado_ativo():
        raise Recusa("O servidor local está em execução; rode 'parar' antes de construir.")
    rc = subprocess.call([node_exe(), str(ROOT / "node_modules" / "vite" / "bin" / "vite.js"), "build"], cwd=ROOT, env=env)
    if rc != 0 or not ENTRY.exists():
        print(f"Build falhou (exit {rc}).", file=sys.stderr)
        return rc or 1
    BUILD_INFO.write_text(json.dumps({"modo": a.modo, "perfil": "local-node", "gerado": time.time()}), encoding="utf-8")
    print(f"Build local pronto em {OUT} (modo {a.modo}).")
    return 0


def cmd_iniciar(a) -> int:
    host, porta = validar_host(a.host), validar_porta(a.porta)
    exigir_versoes()
    modo = ler_build_modo()
    if modo == "api":
        exigir_api_pronta(dict(os.environ))
    st = estado_ativo()
    if st:
        raise Recusa(f"Já existe um servidor deste lançador rodando (porta {st.get('porta')}). Use 'parar'.")
    if not porta_livre(host, porta):
        raise Recusa(f"Porta {porta} já está em uso por outro programa. Nada foi encerrado; escolha outra com --porta.")
    STATE_DIR.mkdir(exist_ok=True)
    env = env_execucao(dict(os.environ), host, porta)
    kw: dict = {}
    if os.name == "nt":
        kw["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | getattr(subprocess, "CREATE_NO_WINDOW", 0)
    else:
        kw["start_new_session"] = True
    log = open(LOG, "ab")
    proc = subprocess.Popen([node_exe(), str(ENTRY)], cwd=OUT, env=env, stdout=log, stderr=log, stdin=subprocess.DEVNULL, **kw)
    url = f"http://{'[::1]' if host == '::1' else host}:{porta}/"
    limite = time.time() + a.espera
    while time.time() < limite:
        if proc.poll() is not None:
            raise Recusa(f"O servidor terminou ao iniciar (exit {proc.returncode}). Veja {LOG}.")
        if http_pronto(url):
            break
        time.sleep(0.4)
    else:
        proc.terminate()
        raise Recusa(f"O servidor não respondeu em {a.espera}s; encerrado. Veja {LOG}.")
    try:
        ident = consultar_processo(proc.pid)
    except ConsultaIndisponivel:
        ident = None
    if not ident:
        proc.terminate()  # objeto Popen próprio, não busca por nome/porta
        raise Recusa("Não foi possível registrar a identidade do processo iniciado; encerrado por segurança.")
    STATE.write_text(json.dumps({"pid": proc.pid, "porta": porta, "host": host, "modo": modo,
                                 "identidade": ident, "inicio": time.time()}), encoding="utf-8")
    aviso = " — DEMONSTRAÇÃO, SEM EMISSÃO FISCAL" if modo == "demo" else ""
    print(f"Pronto: {url}{aviso}")
    if a.abrir:
        webbrowser.open(url)
    return 0


def cmd_estado(_a) -> int:
    st = estado_ativo()
    if not st:
        print("Parado.")
        return 1
    url = f"http://{st['host']}:{st['porta']}/"
    print(f"Rodando (PID {st['pid']}, modo {st['modo']}) em {url} — HTTP {'ok' if http_pronto(url) else 'sem resposta'}")
    return 0


def cmd_parar(_a, consulta=consultar_processo, matar=None) -> int:
    if not STATE.exists():
        print("Nenhum servidor iniciado por este lançador.")
        return 0
    st = validar_estado(ler_json(STATE))
    pid = st["pid"]
    try:
        atual = consulta(pid)  # verificado imediatamente antes de encerrar
    except ConsultaIndisponivel:
        raise Recusa("Não foi possível confirmar a identidade do processo; nada foi encerrado.")
    if atual is None:
        STATE.unlink(missing_ok=True)
        print("Registro antigo: o processo já não existia. Nada foi encerrado.")
        return 0
    if atual != st["identidade"]:
        STATE.unlink(missing_ok=True)
        print(f"O PID {pid} pertence agora a outro processo; NADA foi encerrado. Registro antigo removido.")
        return 0
    (matar or _matar)(pid)
    STATE.unlink(missing_ok=True)
    print(f"Servidor local (PID {pid}) encerrado.")
    return 0


def _matar(pid: int) -> None:
    if os.name == "nt":  # somente o PID verificado; nunca por nome ou porta
        subprocess.call(["taskkill", "/PID", str(pid), "/F"], stdout=subprocess.DEVNULL)
        return
    os.kill(pid, signal.SIGTERM)
    for _ in range(25):
        if not Path(f"/proc/{pid}").exists():
            break
        time.sleep(0.2)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="escritorio")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("verificar")
    c = sub.add_parser("construir")
    c.add_argument("--modo", choices=("demo", "api"), default="demo")
    i = sub.add_parser("iniciar")
    i.add_argument("--porta", type=int, default=DEFAULT_PORT)
    i.add_argument("--host", default="127.0.0.1")
    i.add_argument("--abrir", action="store_true")
    i.add_argument("--espera", type=float, default=30.0)
    sub.add_parser("estado")
    sub.add_parser("parar")
    a = p.parse_args(argv)
    try:
        return {"verificar": cmd_verificar, "construir": cmd_construir, "iniciar": cmd_iniciar,
                "estado": cmd_estado, "parar": cmd_parar}[a.cmd](a)
    except Recusa as e:
        print(f"RECUSADO: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
