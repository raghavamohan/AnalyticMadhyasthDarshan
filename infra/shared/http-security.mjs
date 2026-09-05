// CORS controls response access; writes must also be checked before routing.
// JSON plus an exact trusted Origin rejects simple forms and hostile fetches.
export function rejectUnsafeWrite(request, origins, { machinePath } = {}) {
  if (['GET', 'HEAD', 'OPTIONS'].includes(request.method)) return null;
  const machineRequest = machinePath
    && new URL(request.url).pathname === machinePath
    && !request.headers.has('Cookie') && !request.headers.has('Origin');
  let status;
  let error;
  if (!machineRequest && !origins.includes(request.headers.get('Origin'))) {
    status = 403;
    error = 'Request origin is not allowed.';
  } else if (request.headers.get('Content-Type')?.split(';')[0].trim().toLowerCase() !== 'application/json') {
    status = 415;
    error = 'Use application/json for this request.';
  }
  return status ? new Response(JSON.stringify({ success: false, error }), {
    status, headers: { 'Content-Type': 'application/json' },
  }) : null;
}

export function privateResponse(response, cors = {}) {
  const headers = new Headers(response.headers);
  for (const [name, value] of Object.entries(cors)) headers.set(name, value);
  headers.set('Cache-Control', 'private, no-store');
  headers.set('Pragma', 'no-cache');
  headers.set('Referrer-Policy', 'no-referrer');
  headers.set('X-Content-Type-Options', 'nosniff');
  const vary = new Set((headers.get('Vary') || '').split(',').map(s => s.trim()).filter(Boolean));
  for (const name of ['Origin', 'Cookie']) vary.add(name);
  headers.set('Vary', [...vary].join(', '));
  return new Response(response.body, { status: response.status, statusText: response.statusText, headers });
}
