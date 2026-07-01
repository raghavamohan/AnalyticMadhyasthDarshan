# Security Policy

This repository backs **[AnalyticMadhyasthDarshan.org](https://analyticmadhyasthdarshan.org)** — a
static studies site published from `Studies/`, `References/`, and `Applications/`, plus supporting
Python tooling in `Scripts/` and Cloudflare Worker services in `infra/`.

We take security seriously across three surfaces:

- **The published website and its assets** (studies, catalogs, landing pages, PDFs).
- **Build and lifecycle tooling** in `Scripts/` that runs locally and in CI.
- **Backend services** in `infra/` (Cloudflare Workers for submissions and discussions).

## Supported versions

This project has no released version series; it is continuously published from the default branch.
Security fixes are applied to the current state of the default branch only.

| Branch | Supported |
|--------|-----------|
| `master` (default) | Yes |
| Feature branches / forks | No |

## Reporting a vulnerability

**Please do not report security vulnerabilities through public GitHub issues, discussions, or pull
requests.** Public disclosure before a fix is available puts users at risk.

Instead, report privately through **either** channel:

- **GitHub private vulnerability reporting** (preferred):
  1. Go to the repository's **[Security tab](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/security)**.
  2. Select **Report a vulnerability** to open a private advisory visible only to maintainers.
  3. Include the details below.
- **Email**: [raghavamohan@gmail.com](mailto:raghavamohan@gmail.com) — include the details below, and
  use a subject line beginning with `[SECURITY]`.

### What to include

- A clear description of the issue and the affected area (website, `Scripts/`, or `infra/`).
- Steps to reproduce, a proof of concept, or affected file paths / URLs.
- The impact you believe it has (e.g. data exposure, account takeover, supply-chain risk).
- Any suggested remediation, if you have one.

### What to expect

- **Acknowledgement** of your report within **5 business days**.
- An initial assessment and severity triage within **10 business days**.
- Progress updates through the private advisory until the issue is resolved.
- **Coordinated disclosure**: we will agree on a disclosure timeline with you and credit you in the
  advisory unless you prefer to remain anonymous.

## Scope

### In scope

- Vulnerabilities in the Cloudflare Workers under `infra/` (e.g. submissions and discussions
  workers) — authentication, authorization, injection, secret handling, request forgery.
- Vulnerabilities in `Scripts/` tooling that could enable code execution, path traversal, or
  supply-chain compromise when running the documented workflows.
- Client-side issues on the published site (e.g. stored XSS in study content or catalog rendering).
- Exposure of secrets or credentials committed to the repository.

### Out of scope

- The **philosophical content** of the studies themselves — factual or interpretive corrections go
  through the [study feedback](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/issues/new?template=study-feedback.yml)
  flow, not this policy.
- Vulnerabilities in third-party platforms we depend on (GitHub, Cloudflare, npm, PyPI) — report
  those to the respective vendor. We will still act on any exposure specific to our configuration.
- Reports produced solely by automated scanners with no demonstrated impact.
- Missing security headers or best-practice hardening with no concrete exploit — these are welcome
  as regular issues or pull requests, not as vulnerability reports.

## Handling secrets

If you discover a leaked credential, API token, or private key in this repository or its history,
report it privately as above and do **not** use it. Maintainers will rotate the affected secret and
purge it as needed.

## Safe harbor

We consider good-faith security research that follows this policy to be authorized. We will not
pursue or support legal action against researchers who:

- Make a good-faith effort to avoid privacy violations, data destruction, and service disruption.
- Only interact with accounts they own or have explicit permission to test.
- Report promptly and give us reasonable time to remediate before public disclosure.

Thank you for helping keep this project and its readers safe.
