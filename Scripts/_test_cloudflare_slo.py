"""Analytics Engine SLO export and compiled Web Analytics probes."""
from __future__ import annotations

import ast
import io
import json
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import _cloudflare_performance as cf

SCRIPTS = Path(__file__).resolve().parent
WORKER_DEPLOY_MODULES = (
    "_cloudflare_performance.py",
    "_worker_deployment.py",
)
BLOCKED_IMPORTS = {"_common", "pypdf"}


class WorkerDeployImportTests(unittest.TestCase):
    def test_deploy_helpers_do_not_import_the_study_pdf_stack(self) -> None:
        for name in WORKER_DEPLOY_MODULES:
            source = (SCRIPTS / name).read_text(encoding="utf-8")
            tree = ast.parse(source)
            imported: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.split(".", 1)[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".", 1)[0])
            blocked = imported & BLOCKED_IMPORTS
            self.assertFalse(
                blocked,
                f"{name} imports {sorted(blocked)}; Worker deploy jobs do not install pypdf",
            )


class AnalyticsEngineSqlTests(unittest.TestCase):
    def test_sql_posts_plain_text_and_appends_json_format(self) -> None:
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(
            {"data": [{"service": "studies"}], "meta": []}
        ).encode("utf-8")
        with patch.object(cf.urllib.request, "urlopen", return_value=response) as opener:
            body = cf.analytics_engine_sql("token", "account", "SELECT 1")
        request = opener.call_args.args[0]
        self.assertEqual(request.method, "POST")
        self.assertEqual(
            request.get_header("Content-type"), "text/plain; charset=utf-8"
        )
        self.assertIn(b"FORMAT JSON", request.data)
        self.assertEqual(body["data"][0]["service"], "studies")

    def test_sql_retries_transient_http_errors(self) -> None:
        error = urllib.error.HTTPError(
            "url", 429, "slow", {"Retry-After": "1"}, io.BytesIO(b"busy")
        )
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{"data":[]}'
        with patch.object(
            cf.urllib.request, "urlopen", side_effect=[error, response]
        ), patch.object(cf.time, "sleep"):
            body = cf.analytics_engine_sql("token", "account", "SELECT 1")
        self.assertEqual(body["data"], [])


class WebAnalyticsLoaderTests(unittest.TestCase):
    def test_live_pages_must_embed_the_compiled_loader(self) -> None:
        html = (
            "<html><head><script data-amd-analytics>token "
            "d0ff8fdbff3b4fe39838c048896422ae</script></head></html>"
        )
        with patch.object(
            cf,
            "_public_probe",
            return_value=(200, "text/html; charset=utf-8", html),
        ) as probe:
            ok, issues = cf.verify_web_analytics_loader()
        self.assertTrue(ok, issues)
        self.assertEqual(probe.call_count, 2)

    def test_missing_loader_is_reported(self) -> None:
        with patch.object(
            cf,
            "_public_probe",
            return_value=(200, "text/html", "<html><head></head></html>"),
        ):
            ok, issues = cf.verify_web_analytics_loader()
        self.assertFalse(ok)
        self.assertTrue(any("missing the compiled Web Analytics loader" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
