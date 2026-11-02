"""Guardas dos helpers de teste. Não conectam a banco e não apagam nada."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests import pg_guard

SH = Path(__file__).resolve().parents[2] / "scripts" / "pg_ephemeral.sh"
OK = {pg_guard.RESET_FLAG: pg_guard.RESET_VALUE}
SOCK = "?host=/tmp&port=54329"

try:
    import psycopg  # noqa: F401
    HAS_PSYCOPG = True
except ImportError:
    HAS_PSYCOPG = False


@unittest.skipUnless(HAS_PSYCOPG, "psycopg ausente")
class DbGuard(unittest.TestCase):
    def test_accepts_dedicated(self):
        for db in ("nfse_test", "nfse_test_ci1"):
            pg_guard.check(f"postgresql://postgres@/{db}{SOCK}", OK)
        pg_guard.check("postgresql://u@127.0.0.1:5432/nfse_test", OK)

    def test_rejects_names(self):
        for db in ("latest", "protest", "producao", "test", "nfse_test-x", "nfse_testx", "nfse_test_"):
            with self.assertRaises(pg_guard.UnsafeTestDatabase, msg=db):
                pg_guard.check(f"postgresql://postgres@/{db}{SOCK}", OK)

    def test_rejects_remote_host(self):
        for h in ("db.example.com", "10.0.0.5"):
            with self.assertRaises(pg_guard.UnsafeTestDatabase):
                pg_guard.check(f"postgresql://u@{h}/nfse_test", OK)

    def test_rejects_missing_or_wrong_flag(self):
        for env in ({}, {pg_guard.RESET_FLAG: "1"}, {pg_guard.RESET_FLAG: "yes"}):
            with self.assertRaises(pg_guard.UnsafeTestDatabase):
                pg_guard.check(f"postgresql://postgres@/nfse_test{SOCK}", env)
        with self.assertRaises(pg_guard.UnsafeTestDatabase):
            pg_guard.check("", OK)


class ShellGuard(unittest.TestCase):
    def run_sh(self, d, *args, guard_only=True):
        env = {**os.environ, "PG_EPHEMERAL_DIR": d}
        if guard_only:
            env["PG_EPHEMERAL_GUARD_ONLY"] = "1"
        return subprocess.run(["bash", str(SH), *args], env=env, capture_output=True, text=True)

    def test_rejects_dangerous_paths(self):
        for d in ("/", "/tmp", "/tmp/", "/etc", "/home/x/nfse-pg-test", "/tmp/a/nfse-pg-test",
                  "/tmp/../etc/nfse-pg-test", "relative/nfse-pg-test", "/tmp/other", "/tmp/nfse-pg-testX"):
            r = self.run_sh(d, "start")
            self.assertEqual(r.returncode, 2, (d, r.stdout, r.stderr))

    def test_accepts_dedicated_path(self):
        self.assertEqual(self.run_sh("/tmp/nfse-pg-test-ci", "start").returncode, 0)

    def test_refuses_unmarked_existing_dir(self):
        d = tempfile.mkdtemp(prefix="nfse-pg-test-", dir="/tmp")
        sentinel = Path(d) / "keep"
        sentinel.write_text("x")
        try:
            for cmd in ("start", "stop"):
                r = self.run_sh(d, cmd, guard_only=False)
                self.assertEqual(r.returncode, 2, r.stderr)
                self.assertIn("marcador", r.stderr)
                self.assertTrue(sentinel.exists())
        finally:
            sentinel.unlink(); os.rmdir(d)

    def test_symlink_refused(self):
        link = "/tmp/nfse-pg-test-link"
        if os.path.lexists(link):
            os.unlink(link)
        os.symlink("/etc", link)
        try:
            self.assertEqual(self.run_sh(link, "start").returncode, 2)
        finally:
            os.unlink(link)

    def test_never_touches_passwd(self):
        self.assertNotIn("/etc/passwd", SH.read_text().replace("Nunca edita /etc/passwd", ""))
