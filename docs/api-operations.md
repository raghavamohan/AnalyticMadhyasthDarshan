# Public API operations

This runbook covers the study HTTP/MCP runtime, submission runtime, discussion
runtime, and their discovery contracts. Public reads are anonymous. Human
writes continue to use the existing browser sessions; this telemetry does not
introduce bearer tokens, agent OAuth, or A2A operations.

## Initial service objectives

| Operation class | Monthly availability | p95 latency |
|---|---:|---:|
| Public study reads, citation, MCP discovery/tools | 99.9% | 1,000 ms |
| Authenticated dashboard and source reads | 99.5% | 2,500 ms |
| Human write acceptance and operation lookup | 99.0% | 10,000 ms |
| Discussion reads and writes | 99.5% | 2,500 ms |

Availability counts responses that satisfy the operation's documented status
contract. Expected validation, authentication, conflict, and throttling
responses are not availability failures. The authenticated-write objective
excludes a confirmed upstream GitHub or Resend outage, but the dependency must
still be reported as degraded. Revisit the latency thresholds after 30 days of
production data; do not loosen them merely to hide a regression.

## Telemetry contract

All dynamic API responses return `X-Request-ID`. Workers emit a structured
`api_request` record and one `amd_api_metrics` Analytics Engine point. Neither
record contains URLs, query strings, request or response bodies, study drafts,
GitHub tokens, email addresses, cookies, IP addresses, or session identifiers.

Analytics Engine columns are fixed as follows:

| Column | Meaning |
|---|---|
| `index1` | service (`studies`, `submissions`, `discussions`) |
| `blob1` | schema version (`v1`) |
| `blob2` | service |
| `blob3` | OpenAPI operation ID |
| `blob4` | HTTP method |
| `blob5` | status family |
| `blob6` | dominant dependency |
| `blob7` | retry outcome |
| `blob8` | deployed Worker version ID |
| `double1` | request count (1) |
| `double2` | latency in milliseconds |
| `double3` | HTTP status |

Create three dashboard tiles from the Cloudflare Analytics Engine SQL API:

```sql
SELECT blob2 AS service,
       SUM(_sample_interval) AS requests,
       100 * sumIf(_sample_interval, double3 < 500) / SUM(_sample_interval) AS availability,
       quantileExactWeighted(0.95)(double2, _sample_interval) AS p95_ms
FROM amd_api_metrics
WHERE timestamp > NOW() - INTERVAL '1' DAY
GROUP BY service
ORDER BY service
```

```sql
SELECT blob2 AS service, blob3 AS operation_id, blob5 AS status_family,
       SUM(_sample_interval) AS requests,
       quantileExactWeighted(0.95)(double2, _sample_interval) AS p95_ms
FROM amd_api_metrics
WHERE timestamp > NOW() - INTERVAL '1' HOUR
GROUP BY service, operation_id, status_family
ORDER BY service, requests DESC
```

```sql
SELECT blob6 AS dependency, blob7 AS retry_outcome,
       SUM(_sample_interval) AS requests
FROM amd_api_metrics
WHERE timestamp > NOW() - INTERVAL '1' HOUR
  AND (double3 >= 500 OR blob7 IN ('uncertain', 'throttled'))
GROUP BY dependency, retry_outcome
ORDER BY requests DESC
```

The hourly `Production API synthetics` workflow is the first alerting layer. It
opens one deduplicated GitHub issue on failure, attaches a 30-day evidence
artifact with request IDs, comments on continued failures, and closes the issue
after recovery. Alert immediately on any synthetic failure, a required status
check becoming degraded, or a five-minute 5xx rate above 2%. Page the operator
when the condition persists for 15 minutes or when an authenticated write has
an `uncertain` result.

## Incident localization

1. Start from the synthetic evidence or user-provided `X-Request-ID`.
2. Find the structured event in Workers Logs, then note service, operation ID,
   Worker version, dependency, status family, latency, and retry outcome.
3. Check `/api/studies/health`, the submission `/api/health`, and
   `/api/discussions/health`. `degraded` means the runtime is reachable but the
   publication dependency is unavailable or a required binding is
   unconfigured. Provider outages are localized by the synthetic result and
   dependency dimension in telemetry.
4. For contribution writes, inspect `GET /api/operation` with the same receipt.
   Never send a second operation when the result is `inProgress` or `uncertain`.
5. Compare the active publication receipt and the canonical discovery files
   when the failure is classified as publication drift.
6. Record the request ID, UTC time, operation ID, Worker version, dependency,
   mitigation, and recovery workflow run in the incident issue.

## Authenticated production smoke

Automated synthetics deliberately never request a magic link or create a GitHub
issue/PR. After an authentication, write, or recovery change, an operator with
an authorized disposable identity performs this additional check:

1. Sign in through GitHub OAuth, confirm `/api/auth/me`, and record its request
   ID. Submit exactly one agreed disposable proposal or revision. Preserve the
   browser receipt, then verify `GET /api/operation` reaches `complete` and only
   one GitHub item exists.
2. Repeat the operation-result check after reloading the portal. Simulate an
   interrupted response only against the agreed disposable record; verify the
   browser checks the same receipt and does not blindly duplicate the write.
3. Request one discussion magic link to an authorized mailbox, use it once,
   verify `/api/discuss-auth/me`, reload the study, and confirm the session and
   unsent composer text recover. Reusing the link must fail.
4. Log out of both sessions and confirm protected operations return the shared
   cookie-only `401` envelope.
5. Attach a redacted record containing timestamps, request IDs, operation
   receipt, resulting GitHub URL, and pass/fail only. Never attach cookies,
   tokens, email addresses, Turnstile values, or draft content.

Agree the disposable proposal/revision and mailbox before executing this smoke
test. Local fixtures and read-only synthetics are not evidence that the live
OAuth callback, mailbox delivery, or production write path succeeded.
