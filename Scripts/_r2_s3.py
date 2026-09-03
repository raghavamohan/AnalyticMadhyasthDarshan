"""Small dependency-free AWS Signature V4 client for Cloudflare R2."""
from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import os
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from _common import BASE


def _dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def _first(values: Mapping[str, str], names: tuple[str, ...]) -> str:
    for name in names:
        value = values.get(name, "").strip()
        if value:
            return value
    return ""


@dataclass(frozen=True)
class R2Config:
    endpoint: str
    access_key_id: str
    secret_access_key: str
    bucket: str = ""
    session_token: str = ""
    region: str = "auto"


def load_r2_config(
    environ: Mapping[str, str] | None = None,
    dotenv_path: Path = BASE / ".env",
) -> R2Config:
    values = _dotenv(dotenv_path)
    values.update(dict(os.environ if environ is None else environ))
    config = R2Config(
        endpoint=_first(values, (
            "CLOUDFLARE_R2_ENDPOINT", "R2_ENDPOINT", "AWS_ENDPOINT_URL_S3",
            "AWS_ENDPOINT_URL",
        )).rstrip("/"),
        access_key_id=_first(values, (
            "CLOUDFLARE_R2_ACCESS_KEY_ID", "R2_ACCESS_KEY_ID", "AWS_ACCESS_KEY_ID",
        )),
        secret_access_key=_first(values, (
            "CLOUDFLARE_R2_SECRET_ACCESS_KEY", "R2_SECRET_ACCESS_KEY",
            "AWS_SECRET_ACCESS_KEY",
        )),
        bucket=_first(values, (
            "CLOUDFLARE_R2_BUCKET", "R2_BUCKET", "R2_BUCKET_NAME", "AWS_S3_BUCKET",
        )),
        session_token=_first(values, ("AWS_SESSION_TOKEN",)),
        region=_first(values, ("R2_REGION", "AWS_REGION", "AWS_DEFAULT_REGION")) or "auto",
    )
    if not config.endpoint or not config.access_key_id or not config.secret_access_key:
        raise ValueError(
            "R2 endpoint/access key/secret are required via CLOUDFLARE_R2_*, R2_*, "
            "or AWS_* environment variables"
        )
    parsed = urllib.parse.urlsplit(config.endpoint)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("R2 endpoint must be an absolute https:// URL")
    return config


class R2S3Client:
    def __init__(self, config: R2Config):
        self.config = config
        self._endpoint = urllib.parse.urlsplit(config.endpoint)
        self._resolved_bucket = config.bucket

    @staticmethod
    def _hash(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def _sign(key: bytes, message: str) -> bytes:
        return hmac.new(key, message.encode("utf-8"), hashlib.sha256).digest()

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: bytes = b"",
        headers: Mapping[str, str] | None = None,
        query: Mapping[str, str] | None = None,
        allow_not_found: bool = False,
    ) -> tuple[int, dict[str, str], bytes]:
        now = dt.datetime.now(dt.timezone.utc)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")
        payload_hash = self._hash(body)
        canonical_uri = urllib.parse.quote(path, safe="/-_.~")
        canonical_query = "&".join(
            f"{urllib.parse.quote(str(key), safe='-_.~')}="
            f"{urllib.parse.quote(str(value), safe='-_.~')}"
            for key, value in sorted((query or {}).items())
        )
        request_headers = {key.lower(): " ".join(value.strip().split()) for key, value in (headers or {}).items()}
        request_headers.update({
            "host": self._endpoint.netloc,
            "x-amz-content-sha256": payload_hash,
            "x-amz-date": amz_date,
        })
        if self.config.session_token:
            request_headers["x-amz-security-token"] = self.config.session_token
        signed_names = sorted(request_headers)
        canonical_headers = "".join(f"{name}:{request_headers[name]}\n" for name in signed_names)
        signed_headers = ";".join(signed_names)
        canonical_request = "\n".join((
            method, canonical_uri, canonical_query, canonical_headers,
            signed_headers, payload_hash,
        ))
        scope = f"{date_stamp}/{self.config.region}/s3/aws4_request"
        string_to_sign = "\n".join((
            "AWS4-HMAC-SHA256", amz_date, scope, self._hash(canonical_request.encode()),
        ))
        date_key = self._sign(("AWS4" + self.config.secret_access_key).encode(), date_stamp)
        region_key = self._sign(date_key, self.config.region)
        service_key = self._sign(region_key, "s3")
        signing_key = self._sign(service_key, "aws4_request")
        signature = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()
        request_headers["authorization"] = (
            f"AWS4-HMAC-SHA256 Credential={self.config.access_key_id}/{scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )
        endpoint_path = self._endpoint.path.rstrip("/")
        url = urllib.parse.urlunsplit((
            self._endpoint.scheme, self._endpoint.netloc,
            endpoint_path + canonical_uri, canonical_query, "",
        ))
        request = urllib.request.Request(
            url, data=body if method in {"PUT", "POST"} else None,
            headers=request_headers, method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.status, {k.lower(): v for k, v in response.headers.items()}, response.read()
        except urllib.error.HTTPError as exc:
            if allow_not_found and exc.code == 404:
                return 404, {k.lower(): v for k, v in exc.headers.items()}, b""
            raise RuntimeError(f"R2 S3 request failed: HTTP {exc.code} {exc.reason}") from exc

    def list_buckets(self) -> list[str]:
        _, _, body = self._request("GET", "/")
        root = ET.fromstring(body)
        return [node.text or "" for node in root.findall(".//{*}Bucket/{*}Name") if node.text]

    def bucket(self) -> str:
        if self._resolved_bucket:
            return self._resolved_bucket
        buckets = self.list_buckets()
        if len(buckets) != 1:
            raise RuntimeError(
                "R2 bucket is not configured and the token does not expose exactly one bucket; "
                "set CLOUDFLARE_R2_BUCKET, R2_BUCKET/R2_BUCKET_NAME, or AWS_S3_BUCKET"
            )
        self._resolved_bucket = buckets[0]
        return self._resolved_bucket

    def _object_path(self, key: str) -> str:
        return f"/{self.bucket()}/{key.lstrip('/')}"

    def head_object(self, key: str) -> dict[str, str] | None:
        status, headers, _ = self._request(
            "HEAD", self._object_path(key), allow_not_found=True
        )
        return None if status == 404 else headers

    def put_object(
        self,
        key: str,
        body: bytes,
        *,
        metadata: Mapping[str, str],
        cache_control: str,
        content_disposition: str,
        content_type: str = "application/pdf",
    ) -> dict[str, str]:
        headers = {
            "content-type": content_type,
            "content-length": str(len(body)),
            "cache-control": cache_control,
            "content-disposition": content_disposition,
        }
        headers.update({f"x-amz-meta-{name}": value for name, value in metadata.items()})
        self._request("PUT", self._object_path(key), body=body, headers=headers)
        verified = self.head_object(key)
        if verified is None:
            raise RuntimeError(f"R2 object missing immediately after upload: {key}")
        return verified

    def delete_object(self, key: str) -> None:
        self._request("DELETE", self._object_path(key))

    def list_objects(self, prefix: str) -> list[str]:
        keys: list[str] = []
        continuation = ""
        while True:
            query = {"list-type": "2", "prefix": prefix}
            if continuation:
                query["continuation-token"] = continuation
            _, _, body = self._request(
                "GET", f"/{self.bucket()}", query=query
            )
            root = ET.fromstring(body)
            keys.extend(
                node.text or "" for node in root.findall(".//{*}Contents/{*}Key")
                if node.text
            )
            truncated = (root.findtext(".//{*}IsTruncated") or "").lower() == "true"
            if not truncated:
                break
            continuation = root.findtext(".//{*}NextContinuationToken") or ""
            if not continuation:
                raise RuntimeError("R2 returned a truncated object listing without a continuation token")
        return keys
