const STATUS_CODES = Object.freeze({
  400: 'invalid_request',
  401: 'authentication_required',
  403: 'forbidden',
  404: 'not_found',
  405: 'method_not_allowed',
  409: 'conflict',
  413: 'payload_too_large',
  415: 'unsupported_media_type',
  429: 'rate_limited',
  500: 'internal_error',
  502: 'upstream_error',
  503: 'service_unavailable',
});

const REQUEST_ID_RE = /^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$/;

export function errorCodeForStatus(status) {
  return STATUS_CODES[Number(status)] || 'http_error';
}

export function requestIdFor(request, response, payload = {}) {
  const candidates = [
    response?.headers?.get?.('X-Request-ID'),
    payload?.requestId,
    request?.headers?.get?.('X-Request-ID'),
  ];
  const known = candidates.find(value => typeof value === 'string' && REQUEST_ID_RE.test(value));
  return known || crypto.randomUUID();
}

export function errorEnvelope(status, payload = {}, requestId = crypto.randomUUID()) {
  const nested = payload && typeof payload.error === 'object' ? payload.error : {};
  const message = typeof payload?.message === 'string'
    ? payload.message
    : typeof payload?.error === 'string'
      ? payload.error
      : typeof nested.message === 'string'
        ? nested.message
        : `Request failed with HTTP ${status}.`;
  const code = typeof payload?.code === 'string'
    ? payload.code
    : typeof nested.code === 'string'
      ? nested.code
      : errorCodeForStatus(status);
  const reserved = new Set(['success', 'error', 'code', 'message', 'requestId', 'details']);
  const extra = Object.fromEntries(
    Object.entries(payload || {}).filter(([key, value]) => !reserved.has(key) && value !== undefined)
  );
  const explicit = payload?.details && typeof payload.details === 'object' ? payload.details : {};
  const nestedDetails = nested?.details && typeof nested.details === 'object' ? nested.details : {};
  const details = { ...nestedDetails, ...explicit, ...extra };
  return {
    success: false,
    code,
    message,
    requestId,
    ...(Object.keys(details).length ? { details } : {}),
  };
}

export function apiErrorResponse(request, status, message, options = {}) {
  const requestId = requestIdFor(request, null, options);
  const payload = errorEnvelope(status, {
    code: options.code,
    message,
    details: options.details,
  }, requestId);
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'X-Request-ID': requestId,
      ...(options.headers || {}),
    },
  });
}

export async function normalizeApiErrorResponse(request, response) {
  if (!response || response.status < 400) return response;
  const contentType = response.headers.get('Content-Type') || '';
  if (!contentType.toLowerCase().includes('json')) return response;
  let payload;
  try {
    payload = await response.clone().json();
  } catch {
    return response;
  }
  if (!payload || typeof payload !== 'object' || payload.jsonrpc === '2.0') return response;
  const requestId = requestIdFor(request, response, payload);
  const headers = new Headers(response.headers);
  headers.delete('Content-Length');
  headers.set('Content-Type', 'application/json; charset=utf-8');
  headers.set('X-Request-ID', requestId);
  return new Response(JSON.stringify(errorEnvelope(response.status, payload, requestId)), {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}
