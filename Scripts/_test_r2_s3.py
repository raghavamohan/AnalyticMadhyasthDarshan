"""Regressions for bounded R2 read retries and single-attempt writes."""
import datetime as dt
import http.client
import io
import ssl
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

import _r2_s3 as r2
from _publish_site_release import digest, put_verified


class R2ReadRetryTests(unittest.TestCase):
    def setUp(self):
        self.client = r2.R2S3Client(r2.R2Config(
            endpoint="https://r2.example.test",
            access_key_id="test-key",
            secret_access_key="test-secret",
            bucket="test-bucket",
        ))

    def response(self, body=b"content", headers=None):
        response = MagicMock()
        response.__enter__.return_value = response
        response.status = 200
        response.headers = headers or {"Content-Length": str(len(body))}
        response.read.return_value = body
        return response

    def http_error(self, code, headers=None):
        return urllib.error.HTTPError(
            "https://r2.example.test/test-bucket/key", code, "test error",
            headers or {}, io.BytesIO(b"error"),
        )

    def test_staging_metadata_timeout_then_reuse(self):
        body = b"published bytes"
        response = self.response(headers={
            "Content-Length": str(len(body)), "X-Amz-Meta-Sha256": digest(body),
        })
        failure = urllib.error.URLError(TimeoutError("SSL handshake timed out"))
        with patch.object(r2.urllib.request, "urlopen", side_effect=[failure, response]) as request:
            outcome = put_verified(self.client, "site/objects/hash", body,
                                   "text/plain", filename="file.txt")
        self.assertEqual(outcome, "reused")
        self.assertEqual([c.args[0].method for c in request.call_args_list], ["HEAD", "HEAD"])

    def test_transient_transport_errors_are_bounded(self):
        for failure in (urllib.error.URLError(TimeoutError()), TimeoutError(),
                        ConnectionResetError(), http.client.IncompleteRead(b"partial", 8)):
            with self.subTest(failure=type(failure).__name__), \
                    patch.object(r2.urllib.request, "urlopen", side_effect=failure) as request, \
                    patch.object(r2.time, "sleep") as sleep:
                with self.assertRaises(type(failure)):
                    self.client.head_object("key")
                self.assertEqual(request.call_count, 3)
                self.assertEqual([c.args[0] for c in sleep.call_args_list], [1, 2])

    def test_get_body_read_failure_discards_partial_response(self):
        first = self.response()
        first.read.side_effect = http.client.IncompleteRead(b"partial", 8)
        with patch.object(r2.urllib.request, "urlopen", side_effect=[first, self.response(b"complete")]), \
                patch.object(r2.time, "sleep"):
            self.assertEqual(self.client.get_object("key"), b"complete")
        first.__exit__.assert_called_once()

    def test_transient_http_statuses_retry_and_close_error_response(self):
        for code in (429, 500, 502, 503, 504):
            error = self.http_error(code, {"Retry-After": "3"})
            with self.subTest(code=code), \
                    patch.object(r2.urllib.request, "urlopen", side_effect=[error, self.response()]) as request, \
                    patch.object(r2.time, "sleep") as sleep:
                self.assertEqual(self.client.get_object("key"), b"content")
                self.assertEqual(request.call_count, 2)
                sleep.assert_called_once_with(3)
                self.assertTrue(error.closed)

    def test_http_retry_exhaustion_keeps_failure(self):
        errors = [self.http_error(503) for _ in range(3)]
        with patch.object(r2.urllib.request, "urlopen", side_effect=errors) as request, \
                patch.object(r2.time, "sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "HTTP 503"):
                self.client.head_object("key")
        self.assertEqual(request.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        self.assertTrue(all(error.closed for error in errors))

    def test_permanent_http_errors_are_not_retried(self):
        for code in (400, 401, 403, 404, 409, 412, 501):
            error = self.http_error(code)
            with self.subTest(code=code), \
                    patch.object(r2.urllib.request, "urlopen", side_effect=error) as request, \
                    patch.object(r2.time, "sleep") as sleep:
                with self.assertRaisesRegex(RuntimeError, f"HTTP {code}"):
                    self.client.get_object("key")
                request.assert_called_once()
                sleep.assert_not_called()
                self.assertTrue(error.closed)

    def test_optional_missing_object_still_returns_none(self):
        error = self.http_error(404)
        with patch.object(r2.urllib.request, "urlopen", side_effect=error) as request, \
                patch.object(r2.time, "sleep") as sleep:
            self.assertIsNone(self.client.head_object("key"))
        request.assert_called_once()
        sleep.assert_not_called()
        self.assertTrue(error.closed)

    def test_long_retry_after_does_not_retry_early_or_wait_indefinitely(self):
        with patch.object(r2.urllib.request, "urlopen", side_effect=self.http_error(429, {"Retry-After": "61"})) as request, \
                patch.object(r2.time, "sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "HTTP 429"):
                self.client.head_object("key")
        request.assert_called_once()
        sleep.assert_not_called()

    def test_certificate_verification_failure_is_not_retried(self):
        failure = urllib.error.URLError(ssl.SSLCertVerificationError(1, "invalid certificate"))
        with patch.object(r2.urllib.request, "urlopen", side_effect=failure) as request, \
                patch.object(r2.time, "sleep") as sleep:
            with self.assertRaises(urllib.error.URLError):
                self.client.head_object("key")
        request.assert_called_once()
        sleep.assert_not_called()

    def test_writes_are_not_replayed_after_transport_or_http_failure(self):
        for method in ("PUT", "POST", "DELETE"):
            for failure in (urllib.error.URLError(TimeoutError()), self.http_error(503)):
                expected = RuntimeError if isinstance(failure, urllib.error.HTTPError) else type(failure)
                with self.subTest(method=method, failure=type(failure).__name__), \
                        patch.object(r2.urllib.request, "urlopen", side_effect=failure) as request, \
                        patch.object(r2.time, "sleep") as sleep:
                    with self.assertRaises(expected):
                        self.client._request(method, "/test-bucket/key", body=b"payload")
                    request.assert_called_once()
                    sleep.assert_not_called()

    def test_successful_upload_is_not_replayed_when_verification_read_retries(self):
        with patch.object(r2.urllib.request, "urlopen", side_effect=[
            self.response(), urllib.error.URLError(TimeoutError()), self.response(),
        ]) as request, patch.object(r2.time, "sleep"):
            self.assertEqual(self.client.put_object(
                "key", b"content", metadata={}, cache_control="no-store",
                content_disposition="inline",
            ), {"content-length": "7"})
        self.assertEqual([c.args[0].method for c in request.call_args_list], ["PUT", "HEAD", "HEAD"])

    def test_retry_resigns_request_and_preserves_path_and_query(self):
        instants = [dt.datetime(2026, 9, 15, 0, 0, second, tzinfo=dt.timezone.utc) for second in (0, 2)]
        with patch.object(r2.dt, "datetime") as clock, \
                patch.object(r2.urllib.request, "urlopen", side_effect=[TimeoutError(), self.response()]) as request, \
                patch.object(r2.time, "sleep"):
            clock.now.side_effect = instants
            self.client._request("GET", "/test-bucket/a b", query={"prefix": "a/b", "list-type": "2"})
        first, second = [c.args[0] for c in request.call_args_list]
        self.assertIsNot(first, second)
        self.assertEqual(first.full_url, second.full_url)
        self.assertIn("/a%20b?list-type=2&prefix=a%2Fb", second.full_url)
        self.assertNotEqual(first.get_header("X-amz-date"), second.get_header("X-amz-date"))
        self.assertNotEqual(first.get_header("Authorization"), second.get_header("Authorization"))


if __name__ == "__main__":
    unittest.main()
