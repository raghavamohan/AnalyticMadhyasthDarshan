# Google Search Console verification worker

GitHub Pages does not publish `google*.html` files (platform filter), even with `.nojekyll` and `_config.yml` `include`. This worker serves the Search Console token at the required URL on Cloudflare before the request reaches GitHub Pages.

## Deploy

From the repository root (requires `CLOUDFLARE_API_TOKEN` with Workers deploy permission):

```powershell
cd infra/google-verification-worker
npx wrangler deploy
```

Route: `https://analyticmadhyasthdarshan.org/google8e0758eaee6de8ab.html`

After deploy, confirm the body is:

```text
google-site-verification: google8e0758eaee6de8ab.html
```

Then click **Verify** in Google Search Console.

## Alternative

Use **DNS TXT** verification in Cloudflare (no worker): GSC → Domain → DNS TXT record on `@`.
