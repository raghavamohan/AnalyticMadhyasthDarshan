# Unified email sign-in and contribution plan

Design status: final implementation baseline; implementation remains pending.
The five phases are Phase 0 (isolation) and Phases 1-4 (product and cutover).
Resource names and credentials are provisioning inputs, not architecture gaps.

## Objective and scope

Readers and contributors use one verified-email account across discussions,
proposals, submissions, corrections, and review replies. No normal contributor
action requires a GitHub account. Maintainers continue reviewing and merging on
GitHub through the existing preparation, verification, and publication pipeline.

The website is under development and has one existing user: the maintainer.
Use a coordinated cutover with explicit reassignment of that user's records.
Do not build a public account-linking system, a multi-user migration service,
or a prolonged dual-login period.

Implementation status and remaining work live only in [PENDING.md](../PENDING.md),
under `AUTH-01`. The phases below define delivery order and acceptance contracts;
they are not a second backlog. This document proposes work, not a completed
implementation or authorization to create production test contributions.

## Architecture decisions

- Put identity in a new `amd-auth` Worker as the sole session authority.
  `amd-discussions` and `amd-submissions` call it over service bindings. Do not
  grow `infra/discussions-worker/src/auth.js` into the shared service in place.
  Preserve existing discussion user IDs and comment ownership. Email is the
  verified sign-in address; an immutable internal user ID owns records. Public
  display names are attribution only and are not authorization.
- Provision an isolated staging stack before Phase 1 acceptance: separate
  Workers, D1, KV/Durable Objects, Resend from-address, Turnstile, and GitHub
  destination. `amd-site-canary` and `workers.dev` fallbacks are not that stack.
  Staging must not access private production identity/mail, mutate production
  GitHub objects, or depend on live production contribution state.
- Put browser authentication and contribution APIs on the website origin. Use
  one host-only, Secure, HttpOnly, SameSite=Lax, Path=/ session cookie
  (`__Host-amd_session`, no Domain attribute, 30-day absolute TTL) and revocable
  server-side sessions. The emailed magic-link URL opens a same-origin confirm
  page; only an explicit POST consumes the token. A GET fetch must not sign in.
- Use D1 for contribution and study ownership, GitHub-object mappings,
  synchronization events, and notification outbox records. GitHub remains
  authoritative for review and merge state. Preserve Durable Objects for
  serialized contribution operations and recovery receipts. Bind `amd-auth` to
  the environment's users/sessions tables so comment `user_id` values remain
  valid; do not create a second production users database that orphans comments.
- Use separate staging and production GitHub App registrations for backend
  writes, installed only on their respective repositories. Contributors do
  not authorize either App. Limit permissions to audited API requirements;
  retain branch protection and maintainer approval.
- Retire the discussion `workers.dev` API fallback when the apex (and staging)
  session cookie is host-only Lax. That fallback cannot receive the cookie.
- Publish opaque contribution IDs and chosen display names. Never use public
  markers as authorization or publish private account IDs, email addresses,
  session data, or email hashes. Check commit attribution for email disclosure.
- Preserve source-version conflicts, idempotent operation handling, preparation
  provenance, immutable-head verification, and protected publication. A merged
  submission and a published study remain different states.
- Keep reading public. GitHub links and direct fork/PR contributions remain
  optional. Incoming email replies and optional GitHub linking are outside scope.

### Repository baseline this plan replaces

The checked-in implementation defines two independent logins on two hosts.
Verify deployed settings during Phase 0; this review did not inspect live secrets
or Cloudflare configuration. The cutover replaces that split.

| Checked-in behavior | Target |
| --- | --- |
| GitHub OAuth on `api.analyticmadhyasthdarshan.org` (`amd_session`, 7 days, KV, user access token) | Email magic link on the website origin |
| Discussion email on apex `/api/discuss-auth/*` (`amd_discuss_session`, 30 days, D1, SameSite default None) | Same `amd-auth` session and cookie |
| `GET /api/discuss-auth/verify` consumes the hashed token | Confirm POST; GET does not consume |
| Site Worker `/api/` pass-through; no service bindings | Explicit `/api/auth/*` routes to `amd-auth`; discussions and submissions bind to it |
| Ownership via `issue.user.login`, `### Portal submitter`, registry `submitter`, and `Portal-GitHub: @login` | Private D1 mapping; public contribution IDs |
| Worker secret `GITHUB_TOKEN` plus contributor OAuth tokens (verify deployed credential type) | GitHub App installation token for portal writes |
| Notify prefs in KV keyed by GitHub login; `portal-notify.yml` uses `issue.user.login` | Account-keyed prefs; resolve recipients from the private mapping |
| Successful magic-link verification can overwrite an existing `display_name` | Display name changes only at first account creation or in account settings |
| No logout-all | Per-account session wipe on `amd-auth` |

Moving the cookie to apex Lax without also moving contribution browser APIs off
`api.` would sign My Submissions out. Those origin, routing, and cookie changes
ship together.

### Service, storage, and routing ownership

`amd-auth` alone creates, validates, and revokes shared sessions and writes
accounts, magic tokens, email-change challenges, and account preferences. Reuse
the existing discussion D1 in production for these tables and comments; staging
uses synthetic users in its own equivalent D1. Discussions retain comment/thread
writes and public-author reads, but remove identity/session mutation paths.
A shared D1 binding grants database access, not enforced table permissions:
this is a code ownership boundary checked in tests. Use one ordered migration
directory and runner for that shared database.

Give submissions a separate environment-specific contribution D1 for ownership,
GitHub objects, events, outbox, and audit records. Validate account IDs through
`amd-auth`; there are no cross-database foreign keys. Retain Durable Objects for
serialized operations. Preferences originate in `amd-auth` in Phase 1; Phase 2
imports the maintainer's KV preferences and connects delivery to them. Do not
create competing preference stores.

The site Worker dispatches explicit allowlisted auth, discussion, and submission
paths through service bindings, preserving browser Origin and Set-Cookie.
Existing public API paths retain their handlers; `/mcp` and discovery remain
intact. Do not forward all `/api/*` to submissions or recursively fetch the same
URL for new routes. Session verification is an internal binding-only method,
not a public endpoint trusting caller-supplied user headers. Reject staging
origins and return destinations in production and vice versa, even though the
hosts are same-site.

Authentication returns current account status/profile and explicit discussion
moderation rights, not stale profile snapshots in sessions. Import `ADMIN_EMAILS`
as a one-time verified-user role assignment at cutover, then key roles by user
ID. Email changes cannot give another account that role. Moderation never implies
publication rights. Check revocation against authoritative storage, not a stale
cache. The new cookie prefix prevents parent-domain cookie shadowing; see the
[cookie-prefix contract](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie).

## Website experience and page changes

The main Studies landing page retains its existing layout, catalog, search,
filters, Start here pathway, and study cards. Reading and browsing remain public.
This is a navigation and contribution update, not a landing-page redesign.

| Surface | Intended behavior | Delivery phase |
| --- | --- | --- |
| Staging host | Isolated website origin for Phases 1–3. Production apex is unchanged until Phase 4. | Phase 0 |
| Main-page header and shared navigation | Show one **Sign in** action when signed out. When signed in, show the public display name and an account menu containing **My Submissions**, **Account settings**, and **Sign out**. | Phase 1; production activation in Phase 4 |
| Sign-in screen | Request email through one common flow. Explain the emailed link, show resend/expiry/error states, and return the reader to the originating page or action after verification. The email link opens a confirm page; signing in requires an explicit action, not a GET. | Phase 1 |
| Account settings | Manage public display name, verified email changes, notification preferences, and sign-out-all. Keep email private. | Phase 1 |
| Contribute section | Use the wording “Contribute using your email address. No GitHub account required.” Provide visible **Propose a study** and **My Submissions** actions, including while signed out. | Phase 2; publish the claim only after the full flow passes Phase 4 acceptance |
| Discussion entry points and composer | Recognize the common session. A signed-in reader can post without a separate discussion login; a signed-out reader returns to preserved text after sign-in. | Phase 1 |
| My Submissions | List the account's proposals and study submissions, with corrections added in Phase 3. Show understandable status and the next available action, with access to saved drafts and interrupted-operation recovery. | Phases 2 and 3 |
| Contribution detail page | Show status, reviewer feedback, a reply box, eligible revision controls, and submission/publication history. Use the website page as the destination for notification links. | Phase 3 |
| Suggest a correction | Open a website form with the study and available passage/section context prefilled. Preserve entered text through sign-in and show the resulting correction in My Submissions. | Phase 3 |
| Repository and source links | Keep GitHub available as an optional source/repository or **View on GitHub** link. No normal contributor action depends on following it. | Phases 2-4 |

Contribution actions remain discoverable while signed out. Prompt for sign-in
when a protected action needs it, then resume that action without submitting it
automatically. Reading never redirects to sign-in. Do not require a reader to
find the account menu before discovering how to contribute.

Use the established typography, colors, navigation, and mobile patterns. Keep
the account control compact and keyboard accessible, with clear focus and menu
state. Show a neutral loading state while checking the session; a session lookup
failure must not block the public catalog. Personalized account data is fetched
privately and must not enter generated HTML, shared caches, or offline bundles.

Landing-page shell changes belong in `Scripts/_build_studies_index.py`, followed
by regeneration and `Scripts/_verify_studies_index.py`. Keep shared Contribute
wording synchronized with `Studies/README.md`. Change other generated discussion
or reader entry points through their canonical producers rather than editing
generated pages individually.

## Expected Issue and PR workflow changes

The study sequence remains: website proposal -> GitHub proposal Issue ->
maintainer approval -> approved-proposal bootstrap -> website submission ->
GitHub PR -> preparation and verification -> review and revisions -> maintainer
merge -> protected publication. Feedback and correction Issues remain distinct
from study proposals; filing a correction does not create an approved study.

| Workflow step | Expected change | Rule that remains in force |
| --- | --- | --- |
| Proposal Issue creation | The repository-installed App creates the Issue instead of the contributor's OAuth token. Include chosen display name and an opaque contribution reference; privately map the Issue to its website owner. | Use `study-proposal` and the existing proposal fields. GitHub objects and submitted content remain public. |
| Approval or decline | Resolve website ownership and notifications from the private mapping, not `issue.user.login`. | Maintainers review and apply the existing `proposal-approved` or `proposal-declined` labels. App authorship does not approve a proposal. |
| Approved-proposal bootstrap | Adapt submitter parsing and proposal-registry handling to contribution references. Preserve the link among proposal, workspace, study, and private owner through slug changes. | Only the existing approved-proposal process establishes the workspace; a contributor cannot approve or bootstrap their own proposal by editing metadata. |
| Submission PR creation | Replace the current maintainer-token integration with the repository App. Add contribution attribution instead of requiring `Portal-GitHub: @login`. | Keep the proposal link and required lifecycle fields, including bare slugs and the applicable `new-study`, `study-update`, or `status-change` label. |
| Preparation and verification | Update portal detection and verification identity inputs for the new metadata; verify every affected event and explicit workflow dispatch. | Portal PRs start temporarily as GitHub draft PRs for preparation and become ready only after the existing exact-head checks succeed. Study Draft/Released status remains separate from GitHub draft-PR state. |
| Maintainer review | Mirror GitHub comments, review summaries, and inline feedback onto the website, retaining their original author and context. | Maintainers conduct formal reviews on GitHub; required approvals and branch protections remain authoritative. |
| Contributor reply | Post website replies through the App with clear contributor attribution and a link/reference to the relevant contribution or comment. | These are contributor comments, never formal approving reviews or maintainer decisions. |
| Revision | An authorized website revision updates the existing eligible PR branch and triggers preparation/verification for its new head. | Retain source-version conflicts and review policy. Support mapped portal PRs for editable submitted source, including updates and companions; never grant rights to arbitrary PRs or create duplicate PRs for review fixes. |
| Merge | Refresh the website's PR state and send the configured notification. | Maintainers merge after required checks and reviews. This change grants no merge or protection-bypass capability to contributors. |
| Publication | Show publication progress or failure separately from merge state. | The protected workflow publishes the coherent site revision; neither sign-in nor a merge notification directly publishes artifacts. |
| Correction Issue | The website creates a `study-feedback` Issue through the App and exposes its conversation and closure in My Submissions. | Maintainers triage the correction. If source changes are needed, they follow the applicable existing PR and verification process; an Issue alone changes no published study. |

### Attribution and authority

GitHub shows the App as author of newly created portal Issues, PRs, and website
replies. Human attribution is recorded separately using the chosen public display
name and contribution reference. Display names are not verified legal identities,
and duplicate names must not affect ownership. Preserve the original authorship
of existing Issues and PRs; adding a reference does not transfer GitHub authorship.

The private mapping authorizes website actions. Public Issue bodies, PR bodies,
labels, and copied contribution references cannot grant ownership. Validate
portal provenance using trusted server records and the existing CI trust
boundaries. Any bridge used by CI must disclose only required contribution
metadata, not private account or email information. App-authored content remains
untrusted contributor input and never grants access to workflow secrets.

Keep original maintainers' GitHub comments distinguishable from contributor
comments relayed by the App. Do not infer a review decision from display-name
text, reply text, or the fact that a bot posted it. The existing direct GitHub
fork/PR path remains supported without requiring portal metadata.

### Workflow trigger and lifecycle acceptance

Phase 2 must audit each producer's actual credential: the existing Worker secret
named `GITHUB_TOKEN`, the new App installation token, and workflow-provided
credentials are distinct. Do not infer their event behavior from a variable name
or assume that changing the token leaves automation triggers identical.

Exercise proposal creation, approval bootstrap, initial PR creation, preparation
commits, ready-for-review transition, revision pushes, verification dispatches,
merge, and publication in staging. Preserve necessary explicit dispatches and
their exact source-SHA binding. Where event and explicit dispatch paths overlap,
ensure they cannot create duplicate bootstrap PRs, preparation writes, or
publication side effects. A missed trigger or missing required check must leave
the contribution visibly blocked, never falsely ready or published.

Phase 3 verifies feedback synchronization and notification delivery, including
edited/deleted comments, duplicate events, and avoidance of bot reply loops.
Phase 4 repeats the agreed production smoke and confirms both existing active
portal records and direct GitHub contributions remain valid.

### One notification path per event

Phase 2 temporarily adapts the existing trusted workflow notification call to a
contribution/object reference, validating repository, event, and ownership before
enqueueing delivery. Phase 3 makes signed webhooks the sole source of GitHub
approval, decline, review, merge, and closure notifications, and disables
`portal-notify.yml` for the new mode. Keep `/api/notify` only as a separately
authenticated internal ingestion path for preparation/publication events not
reliably represented by a GitHub webhook. It accepts validated object/revision
references, never a caller-selected recipient, arbitrary email body, or URL.

Both paths feed one persistent outbox and deduplicate by semantic event identity
as well as webhook delivery ID. Acknowledge a webhook only after durable receipt;
run retries/reconciliation from a scheduled consumer, not a request-lifetime
background task alone. Resolve preferences and verified recipient at send time.
Events that arrive before the GitHub-object mapping is committed remain pending
for reconciliation, rather than dropping the notification or guessing an owner.
Provider timeouts can leave email delivery uncertain; use provider idempotency
where supported and do not promise unconditional exactly-once email delivery.

## API contract changes

Public read APIs remain anonymous and retain their existing URLs, response
schemas, pagination, error handling, and documented cache behavior. Preserve
study search/details, glossary, citations, Start here, public discussion reads,
and read-only MCP tools/resources. The absence of other registered accounts does
not establish that there are no anonymous API consumers.

Authentication and contribution APIs change together with the website client.
They remain interactive human browser workflows using a session cookie and the
applicable origin, Turnstile, and rate controls. This project does not introduce
API keys, agent OAuth, bearer-token access for contributors, or MCP write tools.

| Contract area | Proposed change | Phase |
| --- | --- | --- |
| Public study and discussion reads | Preserve existing read contracts and anonymous access; add regression coverage for routing changes. | Phases 1 and 4 |
| Common authentication | Consolidate magic-link request/confirmation, current account, logout, and logout-all under `/api/auth/`. Retain `/api/auth/me` and `/api/auth/logout` with the new shared identity/session semantics. Specify the explicit token-confirmation request before implementation; a GET link fetch must not consume the token. | Phase 1 |
| Account settings | Define authenticated display-name and preference updates and the verified email-change flow. Separate self-only fields from public author representations. | Phase 1 |
| Browser API origin | Move submission browser calls to `https://analyticmadhyasthdarshan.org`; update OpenAPI server URLs, clients, routing, origin policy, and deployment configuration together. Discussion and public read URLs stay on their documented main-origin paths. | Phases 1-4 |
| Existing contribution actions | Keep action paths such as `/api/propose`, `/api/submit`, `/api/revise`, `/api/status-change`, and `/api/delete-artifact` where practical. Replace GitHub-based authorization and identity fields with private website ownership. Apply the same change to source reads, dashboard/status queries, and receipt lookup. | Phase 2 |
| Identity response schemas | Replace required GitHub `login` fields in self/dashboard responses with an opaque stable account identifier and `displayName`. Derive the acting account from the session, never from a submitted owner ID. Expose private account identifiers only where the authenticated client needs them; use public contribution references for GitHub correlation. | Phases 1 and 2 |
| Contribution details and feedback | Add authenticated detail, paginated feedback/history, and reply operations. Website account data and private recovery state remain owner-scoped even when the underlying GitHub discussion is public. | Phase 3 |
| Corrections | Add a correction creation operation with study/location context, explanation, and suggested change; include the result in the account's contribution list. | Phase 3 |
| Notification integration | Replace login-addressed input with validated contribution/object/revision references. Phase 3 replaces GitHub workflow notifications with webhooks; retain `/api/notify` only for authenticated internal preparation/publication ingestion. Both feed one outbox. | Phases 2-4 |
| GitHub event ingestion | Add a signed server-to-server webhook endpoint with delivery deduplication, payload limits, repository/installation validation, and durable processing. Browser cookies do not authenticate this endpoint. | Phase 3 |
| Health and observability | Adjust dependency readiness and route metrics for shared auth, D1 ownership, and App credentials. Retain useful request IDs and existing public health response fields where possible; never expose credentials or account data. | Phases 1-4 |

### Compatibility and security rules

The target browser and event route inventory is:

| Route | Contract |
| --- | --- |
| `POST /api/auth/magic-link` | Request sign-in mail; generic response, Turnstile and rate limits. |
| `GET /auth/confirm` | Token landing UI, no token consumption or session creation; no third-party scripts or referrer leakage. |
| `POST /api/auth/confirm` | Explicit one-time token consumption and session creation; exact Origin and purpose validation. |
| `GET /api/auth/me` | Current account/session summary or signed-out state. |
| `POST /api/auth/logout` and `/api/auth/logout-all` | Revoke current or all account sessions. |
| `POST /api/auth/profile` | Update the authenticated account's display name. |
| `POST /api/auth/email-change` and `/api/auth/email-change/confirm` | Request and confirm an address change after fresh authentication; separate challenge purpose. |
| `GET` and `POST /api/me/notifications` | Preserve existing route names; delegate preferences to `amd-auth`. |
| `GET /api/contributions/{id}` | Owner-scoped contribution details and allowed actions. |
| `GET /api/contributions/{id}/events` | Paginated review/history data. |
| `POST /api/contributions/{id}/replies` | Owner-scoped, recoverable attributed reply. |
| `POST /api/contributions/{id}/withdraw` | Withdraw a mapped open portal request by closing its GitHub object; never delete a published study or merge. |
| `POST /api/corrections` | Recoverable correction Issue creation. |
| `POST /api/webhooks/github` | Signed server event receipt, not a browser write. |
| `POST /api/notify` | Authenticated internal preparation/publication event receipt after Phase 3. |

Existing study actions and receipt lookup retain their paths. Withdrawal is
idempotent, verifies current GitHub state, rejects already merged requests, and
uses the same receipt/ownership controls as other writes. OpenAPI specifies
schema details and errors alongside each implementing phase.

The session cookie, submission origin, GitHub identity fields, and OAuth routes
are deliberate breaking changes to the authenticated API. Document them in the
OpenAPI release notes and increase the affected specification versions; a new
versioned URL hierarchy is not required solely for this single-user cutover.
Use the route inventory above; publish exact schemas in the implementing phase
before wiring clients. Backend and frontend share the same contracts.

Preserve the current error envelope, `X-Request-ID`, rate-limit headers,
`Retry-After`, field/byte limits, and private/no-store handling for authenticated
responses. Continue returning `401` for missing/expired authentication, enforce
ownership on every protected operation, and retain documented `409` source
conflicts. Preserve client operation IDs, payload matching, receipt states, and
recovery semantics. Apply equivalent durable operation recovery to new correction
and reply writes so interrupted requests cannot blindly duplicate GitHub content.

Disable `/api/auth/github` and the old OAuth callback at cutover. Retire separate
`/api/discuss-auth/*` entry points once all shipped clients use common auth.
If a brief deployment alias is necessary, it must delegate to the same service
and cookie rather than keep a second login implementation. Previously emailed
links may be invalidated with a clear instruction to request a new link.

Do not redirect legacy authenticated POST requests across origins. Update all
first-party clients and internal notification callers; retired write endpoints
should return a documented structured retirement response without performing
side effects. Old browser tabs should prompt a reload while preserving draft
text. Remove host routing only after identifying every remaining public read,
health, or trusted integration caller served there.

### Documentation and API acceptance

Update `openapi/submissions.json` and `openapi/discussions.json` in the phases
that implement their contract changes, including security schemes, cookie names,
server URLs, schemas, examples, and failure responses. Define common auth once
and reference it consistently from both documents. Update `api-docs.html`,
`auth.md`, the API catalog/discovery metadata, Worker guides, and relevant
operational documentation through their canonical sources. Leave
`openapi/studies.json` and MCP read contracts unchanged except for any necessary
descriptive cross-references.

Phase 0 verifies isolation. Phase 1 verifies shared-session contracts, routing,
and unchanged anonymous reads. Phase 2 verifies the existing action/source/dashboard/receipt contracts
under website identity, including negative authorization and interrupted writes.
Phase 3 verifies new correction/reply schemas, pagination, webhook rejection and
deduplication, and trusted notification inputs. Phase 4 checks deployed routes
against published OpenAPI/discovery metadata, proves old authenticated routes
cannot perform writes, and reruns anonymous HTTP and MCP read smoke checks.
No acceptance step may treat updating documentation alone as proof that deployed
routes implement it.

## Phase 0: Isolated staging and `amd-auth` skeleton

**Outcome:** Phases 1–3 run without private production identity/mail access,
production mutations, or live contribution-state dependencies. `amd-auth` has bindings,
even if sign-in UI is still incomplete.

**Dependency:** Confirm the host and repository parameters below. Database
layout is fixed by the architecture contract. Do not start Phase
1 acceptance on production Workers, the production D1, or the public repository.
Local coding and mocked tests can proceed before resource names are confirmed.

### Confirm before provisioning

These are implementation parameters, not extra backlog rows. Record the chosen
values in Worker config and this document when Phase 0 lands.

- **Staging website host.** Prefer `staging.analyticmadhyasthdarshan.org` so the
  session cookie is host-only and cannot collide with apex. Do not use
  `workers.dev` as the Phase 1–3 origin.
- **Isolated GitHub destination.** A standalone private sibling repository,
  seeded with the code, workflows, labels, and fixtures needed for acceptance,
  not `raghavamohan/AnalyticMadhyasthDarshan`. A public repository's fork cannot
  independently become private ([GitHub fork rules](https://docs.github.com/en/pull-requests/reference/forks)).
  Verify Actions and required-check support for that repository's plan. Use a
  separate staging App registration/key with no production installation; sharing
  an App private key across both installations would undermine isolation.
- **Users/sessions database.** In each environment, `amd-auth` and
  `amd-discussions` bind the same users/sessions D1 so existing `comments.user_id`
  values stay valid. Staging gets its own D1. Do not copy users into a second
  production database.

### Implementation

1. Add Wrangler environments and names for staging `amd-auth`,
   `amd-discussions`, and `amd-submissions` (and any staging site shell required
   for browser checks). Give each environment its own D1, KV, Durable Objects,
   `SESSION_SECRET`, Turnstile, and GitHub App credentials. Use a separately
   verified staging sending domain and sending-only key restricted to it (or a
   separate provider account), plus a test-recipient allowlist. A different
   from-address alone is not isolation.
2. Implement explicit staging site routes and service bindings. Parameterize
   repository, branch, site/API URLs, return origins, mail links, and workflow
   dispatch destinations before enabling staging writes. The submission Worker's
   hard-coded `REPO` and workflow-generated production links must not survive
   in the staging execution path.
3. Verify resource inventories, runtime bindings, credential scopes, and mocked
   negative writes; do not attempt production writes to prove denial. Staging
   Workers receive no production resource bindings or account-wide deployment
   tokens. If provisioning credentials cannot be resource-scoped, keep them
   outside runtime and guard deployments with environment allowlists. Public
   production repository reads cannot be prohibited by credential scope; prevent
   production objects from being staging runtime dependencies instead.
4. Isolate staging publication too: R2 objects, release markers, site Worker,
   publication API, analytics, schedules, and workflow deployment credentials.
   Seed permitted fixtures, not private production users/tokens or unreviewed
   third-party assets. Staging merges publish only to staging. Disable copied
   production schedules until destinations are configured and verified.
5. Leave production authentication, contribution routes, generated assets, and
   CI behavior unchanged until coordinated Phase 4 activation.

### Acceptance

- Staging hosts, bindings, and secrets are distinct from production.
- Staging cannot receive the host-only production cookie or shadow it with a
  parent-domain cookie; production rejects the staging Origin.
- Staging App registration, mail scope, storage, and publication destinations
  exclude production; negative tests cause no production side effects.
- `amd-auth` is deployable on staging and reachable over service bindings from
  the staging discussion and submission Workers.
- Production anonymous reads, discussion sign-in, and GitHub OAuth still work.

## Phase 1: One account and session

**Outcome:** One email sign-in establishes the same account in discussions and
the contribution portal, and signing out revokes that session in both.

**Dependency:** Phase 0 isolation accepted on staging.

### Implementation

1. Implement `amd-auth` session, account, and magic-link stores. Preserve
   existing discussion user IDs and comments. Stop overwriting `display_name` on
   every magic-link request; set it on first account creation and through
   account settings only. Initialize verified-user moderation roles from
   `ADMIN_EMAILS` as specified above; never infer publication rights from them.
2. Add explicit same-origin API routing on the staging host and production
   contract (activated in Phase 4). The existing site Worker's generic `/api/`
   handling is not sufficient by itself.
3. Provide common sign-in, session, account, and logout endpoints and shared UI
   under `/api/auth/`. Include a public display name, notification preferences,
   and sign-out-all (per-account session wipe). Implement the header/account
   menu, common sign-in screen, account settings, and discussion entry-point
   behavior specified in the website experience above. Remove the discussion
   client fallback to `*.workers.dev`.
4. Retain hashed, expiring, atomically consumed magic tokens, trusted-origin
   validation, Turnstile, rate limits, and private/no-store responses. The email
   contains a same-origin confirm URL; only POST consumes the token so a link
   scanner cannot sign in by fetching GET. Bind purpose, environment, and allowed
   return path to each 15-minute token. Keep tokens out of logs, analytics,
   referrers, and offline caches. Show the intended account before confirmation
   when another account is signed in; never silently switch accounts.
5. Preserve composer and portal text before sign-in. Version browser storage
   around the stable account ID, with explicit recovery of pre-sign-in drafts
   and no silent assignment of another account's data.
6. Define account email changes using fresh authentication, verification of the
   new address, notice to the old address, and session rotation. Retain ownership
   through the unchanged internal account ID. Invalidate other sessions and
   outstanding old-address challenges on completion; reject already-owned
   addresses instead of silently merging accounts. Test logout-all against
   concurrent sign-in using serialized operations or an account session epoch.

### Acceptance

- One email session is recognized by both features on staging; a second sign-in
  is unnecessary. Production need not switch until Phase 4.
- Logout and sign-out-all revoke access; expired or reused magic links fail
  safely. Link-scanner fetches do not consume credentials.
- Draft text survives sign-in, return navigation, and expired-session recovery.
- Account switching does not expose another account's locally saved workspace.
- Authentication service failure denies protected actions without losing text.
- The Phase 1 API contract and security-scheme updates match running routes;
  existing anonymous HTTP and MCP reads pass regression checks.
- Header and account controls work on desktop and mobile with keyboard focus;
  public reading remains available while signed out or when session lookup fails.
- Sign-in returns to the originating action with text intact and does not submit
  a proposal, comment, or correction automatically.
- A GET of the emailed confirm URL does not create a session. Display name is
  unchanged by requesting a new magic link. Discussion API calls do not use a
  `workers.dev` fallback.

**Boundary:** This phase proves shared authentication. It does not claim that
GitHub-dependent contribution authorization has already been replaced.

## Phase 2: Email-owned contribution lifecycle

**Outcome:** An email-only staging account can propose, submit, revise, and
request study updates, status changes, and removal through the existing pipeline.

**Dependency:** Phase 1's stable account and session contract on staging.

### Implementation

1. Add private contribution, GitHub-object, and study-ownership mappings with
   uniqueness constraints and audit fields. Use a stable study identifier whose
   current slug can change. My Submissions queries owned records, then obtains
   current GitHub state for those known objects. Move notification preferences
   off KV keys of the form `notify:{githubLogin}` onto the website account.
2. Replace username, issue-creator, registry-submitter, and PR-body ownership
   checks with centralized authorization across every protected endpoint.
   Approval still gates first drafts; ownership never grants approval or merge.
   Discussion moderation permissions do not imply publication permissions.
3. Use the GitHub App provisioned on the Phase 0 staging repository; implement
   installation-token acquisition and renewal, and audit permissions against
   actual REST/GraphQL calls and required workflow dispatches. Provision the
   separate production App registration and installation only in Phase 4.
4. Create proposals, branches, PRs, and relevant comments through the App. Add
   contribution references alongside required lifecycle metadata. Update proposal
   bootstrap/registry parsing, preparation/verification identity handling, and
   `portal-notify.yml` / `proposal-approved.yml` recipient parsing in the **same
   change** as App-authored Issues. After that cut, `issue.user.login` is the
   App, not the contributor. An editable marker alone must never establish a
   trusted preparation request. Implement the Issue/PR workflow contract above,
   including a credential and trigger audit before replacing the existing
   backend token.
5. Preserve operation IDs, payload matching, quotas, and source-version checks.
   Write pending intent before GitHub side effects and correlate the result with
   the receipt and ownership index. Reconcile ambiguous outcomes before retrying;
   GitHub creation and D1 updates cannot share a transaction.
6. Keep existing preparation, ready-for-review, review, merge, and publication
   states visible. A publication failure must not be presented as an unsubmitted
   contribution that needs to be sent again.
   Update My Submissions and the landing-page contribution actions accordingly;
   keep actions discoverable while signed out. Stage the revised Contribute copy
   for activation only when all required contributor flows are ready.
7. Close the current revision gap: `/api/revise` handles only open first-draft
   Markdown PRs. Add review fixes on owned portal source/update and companion
   PRs within their original file/action allowlist, preserving baselines and
   regeneration. For status/removal requests, offer discussion and withdrawal;
   a changed target is a new lifecycle request after closure. Unsupported direct
   GitHub branch edits remain the maintainer's responsibility.
8. Prepare a narrowly scoped, dry-run-capable reassignment script listing the
   maintainer's selected issues, PRs, studies, preferences, and operation keys.
   Explicitly handle active Durable Object receipts; changing account keys must
   not make unresolved operations disappear.

### Acceptance

- An account with no GitHub identity performs every supported contribution action
  in staging, including companion submissions and source revision of portal
  update/companion PRs as well as first-draft PRs.
- A second staging account cannot claim records through guessed IDs, forged
  markers, registry text, or display names, or read another account's receipts.
- Repeated clicks, timeouts, and failure after GitHub creation recover the same
  result without creating a duplicate proposal or PR.
- Stale source writes return the existing conflict response rather than overwrite.
- Contribution OpenAPI schemas, identity fields, error and receipt contracts,
  and client requests agree under the new account model and API origin.
- From the main page, an email-only user can find Propose a study and My
  Submissions, sign in if needed, and reach the intended workflow. Dashboard
  statuses and next actions do not require interpreting GitHub terminology.
- Proposal approval, artifact preparation, exact-head verification, merge, and
  publication still pass. App credentials never reach untrusted build execution.
- Every lifecycle trigger and required explicit dispatch in the Issue/PR contract
  runs for the intended source SHA without duplicate side effects. Supported
  revisions update the same PR; direct GitHub PRs still pass their existing path.
- The reassignment dry run reports explicit records and any unresolved receipt;
  it does not assign all repository history to the maintainer implicitly.

## Phase 3: Review conversations and corrections on the website

**Outcome:** Contributors can read reviewer feedback, respond, revise, and
follow a correction entirely on the website.

**Dependency:** Phase 2's ownership mappings and GitHub integration.

### Implementation

1. Add a contribution detail page showing current state, proposal discussion,
   general PR comments, review summaries, inline feedback with file/line context,
   and relevant preparation or publication events. Distinguish outdated feedback.
2. Add a reply box that posts attributed bot comments. Initially a response to
   inline feedback may be a general PR comment referencing the original review
   comment. Sanitize displayed content and apply ownership, size, abuse, and
   operation-recovery controls to new write endpoints.
3. Replace the GitHub correction redirect with a website form that creates the
   existing `study-feedback` issue type. Capture study, location, explanation,
   and suggested correction; show it in My Submissions with its conversation.
4. Receive signed GitHub webhooks. Validate repository and installation identity,
   deduplicate delivery IDs, persist processing state, and reconcile missed or
   out-of-order events through bounded GitHub reads. Process edits/deletions so
   the website does not indefinitely display superseded review content.
5. Extend notifications to meaningful feedback, changes requested, decisions,
   merge, and actionable failures. Resolve recipients privately, use a retryable
   outbox, honor preferences, avoid self-notifications and bot loops, and link to
   the website detail page. Implement the single-producer transition above in
   the same change; do not leave workflow and webhook senders active for the
   same event. Explain that email replies are not supported.

### Acceptance

- A maintainer's GitHub review appears on the website; an email-only contributor
  replies there and the reply appears on GitHub with clear attribution.
- The contributor can revise in response without visiting GitHub.
- GitHub and website views clearly distinguish maintainer review from attributed
  App-posted contributor replies. A reply cannot satisfy a required approval or
  apply a maintainer decision.
- A correction can be submitted, discussed, and followed to closure on the site.
- Correction entry points preserve study/passage context through sign-in; the
  resulting item appears in My Submissions. Notification links open the matching
  website detail page and preserve that destination through sign-in.
- Duplicate events do not duplicate timeline entries or notifications; temporary
  webhook, GitHub, and email failures recover without losing submitted replies.
- No private account data appears in public metadata or notification links.
- New feedback, reply, and correction endpoints match their published schemas;
  forged webhook signatures and unauthorized notification requests are rejected.
- Review notification work does not silently expand into the separate discussion
  report-control/reply-mail scope tracked by `DIS-01`.

## Phase 4: Single-user cutover and retirement of OAuth

**Outcome:** Production has one email sign-in mechanism; the maintainer retains
existing work, and future contributors can participate without GitHub accounts.

**Dependency:** Phase 0 isolation plus Phases 1-3 accepted in staging;
coordinated deployment and an identified production smoke-test mailbox and
disposable contribution record. Confirm the production admin mailbox for
`amd-auth` and the explicit reassignment list.

### Cutover procedure

1. Export valuable local drafts and back up relevant database and mapping data.
   Inventory selected legacy records, preferences, and unresolved operations.
2. Resolve or preserve active operations before changing their account keys.
   Verify the maintainer email account and review the reassignment dry run.
3. Pause legacy contribution, discussion, and identity mutations, including
   magic-link verification and preference changes, while taking the final
   snapshot/reassignment. Keep anonymous reads available. Pause event consumers
   or durably queue deliveries so notification state does not race the mapping.
   Provision production App credentials and deploy additive schema changes and
   compatible Workers/bindings in dependency order.
4. Apply the explicit ownership mapping and update active GitHub records and
   registry metadata needed by the new flow. Preserve closed historical text
   without treating it as authorization. Restore selected drafts explicitly.
5. Activate common routing and UI as one controlled release. Revoke both old
   portal and discussion sessions and outstanding legacy magic links before new
   auth becomes authoritative. A server-side gate admits only the agreed smoke
   account while verifying new writes; then resume normal traffic and queued
   event processing. Do not call an ungated production write a read-only check.
6. Retire OAuth and separate discussion-auth entry points, remove stored OAuth
   tokens and unused OAuth credentials, and remove obsolete authorization code.
   Retire the former portal backend token only after all its consumers are
   audited; do not remove unrelated CI credentials. Clear old apex cookies, and
   clear old `api.` cookies from that host if retained (otherwise let them expire;
   server revocation is authoritative). Keep the new App credentials in use.
7. Update `CONTRIBUTING.md`, `auth.md`, API documentation/OpenAPI, Worker guides,
   contributor-reliability documentation, and affected generated website assets
   through their canonical producers. Verify route inventory and deployed config.

### Acceptance

- Production sign-in, discussion, proposal, submission, feedback, reply, revision,
  correction, and notification behavior matches the staging acceptance results.
- The maintainer's selected historical contributions and drafts remain usable.
- A logged-out browser finds one email sign-in flow and no required GitHub login.
- Main-page navigation, Contribute copy, account settings, discussion controls,
  correction forms, and submission detail pages match the website experience
  contract. Catalog/search/filter/Start here behavior remains intact, shared
  README copy is synchronized, and generated-index verification passes.
- Account details never appear in shared cached pages or offline bundles.
- Safari/iOS and at least one desktop browser complete email return navigation,
  session recovery, and draft preservation; keyboard use and focus are checked.
  This is targeted acceptance, not closure of the full `UX-04` device/AT matrix.
- Existing security, route, receipt, lifecycle, preparation, and publication tests
  pass with new identities, alongside focused negative authorization tests.
- No old OAuth secret or stored user token is required by an active route.
- Deployed API routes and discovery metadata match the new documented contracts;
  retired authenticated endpoints cannot write, and anonymous HTTP/MCP reads
  still pass with their existing URLs and response schemas.

### Recovery boundary

Keep backups and a backend compatible with the new identity schema until cutover
is accepted. If acceptance fails, keep contribution writes disabled while
retaining account access, drafts, and receipt recovery. Do not roll back to a
GitHub-only backend after creating email-owned contributions, and do not restore
a stale database over new writes. Reconcile side effects before resuming.

## Deployment sequencing and final gates

Phases 0-3 deploy only to staging. Commits can land on the main repository only
with production-default behavior preserved: gate Worker routing/configuration,
generated UI/copy, API discovery, and CI selectors, not just browser buttons.
Hold changes that cannot preserve the current deployment for the coordinated
Phase 4 release. Staging serves its updated OpenAPI; do not publish future
contracts as live production documentation before activation. Temporary dual-read
CI metadata support is permitted until active records are reconciled; it does
not introduce a second website login and is removed after cutover acceptance.

Record each phase's tested commit, environment, acceptance evidence, and any
blockers in its PR; only `PENDING.md` tracks open implementation work. Production
activation requires isolation evidence, full lifecycle and two-account negative
tests, a rehearsed recovery, reviewed ownership mapping, and the agreed smoke
record/mailbox. Verify no staging resource identifiers or private data enter the
production release. Confirmation of resource names belongs at provisioning and
does not block local implementation.

## Delivery and sizing

Use a Phase 0 infrastructure PR, then approximately four reviewable
implementation PRs aligned with Phases 1–4; split a phase further if its diff
becomes difficult to review. Merge additive backend support before enabling
dependent UI. Complete the same repository gates as any other change; feature
flags are not substitutes for authorization checks.

The earlier estimate remains a planning range: roughly 35-60 distinct files and
12-20 focused engineering days, including integration, testing, and deployment.
That estimate predates dedicated staging, isolated publication, and expanded
portal revision coverage. It is a historical baseline, not a total or commitment
for this final scope; re-estimate after Phase 0 inventories dependencies.
The single-user reassignment is a
small part of Phase 4; conversation integration and full authorization
replacement are the larger work. Study prose and PDF rendering behavior are
outside this change.

## Implementation map

- Isolation and auth Worker: new `infra/auth-worker/`, environment-specific
  site dispatch/bindings, `Scripts/_worker_deployment.py`, and publication/deploy
  configuration. Parameterize hard-coded repository/host targets in Workers,
  lifecycle scripts, and workflows; isolate staging R2 release storage too.
- Identity consumers: `infra/discussions-worker/src/auth.js`, `db.js`,
  `index.js`, and D1 migrations; preserve `users.id` / `comments.user_id`.
- Contributions: `infra/worker/src/auth.js`, `index.js`, `operations.js`, email
  handling, Worker configuration, and explicit main-origin routing. Durable
  Object receipt keys must remain findable after account reassignment.
- Browser: `Studies/portal/`, `Studies/assets/discuss.js` (remove `workers.dev`
  fallback), portal page sources, and correction-link generators. Follow the
  study-path branch and generation rules when editing these files.
- GitHub/CI: proposal bootstrap and registry code, `prepare-study.yml`,
  `_verification_identity.py`, `_validate_study_change.py`, `proposal-approved.yml`,
  and `portal-notify.yml`; read `.github/CI.md` before workflow changes.
- Verification: existing portal security, API route, contribution receipt, and
  lifecycle tests, extended with isolation, shared-session, ownership-isolation,
  App, webhook, notification, and interrupted-write cases.
- Contracts: submission/discussion OpenAPI and common authentication schemas,
  `api-docs.html`, `auth.md`, discovery producers, and operational documentation;
  publish production contract changes together with activation.

## Related backlog boundaries

`AUTH-01` owns this implementation, beginning with Phase 0 isolation. `UX-05`
supplies the contributor/discussion recovery acceptance requirement. The former
`FBK-01` deferral is superseded by the explicit decision to support corrections
without GitHub login; its work is included in Phase 3 rather than tracked twice.
Coordinate the production write smoke with `API-SMOKE` and lifecycle acceptance
with `R2`. `DIS-01` remains separate except where shared authentication or email
infrastructure is reused.
