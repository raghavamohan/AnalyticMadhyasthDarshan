export const EDGE_RATE_LIMIT_POLICY = '"edge-ip";q=40;w=10';

function httpError(status, message) {
  const error = new Error(message);
  error.status = status;
  return error;
}

export async function readJsonWithin(request, maxBytes) {
  const advertised = request.headers.get('Content-Length');
  if (advertised && Number(advertised) > maxBytes) {
    throw httpError(413, `Request body must be ${maxBytes} bytes or fewer.`);
  }
  const raw = await request.text();
  if (new TextEncoder().encode(raw).byteLength > maxBytes) {
    throw httpError(413, `Request body must be ${maxBytes} bytes or fewer.`);
  }
  try {
    return JSON.parse(raw);
  } catch (_) {
    throw httpError(400, 'Request body must be valid JSON.');
  }
}

export function parsePagination(url, {
  defaultLimit = 50,
  maxLimit = 100,
  maxOffset = 10000,
} = {}) {
  const integer = (name, fallback, min, max) => {
    const raw = url.searchParams.get(name);
    if (raw == null || raw === '') return fallback;
    if (!/^\d+$/.test(raw)) {
      throw httpError(400, `${name} must be an integer from ${min} to ${max}.`);
    }
    const value = Number(raw);
    if (!Number.isSafeInteger(value) || value < min || value > max) {
      throw httpError(400, `${name} must be an integer from ${min} to ${max}.`);
    }
    return value;
  };
  return {
    limit: integer('limit', defaultLimit, 1, maxLimit),
    offset: integer('offset', 0, 0, maxOffset),
  };
}

export function paginationMeta(total, limit, offset) {
  const hasMore = offset + limit < total;
  return {
    total,
    limit,
    offset,
    hasMore,
    nextOffset: hasMore ? offset + limit : null,
  };
}

export function withRateLimitPolicy(response, policy = EDGE_RATE_LIMIT_POLICY) {
  const headers = new Headers(response.headers);
  if (!headers.has('RateLimit-Policy')) headers.set('RateLimit-Policy', policy);
  headers.delete('Content-Length');
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}
