export async function sendMagicLinkEmail(env, { to, displayName, verifyUrl }) {
  const apiKey = env.RESEND_API_KEY;
  if (!apiKey) {
    throw new Error('Email is not configured on the server (RESEND_API_KEY missing).');
  }

  const from = env.EMAIL_FROM || 'Discussions <discussions@analyticmadhyasthdarshan.org>';
  const subject = 'Sign in to Analytic Madhyasth Darshan discussions';
  const html = `
    <p>Hello ${escapeHtml(displayName)},</p>
    <p>Click the link below to sign in and post on the study discussion board. This link expires in 15 minutes.</p>
    <p><a href="${escapeHtml(verifyUrl)}">Sign in</a></p>
    <p>If you did not request this email, you can ignore it.</p>
  `.trim();

  const response = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      from,
      to: [to],
      subject,
      html,
    }),
  });

  const result = await response.json();
  if (!response.ok) {
    const message = result?.message || result?.error || 'Failed to send sign-in email.';
    throw new Error(message);
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
