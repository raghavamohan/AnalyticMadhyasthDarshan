"""Analytics Engine SLO export and compiled Web Analytics probes."""
from __future__ import annotations

import io
import json
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

import _cloudflare_performance as cf


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
