// No storage reads, analytics, external assets, or credential use on GET.
export function confirmationPage() {
  const nonce = crypto.randomUUID();
  const html = `<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer"><title>Confirm discussion sign-in</title>
<style nonce="${nonce}">body{font:18px/1.6 Georgia,serif;background:#f7f4ef;color:#2a241c;margin:0}main{max-width:560px;margin:8vh auto;padding:24px}button,a{font:inherit}button{padding:12px 20px;border-radius:8px;background:#1a5276;color:white;border:0;cursor:pointer}button:focus-visible,a:focus-visible{outline:3px solid #b47b46;outline-offset:4px}button:disabled{opacity:.6}p{overflow-wrap:anywhere}</style>
</head><body><main><h1>Confirm discussion sign-in</h1>
<p>This email link signs you in to study discussions. Contributions use a separate GitHub sign-in.</p>
<p id="status" role="status">Confirm only if you requested this email. Your saved comment will not be posted automatically. Continuing replaces any discussion session in this browser.</p>
<button id="confirm" type="button">Confirm email sign-in</button>
<p><a id="back" href="/Studies/index.html">Return to studies</a></p>
<noscript>Enable JavaScript to confirm, or return to the discussion and request a new link.</noscript>
<script nonce="${nonce}">
const params = new URLSearchParams(location.hash.slice(1));
const token = params.get('token') || new URLSearchParams(location.search).get('token');
history.replaceState(null, '', location.pathname);
const button = document.getElementById('confirm'), status = document.getElementById('status');
if (!token || token.length > 64) { button.disabled = true; status.textContent = 'This link is incomplete. Return to the discussion and request a new link.'; }
button.addEventListener('click', async () => {
  button.disabled = true; status.textContent = 'Confirming sign-in…';
  try {
    const response = await fetch('/api/discuss-auth/confirm', {method:'POST', credentials:'include', headers:{'Content-Type':'application/json'}, body:JSON.stringify({token})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || 'Could not confirm sign-in. Request a new link if this one expired.');
    const destination = new URL(data.returnTo, location.origin);
    if (destination.origin !== location.origin) throw new Error('Return to your discussion to continue.');
    location.replace(destination.href);
  } catch (error) { status.textContent = error.message + ' Your browser draft is kept. Return to the original discussion to retry.'; button.disabled = false; }
});
</script></main></body></html>`;
  return new Response(html, {headers:{
    'Content-Type':'text/html; charset=utf-8',
    'Content-Security-Policy':`default-src 'none'; script-src 'nonce-${nonce}'; style-src 'nonce-${nonce}'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'`,
    'X-Frame-Options':'DENY', 'Referrer-Policy':'no-referrer',
  }});
}
