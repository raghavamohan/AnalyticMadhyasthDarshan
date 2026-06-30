const SESSION_COOKIE = 'amd_discuss_session';
const SESSION_MAX_AGE_SEC = 30 * 24 * 60 * 60;

const DEFAULT_ALLOWED_ORIGINS = [
  'https://analyticmadhyasthdarshan.org',
  'http://localhost:8788',
  'http://127.0.0.1:8788',
  'http://localhost:8787',
  'http://127.0.0.1:8787',
];

export function allowedOrigins(env) {
  const extra = (env.ALLOWED_ORIGINS || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
  return [...new Set([...DEFAULT_ALLOWED_ORIGINS, ...extra])];
}

export function corsHeaders(request, env) {
  const origin = request.headers.get('Origin');
  const allowed = allowedOrigins(env);
  const headers = {
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Credentials': 'true',
  };
  if (origin && allowed.includes(origin)) {
    headers['Access-Control-Allow-Origin'] = origin;
    headers['Vary'] = 'Origin';
  }
  return headers;
}

function textEncoder() {
  return new TextEncoder();
}

async function importHmacKey(secret) {
  return crypto.subtle.importKey(
    'raw',
    textEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign', 'verify'],
  );
}

function base64UrlEncode(bytes) {
  let binary = '';
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function base64UrlDecode(str) {
  const padded = str.replace(/-/g, '+').replace(/_/g, '/');
  const pad = padded.length % 4 === 0 ? '' : '='.repeat(4 - (padded.length % 4));
  const binary = atob(padded + pad);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

async function signSession(payload, secret) {
  const header = base64UrlEncode(textEncoder().encode(JSON.stringify({ alg: 'HS256', typ: 'JWT' })));
  const body = base64UrlEncode(textEncoder().encode(JSON.stringify(payload)));
  const data = `${header}.${body}`;
  const key = await importHmacKey(secret);
  const signature = await crypto.subtle.sign('HMAC', key, textEncoder().encode(data));
  return `${data}.${base64UrlEncode(new Uint8Array(signature))}`;
}

async function verifySession(token, secret) {
  const parts = token.split('.');
  if (parts.length !== 3) return null;
  const [header, body, sig] = parts;
  const data = `${header}.${body}`;
  const key = await importHmacKey(secret);
  const expected = await crypto.subtle.sign('HMAC', key, textEncoder().encode(data));
  const actual = base64UrlDecode(sig);
  if (actual.length !== expected.byteLength) return null;
  const a = new Uint8Array(expected);
  let diff = 0;
  for (let i = 0; i < a.length; i++) {
    diff |= a[i] ^ actual[i];
  }
  if (diff !== 0) return null;
  const payload = JSON.parse(new TextDecoder().decode(base64UrlDecode(body)));
  if (!payload.exp || payload.exp < Math.floor(Date.now() / 1000)) return null;
  return payload;
}

function parseCookies(request) {
  const header = request.headers.get('Cookie') || '';
  const cookies = {};
  for (const part of header.split(';')) {
    const [name, ...rest] = part.trim().split('=');
    if (name) cookies[name] = rest.join('=');
  }
  return cookies;
}

function sameSiteValue(env) {
  // Default None preserves cross-origin (workers.dev) deployments. Set
  // COOKIE_SAMESITE=Lax once the worker is routed same-origin with the site.
  const value = ((env && env.COOKIE_SAMESITE) || 'None').trim();
  return value === 'Lax' || value === 'Strict' ? value : 'None';
}

export function sessionCookieOptions(maxAgeSec, env) {
  return `Path=/; HttpOnly; Secure; SameSite=${sameSiteValue(env)}; Max-Age=${maxAgeSec}`;
}

export function setSessionCookie(token, env) {
  return `${SESSION_COOKIE}=${token}; ${sessionCookieOptions(SESSION_MAX_AGE_SEC, env)}`;
}

export function clearSessionCookie(env) {
  return `${SESSION_COOKIE}=; ${sessionCookieOptions(0, env)}`;
}

export async function createSession(env, { userId, email, displayName }) {
  const exp = Math.floor(Date.now() / 1000) + SESSION_MAX_AGE_SEC;
  return signSession({ userId, email, displayName, exp }, env.SESSION_SECRET);
}

export async function getSession(request, env) {
  if (!env.SESSION_SECRET) return null;
  const cookies = parseCookies(request);
  const token = cookies[SESSION_COOKIE];
  if (!token) return null;
  try {
    return await verifySession(token, env.SESSION_SECRET);
  } catch {
    return null;
  }
}

export function requireSession(session) {
  if (!session) {
    const err = new Error('Sign in to post a comment.');
    err.status = 401;
    throw err;
  }
  return session;
}

export function sanitizeReturnTo(returnTo, env) {
  const fallback = env.SITE_ORIGIN || 'https://analyticmadhyasthdarshan.org';
  if (!returnTo) return `${fallback}/Studies/index.html`;
  try {
    const url = new URL(returnTo);
    if (allowedOrigins(env).some((origin) => {
      const allowed = new URL(origin);
      return allowed.origin === url.origin;
    })) {
      return url.href;
    }
  } catch {
    // ignore
  }
  return `${fallback}/Studies/index.html`;
}

export function adminEmails(env) {
  return (env.ADMIN_EMAILS || '')
    .split(',')
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean);
}

export function isAdmin(session, env) {
  if (!session?.email) return false;
  const admins = adminEmails(env);
  return admins.includes(String(session.email).toLowerCase());
}
