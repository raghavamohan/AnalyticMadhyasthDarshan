import { Router } from 'itty-router';
import {
  buildOAuthState,
  clearOAuthStateCookie,
  clearSessionCookie,
  corsHeaders,
  createSession,
  destroySession,
  exchangeGitHubCode,
  fetchGitHubPrimaryEmail,
  fetchGitHubUser,
  getSession,
  githubAuthorizeUrl,
  parseOAuthState,
  requireSession,
  sanitizeReturnTo,
  setOAuthStateCookie,
  setSessionCookie,
} from './auth.js';
import {
  getNotifyPrefs,
  sendNotificationEmail,
  setNotifyPrefs,
} from './email.js';

const router = Router();
const DEFAULT_BRANCH = 'master';
const SITEVERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify';
const REPO = 'raghavamohan/AnalyticMadhyasthDarshan';
const PORTAL_BASE = 'https://analyticmadhyasthdarshan.org/Studies/submit.html';
const CATALOG_FILES = [
  'Studies/catalog-topical.json',
  'Studies/catalog-formal.json',
  'Studies/catalog-applied.json',
];
// Applied studies live under Applications/<slug>/, every other study under
// Studies/<slug>/. The write-side endpoints resolve the base folder per slug
// from this catalog file.
const CATALOG_APPLIED_FILE = 'Studies/catalog-applied.json';
const CATALOG_CACHE_KEY = 'https://amd-submissions.internal/catalog-slug-map';
const APPLIED_SLUGS_CACHE_KEY = 'https://amd-submissions.internal/applied-slugs';
const PROPOSAL_REGISTRY_PATH = 'Studies/proposal-registry.json';
const PROPOSAL_REGISTRY_CACHE_KEY = 'https://amd-submissions.internal/proposal-registry';
const CHECK_POOL_SIZE = 5;

function jsonResponse(request, env, payload, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { ...corsHeaders(request, env), 'Content-Type': 'application/json', ...extraHeaders },
  });
}

function redirectResponse(url, extraHeaders = {}) {
  return new Response(null, { status: 302, headers: { Location: url, ...extraHeaders } });
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

async function githubRequest(path, method, body, env, userToken = null, stats = null) {
  const url = `https://api.github.com/repos/${REPO}${path}`;
  const token = userToken || env.GITHUB_TOKEN;
  if (stats) stats.githubRequests += 1;
  const options = {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github.v3+json',
      'User-Agent': 'Cloudflare-Worker-Submission-Portal',
    },
  };
  if (body) {
    options.body = JSON.stringify(body);
  }
  const response = await fetch(url, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`GitHub API Error (${response.status}): ${text}`);
  }
  if (response.status === 204) {
    return null;
  }
  return response.json();
}

async function githubSearch(query, env, userToken = null, stats = null) {
  const token = userToken || env.GITHUB_TOKEN;
  const url = `https://api.github.com/search/issues?q=${encodeURIComponent(query)}&per_page=20`;
  if (stats) stats.githubRequests += 1;
  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github.v3+json',
      'User-Agent': 'Cloudflare-Worker-Submission-Portal',
    },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`GitHub search error (${response.status}): ${text}`);
  }
  const data = await response.json();
  return { items: data.items || [], totalCount: data.total_count || 0 };
}

async function githubRawFile(path, env, stats = null) {
  const branch = defaultBranch(env);
  const url = `https://api.github.com/repos/${REPO}/contents/${path}?ref=${branch}`;
  if (stats) stats.githubRequests += 1;
  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: 'application/vnd.github.raw',
      'User-Agent': 'Cloudflare-Worker-Submission-Portal',
    },
  });
  if (!response.ok) {
    throw new Error(`Could not fetch ${path} (${response.status})`);
  }
  return response.text();
}

async function fetchCatalogSlugMap(env, stats) {
  const cache = caches.default;
  const cacheRequest = new Request(CATALOG_CACHE_KEY);
  const cached = await cache.match(cacheRequest);
  if (cached) {
    const parsed = await cached.json();
    return new Map(Object.entries(parsed));
  }

  const texts = await Promise.all(
    CATALOG_FILES.map((file) => githubRawFile(file, env, stats))
  );
  const map = new Map();
  for (const text of texts) {
    const rows = JSON.parse(text);
    for (const row of rows) {
      if (row.slug && row.status) {
        map.set(row.slug, row.status);
      }
    }
  }

  const body = JSON.stringify(Object.fromEntries(map));
  await cache.put(
    cacheRequest,
    new Response(body, { headers: { 'Cache-Control': 'max-age=60' } })
  );
  return map;
}

// Set of slugs registered in the applied catalog. Used to resolve the study's
// markdown path: applied studies live under Applications/, not Studies/.
async function fetchAppliedSlugSet(env, stats) {
  const cache = caches.default;
  const cacheRequest = new Request(APPLIED_SLUGS_CACHE_KEY);
  const cached = await cache.match(cacheRequest);
  if (cached) {
    const parsed = await cached.json();
    return new Set(parsed);
  }

  const slugs = [];
  try {
    const rows = JSON.parse(await githubRawFile(CATALOG_APPLIED_FILE, env, stats));
    for (const row of rows) {
      if (row.slug) slugs.push(row.slug);
    }
  } catch (e) {
    // Applied catalog is optional; treat as empty when unavailable.
  }

  await cache.put(
    cacheRequest,
    new Response(JSON.stringify(slugs), { headers: { 'Cache-Control': 'max-age=60' } })
  );
  return new Set(slugs);
}

// Repository path to a study's markdown source. Applied studies are stored
// under Applications/<slug>/<slug>.md; all others under Studies/<slug>/<slug>.md.
function studyMdPath(slug, appliedSlugs) {
  const base = appliedSlugs && appliedSlugs.has(slug) ? 'Applications' : 'Studies';
  return `${base}/${slug}/${slug}.md`;
}

async function runPool(items, limit, worker) {
  const results = new Array(items.length);
  let index = 0;
  async function runner() {
    while (index < items.length) {
      const i = index;
      index += 1;
      results[i] = await worker(items[i], i);
    }
  }
  const runners = Array.from({ length: Math.min(limit, items.length) }, () => runner());
  await Promise.all(runners);
  return results;
}

function defaultBranch(env) {
  return env.DEFAULT_BRANCH || DEFAULT_BRANCH;
}

async function deleteBranchQuietly(branchName, env, stats = null) {
  try {
    await githubRequest(`/git/refs/heads/${branchName}`, 'DELETE', null, env, null, stats);
  } catch (e) {
    // Best-effort cleanup; ignore failures (branch may not exist yet).
  }
}

function titleToSlug(title) {
  const words = title.trim().match(/[\w']+/g);
  if (!words || words.length === 0) return null;
  return words.map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join('-');
}

function issueLabels(issue) {
  return (issue.labels || []).map((label) =>
    typeof label === 'string' ? label : label.name
  );
}

function proposedTitleFromIssue(issue) {
  const match = (issue.title || '').match(/^Study proposal:\s*(.+)$/i);
  return match ? match[1].trim() : null;
}

function parseIssueFormSection(body, heading) {
  const pattern = new RegExp(
    `###\\s*${heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*\\r?\\n+([\\s\\S]+?)(?=\\r?\\n###|$)`,
    'i'
  );
  const match = (body || '').match(pattern);
  return match ? match[1].trim() : null;
}

function parseSlugFromIssueBody(issue) {
  const fromSection = parseIssueFormSection(issue?.body, 'Slug');
  if (fromSection) {
    const slug = fromSection.split('\n')[0].trim().replace(/\.md$/i, '');
    if (slug) return slug;
  }
  const title = proposedTitleFromIssue(issue);
  return title ? titleToSlug(title) : null;
}

async function fetchProposalRegistry(env, stats) {
  const cache = caches.default;
  const cacheRequest = new Request(PROPOSAL_REGISTRY_CACHE_KEY);
  const cached = await cache.match(cacheRequest);
  if (cached) {
    return cached.json();
  }

  let registry = { version: 1, proposals: [] };
  try {
    const text = await githubRawFile(PROPOSAL_REGISTRY_PATH, env, stats);
    registry = JSON.parse(text);
  } catch (e) {
    // Registry is optional until first bootstrap.
  }

  await cache.put(
    cacheRequest,
    new Response(JSON.stringify(registry), { headers: { 'Cache-Control': 'max-age=60' } })
  );
  return registry;
}

function registryByIssue(registry, issueNumber) {
  const rows = registry?.proposals || [];
  return rows.find((row) => Number(row.issueNumber) === Number(issueNumber)) || null;
}

function registryBySlug(registry, slug) {
  const rows = registry?.proposals || [];
  return rows.find((row) => row.slug === slug) || null;
}

function preCatalogSlugSet(registry) {
  const slugs = new Set();
  for (const row of registry?.proposals || []) {
    if (row.slug && row.phase === 'pre-catalog') {
      slugs.add(row.slug);
    }
  }
  return slugs;
}

function slugForProposal(issue, registry) {
  const fromBody = parseSlugFromIssueBody(issue);
  if (fromBody) return fromBody;
  const linked = registryByIssue(registry, issue?.number);
  return linked?.slug || null;
}

function assertProposalSlugMatch(proposal, slug, registry) {
  const expected = slugForProposal(proposal, registry);
  if (!expected) return;
  if (expected !== slug) {
    throw new Error(
      `Slug must match the approved proposal (${expected}). The portal locks the slug when a proposal is approved.`
    );
  }
}

function buildOpenStudyPrIndex(prItems) {
  const bySlug = new Map();
  for (const item of prItems) {
    if (item.state !== 'open') continue;
    const labels = issueLabels(item);
    const prType = prTypeFromLabels(labels);
    if (!prType || prType === 'status-change') continue;
    const slug = parseSlugFromBody(item.body) || slugFromPrTitle(item.title);
    if (!slug) continue;
    bySlug.set(slug, {
      number: item.number,
      url: item.pull_request?.html_url || item.html_url,
      prType,
    });
  }
  return bySlug;
}

function assertNoOpenStudyPr(slug, openStudyPrs) {
  if (!slug || !openStudyPrs.has(slug)) return;
  const pr = openStudyPrs.get(slug);
  throw new Error(
    `An open ${pr.prType} pull request already exists for "${slug}" (#${pr.number}). Wait for review or close it before opening another.`
  );
}

async function fetchPrReviewState(prNumber, env, userToken, stats) {
  const reviews = await githubRequest(
    `/pulls/${prNumber}/reviews`,
    'GET',
    null,
    env,
    userToken,
    stats
  );
  const list = Array.isArray(reviews) ? reviews : [];
  if (list.some((review) => review.state === 'CHANGES_REQUESTED')) {
    return 'changes_requested';
  }
  return null;
}

async function assertProposalApproved(issueNumber, env, userToken = null) {
  const issue = await githubRequest(`/issues/${issueNumber}`, 'GET', null, env, userToken);
  const labels = issueLabels(issue);
  if (labels.includes('proposal-declined')) {
    throw new Error(
      `Issue #${issueNumber} was declined. Open a new proposal or discuss on the issue before submitting.`
    );
  }
  if (!labels.includes('proposal-approved')) {
    throw new Error(
      `Issue #${issueNumber} is not approved. Wait for maintainers to add the proposal-approved label.`
    );
  }
  return issue;
}

function assertProposalOwner(issue, login) {
  const owner = issue.user?.login;
  const body = issue.body || '';
  const taggedInPortal = body.includes('### Portal submitter') && body.includes(`@${login}`);
  if (owner === login || taggedInPortal) {
    return;
  }
  if (owner) {
    throw new Error(`Issue #${issue.number} belongs to @${owner}. Sign in as that GitHub user to submit.`);
  }
}

function getISTDateString() {
  const now = new Date();
  const options = {
    timeZone: 'Asia/Kolkata',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  };
  let str = new Intl.DateTimeFormat('en-US', options).format(now);
  str = str.replace(' at ', ', ');
  return str + ' IST';
}

function slugToTitle(slug) {
  return slug.split('-').join(' ');
}

function ensureH1Heading(content, slug) {
  if (/^# .+/m.test(content)) {
    return content;
  }
  const trimmed = content.trim();
  const fallbackTitle = slugToTitle(slug);
  if (!trimmed) {
    return `# ${fallbackTitle}\n\n`;
  }
  const newline = trimmed.indexOf('\n');
  const firstLine = (newline === -1 ? trimmed : trimmed.slice(0, newline)).replace(/^#+\s*/, '').trim();
  const heading = firstLine || fallbackTitle;
  const rest = newline === -1 ? '' : trimmed.slice(newline + 1).trimStart();
  return rest ? `# ${heading}\n\n${rest}` : `# ${heading}\n\n`;
}

function applyStudyMetadata(content, author, istTime, slug) {
  content = ensureH1Heading(content, slug);
  if (content.includes('**Author:**')) {
    if (!content.includes('**Edited on:**')) {
      content = content.replace(/(\*\*Author:\*\*.*)(\r?\n)/, `$1$2\n**Edited on:** ${istTime}\n`);
    } else {
      content = content.replace(/\*\*Edited on:\*\*.*(\r?\n|$)/, `**Edited on:** ${istTime}$1`);
    }
  } else if (content.includes('**Edited on:**')) {
    content = content.replace(/\*\*Edited on:\*\*.*(\r?\n|$)/, `**Edited on:** ${istTime}$1`);
    content = content.replace(/^(# .*?)(\r?\n)/, `$1$2\n**Author:** ${author}\n\n`);
  } else {
    content = content.replace(/^(# .*?)(\r?\n)/, `$1$2\n**Author:** ${author}\n\n**Edited on:** ${istTime}\n\n`);
  }
  return content;
}

function setEditedOnLine(content, istTime) {
  if (/\*\*Edited on:\*\*/.test(content)) {
    return content.replace(/\*\*Edited on:\*\*.*(\r?\n|$)/, `**Edited on:** ${istTime}$1`);
  }
  if (/\*\*Author:\*\*/.test(content)) {
    return content.replace(/(\*\*Author:\*\*.*)(\r?\n)/, `$1$2\n**Edited on:** ${istTime}\n`);
  }
  return content;
}

function setStatusLine(content, targetStatus) {
  const label = targetStatus === 'released' ? 'Released' : 'Draft';
  const statusRe = /^\*\*Status:\*\*[ \t]+(?:Draft|Released)[ \t]*$/m;
  if (statusRe.test(content)) {
    return content.replace(statusRe, `**Status:** ${label}`);
  }
  const line = `**Status:** ${label}`;
  if (/\*\*Edited on:\*\*/.test(content)) {
    return content.replace(/(\*\*Edited on:\*\*.*?)(\r?\n)/, `$1$2\n${line}\n`);
  }
  if (/\*\*Author:\*\*/.test(content)) {
    return content.replace(/(\*\*Author:\*\*.*?)(\r?\n)/, `$1$2\n${line}\n`);
  }
  return content.replace(/^(# .*?)(\r?\n)/, `$1$2\n${line}\n`);
}

function decodeBase64Content(encoded) {
  return decodeURIComponent(escape(atob((encoded || '').replace(/\n/g, ''))));
}

function submissionStage(issue, pullRequest, options = {}) {
  const labels = issue ? issueLabels(issue) : [];
  if (labels.includes('proposal-declined')) {
    return 'declined';
  }
  if (pullRequest) {
    if (pullRequest.state === 'open') {
      if (pullRequest.changesRequested) {
        return 'changes_requested';
      }
      return 'pr-open';
    }
    if (pullRequest.merged_at) {
      return 'merged';
    }
    return 'pr-closed';
  }
  if (labels.includes('proposal-approved')) {
    if (options.preCatalog) {
      return 'accepted';
    }
    return 'approved';
  }
  if (issue && issue.state === 'closed' && !labels.includes('proposal-approved')) {
    return 'closed';
  }
  return 'pending';
}

function prStageFromSearchItem(item) {
  if (item.state === 'open') {
    return 'pr-open';
  }
  if (item.pull_request?.merged_at) {
    return 'merged';
  }
  return 'pr-closed';
}

function prTypeFromLabels(labels) {
  if (labels.includes('new-study')) return 'new-study';
  if (labels.includes('study-update')) return 'study-update';
  if (labels.includes('status-change')) return 'status-change';
  return null;
}

function parseProposalIssueFromBody(body) {
  const match = (body || '').match(/Proposal issue:\s*#(\d+)/i);
  return match ? Number(match[1]) : null;
}

function stripMdSuffix(value) {
  const trimmed = value.trim();
  return trimmed.endsWith('.md') ? trimmed.slice(0, -3) : trimmed;
}

// Both `.github/PULL_REQUEST_TEMPLATE/study-update.md` and `status-change.md` use
// "Study slug:"; only `new-study.md` uses plain "Slug:". Check "Study slug:" first for
// every prType (mirroring Scripts/_ci_study_pr.py's handle_study_update, which tries
// `^Study slug:` before falling back to `^Slug:`) so a study-update PR filled in exactly
// as its own template instructs still resolves -- previously only the status-change branch
// recognized "Study slug:", so a template-following study-update PR's slug (and therefore
// its catalog status and dashboard actions) silently failed to resolve.
function parseSlugFromBody(body) {
  const text = body || '';
  const studySlugMatch = text.match(/^Study slug:\s*(.+)$/im);
  if (studySlugMatch) return stripMdSuffix(studySlugMatch[1]);
  const slugMatch = text.match(/^Slug:\s*(.+)$/im);
  return slugMatch ? stripMdSuffix(slugMatch[1]) : null;
}

function slugFromPrTitle(title) {
  const addMatch = (title || '').match(/^Add study:\s*(.+)$/i);
  if (addMatch) return addMatch[1].trim();
  // "Update study: <slug>" is the portal-generated title; "Study update: <slug>" is the
  // PR template's own section heading ("## Study update") and a natural title for a
  // hand-authored PR that follows the template literally -- accept both.
  const updateMatch = (title || '').match(/^(?:Update study|Study update):\s*(.+)$/i);
  if (updateMatch) return updateMatch[1].trim();
  const statusMatch = (title || '').match(/^Status change:\s*(.+?)\s*→/i);
  if (statusMatch) return statusMatch[1].trim();
  return null;
}

function isStudyProposalIssue(issue) {
  const title = issue.title || '';
  if (title.startsWith('Study proposal:')) {
    return true;
  }
  const labels = issueLabels(issue);
  if (labels.includes('study-proposal') || labels.includes('proposal-approved')) {
    return true;
  }
  return (issue.body || '').includes('### Portal submitter');
}

function isPortalPullRequest(item, login) {
  if (!item.pull_request) return false;
  // Only surface the signed-in user's own portal pull requests. Portal PRs are
  // opened by the bot token but tag the submitter as `Portal-GitHub: @<login>`;
  // a PR the user authored directly also counts.
  const taggedInBody = (item.body || '').includes(`Portal-GitHub: @${login}`);
  const authoredByUser = item.user?.login === login;
  if (!taggedInBody && !authoredByUser) return false;
  const labels = issueLabels(item);
  return Boolean(prTypeFromLabels(labels)) || taggedInBody;
}

function summarizePullRequest(prDetails) {
  if (!prDetails) return null;
  return {
    number: prDetails.number,
    url: prDetails.html_url,
    state: prDetails.state,
    merged: Boolean(prDetails.merged_at),
    draft: Boolean(prDetails.draft),
    headSha: prDetails.head?.sha || null,
  };
}

function summarizePullRequestFromSearch(item) {
  if (!item.pull_request) return null;
  return {
    number: item.number,
    url: item.pull_request.html_url || item.html_url,
    state: item.state,
    merged: Boolean(item.pull_request.merged_at),
    draft: false,
    headSha: null,
  };
}

async function aggregateCheckRuns(sha, env, stats) {
  const data = await githubRequest(
    `/commits/${sha}/check-runs?per_page=100`,
    'GET',
    null,
    env,
    null,
    stats
  );
  const runs = (data.check_runs || []).filter((run) =>
    /study\s*pr/i.test(run.name || '') || /study-pr/i.test(run.name || '')
  );
  const relevant = runs.length ? runs : data.check_runs || [];
  if (!relevant.length) {
    return { state: 'pending', summary: null };
  }
  if (relevant.some((run) => run.status !== 'completed')) {
    return { state: 'pending', summary: relevant[0]?.name || 'CI' };
  }
  if (relevant.some((run) => run.conclusion === 'failure' || run.conclusion === 'cancelled' || run.conclusion === 'timed_out')) {
    return { state: 'failure', summary: relevant.find((run) => run.conclusion === 'failure')?.name || relevant[0]?.name };
  }
  if (relevant.every((run) => run.conclusion === 'success' || run.conclusion === 'skipped' || run.conclusion === 'neutral')) {
    return { state: 'success', summary: relevant[0]?.name || 'CI' };
  }
  return { state: 'pending', summary: relevant[0]?.name || 'CI' };
}

function portalUrl(params) {
  const url = new URL(PORTAL_BASE);
  Object.entries(params).forEach(([key, value]) => {
    if (value != null && value !== '') url.searchParams.set(key, String(value));
  });
  return url.toString();
}

function buildOpenStatusChangeIndex(prItems) {
  const bySlug = new Map();
  for (const item of prItems) {
    const labels = issueLabels(item);
    if (!labels.includes('status-change') || item.state !== 'open') continue;
    const slug = parseSlugFromBody(item.body) || slugFromPrTitle(item.title);
    if (slug) {
      bySlug.set(slug, {
        number: item.number,
        url: item.pull_request?.html_url || item.html_url,
      });
    }
  }
  return bySlug;
}

function buildActions(stage, slug, catalogStatus, statusChangeBlocked, issueNumber, studyPrBlocked) {
  const updateUrl = slug ? portalUrl({ tab: 'submit', mode: 'update', slug }) : null;
  const primaryAction = null;
  const secondaryActions = [];

  if (stage === 'pending' && issueNumber) {
    return {
      primaryAction: { label: 'View proposal', href: null, variant: 'secondary', issueOnly: true },
      secondaryActions: [],
      updateUrl,
      statusUrl: null,
    };
  }
  if (stage === 'declined' && issueNumber) {
    return {
      primaryAction: { label: 'View feedback', href: null, variant: 'secondary', issueOnly: true },
      secondaryActions: [],
      updateUrl,
      statusUrl: null,
    };
  }
  if ((stage === 'approved' || stage === 'accepted') && issueNumber) {
    return {
      primaryAction: {
        label: studyPrBlocked ? 'Draft PR in review' : 'Submit draft',
        href: studyPrBlocked ? null : portalUrl({ tab: 'submit', proposal: issueNumber }),
        variant: studyPrBlocked ? 'secondary' : 'primary',
        disabled: studyPrBlocked,
      },
      secondaryActions: [],
      updateUrl,
      statusUrl: null,
    };
  }
  if (stage === 'pr-open' || stage === 'changes_requested') {
    return {
      primaryAction: {
        label: stage === 'changes_requested' ? 'Address review' : 'View pull request',
        href: null,
        variant: 'secondary',
        prOnly: true,
      },
      secondaryActions: [],
      updateUrl,
      statusUrl: null,
    };
  }
  if (stage === 'merged' && slug && catalogStatus && catalogStatus !== 'ongoing') {
    const actions = {
      primaryAction: {
        label: 'Update study',
        href: updateUrl,
        variant: 'primary',
      },
      secondaryActions: [],
      updateUrl,
      statusUrl: portalUrl({ tab: 'status', slug }),
    };
    if (!statusChangeBlocked) {
      if (catalogStatus === 'draft') {
        actions.secondaryActions.push({
          label: 'Release study',
          href: portalUrl({ tab: 'status', slug, target: 'released' }),
          variant: 'secondary',
        });
      } else if (catalogStatus === 'released') {
        actions.secondaryActions.push({
          label: 'Revert to draft',
          href: portalUrl({ tab: 'status', slug, target: 'draft' }),
          variant: 'secondary',
        });
      }
    }
    return actions;
  }
  return { primaryAction, secondaryActions, updateUrl, statusUrl: slug ? portalUrl({ tab: 'status', slug }) : null };
}

function kindLabel(kind, prType) {
  if (kind === 'proposal') return 'Proposal';
  if (prType === 'new-study') return 'New study';
  if (prType === 'study-update') return 'Update';
  if (prType === 'status-change') return 'Status change';
  return 'Pull request';
}

async function listProposalIssues(login, env, userToken, stats) {
  // The REST issues list is immediately consistent (unlike the Search API,
  // which lags by seconds), so a just-submitted proposal shows up right away.
  const perPage = 50;
  const path = `/issues?creator=${encodeURIComponent(login)}&labels=study-proposal&state=all&per_page=${perPage}&sort=created&direction=desc`;
  const items = await githubRequest(path, 'GET', null, env, userToken, stats);
  const list = Array.isArray(items) ? items : [];
  return { items: list, truncated: list.length >= perPage };
}

function submissionRecency(row) {
  return row.pullRequest?.number || row.issueNumber || 0;
}

// Collapse the dashboard to one row per study. A single study accumulates
// several GitHub items over its lifetime — the proposal issue, the new-study
// PR, and every merged status-change / study-update PR (e.g. each draft <->
// released toggle). Only the current state is useful, so for each slug we keep
// a single representative row: the proposal row when one exists (it carries the
// full lifecycle actions and reflects any in-flight PR), otherwise the most
// recent pull request. Rows without a slug (e.g. proposals not yet approved)
// are always kept.
function dedupeSubmissionsBySlug(submissions) {
  const preferred = new Map();
  const keep = (a, b) => {
    if (!a) return b;
    if (!b) return a;
    const aProposal = a.kind === 'proposal';
    const bProposal = b.kind === 'proposal';
    if (aProposal !== bProposal) return aProposal ? a : b;
    return submissionRecency(a) >= submissionRecency(b) ? a : b;
  };
  const result = [];
  for (const row of submissions) {
    if (!row.slug) {
      result.push(row);
      continue;
    }
    preferred.set(row.slug, keep(preferred.get(row.slug), row));
  }
  for (const row of preferred.values()) result.push(row);
  return result;
}

async function buildDashboard(session, env) {
  const started = Date.now();
  const stats = { githubRequests: 0 };
  const login = session.login;
  const userToken = session.accessToken;

  const [proposalList, prSearch, catalogMap, proposalRegistry] = await Promise.all([
    listProposalIssues(login, env, userToken, stats),
    githubSearch(
      `repo:${REPO} is:pr label:new-study,study-update,status-change`,
      env,
      userToken,
      stats
    ),
    fetchCatalogSlugMap(env, stats),
    fetchProposalRegistry(env, stats),
  ]);

  const preCatalogSlugs = preCatalogSlugSet(proposalRegistry);
  const proposals = proposalList.items.filter(isStudyProposalIssue);
  const prItems = prSearch.items.filter((item) => isPortalPullRequest(item, login));
  const openStatusChanges = buildOpenStatusChangeIndex(prItems);
  const openStudyPrs = buildOpenStudyPrIndex(prItems);

  const prByProposal = new Map();
  const prByNumber = new Map();
  for (const item of prItems) {
    prByNumber.set(item.number, item);
    const linked = parseProposalIssueFromBody(item.body);
    if (linked) prByProposal.set(linked, item);
  }

  const usedPrNumbers = new Set();
  const submissions = [];

  for (const issue of proposals) {
    const title = proposedTitleFromIssue(issue) || issue.title;
    const slug = slugForProposal(issue, proposalRegistry);
    const linkedItem = prByProposal.get(issue.number) || null;
    let prDetails = linkedItem ? summarizePullRequestFromSearch(linkedItem) : null;
    if (linkedItem) usedPrNumbers.add(linkedItem.number);

    const preCatalog = Boolean(slug && preCatalogSlugs.has(slug) && !catalogMap.get(slug));
    let stage = submissionStage(issue, linkedItem ? {
      state: linkedItem.state,
      merged_at: linkedItem.pull_request?.merged_at,
    } : null, { preCatalog });
    const catalogStatus = slug ? (catalogMap.get(slug) || (preCatalog ? 'pre-catalog' : null)) : null;
    // A proposal whose study is already published (draft/released in the
    // catalog) is treated as merged so the dashboard offers "Submit new
    // version" and the status toggle, even when no portal PR is linked.
    if (
      (catalogStatus === 'draft' || catalogStatus === 'released') &&
      stage !== 'pr-open' &&
      stage !== 'changes_requested'
    ) {
      stage = 'merged';
    }
    const statusBlocked = slug ? openStatusChanges.has(slug) : false;
    const studyPrBlocked = slug ? openStudyPrs.has(slug) : false;
    const actions = buildActions(
      stage,
      slug,
      catalogStatus,
      statusBlocked,
      issue.number,
      studyPrBlocked
    );

    submissions.push({
      kind: 'proposal',
      prType: linkedItem ? prTypeFromLabels(issueLabels(linkedItem)) : null,
      kindLabel: 'Proposal',
      issueNumber: issue.number,
      title: title || issue.title,
      slug,
      issueUrl: issue.html_url,
      issueState: issue.state,
      approved: issueLabels(issue).includes('proposal-approved'),
      declined: issueLabels(issue).includes('proposal-declined'),
      stage,
      catalogStatus,
      preCatalog,
      studyPrBlocked,
      statusChangeBlocked: statusBlocked,
      statusChangePr: statusBlocked && slug ? openStatusChanges.get(slug) : null,
      studyPr: studyPrBlocked && slug ? openStudyPrs.get(slug) : null,
      pullRequest: prDetails,
      checks: null,
      ...actions,
      submitUrl: portalUrl({ tab: 'submit', proposal: issue.number }),
    });
  }

  for (const item of prItems) {
    if (usedPrNumbers.has(item.number)) continue;
    const labels = issueLabels(item);
    const prType = prTypeFromLabels(labels);
    const slug =
      parseSlugFromBody(item.body) ||
      slugFromPrTitle(item.title);
    const stage = prStageFromSearchItem(item);
    const catalogStatus = slug ? (catalogMap.get(slug) || null) : null;
    const statusBlocked = slug ? openStatusChanges.has(slug) : false;
    const studyPrBlocked = slug ? openStudyPrs.has(slug) : false;
    const actions = buildActions(stage, slug, catalogStatus, statusBlocked, null, studyPrBlocked);

    submissions.push({
      kind: 'pull-request',
      prType,
      kindLabel: kindLabel('pull-request', prType),
      issueNumber: null,
      title: item.title,
      slug,
      issueUrl: item.html_url,
      issueState: item.state,
      approved: false,
      stage,
      catalogStatus,
      preCatalog: Boolean(slug && preCatalogSlugs.has(slug) && !catalogMap.get(slug)),
      studyPrBlocked,
      statusChangeBlocked: statusBlocked,
      statusChangePr: statusBlocked && slug ? openStatusChanges.get(slug) : null,
      studyPr: studyPrBlocked && slug ? openStudyPrs.get(slug) : null,
      pullRequest: summarizePullRequestFromSearch(item),
      checks: null,
      ...actions,
      submitUrl: null,
    });
  }

  const dedupedSubmissions = dedupeSubmissionsBySlug(submissions);

  dedupedSubmissions.sort((a, b) => submissionRecency(b) - submissionRecency(a));

  const openRows = dedupedSubmissions.filter((row) => row.stage === 'pr-open' && row.pullRequest);
  const prDetailsCache = new Map();
  await runPool(openRows, CHECK_POOL_SIZE, async (row) => {
    const num = row.pullRequest.number;
    if (!prDetailsCache.has(num)) {
      const full = await githubRequest(`/pulls/${num}`, 'GET', null, env, userToken, stats);
      prDetailsCache.set(num, full);
    }
    const full = prDetailsCache.get(num);
    const summary = summarizePullRequest(full);
    const reviewState = await fetchPrReviewState(num, env, userToken, stats);
    if (reviewState === 'changes_requested') {
      summary.changesRequested = true;
      if (row.stage === 'pr-open') {
        row.stage = 'changes_requested';
      }
    }
    row.pullRequest = summary;
  });

  await runPool(openRows, CHECK_POOL_SIZE, async (row) => {
    const sha = row.pullRequest?.headSha;
    if (!sha) {
      row.checks = { state: null, url: `${row.pullRequest.url}/checks`, summary: null };
      return;
    }
    const summary = await aggregateCheckRuns(sha, env, stats);
    row.checks = {
      state: summary.state,
      url: `${row.pullRequest.url}/checks`,
      summary: summary.summary,
    };
  });

  const truncated = proposalList.truncated || prSearch.totalCount > 20;

  return {
    login,
    submissions: dedupedSubmissions,
    meta: {
      timingMs: Date.now() - started,
      githubRequests: stats.githubRequests,
      truncated,
    },
  };
}

function catalogStatusForSlug(slug, catalogMap) {
  const status = catalogMap.get(slug);
  if (!status) {
    throw new Error(
      `Study "${slug}" is not in the public catalog yet. Submit and merge a draft pull request first.`
    );
  }
  return status;
}

function assertStatusChangeAllowed(slug, targetStatus, catalogMap, prItems) {
  const current = catalogStatusForSlug(slug, catalogMap);
  if (current === targetStatus) {
    throw new Error(`"${slug}" is already ${targetStatus}.`);
  }
  const open = buildOpenStatusChangeIndex(prItems);
  if (open.has(slug)) {
    const pr = open.get(slug);
    throw new Error(`A status-change pull request is already open for "${slug}" (#${pr.number}).`);
  }
}

router.options('*', (request, env) => new Response(null, { headers: corsHeaders(request, env) }));

router.get('/api/auth/github', (request, env) => {
  if (!env.GITHUB_CLIENT_ID || !env.GITHUB_CLIENT_SECRET || !env.SESSION_SECRET) {
    return jsonResponse(request, env, { success: false, error: 'GitHub sign-in is not configured.' }, 503);
  }
  const url = new URL(request.url);
  const returnTo = sanitizeReturnTo(url.searchParams.get('return_to'), env);
  const stateValue = buildOAuthState(returnTo);
  const headers = {
    Location: githubAuthorizeUrl(env, request, returnTo),
    'Set-Cookie': setOAuthStateCookie(stateValue, env),
  };
  return redirectResponse(headers.Location, headers);
});

router.get('/api/auth/callback', async (request, env) => {
  try {
    if (!env.GITHUB_CLIENT_ID || !env.GITHUB_CLIENT_SECRET || !env.SESSION_SECRET) {
      throw new Error('GitHub sign-in is not configured.');
    }
    const url = new URL(request.url);
    const code = url.searchParams.get('code');
    const oauthState = parseOAuthState(request);
    if (!code || !oauthState) {
      throw new Error('Invalid OAuth callback.');
    }
    const accessToken = await exchangeGitHubCode(code, env, request);
    const user = await fetchGitHubUser(accessToken);
    const sessionToken = await createSession(env, {
      login: user.login,
      userId: user.id,
      accessToken,
    });
    // Best-effort: capture a notification email so optional approval/merge
    // emails can be sent. Only set the address when none is stored yet, so a
    // contributor who later changes or disables it is not overwritten on login.
    try {
      const existing = await getNotifyPrefs(env, user.login);
      if (!existing.email) {
        const email = await fetchGitHubPrimaryEmail(accessToken, user);
        if (email) await setNotifyPrefs(env, user.login, { email, enabled: true });
      }
    } catch {
      // Notifications are optional; never block sign-in on this.
    }
    const returnTo = sanitizeReturnTo(oauthState.returnTo, env);
    const headers = new Headers({ Location: returnTo });
    headers.append('Set-Cookie', setSessionCookie(sessionToken, env));
    headers.append('Set-Cookie', clearOAuthStateCookie(env));
    return new Response(null, { status: 302, headers });
  } catch (err) {
    const fallback = sanitizeReturnTo(null, env);
    const message = encodeURIComponent(err.message || 'Sign-in failed');
    return redirectResponse(`${fallback}?auth_error=${message}`, {
      'Set-Cookie': clearOAuthStateCookie(env),
    });
  }
});

router.get('/api/auth/me', async (request, env) => {
  const session = await getSession(request, env);
  if (!session) {
    return jsonResponse(request, env, { loggedIn: false });
  }
  return jsonResponse(request, env, {
    loggedIn: true,
    login: session.login,
    userId: session.userId,
  });
});

router.post('/api/auth/logout', async (request, env) => {
  await destroySession(request, env);
  return jsonResponse(request, env, { success: true }, 200, {
    'Set-Cookie': clearSessionCookie(env),
  });
});

router.get('/api/me/submissions', async (request, env) => {
  try {
    const session = requireSession(await getSession(request, env));
    const dashboard = await buildDashboard(session, env);
    return jsonResponse(request, env, { success: true, ...dashboard });
  } catch (err) {
    return jsonResponse(request, env, { success: false, error: err.message }, err.status || 500);
  }
});

router.get('/api/me/notifications', async (request, env) => {
  try {
    const session = requireSession(await getSession(request, env));
    const prefs = await getNotifyPrefs(env, session.login);
    return jsonResponse(request, env, {
      success: true,
      configured: Boolean(env.RESEND_API_KEY),
      email: prefs.email,
      enabled: prefs.enabled,
    });
  } catch (err) {
    return jsonResponse(request, env, { success: false, error: err.message }, err.status || 500);
  }
});

router.post('/api/me/notifications', async (request, env) => {
  try {
    const session = requireSession(await getSession(request, env));
    const data = await request.json();
    const update = {};
    if (data.email !== undefined) {
      const email = String(data.email || '').trim();
      if (email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
        throw new Error('Enter a valid email address.');
      }
      update.email = email;
    }
    if (data.enabled !== undefined) update.enabled = Boolean(data.enabled);
    const prefs = await setNotifyPrefs(env, session.login, update);
    return jsonResponse(request, env, { success: true, email: prefs.email, enabled: prefs.enabled });
  } catch (err) {
    return jsonResponse(request, env, { success: false, error: err.message }, err.status || 500);
  }
});

router.post('/api/notify', async (request, env) => {
  try {
    if (!env.NOTIFY_SECRET) {
      return jsonResponse(request, env, { success: false, error: 'Notifications are not configured.' }, 503);
    }
    const provided = request.headers.get('X-Notify-Secret') || '';
    if (provided !== env.NOTIFY_SECRET) {
      return jsonResponse(request, env, { success: false, error: 'Unauthorized.' }, 401);
    }
    const data = await request.json();
    const login = String(data.login || '').replace(/^@/, '').trim();
    const event = String(data.event || '').trim();
    if (!login || !['approved', 'declined', 'merged'].includes(event)) {
      return jsonResponse(request, env, { success: false, error: 'login and a valid event are required.' }, 400);
    }
    const prefs = await getNotifyPrefs(env, login);
    if (!prefs.enabled || !prefs.email) {
      return jsonResponse(request, env, { success: true, sent: false, reason: 'no-opt-in' });
    }
    await sendNotificationEmail(env, {
      to: prefs.email,
      event,
      title: data.title,
      url: data.url,
    });
    return jsonResponse(request, env, { success: true, sent: true });
  } catch (err) {
    return jsonResponse(request, env, { success: false, error: err.message }, err.status || 500);
  }
});

router.post('/api/propose', async (request, env) => {
  try {
    const session = requireSession(await getSession(request, env));
    const data = await request.json();
    await verifyTurnstile(data.turnstileToken, env, request);

    const { title, category, description, summary, formal, familiarity } = data;

    const body = `Propose a new analytic study before writing the full paper.
Maintainers will review and label approved proposals \`proposal-approved\`.

### Proposed title

${title}

### Category

${category}

### One-line description

${description}

### Study summary

${summary}

### Catalog table

- [${formal ? 'x' : ' '}] Register in the Formal Studies table (instead of Topical Studies)

### Prior familiarity with Madhyasth Darshan

${familiarity}

### Portal submitter

@${session.login}
`;

    const issue = await githubRequest('/issues', 'POST', {
      title: `Study proposal: ${title}`,
      body,
      labels: ['study-proposal'],
    }, env, session.accessToken);

    return jsonResponse(request, env, {
      success: true,
      url: issue.html_url,
      issueNumber: issue.number,
    });
  } catch (err) {
    return jsonResponse(request, env, { success: false, error: err.message }, err.status || 500);
  }
});

router.get('/api/proposal-status', async (request, env) => {
  try {
    const url = new URL(request.url);
    const issueParam = url.searchParams.get('issue');
    if (!issueParam) {
      return jsonResponse(request, env, { success: false, error: 'issue parameter is required' }, 400);
    }
    const issueNumber = Number(issueParam);
    if (!Number.isInteger(issueNumber) || issueNumber < 1) {
      return jsonResponse(request, env, { success: false, error: 'issue must be a positive integer' }, 400);
    }

    const session = await getSession(request, env);
    const issue = await githubRequest(`/issues/${issueNumber}`, 'GET', null, env, session?.accessToken);
    const labels = issueLabels(issue);
    const approved = labels.includes('proposal-approved');
    const declined = labels.includes('proposal-declined');
    const title = proposedTitleFromIssue(issue);
    let registry = { proposals: [] };
    try {
      registry = await fetchProposalRegistry(env, { githubRequests: 0 });
    } catch (e) {
      // optional
    }
    const slug = slugForProposal(issue, registry);
    const ownedByYou = session ? issue.user?.login === session.login : null;
    const preCatalog = Boolean(
      slug && preCatalogSlugSet(registry).has(slug)
    );

    return jsonResponse(request, env, {
      success: true,
      approved,
      declined,
      issueNumber,
      title,
      slug,
      preCatalog,
      url: issue.html_url,
      ownedByYou,
    });
  } catch (err) {
    return jsonResponse(request, env, { success: false, error: err.message }, 500);
  }
});

router.get('/api/study-source', async (request, env) => {
  try {
    const url = new URL(request.url);
    const slug = (url.searchParams.get('slug') || '').trim();
    if (!/^[A-Za-z0-9-]+$/.test(slug)) {
      return jsonResponse(request, env, { success: false, error: 'Invalid slug.' }, 400);
    }
    const appliedSlugs = await fetchAppliedSlugSet(env, { githubRequests: 0 });
    let content;
    try {
      content = await githubRawFile(studyMdPath(slug, appliedSlugs), env);
    } catch (e) {
      return jsonResponse(request, env, { success: false, error: `No published markdown found for "${slug}".` }, 404);
    }
    return jsonResponse(request, env, { success: true, slug, content });
  } catch (err) {
    return jsonResponse(request, env, { success: false, error: err.message }, err.status || 500);
  }
});

router.post('/api/submit', async (request, env) => {
  try {
    const session = requireSession(await getSession(request, env));
    const data = await request.json();
    await verifyTurnstile(data.turnstileToken, env, request);

    const { slug, author, isNew, proposalIssue } = data;
    let { content } = data;

    const stats = { githubRequests: 0 };
    let proposal = null;
    let proposalRegistry = { proposals: [] };
    if (isNew) {
      if (!proposalIssue) {
        throw new Error('Proposal issue number is required for new studies.');
      }
      [proposal, proposalRegistry] = await Promise.all([
        assertProposalApproved(Number(proposalIssue), env, session.accessToken),
        fetchProposalRegistry(env, stats),
      ]);
      await assertProposalOwner(proposal, session.login);
      assertProposalSlugMatch(proposal, slug, proposalRegistry);
    }

    const prSearch = await githubSearch(
      `repo:${REPO} is:pr is:open label:new-study,study-update`,
      env,
      session.accessToken,
      stats
    );
    const openStudyPrs = buildOpenStudyPrIndex(prSearch.items);
    assertNoOpenStudyPr(slug, openStudyPrs);

    const istTime = getISTDateString();
    content = applyStudyMetadata(content, author, istTime, slug);

    // Updates to an existing applied study must target Applications/<slug>/.
    // Brand-new studies proposed via the portal are always created under Studies/.
    const appliedSlugs = isNew ? new Set() : await fetchAppliedSlugSet(env, stats);
    const branchName = `submission-${slug}-${Date.now()}`;
    const filePath = studyMdPath(slug, appliedSlugs);
    const base = defaultBranch(env);

    const baseRef = await githubRequest(`/git/refs/heads/${base}`, 'GET', null, env);
    const baseSha = baseRef.object.sha;

    await githubRequest('/git/refs', 'POST', {
      ref: `refs/heads/${branchName}`,
      sha: baseSha,
    }, env);

    try {
      let fileSha;
      try {
        const fileData = await githubRequest(`/contents/${filePath}?ref=${branchName}`, 'GET', null, env);
        fileSha = fileData.sha;
      } catch (e) {
        // File doesn't exist, which is fine for new studies
      }

      const contentEncoded = btoa(unescape(encodeURIComponent(content)));

      await githubRequest(`/contents/${filePath}`, 'PUT', {
        message: `Update ${slug} via Web Portal`,
        content: contentEncoded,
        branch: branchName,
        sha: fileSha,
      }, env);

      const prTitle = isNew ? `Add study: ${slug}` : `Update study: ${slug}`;
      let prBody = `Submitted via Web Portal by ${author}.\nPortal-GitHub: @${session.login}\n\nSlug: ${slug}`;
      if (isNew) {
        prBody = `Proposal issue: #${proposalIssue}\nSlug: ${slug}\nTags: MVD, SB, JV\nPortal-GitHub: @${session.login}\n\nSubmitted via Web Portal by ${author}.`;
      }

      const pr = await githubRequest('/pulls', 'POST', {
        title: prTitle,
        head: branchName,
        base,
        body: prBody,
      }, env);

      const label = isNew ? 'new-study' : 'study-update';
      await githubRequest(`/issues/${pr.number}/labels`, 'POST', {
        labels: [label],
      }, env);

      return jsonResponse(request, env, { success: true, url: pr.html_url, number: pr.number });
    } catch (innerErr) {
      await deleteBranchQuietly(branchName, env);
      throw innerErr;
    }
  } catch (err) {
    return jsonResponse(request, env, { success: false, error: err.message }, err.status || 500);
  }
});

router.post('/api/status-change', async (request, env) => {
  try {
    const session = requireSession(await getSession(request, env));
    const data = await request.json();
    await verifyTurnstile(data.turnstileToken, env, request);

    const slug = (data.slug || '').trim();
    const targetStatus = (data.targetStatus || '').trim().toLowerCase();
    const reason = (data.reason || '').trim();

    if (!slug) {
      throw new Error('Study slug is required.');
    }
    if (targetStatus !== 'draft' && targetStatus !== 'released') {
      throw new Error('Target status must be draft or released.');
    }

    const stats = { githubRequests: 0 };
    const [catalogMap, appliedSlugs, prSearch] = await Promise.all([
      fetchCatalogSlugMap(env, stats),
      fetchAppliedSlugSet(env, stats),
      githubSearch(
        `repo:${REPO} is:pr author:${session.login} label:status-change`,
        env,
        session.accessToken,
        stats
      ),
    ]);

    assertStatusChangeAllowed(slug, targetStatus, catalogMap, prSearch.items);

    const branchName = `status-${slug}-${Date.now()}`;
    const base = defaultBranch(env);
    const baseRef = await githubRequest(`/git/refs/heads/${base}`, 'GET', null, env, null, stats);
    const baseSha = baseRef.object.sha;

    await githubRequest('/git/refs', 'POST', {
      ref: `refs/heads/${branchName}`,
      sha: baseSha,
    }, env, null, stats);

    try {
      // Commit the status flip on the branch so the pull request has a diff.
      // CI (_set_study_status via _ci_study_pr.py) then finalizes the catalog,
      // timestamp, and PDF watermark on merge.
      const filePath = studyMdPath(slug, appliedSlugs);
      let fileData;
      try {
        fileData = await githubRequest(`/contents/${filePath}?ref=${branchName}`, 'GET', null, env, null, stats);
      } catch (e) {
        throw new Error(`Could not load ${filePath} to apply the status change.`);
      }
      const currentContent = decodeBase64Content(fileData.content);
      const istTime = getISTDateString();
      let newContent = setStatusLine(currentContent, targetStatus);
      newContent = setEditedOnLine(newContent, istTime);
      if (newContent === currentContent) {
        throw new Error(`"${slug}" already appears to be ${targetStatus}.`);
      }
      await githubRequest(`/contents/${filePath}`, 'PUT', {
        message: `Set ${slug} status to ${targetStatus} via Web Portal`,
        content: btoa(unescape(encodeURIComponent(newContent))),
        branch: branchName,
        sha: fileData.sha,
      }, env, null, stats);

      const prBody = [
        `Study slug: ${slug}`,
        `Target status: ${targetStatus}`,
        '',
        '### Reason',
        '',
        reason || 'Submitted via Web Submission Portal.',
        '',
        `Portal-GitHub: @${session.login}`,
      ].join('\n');

      const pr = await githubRequest('/pulls', 'POST', {
        title: `Status change: ${slug} → ${targetStatus}`,
        head: branchName,
        base,
        body: prBody,
      }, env, null, stats);

      await githubRequest(`/issues/${pr.number}/labels`, 'POST', {
        labels: ['status-change'],
      }, env, null, stats);

      return jsonResponse(request, env, { success: true, url: pr.html_url, number: pr.number });
    } catch (innerErr) {
      await deleteBranchQuietly(branchName, env, stats);
      throw innerErr;
    }
  } catch (err) {
    return jsonResponse(request, env, { success: false, error: err.message }, err.status || 500);
  }
});

router.all('*', (request, env) => new Response('Not Found', { status: 404, headers: corsHeaders(request, env) }));

export default {
  fetch: (request, env, ctx) => router.fetch(request, env, ctx).catch((err) =>
    new Response(err.message, { status: 500, headers: corsHeaders(request, env) })
  ),
};
