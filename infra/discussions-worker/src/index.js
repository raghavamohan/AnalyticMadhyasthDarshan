import { Router } from 'itty-router';
import {
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
  countRecentMagicTokens,
  ensureThread,
  findOrCreateUser,
  getComment,
  hideComment,
  insertComment,
  listComments,
  listThreadStats,
  nowMs,
  storeMagicToken,
} from './db.js';
import { sendMagicLinkEmail } from './email.js';

const router = Router();
const SITEVERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify';
const MAGIC_LINK_TTL_MS = 15 * 60 * 1000;
const MAX_BODY_LENGTH = 8192;
const MAX_DISPLAY_NAME_LENGTH = 80;
const SLUG_RE = /^[A-Za-z0-9][A-Za-z0-9-]*$/;

function jsonResponse(request, env, payload, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { ...corsHeaders(request, env), 'Content-Type': 'application/json', ...extraHeaders },
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

async function verifyTurnstile(token, env, request) {
  if (!env.TURNSTILE_SECRET_KEY) {
    throw new Error('Turnstile is not configured on the server.');
  }
  if (!token) {
    throw new Error('Turnstile verification is required.');
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
    throw new Error(`Turnstile verification failed: ${codes}`);
  }
  return result;
}

function sanitizeBody(body) {
  const text = String(body || '').replace(/\r\n/g, '\n').trim();
  if (!text) {
    throw new Error('Comment cannot be empty.');
  }
  if (text.length > MAX_BODY_LENGTH) {
    throw new Error(`Comment must be at most ${MAX_BODY_LENGTH} characters.`);
  }
  return text.replace(/<[^>]*>/g, '');
}

function validateSlug(slug) {
  const value = String(slug || '').trim();
  if (!value || !SLUG_RE.test(value)) {
    throw new Error('Invalid study slug.');
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

router.options('*', (request, env) => new Response(null, { headers: corsHeaders(request, env) }));

router.get('/api/discussions/stats', async (request, env) => {
  try {
    const db = requireDb(env);
    const rows = await listThreadStats(db);
    return jsonResponse(request, env, {
      threads: rows.map((row) => ({
        slug: row.slug,
        count: Number(row.count || 0),
        latestAt: Number(row.latest_at || 0),
      })),
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
    const limit = Math.min(Number(url.searchParams.get('limit') || 50), 100);
    const offset = Math.max(Number(url.searchParams.get('offset') || 0), 0);
    const comments = await listComments(db, slug, { limit, offset });
    return jsonResponse(request, env, {
      slug,
      comments: comments.map((row) => mapCommentRow(row, session, env)),
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
    const data = await request.json();
    await verifyTurnstile(data.turnstileToken, env, request);

    const body = sanitizeBody(data.body);
    const title = String(data.title || slug).trim() || slug;
    await ensureThread(db, slug, title);

    const commentId = crypto.randomUUID();
    await insertComment(db, {
      id: commentId,
      threadSlug: slug,
      parentId: data.parentId || null,
      userId: session.userId,
      body,
    });

    const createdAt = nowMs();
    return jsonResponse(request, env, {
      success: true,
      comment: {
        id: commentId,
        parentId: data.parentId || null,
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
    const comment = await getComment(db, request.params.commentId, slug);
    if (!comment || comment.status !== 'visible') {
      const err = new Error('Comment not found.');
      err.status = 404;
      throw err;
    }
    await hideComment(db, request.params.commentId);
    return jsonResponse(request, env, { success: true });
  } catch (err) {
    return jsonResponse(request, env, { success: false, error: err.message }, err.status || 500);
  }
});

router.post('/api/discussions/:slug/comments/:commentId/delete', async (request, env) => {
  try {
    const session = requireSession(await getSession(request, env));
    const db = requireDb(env);
    const slug = validateSlug(request.params.slug);
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
    await hideComment(db, request.params.commentId);
    return jsonResponse(request, env, { success: true });
  } catch (err) {
    return jsonResponse(request, env, { success: false, error: err.message }, err.status || 500);
  }
});

router.post('/api/discuss-auth/magic-link', async (request, env) => {
  try {
    const db = requireDb(env);
    const data = await request.json();
    await verifyTurnstile(data.turnstileToken, env, request);

    const email = String(data.email || '').trim().toLowerCase();
    const displayName = String(data.displayName || '').trim();
    const returnTo = sanitizeReturnTo(data.returnTo, env);

    if (!email || !email.includes('@')) {
      throw new Error('A valid email address is required.');
    }
    if (!displayName || displayName.length > MAX_DISPLAY_NAME_LENGTH) {
      throw new Error(`Display name is required (max ${MAX_DISPLAY_NAME_LENGTH} characters).`);
    }

    const recentCount = await countRecentMagicTokens(db, email, nowMs() - 60 * 60 * 1000);
    if (recentCount >= 5) {
      throw new Error('Too many sign-in requests. Try again later.');
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
      });
    } else {
      throw new Error('Email is not configured on the server.');
    }

    return jsonResponse(request, env, {
      success: true,
      message: 'Check your email for a sign-in link.',
    });
  } catch (err) {
    return jsonResponse(request, env, { success: false, error: err.message }, err.status || 500);
  }
});

router.get('/api/discuss-auth/verify', async (request, env) => {
  try {
    const db = requireDb(env);
    const url = new URL(request.url);
    const token = url.searchParams.get('token');
    const returnTo = sanitizeReturnTo(url.searchParams.get('return_to'), env);
    if (!token) {
      throw new Error('Missing sign-in token.');
    }

    const payload = await consumeMagicToken(db, token);
    if (!payload) {
      throw new Error('This sign-in link is invalid or has expired.');
    }

    const user = await findOrCreateUser(db, payload.email, payload.displayName);
    const sessionToken = await createSession(env, {
      userId: user.id,
      email: user.email,
      displayName: user.displayName,
    });

    return redirectResponse(returnTo, { 'Set-Cookie': setSessionCookie(sessionToken) });
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
    'Set-Cookie': clearSessionCookie(),
  });
});

router.all('*', (request, env) => new Response('Not Found', { status: 404, headers: corsHeaders(request, env) }));

export default {
  fetch: (request, env, ctx) => router.fetch(request, env, ctx).catch((err) =>
    new Response(err.message, { status: 500, headers: corsHeaders(request, env) }),
  ),
};
