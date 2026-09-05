"""Security regressions, including the actual atomic SQL on two connections."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
import re
import sqlite3
import subprocess
import tempfile
import unittest

from _common import BASE


class PortalSecurityTests(unittest.TestCase):
    def test_javascript_security_contracts(self):
        result = subprocess.run(["node", str(BASE / "Scripts/_test_portal_security.mjs")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_magic_link_consumption_is_atomic_and_checks_expiry(self):
        source = (BASE / "infra/discussions-worker/src/db.js").read_text(encoding="utf-8")
        sql = re.search(r"UPDATE magic_tokens SET used_at = \?[\s\S]*?RETURNING email, display_name", source)[0]
        with tempfile.TemporaryDirectory() as directory:
            database = str(Path(directory) / "tokens.sqlite")
            with closing(sqlite3.connect(database)) as connection, connection:
                connection.executescript((BASE / "infra/discussions-worker/migrations/0001_init.sql").read_text(encoding="utf-8"))
                connection.executemany("INSERT INTO magic_tokens (token,email,display_name,expires_at) VALUES (?, 'test@example.org', 'Test', ?)", [("valid", 200), ("expired", 100)])

            def consume(token):
                with closing(sqlite3.connect(database, timeout=5)) as connection, connection:
                    return connection.execute(sql, (100, token, 100)).fetchone()

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(consume, ["valid", "valid"]))
            self.assertEqual(sum(result is not None for result in results), 1)
            self.assertIsNone(consume("expired"))
            self.assertIsNone(consume("missing"))


if __name__ == "__main__":
    unittest.main()
