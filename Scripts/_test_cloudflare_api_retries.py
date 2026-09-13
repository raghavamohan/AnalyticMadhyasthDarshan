"""Verify safe Cloudflare read retries and single-attempt writes."""
import io
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

import _cloudflare_performance as cf


class RetryTests(unittest.TestCase):
    def response(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{"success": true, "result": {}}'
        return response

    def test_connection_reset_then_success(self):
        with patch.object(cf.urllib.request, "urlopen", side_effect=[
            urllib.error.URLError(ConnectionResetError()), self.response()
        ]) as request, patch.object(cf.time, "sleep") as sleep:
            self.assertTrue(cf._api_request("GET", "/zones", "secret")["success"])
        self.assertEqual(request.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_retryable_http_errors(self):
        for code in (429, 500, 502, 503, 504):
            with self.subTest(code=code):
                error = urllib.error.HTTPError("url", code, "transient", {"Retry-After": "3"}, io.BytesIO())
                with patch.object(cf.urllib.request, "urlopen", side_effect=[error, self.response()]), \
                        patch.object(cf.time, "sleep") as sleep:
                    self.assertTrue(cf._api_request("GET", "/zones", "secret")["success"])
                sleep.assert_called_once_with(3)

    def test_exhaustion_is_bounded(self):
        with patch.object(cf.urllib.request, "urlopen", side_effect=TimeoutError()) as request, \
                patch.object(cf.time, "sleep") as sleep:
            with self.assertRaises(TimeoutError):
                cf._api_request("GET", "/zones", "secret")
        self.assertEqual(request.call_count, 3)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [1, 2])

    def test_writes_are_not_replayed(self):
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            with self.subTest(method=method), patch.object(
                cf.urllib.request, "urlopen", side_effect=urllib.error.URLError("reset")
            ) as request, patch.object(cf.time, "sleep") as sleep:
                with self.assertRaises(urllib.error.URLError):
                    cf._api_request(method, "/zones", "secret", {})
                self.assertEqual(request.call_count, 1)
                sleep.assert_not_called()

    def test_permanent_http_error_is_not_retried(self):
        error = urllib.error.HTTPError("url", 403, "forbidden", {}, io.BytesIO(b'{"success": false}'))
        with patch.object(cf.urllib.request, "urlopen", side_effect=error) as request, \
                patch.object(cf.time, "sleep") as sleep:
            with self.assertRaises(RuntimeError):
                cf._api_request("GET", "/zones", "secret")
        self.assertEqual(request.call_count, 1)
        sleep.assert_not_called()

    def test_optional_missing_resource_still_returns_none(self):
        error = urllib.error.HTTPError("url", 404, "missing", {}, io.BytesIO())
        with patch.object(cf.urllib.request, "urlopen", side_effect=error):
            self.assertIsNone(cf._api_request("GET", "/zones", "secret", allow_404=True))


if __name__ == "__main__":
    unittest.main()
