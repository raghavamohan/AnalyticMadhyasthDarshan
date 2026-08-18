# Web Bot Auth worker (`amd-web-bot-auth`)

Serves the [HTTP Message Signatures Directory](https://datatracker.ietf.org/doc/draft-meunier-http-message-signatures-directory/)
for [Web Bot Auth](https://developers.cloudflare.com/bots/reference/bot-verification/web-bot-auth/)
at `https://analyticmadhyasthdarshan.org/.well-known/http-message-signatures-directory`.

The public JWKS is [`.well-known/http-message-signatures-directory`](../../.well-known/http-message-signatures-directory).
The Worker embeds that JWKS and signs the HTTP response with the matching
Ed25519 private key (`WEB_BOT_AUTH_PRIVATE_JWK` in `.env`, never committed).

Production attaches the zone Workers Route
`analyticmadhyasthdarshan.org/.well-known/http-message-signatures-directory` →
`amd-web-bot-auth`. `--apply-redirect` binds that route and does not 302 to
workers.dev.

Outbound site automation signs requests with `Signature-Agent` and
`Signature-Input` via `Scripts/_web_bot_auth.py`. This site does not crawl other
origins as a verified bot.

## Deploy

From the repository root:

```powershell
python Scripts/_publish_web_bot_auth.py
python Scripts/_test_web_bot_auth.py --live
```

The publish script writes `src/index.js` (gitignored), uploads Worker
`amd-web-bot-auth`, enables the workers.dev host, and upserts the redirect.
