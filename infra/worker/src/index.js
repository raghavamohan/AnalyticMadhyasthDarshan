import { Router } from 'itty-router';

const router = Router();
const DEFAULT_BRANCH = 'master';
const SITEVERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify';

// CORS Headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
  });
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

// Helper for sending GitHub API requests
async function githubRequest(path, method, body, env) {
  const url = `https://api.github.com/repos/raghavamohan/AnalyticMadhyasthDarshan${path}`;
  const options = {
    method,
    headers: {
      'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
      'Accept': 'application/vnd.github.v3+json',
      'User-Agent': 'Cloudflare-Worker-Submission-Portal'
    }
  };
  if (body) {
    options.body = JSON.stringify(body);
  }
  const response = await fetch(url, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`GitHub API Error (${response.status}): ${text}`);
  }
  return response.json();
}

function defaultBranch(env) {
  return env.DEFAULT_BRANCH || DEFAULT_BRANCH;
}

async function assertProposalApproved(issueNumber, env) {
  const issue = await githubRequest(`/issues/${issueNumber}`, 'GET', null, env);
  const labels = (issue.labels || []).map((label) =>
    typeof label === 'string' ? label : label.name
  );
  if (!labels.includes('proposal-approved')) {
    throw new Error(
      `Issue #${issueNumber} is not approved. Wait for maintainers to add the proposal-approved label.`
    );
  }
  return issue;
}

// Format IST Date
function getISTDateString() {
  const now = new Date();
  const options = {
    timeZone: 'Asia/Kolkata',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  };
  // Example output: "June 16, 2026, 3:45 PM"
  let str = new Intl.DateTimeFormat('en-US', options).format(now);
  // Remove " at " if present, depending on JS engine
  str = str.replace(' at ', ', ');
  return str + ' IST';
}

router.options('*', () => new Response(null, { headers: corsHeaders }));

router.post('/api/propose', async (request, env) => {
  try {
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
`;

    const issue = await githubRequest('/issues', 'POST', {
      title: `Study proposal: ${title}`,
      body: body,
      labels: ['study-proposal']
    }, env);

    return jsonResponse({ success: true, url: issue.html_url });
  } catch (err) {
    return jsonResponse({ success: false, error: err.message }, 500);
  }
});

router.post('/api/submit', async (request, env) => {
  try {
    const data = await request.json();
    await verifyTurnstile(data.turnstileToken, env, request);

    const { slug, author, isNew, proposalIssue } = data;
    let { content } = data;

    if (isNew) {
      if (!proposalIssue) {
        throw new Error('Proposal issue number is required for new studies.');
      }
      await assertProposalApproved(Number(proposalIssue), env);
    }

    // Ensure Author and Edited on metadata
    const istTime = getISTDateString();
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

    const branchName = `submission-${slug}-${Date.now()}`;
    const filePath = `Studies/${slug}/${slug}.md`;
    const base = defaultBranch(env);

    // 1. Get base branch SHA
    const baseRef = await githubRequest(`/git/refs/heads/${base}`, 'GET', null, env);
    const baseSha = baseRef.object.sha;

    // 2. Create Branch
    await githubRequest('/git/refs', 'POST', {
      ref: `refs/heads/${branchName}`,
      sha: baseSha
    }, env);

    // 3. Create or Update File
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
      sha: fileSha
    }, env);

    // 4. Create PR
    const prTitle = isNew ? `Add study: ${slug}` : `Update study: ${slug}`;
    let prBody = `Submitted via Web Portal by ${author}.\n\nSlug: ${slug}`;
    if (isNew) {
      prBody = `Proposal issue: #${proposalIssue}\nSlug: ${slug}\nTags: MVD, SB, JV\n\nSubmitted via Web Portal by ${author}.`;
    }

    const pr = await githubRequest('/pulls', 'POST', {
      title: prTitle,
      head: branchName,
      base,
      body: prBody
    }, env);

    // 5. Add Label
    const label = isNew ? 'new-study' : 'study-update';
    await githubRequest(`/issues/${pr.number}/labels`, 'POST', {
      labels: [label]
    }, env);

    return jsonResponse({ success: true, url: pr.html_url });
  } catch (err) {
    return jsonResponse({ success: false, error: err.message }, 500);
  }
});

// Fallback for all other routes
router.all('*', () => new Response('Not Found', { status: 404, headers: corsHeaders }));

export default {
  fetch: (request, env, ctx) => router.fetch(request, env, ctx).catch(err => new Response(err.message, { status: 500 }))
};
