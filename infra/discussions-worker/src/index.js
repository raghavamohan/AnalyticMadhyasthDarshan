import { privateResponse, rejectUnsafeWrite } from '../../shared/http-security.mjs';
import { normalizeApiErrorResponse } from '../../shared/api-errors.mjs';
import {
  observedResponse,
  operationIdFor as observedOperationIdFor,
  readinessStatus,
} from '../../shared/api-observability.mjs';
import {
  paginationMeta,
  parsePagination,
  readJsonWithin,
  withRateLimitPolicy,
} from '../../shared/api-contract.mjs';
import { Router } from 'itty-router';
import {
  allowedOrigins,
  clearSessionCookie,
  corsHeaders,
  createSession,
  getSession,
  isAdmin,
  requireSession,
  sanitizeReturnTo,
  setSessionCookie,
} from './auth.js';
import {
  consumeMagicToken,
  countComments,
  countThreadStats,
  ensureThread,
  findOrCreateUser,
  getComment,
  hideComment,
  insertComment,
  listComments,
  listThreadStats,
  magicLinkRateState,
  nowMs,
  storeMagicToken,
} from './db.js';
import { sendMagicLinkEmail } from './email.js';

const router = Router();
const SITEVERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify';
const MAGIC_LINK_TTL_MS = 15 * 60 * 1000;
const MAX_BODY_LENGTH = 8192;
const MAX_DISPLAY_NAME_LENGTH = 80;
const MAX_SLUG_LENGTH = 60;
const MAX_TITLE_LENGTH = 160;
const MAX_EMAIL_LENGTH = 254;
const MAX_RETURN_TO_LENGTH = 2048;
const MAX_TURNSTILE_TOKEN_LENGTH = 4096;
const MAX_JSON_BYTES = 16 * 1024;
const MAGIC_LINK_LIMIT = 5;
const MAGIC_LINK_WINDOW_SECONDS = 3600;
const MAGIC_LINK_POLICY = `"magic-link-email";q=${MAGIC_LINK_LIMIT};w=${MAGIC_LINK_WINDOW_SECONDS}, "edge-ip";q=40;w=10`;
const SLUG_RE = /^[A-Za-z0-9][A-Za-z0-9-]*$/;
const RESERVED_SLUGS = new Set(['health', 'stats']);
const OBSERVABILITY_ROUTES = Object.freeze([
  ['GET', '/api/discussions/health', 'getDiscussionsHealth', 'none'],
  ['GET', '/api/discussions/stats', 'listDiscussionStats', 'd1'],
  ['GET', /^\/api\/discussions\/[A-Za-z0-9-]+$/, 'listComments', 'd1'],
  ['POST', /^\/api\/discussions\/[A-Za-z0-9-]+\/comments$/, 'postComment', 'd1'],
  ['POST', /^\/api\/discussions\/[A-Za-z0-9-]+\/comments\/[^/]+\/hide$/, 'hideComment', 'd1'],
  ['POST', /^\/api\/discussions\/[A-Za-z0-9-]+\/comments\/[^/]+\/delete$/, 'deleteComment', 'd1'],
  ['POST', '/api/discuss-auth/magic-link', 'requestMagicLink', 'd1_resend'],
  ['GET', '/api/discuss-auth/verify', 'verifyMagicLink', 'd1'],
  ['GET', '/api/discuss-auth/me', 'getDiscussAuthMe', 'none'],
  ['POST', '/api/discuss-auth/logout', 'discussLogout', 'none'],
].map(([method, path, operationId, dependency]) => ({method, path, operationId, dependency})));

function discussionReadiness(env) {
  return readinessStatus('discussions', {
    database: { configured: Boolean(env.DB), required: true },
    sessions: { configured: Boolean(env.SESSION_SECRET), required: true },
    turnstile: { configured: Boolean(env.TURNSTILE_SECRET_KEY), required: true },
    email: { configured: Boolean(env.RESEND_API_KEY), required: true },
  });
}
function jsonResponse(request, env, payload, status = 200, extraHeaders = {}) {
  const headers = {
    ...corsHeaders(request, env),
    'Content-Type': 'application/json',
  };
  Object.assign(headers, extraHeaders);
  return new Response(JSON.stringify(payload), {
    status,
    headers,
  });
}

function redirectResponse(url, extraHeaders = {}) {
  return new Response(null, { status: 302, headers: { Location: url, ...extraHeaders } });
}

function requireDb(env) {
  if (!env.DB) {
    const err = new Error('Discussion database is not configured.');
    err.status = 503;
    throw err;
  }
  return env.DB;
}

function httpError(status, message, options = {}) {
  const error = new Error(message);
  error.status = status;
  error.details = options.details;
  error.headers = options.headers;
  return error;
}

function validationError(message) {
  return httpError(400, message);
}

async function readJson(request) {
  return readJsonWithin(request, MAX_JSON_BYTES);
}

function errorPayload(error) {
  return {
    success: false,
    error: error.message,
    ...(error.details ? {details: error.details} : {}),
  };
}

function magicLinkHeaders(used, retryAfter, includeRetryAfter = false) {
  const remaining = Math.max(0, MAGIC_LINK_LIMIT - used);
  return {
    'RateLimit-Policy': MAGIC_LINK_POLICY,
    'RateLimit': `"magic-link-email";r=${remaining};t=${retryAfter}`,
    ...(includeRetryAfter ? {'Retry-After': String(retryAfter)} : {}),
  };
}

function sourceConflict(currentSource, providedSource) {
  return httpError(409, 'The comment changed. Reload the discussion and try again.', {
    details: {currentSource, providedSource: providedSource ?? null},
  });
}

function sourceUpdatedAt(value) {
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed < 0) {
    throw validationError('sourceUpdatedAt must be the current comment source identifier.');
  }
  return parsed;
}

async function verifyTurnstile(token, env, request) {
  if (!env.TURNSTILE_SECRET_KEY) {
    throw httpError(503, 'Turnstile is not configured on the server.');
  }
  if (!token || String(token).length > MAX_TURNSTILE_TOKEN_LENGTH) {
    throw validationError('Turnstile verification is required.');
  }

  const body = new FormData();
  body.append('secret', env.TURNSTILE_SECRET_KEY);
  body.append('response', token);
  const clientIp = request.headers.get('CF-Connecting-IP');
  if (clientIp) {
    body.append('remoteip', clientIp);
  }

  const response = await fetch(SITEVERIFY_URL, { method: 'POST', body });
  const result = await response.json();
  if (!result.success) {
    const codes = (result['error-codes'] || []).join(', ') || 'verification failed';
    throw validationError(`Turnstile verification failed: ${codes}`);
  }
  return result;
}

function sanitizeBody(body) {
  // Store the raw text (including characters like "<" so "a < b" survives).
  // Clients always escape and render this through a safe minimal-Markdown
  // renderer, so no HTML is interpreted from stored comment bodies.
  const text = String(body || '').replace(/\r\n/g, '\n').trim();
  if (!text) {
    throw validationError('Comment cannot be empty.');
  }
  if (text.length > MAX_BODY_LENGTH) {
    throw validationError(`Comment must be at most ${MAX_BODY_LENGTH} characters.`);
  }
  return text;
}

function validateSlug(slug) {
  const value = String(slug || '').trim();
  if (!value || value.length > MAX_SLUG_LENGTH || !SLUG_RE.test(value) || RESERVED_SLUGS.has(value.toLowerCase())) {
    throw validationError('Invalid study slug.');
  }
  return value;
}

function workerOrigin(request) {
  const url = new URL(request.url);
  return `${url.protocol}//${url.host}`;
}

function commentPermissions(row, session, env) {
  const isOwn = Boolean(session?.userId && row.user_id === session.userId);
  const admin = Boolean(session && isAdmin(session, env));
  return {
    canDelete: isOwn,
    canHide: admin && !isOwn,
  };
}

function mapCommentRow(row, session, env) {
  const { canDelete, canHide } = commentPermissions(row, session, env);
  return {
    id: row.id,
    parentId: row.parent_id,
    body: row.body,
    authorName: row.author_name,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
    canDelete,
    canHide,
  };
}

function discussionViewer(session, env) {
  if (!session) return { loggedIn: false };
  return {
    loggedIn: true,
    isAdmin: isAdmin(session, env),
  };
}

router.options('*', (request, env) => new Response(null, { headers: corsHeaders(request, env) }));

router.get('/api/discussions/health', (request, env) => jsonResponse(request, env, discussionReadiness(env)));

router.get('/api/discussions/stats', async (request, env) => {
  try {
    const db = requireDb(env);
    const url = new URL(request.url);
    const {limit, offset} = parsePagination(url);
    const [rows, total] = await Promise.all([
      listThreadStats(db, {limit, offset}),
      countThreadStats(db),
    ]);
    return jsonResponse(request, env, {
      threads: rows.map((row) => ({
        slug: row.slug,
        count: Number(row.count || 0),
        latestAt: Number(row.latest_at || 0),
      })),
      meta: paginationMeta(total, limit, offset),
    });
  } catch (err) {
    return jsonResponse(request, env, { error: err.message }, err.status || 500);
  }
});

router.get('/api/discussions/:slug', async (request, env) => {
  try {
    const db = requireDb(env);
    const slug = validateSlug(request.params.slug);
    const session = await getSession(request, env);
    const url = new URL(request.url);
    const {limit, offset} = parsePagination(url);
    const [comments, total] = await Promise.all([
      listComments(db, slug, {limit, offset}),
      countComments(db, slug),
    ]);
    return jsonResponse(request, env, {
      slug,
      viewer: discussionViewer(session, env),
      comments: comments.map((row) => mapCommentRow(row, session, env)),
      meta: paginationMeta(total, limit, offset),
    });
  } catch (err) {
    return jsonResponse(request, env, { error: err.message }, err.status || 500);
  }
});

router.post('/api/discussions/:slug/comments', async (request, env) => {
  try {
    const session = requireSession(await getSession(request, env));
    const db = requireDb(env);
    const slug = validateSlug(request.params.slug);
    const data = await readJson(request);

    const body = sanitizeBody(data.body);
    const title = String(data.title || slug).trim() || slug;
    if (title.length > MAX_TITLE_LENGTH) {
      throw validationError(`Discussion title must be ${MAX_TITLE_LENGTH} characters or fewer.`);
    }
    await ensureThread(db, slug, title);

    // Only accept a parent that is a visible comment in this same thread;
    // otherwise treat the comment as a new top-level entry.
    let parentId = null;
    if (data.parentId) {
      const parent = await getComment(db, String(data.parentId), slug);
      if (parent && parent.status === 'visible') {
        parentId = parent.id;
      }
    }

    const commentId = crypto.randomUUID();
    const createdAt = await insertComment(db, {
      id: commentId,
      threadSlug: slug,
      parentId,
      userId: session.userId,
      body,
    });

    return jsonResponse(request, env, {
      success: true,
      comment: {
        id: commentId,
        parentId,
        body,
        authorName: session.displayName,
        createdAt,
        updatedAt: createdAt,
        canDelete: true,
        canHide: false,
      },
    }, 201);
  } catch (err) {
    return jsonResponse(request, env, { success: false, error: err.message }, err.status || 500);
  }
});

router.post('/api/discussions/:slug/comments/:commentId/hide', async (request, env) => {
  try {
    const session = requireSession(await getSession(request, env));
    if (!isAdmin(session, env)) {
      const err = new Error('Admin access required.');
      err.status = 403;
      throw err;
    }
    const db = requireDb(env);
    const slug = validateSlug(request.params.slug);
    const data = await readJson(request);
    const expectedUpdatedAt = sourceUpdatedAt(data.sourceUpdatedAt);
    const comment = await getComment(db, request.params.commentId, slug);
    if (!comment || comment.status !== 'visible') {
      const err = new Error('Comment not found.');
      err.status = 404;
      throw err;
    }
    if (Number(comment.updated_at) !== expectedUpdatedAt) {
      throw sourceConflict(Number(comment.updated_at), expectedUpdatedAt);
    }
    if (!await hideComment(db, request.params.commentId, expectedUpdatedAt)) {
      const current = await getComment(db, request.params.commentId, slug);
      throw sourceConflict(current ? Number(current.updated_at) : null, expectedUpdatedAt);
    }
    return jsonResponse(request, env, { success: true });
  } catch (err) {
    return jsonResponse(request, env, errorPayload(err), err.status || 500, err.headers);
  }
});

router.post('/api/discussions/:slug/comments/:commentId/delete', async (request, env) => {
  try {
    const session = requireSession(await getSession(request, env));
    const db = requireDb(env);
    const slug = validateSlug(request.params.slug);
    const data = await readJson(request);
    const expectedUpdatedAt = sourceUpdatedAt(data.sourceUpdatedAt);
    const comment = await getComment(db, request.params.commentId, slug);
    if (!comment || comment.status !== 'visible') {
      const err = new Error('Comment not found.');
      err.status = 404;
      throw err;
    }
    if (comment.user_id !== session.userId) {
      const err = new Error('You can only delete your own comments.');
      err.status = 403;
      throw err;
    }
    if (Number(comment.updated_at) !== expectedUpdatedAt) {
      throw sourceConflict(Number(comment.updated_at), expectedUpdatedAt);
    }
    if (!await hideComment(db, request.params.commentId, expectedUpdatedAt)) {
      const current = await getComment(db, request.params.commentId, slug);
      throw sourceConflict(current ? Number(current.updated_at) : null, expectedUpdatedAt);
    }
    return jsonResponse(request, env, { success: true });
  } catch (err) {
    return jsonResponse(request, env, errorPayload(err), err.status || 500, err.headers);
  }
});

router.post('/api/discuss-auth/magic-link', async (request, env) => {
  try {
    const db = requireDb(env);
    const data = await readJson(request);
    await verifyTurnstile(data.turnstileToken, env, request);

    const email = String(data.email || '').trim().toLowerCase();
    const displayName = String(data.displayName || '').trim();
    if (String(data.returnTo || '').length > MAX_RETURN_TO_LENGTH) {
      throw validationError(`returnTo must be ${MAX_RETURN_TO_LENGTH} characters or fewer.`);
    }
    const returnTo = sanitizeReturnTo(data.returnTo, env);

    if (!email || email.length > MAX_EMAIL_LENGTH || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
      throw validationError('A valid email address is required.');
    }
    if (!displayName || displayName.length > MAX_DISPLAY_NAME_LENGTH) {
      throw validationError(`Display name is required (max ${MAX_DISPLAY_NAME_LENGTH} characters).`);
    }

    const now = nowMs();
    // Tokens expire after 15 minutes, so an expiry newer than now - 45 minutes
    // corresponds to an issuance time inside the rolling one-hour window.
    const rate = await magicLinkRateState(db, email, now - 45 * 60 * 1000, now);
    if (rate.count >= MAGIC_LINK_LIMIT) {
      throw httpError(429, 'Too many sign-in requests. Retry after the indicated delay.', {
        headers: magicLinkHeaders(rate.count, rate.retryAfter, true),
      });
    }

    const token = crypto.randomUUID();
    const expiresAt = nowMs() + MAGIC_LINK_TTL_MS;
    await storeMagicToken(db, { token, email, displayName, expiresAt });

    const verifyUrl = `${workerOrigin(request)}/api/discuss-auth/verify?token=${encodeURIComponent(token)}&return_to=${encodeURIComponent(returnTo)}`;

    if (env.RESEND_API_KEY) {
      await sendMagicLinkEmail(env, { to: email, displayName, verifyUrl });
    } else if (env.DEV_EXPOSE_MAGIC_LINK === 'true') {
      return jsonResponse(request, env, {
        success: true,
        message: 'Magic link generated (dev mode).',
        verifyUrl,
      }, 200, magicLinkHeaders(rate.count + 1, rate.retryAfter));
    } else {
      throw httpError(503, 'Email is not configured on the server.');
    }

    return jsonResponse(request, env, {
      success: true,
      message: 'Check your email for a sign-in link.',
    }, 200, magicLinkHeaders(rate.count + 1, rate.retryAfter));
  } catch (err) {
    return jsonResponse(request, env, errorPayload(err), err.status || 500, err.headers);
  }
});

router.get('/api/discuss-auth/verify', async (request, env) => {
  try {
    const db = requireDb(env);
    const url = new URL(request.url);
    const token = url.searchParams.get('token');
    const returnToParam = url.searchParams.get('return_to');
    if (String(returnToParam || '').length > MAX_RETURN_TO_LENGTH) {
      throw validationError(`return_to must be ${MAX_RETURN_TO_LENGTH} characters or fewer.`);
    }
    const returnTo = sanitizeReturnTo(returnToParam, env);
    if (!token || token.length > 64) {
      throw validationError('Missing sign-in token.');
    }

    const payload = await consumeMagicToken(db, token);
    if (!payload) {
      throw validationError('This sign-in link is invalid or has expired.');
    }

    const user = await findOrCreateUser(db, payload.email, payload.displayName);
    const sessionToken = await createSession(env, {
      userId: user.id,
      email: user.email,
      displayName: user.displayName,
    });

    return redirectResponse(returnTo, { 'Set-Cookie': setSessionCookie(sessionToken, env) });
  } catch (err) {
    const fallback = sanitizeReturnTo(null, env);
    const message = encodeURIComponent(err.message);
    return redirectResponse(`${fallback}?discuss_error=${message}`);
  }
});

router.get('/api/discuss-auth/me', async (request, env) => {
  const session = await getSession(request, env);
  if (!session) {
    return jsonResponse(request, env, { loggedIn: false });
  }
  return jsonResponse(request, env, {
    loggedIn: true,
    email: session.email,
    displayName: session.displayName,
    isAdmin: isAdmin(session, env),
  });
});

router.post('/api/discuss-auth/logout', async (request, env) => {
  return jsonResponse(request, env, { success: true }, 200, {
    'Set-Cookie': clearSessionCookie(env),
  });
});

router.all('*', (request, env) => new Response('Not Found', { status: 404, headers: corsHeaders(request, env) }));

export default {
  async fetch(request, env, ctx) {
    const startedAt = Date.now();
    let response = rejectUnsafeWrite(request, allowedOrigins(env), {});
    if (!response) {
      try {
        response = await router.fetch(request, env, ctx);
      } catch {
        response = new Response(JSON.stringify({ error: 'Request failed. Please try again.' }), {
          status: 500, headers: { 'Content-Type': 'application/json' },
        });
      }
    }
    response = await normalizeApiErrorResponse(request, response);
    response = privateResponse(withRateLimitPolicy(response), corsHeaders(request, env));
    const operationId = observedOperationIdFor(request, OBSERVABILITY_ROUTES);
    const route = OBSERVABILITY_ROUTES.find(item => item.operationId === operationId);
    return observedResponse({
      env,
      request,
      response,
      service: 'discussions',
      operationId,
      dependency: route?.dependency || 'none',
      startedAt,
    });
  },
};
