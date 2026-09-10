import { requestIdFor } from './api-errors.mjs';

const UNKNOWN_OPERATION = 'unmatchedRequest';

function boundedLabel(value, fallback = 'none') {
  const label = String(value || fallback).trim();
  return (label || fallback).slice(0, 96);
}

export function operationIdFor(request, routes, fallback = UNKNOWN_OPERATION) {
  const method = request.method.toUpperCase();
  const path = new URL(request.url).pathname.replace(/\/+$/, '') || '/';
  for (const route of routes) {
    if (route.method !== method) continue;
    if (typeof route.path === 'string' ? route.path === path : route.path.test(path)) {
      return route.operationId;
    }
  }
  return fallback;
}

export function withRequestId(request, response) {
  const requestId = requestIdFor(request, response);
  const headers = new Headers(response.headers);
  headers.set('X-Request-ID', requestId);
  headers.delete('Content-Length');
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

export function retryOutcomeFor(request, response) {
  const supplied = response.headers.get('X-AMD-Retry-Outcome');
  if (supplied) return boundedLabel(supplied);
  if (response.status === 429) return 'throttled';
  if (request.method === 'GET' || request.method === 'HEAD') return 'not_applicable';
  if (response.status >= 500) return 'uncertain';
  if (response.status >= 400) return 'rejected';
  return 'accepted';
}

export function recordApiRequest({
  env,
  request,
  response,
  service,
  operationId,
  dependency = 'none',
  startedAt,
}) {
  try {
    const requestId = response.headers.get('X-Request-ID') || 'missing';
    const latencyMs = Math.max(0, Date.now() - startedAt);
    const statusFamily = `${Math.floor(response.status / 100)}xx`;
    const retryOutcome = retryOutcomeFor(request, response);
    const versionId = boundedLabel(env?.CF_VERSION_METADATA?.id, 'unknown');
    const event = {
      event: 'api_request',
      schema: 1,
      service: boundedLabel(service),
      operationId: boundedLabel(operationId, UNKNOWN_OPERATION),
      requestId: boundedLabel(requestId, 'missing'),
      method: request.method,
      status: response.status,
      statusFamily,
      latencyMs,
      dependency: boundedLabel(dependency),
      retryOutcome,
      versionId,
    };
    console.log(JSON.stringify(event));
    env?.API_METRICS?.writeDataPoint({
      indexes: [boundedLabel(service)],
      blobs: [
        'v1',
        event.service,
        event.operationId,
        event.method,
        statusFamily,
        event.dependency,
        retryOutcome,
        versionId,
      ],
      doubles: [1, latencyMs, response.status],
    });
  } catch (error) {
    console.warn(JSON.stringify({
      event: 'api_observation_error',
      schema: 1,
      service: boundedLabel(service),
      operationId: boundedLabel(operationId, UNKNOWN_OPERATION),
      errorType: boundedLabel(error?.name, 'Error'),
    }));
  }
}

export function observedResponse(options) {
  const response = withRequestId(options.request, options.response);
  recordApiRequest({ ...options, response });
  return response;
}

export function readinessStatus(service, checks) {
  const normalized = Object.fromEntries(Object.entries(checks).map(([name, check]) => [
    name,
    {
      status: check.configured ? 'ready' : check.required ? 'degraded' : 'disabled',
      required: Boolean(check.required),
    },
  ]));
  const degraded = Object.values(normalized).some(check => check.required && check.status !== 'ready');
  return {
    status: degraded ? 'degraded' : 'ok',
    service,
    schemaVersion: 1,
    checks: normalized,
  };
}
