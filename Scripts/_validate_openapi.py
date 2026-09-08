"""Validate every public OpenAPI document and the repository's API conventions.

Install the isolated validator dependency, then run from the repository root:

    python -m pip install -r Scripts/requirements-api.txt
    python Scripts/_validate_openapi.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from openapi_spec_validator import validate


BASE = Path(__file__).resolve().parent.parent
SPEC_PATHS = tuple(sorted((BASE / "openapi").glob("*.json")))
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}
REQUIRED_ERROR_RESPONSES = {
    "400": ("BadRequest", "invalid_request"),
    "401": ("AuthenticationRequired", "authentication_required"),
    "403": ("Forbidden", "forbidden"),
    "409": ("Conflict", "conflict"),
    "413": ("PayloadTooLarge", "payload_too_large"),
    "415": ("UnsupportedMediaType", "unsupported_media_type"),
    "429": ("RateLimited", "rate_limited"),
    "503": ("ServiceUnavailable", "service_unavailable"),
}
ALL_ERROR_RESPONSES = {
    **REQUIRED_ERROR_RESPONSES,
    "404": ("NotFound", "not_found"),
    "405": ("MethodNotAllowed", "method_not_allowed"),
    "500": ("InternalError", "internal_error"),
    "502": ("UpstreamError", "upstream_error"),
}
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def load_spec(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{path.relative_to(BASE)} is not valid JSON: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(BASE)} must contain a JSON object")
    return value


def resolve_local_ref(spec: dict, value: object, location: str) -> dict:
    if not isinstance(value, dict) or set(value) != {"$ref"}:
        fail(f"{location} must be a reusable local response reference")
    ref = value["$ref"]
    prefix = "#/components/responses/"
    if not isinstance(ref, str) or not ref.startswith(prefix):
        fail(f"{location} must reference {prefix}...")
    name = ref[len(prefix):]
    response = ((spec.get("components") or {}).get("responses") or {}).get(name)
    if not isinstance(response, dict):
        fail(f"{location} references missing response component {name!r}")
    return response


def check_error_response(response: dict, status: str, location: str) -> None:
    headers = response.get("headers") or {}
    request_id = headers.get("X-Request-ID")
    if request_id != {"$ref": "#/components/headers/RequestId"}:
        fail(f"{location} must expose the reusable X-Request-ID header")
    media = ((response.get("content") or {}).get("application/json") or {})
    if media.get("schema") != {"$ref": "#/components/schemas/ErrorResponse"}:
        fail(f"{location} must use the ErrorResponse JSON schema")
    example = media.get("example")
    if not isinstance(example, dict):
        fail(f"{location} must include a concrete JSON error example")
    expected_code = ALL_ERROR_RESPONSES[status][1]
    required = {"success", "code", "message", "requestId"}
    if not required.issubset(example):
        fail(f"{location} example omits {sorted(required - set(example))}")
    if example["success"] is not False or example["code"] != expected_code:
        fail(f"{location} example must use success=false and code={expected_code!r}")
    if not isinstance(example["message"], str) or not example["message"]:
        fail(f"{location} example needs a non-empty message")
    if not isinstance(example["requestId"], str) or not REQUEST_ID_RE.fullmatch(example["requestId"]):
        fail(f"{location} example has an invalid requestId")


def check_components(spec: dict, label: str) -> None:
    components = spec.get("components") or {}
    schemas = components.get("schemas") or {}
    error_schema = schemas.get("ErrorResponse") or {}
    required = set(error_schema.get("required") or [])
    if required != {"success", "code", "message", "requestId"}:
        fail(f"{label} ErrorResponse must require success, code, message, and requestId")
    if error_schema.get("additionalProperties") is not False:
        fail(f"{label} ErrorResponse must reject undocumented top-level fields")
    properties = error_schema.get("properties") or {}
    if properties.get("success") != {"type": "boolean", "const": False}:
        fail(f"{label} ErrorResponse.success must be the constant false")
    if "details" not in properties:
        fail(f"{label} ErrorResponse must define optional details")
    request_header = (components.get("headers") or {}).get("RequestId") or {}
    if request_header.get("required") is not True:
        fail(f"{label} RequestId header component must be required")
    responses = components.get("responses") or {}
    for status, (component, _code) in REQUIRED_ERROR_RESPONSES.items():
        response = responses.get(component)
        if not isinstance(response, dict):
            fail(f"{label} is missing reusable {status} response {component}")
        check_error_response(response, status, f"{label} components.responses.{component}")
    rate_limited = responses.get("RateLimited") or {}
    rate_headers = rate_limited.get("headers") or {}
    if rate_headers.get("RateLimit-Policy") != {"$ref": "#/components/headers/RateLimitPolicy"}:
        fail(f"{label} RateLimited must expose the reusable RateLimit-Policy header")
    if rate_headers.get("Retry-After") != {"$ref": "#/components/headers/RetryAfter"}:
        fail(f"{label} RateLimited must expose the reusable Retry-After header")


def check_operations(spec: dict, label: str) -> tuple[int, int]:
    seen_operation_ids: set[str] = set()
    operation_count = 0
    error_count = 0
    paths = spec.get("paths") or {}
    if not paths:
        fail(f"{label} has no paths")
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            fail(f"{label} path {path} must be an object")
        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS:
                continue
            operation_count += 1
            location = f"{label} {method.upper()} {path}"
            if not isinstance(operation, dict):
                fail(f"{location} must be an object")
            operation_id = operation.get("operationId")
            if not isinstance(operation_id, str) or not operation_id:
                fail(f"{location} needs operationId")
            if operation_id in seen_operation_ids:
                fail(f"{label} duplicates operationId {operation_id!r}")
            seen_operation_ids.add(operation_id)
            if not operation.get("summary"):
                fail(f"{location} needs summary")
            responses = operation.get("responses") or {}
            if not any(str(status).startswith(("2", "3")) for status in responses):
                fail(f"{location} needs a success or redirect response")
            if path.startswith("/api/"):
                if responses.get("429") != {"$ref": "#/components/responses/RateLimited"}:
                    fail(f"{location} must document the edge 429 response")
                for status, success_response in responses.items():
                    if not str(status).startswith("2") or not isinstance(success_response, dict):
                        continue
                    if success_response.get("$ref"):
                        continue
                    headers = success_response.get("headers") or {}
                    if headers.get("RateLimit-Policy") != {"$ref": "#/components/headers/RateLimitPolicy"}:
                        fail(f"{location} {status} must advertise RateLimit-Policy")
            request_body = operation.get("requestBody")
            if request_body:
                maximum = request_body.get("x-maxBodyBytes")
                if not isinstance(maximum, int) or maximum < 1:
                    fail(f"{location} requestBody needs a positive x-maxBodyBytes limit")
                if responses.get("413") != {"$ref": "#/components/responses/PayloadTooLarge"}:
                    fail(f"{location} with a request body must document 413")
            for status, response_ref in responses.items():
                status = str(status)
                if not status.startswith(("4", "5")):
                    continue
                if status not in ALL_ERROR_RESPONSES:
                    fail(f"{location} uses unsupported error status {status}")
                expected_component = ALL_ERROR_RESPONSES[status][0]
                expected_ref = f"#/components/responses/{expected_component}"
                if response_ref != {"$ref": expected_ref}:
                    fail(f"{location} {status} must reference {expected_component}")
                response = resolve_local_ref(spec, response_ref, f"{location} {status}")
                check_error_response(response, status, f"{location} {status}")
                error_count += 1
    return operation_count, error_count


def main() -> None:
    if not SPEC_PATHS:
        fail("openapi/ contains no JSON specifications")
    total_operations = 0
    total_errors = 0
    for path in SPEC_PATHS:
        spec = load_spec(path)
        try:
            validate(spec)
        except Exception as exc:
            fail(f"{path.relative_to(BASE)} is not valid OpenAPI: {exc}")
        label = str(path.relative_to(BASE)).replace("\\", "/")
        check_components(spec, label)
        operations, errors = check_operations(spec, label)
        total_operations += operations
        total_errors += errors
        print(f"OK: {label} validates ({operations} operations, {errors} error contracts).")
    print(f"OK: validated {len(SPEC_PATHS)} OpenAPI documents, {total_operations} operations, and {total_errors} documented errors.")


if __name__ == "__main__":
    main()
