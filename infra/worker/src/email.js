// Optional email notifications for the submission portal. Reuses the Resend
// transactional-email pattern from the discussions worker. Notifications are a
// no-op unless RESEND_API_KEY is configured and the contributor has a stored,
// enabled notification email (see notify prefs below).

const NOTIFY_PREFIX = 'notify:';

export function notifyKey(login) {
  return `${NOTIFY_PREFIX}${String(login || '').toLowerCase()}`;
}

export async function getNotifyPrefs(env, login) {
  if (!env.SESSIONS || !login) return { email: null, enabled: false };
  try {
    const raw = await env.SESSIONS.get(notifyKey(login));
    if (!raw) return { email: null, enabled: false };
    const data = JSON.parse(raw);
    return {
      email: data.email || null,
      enabled: data.enabled !== false && Boolean(data.email),
    };
  } catch {
    return { email: null, enabled: false };
  }
}

export async function setNotifyPrefs(env, login, { email, enabled }) {
  if (!env.SESSIONS || !login) return { email: null, enabled: false };
  const current = await getNotifyPrefs(env, login);
  const next = {
    email: email === undefined ? current.email : (email || null),
    enabled: enabled === undefined ? current.enabled : Boolean(enabled),
    updatedAt: Math.floor(Date.now() / 1000),
  };
  if (!next.email) next.enabled = false;
  await env.SESSIONS.put(notifyKey(login), JSON.stringify(next));
  return { email: next.email, enabled: next.enabled };
}

const EVENT_COPY = {
  approved: {
    subject: 'Your study proposal was approved',
    line: 'Your study proposal has been approved. You can now sign in and submit your full draft.',
    cta: 'Submit your draft',
  },
  declined: {
    subject: 'Update on your study proposal',
    line: 'A maintainer has reviewed your study proposal and was not able to accept it. Open the issue to read their comments.',
    cta: 'View the proposal',
  },
  merged: {
    subject: 'Your study pull request was merged',
    line: 'Your study pull request has been merged. The study now appears in the public catalog.',
    cta: 'View the pull request',
  },
};

export async function sendNotificationEmail(env, { to, event, title, url }) {
  const apiKey = env.RESEND_API_KEY;
  if (!apiKey || !to) return { skipped: true };

  const copy = EVENT_COPY[event];
  if (!copy) return { skipped: true };

  const from = env.EMAIL_FROM || 'Submissions <submissions@analyticmadhyasthdarshan.org>';
  const safeTitle = title ? escapeHtml(title) : '';
  const portalUrl = 'https://analyticmadhyasthdarshan.org/Studies/submit.html';
  const linkUrl = url || portalUrl;
  const html = `
    <p>Hello,</p>
    ${safeTitle ? `<p><strong>${safeTitle}</strong></p>` : ''}
    <p>${copy.line}</p>
    <p><a href="${escapeHtml(linkUrl)}">${escapeHtml(copy.cta)}</a></p>
    <p style="color:#666;font-size:13px;">Track all your submissions on <a href="${portalUrl}">My Submissions</a>. You are receiving this because you enabled email notifications on the submission portal.</p>
  `.trim();

  const response = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ from, to: [to], subject: copy.subject, html }),
  });
  const result = await response.json();
  if (!response.ok) {
    throw new Error(result?.message || result?.error || 'Failed to send notification email.');
  }
  return result;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
