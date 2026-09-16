# Reader analytics

Cloudflare Web Analytics measures reading on analyticmadhyasthdarshan.org.
coexistentialism.org redirects there; it does not represent a separate readership.

The release compiler embeds `infra/site-worker/analytics.js` in HTML before
calculating content hashes and offline manifests. The public site token in that
script is an identifier, not a credential. It loads Cloudflare's beacon only on
the production HTTPS hostname. Reference-library HTML is currently outside this
release transformation and is not covered by this loader.

The loader works with the existing enabled Web Analytics registration and token.
Keep immutable responses marked `no-transform`: automatic injection cannot modify
them or bypass the browser exclusion policy. If delivery changes to allow edge
rewriting, switch Cloudflare to **manual JS snippet installation** first; otherwise
an automatically injected beacon could bypass the opt-out. The CSP already allows `static.cloudflareinsights.com` and
`cloudflareinsights.com`. Never inject analytics into PDF rendering sources or
alter immutable HTML during delivery.

## Exclude maintainer browsing

After the release is published, open this link in each browser/profile used on
the Lenovo laptop and Pixel phone:

[Exclude my visits](https://analyticmadhyasthdarshan.org/Studies/index.html?analytics=off)

Wait for the confirmation saying visits are excluded in this browser. The setting
is saved locally; it follows that browser across IP/network changes. It does not
exclude other readers on the same network or in Bangalore. Repeat for other
browsers, private sessions, or after clearing site data. In-app browsers may have
separate storage and also need the link opened within them.

[Check this browser's setting](https://analyticmadhyasthdarshan.org/Studies/index.html?analytics=status)

[Include future visits again](https://analyticmadhyasthdarshan.org/Studies/index.html?analytics=on)

Preference links show a confirmation and do not record a visit. The preference
parameter is removed from the URL to avoid propagating it in shared links. If
storage is blocked, analytics stays off for that page and the notice explains
that the preference could not be saved.

## Automated checks

The loader skips `navigator.webdriver`, common headless/testing user agents,
offline pages, embedded frames, local/canary hosts, submission/portal pages, and
the personal notebook. Browser tests with unusual configurations must set
`window.__AMD_DISABLE_ANALYTICS__ = true` before page scripts run, or block
Cloudflare Insights requests. Plain HTTP publication audits do not execute JS.

Run `node Scripts/_test_analytics.cjs --browser` for the real-browser check.
Every request in that test is intercepted; it sends no production telemetry.
The policy tests also run inside `python Scripts/_test_site_release.py` in CI.

## Reading the results

Use Web Analytics with **Exclude Bots = Yes** (`bot: 0` in page-load GraphQL
queries). The opt-out prevents new browser beacons; it does not remove historical
visits or raw network/security logs. Bot classification is imperfect, counts may
be sampled estimates, and Cloudflare visits are entrances, not unique people.
Do not use request totals as readership: assets, API calls, monitors, scanners,
and opted-out maintainer browsing still appear there.

After publication, verify the compiled loader is present in a landing page and a
study reader. In an opted-out browser no beacon should load; a normal browser
should load it once. Check fresh page-load data after allowing ingestion time.
The missing September 10–16 data cannot be recovered from Web Analytics.

Cloudflare documents the `no-transform` restriction in its
[Web Analytics setup guide](https://developers.cloudflare.com/web-analytics/get-started/).
