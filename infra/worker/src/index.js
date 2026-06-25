import { Router } from 'itty-router';
import {
  buildOAuthState,
  clearOAuthStateCookie,
  clearSessionCookie,
  corsHeaders,
  createSession,
  exchangeGitHubCode,
  fetchGitHubUser,
  getSession,
  githubAuthorizeUrl,
  parseOAuthState,
  requireSession,
  sanitizeReturnTo,
  setOAuthStateCookie,
  setSessionCookie,
} from './auth.js';

const router = Router();
const DEFAULT_BRANCH = 'master';
const SITEVERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify';
const REPO = 'raghavamohan/AnalyticMadhyasthDarshan';

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

async function githubRequest(path, method, body, env, userToken = null) {
  const url = `https://api.github.com/repos/${REPO}${path}`;
  const token = userToken || env.GITHUB_TOKEN;
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

async function githubSearch(query, env, userToken = null) {
  const token = userToken || env.GITHUB_TOKEN;
  const url = `https://api.github.com/search/issues?q=${encodeURIComponent(query)}&per_page=20`;
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
  return data.items || [];
}

function defaultBranch(env) {
  return env.DEFAULT_BRANCH || DEFAULT_BRANCH;
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
  const match = (issue.title || '').match(/^Study proposal:\s*(.+)$/);
  return match ? match[1].trim() : null;
}

async function assertProposalApproved(issueNumber, env, userToken = null) {
  const issue = await githubRequest(`/issues/${issueNumber}`, 'GET', null, env, userToken);
  const labels = issueLabels(issue);
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

function submissionStage(issue, pullRequest) {
  const labels = issueLabels(issue);
  if (pullRequest) {
    if (pullRequest.state === 'open') {
      return 'pr-open';
    }
    if (pullRequest.merged_at) {
      return 'merged';
    }
    return 'pr-closed';
  }
  if (labels.includes('proposal-approved')) {
    return 'approved';
  }
  if (issue.state === 'closed') {
    return 'closed';
  }
  return 'pending';
}

async function findLinkedPullRequest(issueNumber, env, userToken) {
  const items = await githubSearch(
    `repo:${REPO} is:pr "Proposal issue: #${issueNumber}"`,
    env,
    userToken
  );
  return items[0] || null;
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

async function buildDashboard(session, env) {
  const login = session.login;
  const userToken = session.accessToken;
  // Comma-separated labels are OR in GitHub search. Approved issues sometimes
  // retain only proposal-approved if maintainers relabeled in the UI.
  const proposals = await githubSearch(
    `repo:${REPO} is:issue author:${login} label:study-proposal,proposal-approved`,
    env,
    userToken
  );

  const submissions = [];
  for (const issue of proposals.filter(isStudyProposalIssue)) {
    const title = proposedTitleFromIssue(issue);
    const slug = title ? titleToSlug(title) : null;
    const linkedPr = await findLinkedPullRequest(issue.number, env, userToken);
    let prDetails = null;
    if (linkedPr) {
      prDetails = await githubRequest(`/pulls/${linkedPr.number}`, 'GET', null, env, userToken);
    }
    submissions.push({
      issueNumber: issue.number,
      title: title || issue.title,
      slug,
      issueUrl: issue.html_url,
      issueState: issue.state,
      approved: issueLabels(issue).includes('proposal-approved'),
      stage: submissionStage(issue, prDetails),
      pullRequest: prDetails
        ? {
            number: prDetails.number,
            url: prDetails.html_url,
            state: prDetails.state,
            merged: Boolean(prDetails.merged_at),
            draft: Boolean(prDetails.draft),
          }
        : null,
      submitUrl: slug
        ? `https://analyticmadhyasthdarshan.org/Studies/submit.html?tab=submit&proposal=${issue.number}`
        : `https://analyticmadhyasthdarshan.org/Studies/submit.html?tab=submit&proposal=${issue.number}`,
    });
  }

  submissions.sort((a, b) => b.issueNumber - a.issueNumber);
  return { login, submissions };
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
    'Set-Cookie': setOAuthStateCookie(stateValue),
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
    const returnTo = sanitizeReturnTo(oauthState.returnTo, env);
    const headers = new Headers({ Location: returnTo });
    headers.append('Set-Cookie', setSessionCookie(sessionToken));
    headers.append('Set-Cookie', clearOAuthStateCookie());
    return new Response(null, { status: 302, headers });
  } catch (err) {
    const fallback = sanitizeReturnTo(null, env);
    const message = encodeURIComponent(err.message || 'Sign-in failed');
    return redirectResponse(`${fallback}?auth_error=${message}`, {
      'Set-Cookie': clearOAuthStateCookie(),
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

router.post('/api/auth/logout', (request, env) => {
  return jsonResponse(request, env, { success: true }, 200, {
    'Set-Cookie': clearSessionCookie(),
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
    const title = proposedTitleFromIssue(issue);
    const slug = title ? titleToSlug(title) : null;
    const ownedByYou = session ? issue.user?.login === session.login : null;

    return jsonResponse(request, env, {
      success: true,
      approved,
      issueNumber,
      title,
      slug,
      url: issue.html_url,
      ownedByYou,
    });
  } catch (err) {
    return jsonResponse(request, env, { success: false, error: err.message }, 500);
  }
});

router.post('/api/submit', async (request, env) => {
  try {
    const session = requireSession(await getSession(request, env));
    const data = await request.json();
    await verifyTurnstile(data.turnstileToken, env, request);

    const { slug, author, isNew, proposalIssue } = data;
    let { content } = data;

    let proposal = null;
    if (isNew) {
      if (!proposalIssue) {
        throw new Error('Proposal issue number is required for new studies.');
      }
      proposal = await assertProposalApproved(Number(proposalIssue), env, session.accessToken);
      await assertProposalOwner(proposal, session.login);
    }

    const istTime = getISTDateString();
    content = applyStudyMetadata(content, author, istTime, slug);

    const branchName = `submission-${slug}-${Date.now()}`;
    const filePath = `Studies/${slug}/${slug}.md`;
    const base = defaultBranch(env);

    const baseRef = await githubRequest(`/git/refs/heads/${base}`, 'GET', null, env);
    const baseSha = baseRef.object.sha;

    await githubRequest('/git/refs', 'POST', {
      ref: `refs/heads/${branchName}`,
      sha: baseSha,
    }, env);

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
