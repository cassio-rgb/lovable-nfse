"""Guardas do lançador local (scripts/escritorio.py). Não inicia servidor nem acessa rede externa."""
import importlib.util
import io
import os
import socket
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("escritorio", ROOT / "scripts" / "escritorio.py")
esc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(esc)


class Host(unittest.TestCase):
    def test_loopback_aceito(self):
        for h in ("127.0.0.1", "localhost", "::1", "127.0.0.5"):
            esc.validar_host(h)

    def test_lan_e_externo_recusados(self):
        for h in ("0.0.0.0", "::", "192.168.0.10", "10.0.0.2", "meu-pc", "example.com", "127.0.0.1.nip.io"):
            with self.assertRaises(esc.Recusa, msg=h):
                esc.validar_host(h)

    def test_cli_recusa_host_lan_antes_de_iniciar(self):
        err = io.StringIO()
        with redirect_stderr(err):
            rc = esc.main(["iniciar", "--host", "0.0.0.0"])
        self.assertEqual(rc, 3)
        self.assertIn("BLOQUEADO", err.getvalue())

    def test_porta_privilegiada_recusada(self):
        with self.assertRaises(esc.Recusa):
            esc.validar_porta(80)


class Porta(unittest.TestCase):
    def test_conflito_detectado(self):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        try:
            self.assertFalse(esc.porta_livre("127.0.0.1", s.getsockname()[1]))
        finally:
            s.close()


class Api(unittest.TestCase):
    def test_sem_url_recusa(self):
        with self.assertRaises(esc.Recusa) as c:
            esc.exigir_api_pronta({}, preflight=lambda e: 0)
        self.assertIn("BLOQUEADO", str(c.exception))

    def test_preflight_falho_recusa_sem_fallback(self):
        with self.assertRaises(esc.Recusa) as c:
            esc.exigir_api_pronta({"VITE_NFSE_API_URL": "http://127.0.0.1:8000"}, preflight=lambda e: 1)
        self.assertIn("identidade", str(c.exception))

    def test_preflight_real_bloqueia_hoje(self):
        env = {"VITE_NFSE_API_URL": "http://127.0.0.1:8000", "PATH": os.environ.get("PATH", "")}
        with self.assertRaises(esc.Recusa):
            esc.exigir_api_pronta(env)

    def test_api_externa_ou_com_credencial_recusada(self):
        for u in ("https://api.exemplo.com", "http://192.168.1.2:8000", "http://u:segredo@127.0.0.1:8000", "ftp://127.0.0.1"):
            with self.assertRaises(esc.Recusa, msg=u):
                esc.validar_api_url(u)

    def test_mensagem_nao_vaza_url(self):
        try:
            esc.validar_api_url("http://u:SEGREDO123@127.0.0.1:8000")
        except esc.Recusa as e:
            self.assertNotIn("SEGREDO123", str(e))


class Build(unittest.TestCase):
    def test_demo_sobrepoe_url_e_remove_sandbox(self):
        env = esc.env_construcao({"VITE_NFSE_API_URL": "http://127.0.0.1:8000", "LOVABLE_SANDBOX": "1",
                                  "DEV_SERVER__PROJECT_PATH": "/x", "NITRO_PRESET": "cloudflare-module"}, "demo")
        self.assertEqual(env["VITE_NFSE_API_URL"], "")
        self.assertEqual(env["NFSE_BUILD_PROFILE"], "local-node")
        for k in esc.SANDBOX_VARS:
            self.assertNotIn(k, env)

    def test_verificar_nao_imprime_valores(self):
        old = os.environ.get("VITE_NFSE_API_URL")
        os.environ["VITE_NFSE_API_URL"] = "http://u:SEGREDO999@127.0.0.1:1"
        try:
            out = io.StringIO()
            with redirect_stdout(out):
                esc.cmd_verificar(None)
            self.assertNotIn("SEGREDO999", out.getvalue())
            self.assertIn("não validada", out.getvalue())
        finally:
            if old is None:
                os.environ.pop("VITE_NFSE_API_URL")
            else:
                os.environ["VITE_NFSE_API_URL"] = old



import json as _json
import subprocess as _sp
import tempfile as _tf

ID = {"exe": r"C:\Program Files\nodejs\node.exe", "cmd": r'"C:\Program Files\nodejs\node.exe" C:\nfse\.output-local\server\index.mjs', "criado": "2026-11-02T12:00:00.0000000Z"}
ST = {"pid": 4242, "porta": 4517, "host": "127.0.0.1", "modo": "demo", "identidade": ID, "inicio": 1.0}


def _run(stdout="", rc=0, exc=None):
    def f(*a, **k):
        if exc:
            raise exc
        return _sp.CompletedProcess(a, rc, stdout=stdout, stderr="")
    return f


class ConsultaWindows(unittest.TestCase):
    def test_cim_ok(self):
        r = esc.consultar_processo(4242, "nt", _run(_json.dumps(ID)))
        self.assertEqual(r, ID)

    def test_pid_inexistente(self):
        self.assertIsNone(esc.consultar_processo(4242, "nt", _run("")))

    def test_falha_consulta(self):
        for run in (_run(rc=1), _run(exc=FileNotFoundError()), _run("{lixo"), _run(_json.dumps({"exe": "x"}))):
            with self.assertRaises(esc.ConsultaIndisponivel):
                esc.consultar_processo(4242, "nt", run)


class Parar(unittest.TestCase):
    def setUp(self):
        self.tmp = _tf.TemporaryDirectory()
        self.old = esc.STATE
        esc.STATE = Path(self.tmp.name) / "frontend.json"
        self.mortos = []

    def tearDown(self):
        esc.STATE = self.old
        self.tmp.cleanup()

    def _parar(self, estado, consulta):
        esc.STATE.write_text(_json.dumps(estado))
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return esc.main.__globals__["cmd_parar"](None, consulta=consulta, matar=self.mortos.append)

    def test_dono_normal_encerra(self):
        self.assertEqual(self._parar(ST, lambda p: dict(ID)), 0)
        self.assertEqual(self.mortos, [4242])

    def test_pid_reusado_por_outro_node(self):
        outro = {**ID, "cmd": r'"C:\Program Files\nodejs\node.exe" C:\outro\app.js'}
        self._parar(ST, lambda p: outro)
        self.assertEqual(self.mortos, [])

    def test_criacao_diferente(self):
        self._parar(ST, lambda p: {**ID, "criado": "2026-11-02T13:00:00.0000000Z"})
        self.assertEqual(self.mortos, [])

    def test_pid_inexistente(self):
        self._parar(ST, lambda p: None)
        self.assertEqual(self.mortos, [])

    def test_consulta_falhou_recusa(self):
        def falha(p):
            raise esc.ConsultaIndisponivel("x")
        with self.assertRaises(esc.Recusa):
            self._parar(ST, falha)
        self.assertEqual(self.mortos, [])
        self.assertTrue(esc.STATE.exists())

    def test_estado_invalido_recusa(self):
        for ruim in ({**ST, "pid": -1}, {**ST, "pid": 0}, {**ST, "pid": True}, {**ST, "pid": "4242"},
                     {**ST, "modo": "prod"}, {**ST, "host": "0.0.0.0"}, {k: v for k, v in ST.items() if k != "identidade"},
                     {**ST, "identidade": {**ID, "extra": "x"}}, [1]):
            with self.assertRaises(esc.Recusa, msg=str(ruim)):
                self._parar(ruim, lambda p: dict(ID))
        self.assertEqual(self.mortos, [])


class Ambiente(unittest.TestCase):
    def test_env_execucao_nao_herda_bind(self):
        env = esc.env_execucao({"HOST": "0.0.0.0", "PORT": "80", "NITRO_HOST": "0.0.0.0", "NITRO_SSL_KEY": "k", "X": "1"}, "127.0.0.1", 4517)
        self.assertEqual((env["HOST"], env["NITRO_HOST"], env["PORT"]), ("127.0.0.1", "127.0.0.1", "4517"))
        self.assertNotIn("NITRO_SSL_KEY", env)

    def test_manifesto_modo_estrito(self):
        tmp = _tf.TemporaryDirectory(); old = (esc.BUILD_INFO, esc.ENTRY)
        try:
            esc.ENTRY = Path(tmp.name) / "index.mjs"; esc.ENTRY.write_text("")
            esc.BUILD_INFO = Path(tmp.name) / "b.json"
            for m in ({"modo": "producao", "perfil": "local-node"}, {"perfil": "local-node"}, {"modo": "demo"}, []):
                esc.BUILD_INFO.write_text(_json.dumps(m))
                with self.assertRaises(esc.Recusa):
                    esc.ler_build_modo()
            esc.BUILD_INFO.write_text(_json.dumps({"modo": "demo", "perfil": "local-node"}))
            self.assertEqual(esc.ler_build_modo(), "demo")
        finally:
            esc.BUILD_INFO, esc.ENTRY = old; tmp.cleanup()

    def test_node_minimo(self):
        self.assertLess((22, 11, 9), esc.MIN_NODE)
        self.assertLess((20, 19, 0), esc.MIN_NODE)


if __name__ == "__main__":
    unittest.main()
