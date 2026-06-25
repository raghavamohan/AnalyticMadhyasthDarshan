const SESSION_COOKIE = 'amd_session';
const SESSION_MAX_AGE_SEC = 7 * 24 * 60 * 60;
const OAUTH_STATE_COOKIE = 'amd_oauth_state';
const OAUTH_STATE_MAX_AGE_SEC = 600;

const DEFAULT_ALLOWED_ORIGINS = [
  'https://analyticmadhyasthdarshan.org',
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
    ['sign', 'verify']
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

export function sessionCookieOptions(maxAgeSec) {
  return `Path=/; HttpOnly; Secure; SameSite=None; Max-Age=${maxAgeSec}`;
}

export function setSessionCookie(token) {
  return `${SESSION_COOKIE}=${token}; ${sessionCookieOptions(SESSION_MAX_AGE_SEC)}`;
}

export function clearSessionCookie() {
  return `${SESSION_COOKIE}=; ${sessionCookieOptions(0)}`;
}

export function setOAuthStateCookie(value) {
  return `${OAUTH_STATE_COOKIE}=${value}; ${sessionCookieOptions(OAUTH_STATE_MAX_AGE_SEC)}`;
}

export function clearOAuthStateCookie() {
  return `${OAUTH_STATE_COOKIE}=; ${sessionCookieOptions(0)}`;
}

export async function createSession(env, { login, userId, accessToken }) {
  const exp = Math.floor(Date.now() / 1000) + SESSION_MAX_AGE_SEC;
  return signSession({ login, userId, accessToken, exp }, env.SESSION_SECRET);
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

export function parseOAuthState(request) {
  const cookies = parseCookies(request);
  const raw = cookies[OAUTH_STATE_COOKIE];
  if (!raw) return null;
  try {
    return JSON.parse(decodeURIComponent(raw));
  } catch {
    return null;
  }
}

export function buildOAuthState(returnTo) {
  return encodeURIComponent(JSON.stringify({
    nonce: crypto.randomUUID(),
    returnTo: returnTo || 'https://analyticmadhyasthdarshan.org/Studies/submit.html',
  }));
}

export function workerOrigin(request) {
  const url = new URL(request.url);
  return `${url.protocol}//${url.host}`;
}

export function githubAuthorizeUrl(env, request, returnTo) {
  const origin = workerOrigin(request);
  const params = new URLSearchParams({
    client_id: env.GITHUB_CLIENT_ID,
    redirect_uri: `${origin}/api/auth/callback`,
    scope: 'read:user public_repo',
    state: 'via-cookie',
  });
  return `https://github.com/login/oauth/authorize?${params}`;
}

export async function exchangeGitHubCode(code, env, request) {
  const origin = workerOrigin(request);
  const response = await fetch('https://github.com/login/oauth/access_token', {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      client_id: env.GITHUB_CLIENT_ID,
      client_secret: env.GITHUB_CLIENT_SECRET,
      code,
      redirect_uri: `${origin}/api/auth/callback`,
    }),
  });
  const data = await response.json();
  if (data.error) {
    throw new Error(data.error_description || data.error);
  }
  return data.access_token;
}

export async function fetchGitHubUser(accessToken) {
  const response = await fetch('https://api.github.com/user', {
    headers: {
      Authorization: `Bearer ${accessToken}`,
      Accept: 'application/vnd.github.v3+json',
      'User-Agent': 'Cloudflare-Worker-Submission-Portal',
    },
  });
  if (!response.ok) {
    throw new Error('Failed to load GitHub profile');
  }
  return response.json();
}

export function requireSession(session) {
  if (!session) {
    const err = new Error('Sign in with GitHub to continue.');
    err.status = 401;
    throw err;
  }
  return session;
}

export function sanitizeReturnTo(returnTo, env) {
  const fallback = 'https://analyticmadhyasthdarshan.org/Studies/submit.html';
  if (!returnTo) return fallback;
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
  return fallback;
}
