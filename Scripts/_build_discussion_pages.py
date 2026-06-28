#!/usr/bin/env python3
"""Generate per-study discussion.html pages for published studies."""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path
from urllib.parse import quote

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _common import (  # noqa: E402
    APPLICATIONS,
    STUDIES,
    site_base_url,
)
from _study_catalog import (  # noqa: E402
    CATALOG_TABLES,
    StudyRow,
    StudyStatus,
    StudyTable,
    display_title,
    load_catalog_rows,
)

FEEDBACK_ISSUES_URL = "https://github.com/raghavamohan/AnalyticMadhyasthDarshan/issues/new"
TURNSTILE_SITE_KEY = "0x4AAAAAADoBfrNV5lPeJQWO"
TURNSTILE_ACTION = "turnstile-spin-v1"
DISCUSSIONS_API_FALLBACK = "https://amd-discussions.raghavamohan.workers.dev"


def feedback_href(title: str) -> str:
    issue_title = quote(f"Study feedback: {title}")
    return f"{FEEDBACK_ISSUES_URL}?template=study-feedback.yml&title={issue_title}"


def discussion_output_path(row: StudyRow) -> Path | None:
    if not row.has_pdf:
        return None
    if row.table == StudyTable.APPLIED:
        return APPLICATIONS / row.slug / "discussion.html"
    return STUDIES / row.slug / "discussion.html"


def _relative_links(row: StudyRow) -> dict[str, str]:
    if row.table == StudyTable.APPLIED:
        return {
            "catalog": "../../Studies/index.html",
            "read": f"{row.slug}.html",
            "pdf": f"{row.slug}.pdf",
        }
    return {
        "catalog": "../index.html",
        "read": f"{row.slug}.html",
        "pdf": f"{row.slug}.pdf",
    }


def render_discussion_page(row: StudyRow) -> str:
    title = display_title(row)
    links = _relative_links(row)
    draft_note = (
        ' <span class="status-badge status-badge--draft">Draft</span>'
        if row.status == StudyStatus.DRAFT
        else ""
    )
    feedback = feedback_href(title)
    slug_json = json.dumps(row.slug)
    title_json = json.dumps(title)
    site_host = json.dumps(site_base_url().replace("https://", ""))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Discussion — {html.escape(title)}</title>
<style>
  :root {{
    --bg: #f7f3ec;
    --surface: #fffdf9;
    --text: #2a241c;
    --text-muted: #5c5348;
    --accent: #1f5f8b;
    --accent-soft: #e8f1f8;
    --border: #ddd3c4;
    --radius: 10px;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: "Segoe UI", system-ui, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.55;
  }}
  a {{ color: var(--accent); }}
  .wrap {{ max-width: 820px; margin: 0 auto; padding: 24px 20px 64px; }}
  .toolbar {{
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 20px;
  }}
  .toolbar-main {{
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
    flex: 1 1 240px;
    min-width: 0;
  }}
  .toolbar h1 {{
    margin: 0;
    font-size: 1.35rem;
    font-weight: 700;
    flex: 1 1 180px;
    min-width: 0;
  }}
  .toolbar-end {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
    margin-left: auto;
  }}
  .toolbar-actions {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }}
  .btn-auth {{
    cursor: pointer;
    font: inherit;
  }}
  .btn {{
    display: inline-flex;
    align-items: center;
    padding: 8px 14px;
    border-radius: 999px;
    border: 1px solid var(--border);
    background: var(--surface);
    color: var(--text);
    text-decoration: none;
    font-size: 0.92rem;
    font-weight: 600;
  }}
  .btn-primary {{
    background: var(--accent);
    border-color: var(--accent);
    color: #fff;
  }}
  .btn:hover {{ filter: brightness(0.97); }}
  .status-badge {{
    display: inline-block;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    padding: 2px 8px;
    border-radius: 999px;
    background: var(--accent-soft);
    color: var(--accent);
    vertical-align: middle;
  }}
  .status-badge--draft {{ background: #fff4e5; color: #9a6700; }}
  .auth-row {{ display: grid; gap: 10px; max-width: 420px; }}
  .auth-row label {{ display: grid; gap: 4px; font-size: 0.9rem; font-weight: 600; }}
  .auth-row input, .auth-row textarea {{
    width: 100%;
    padding: 10px 12px;
    border: 1px solid var(--border);
    border-radius: 8px;
    font: inherit;
  }}
  .auth-row textarea {{ min-height: 120px; resize: vertical; }}
  .turnstile-wrap {{ margin: 10px 0; min-height: 65px; }}
  .comments {{ list-style: none; padding: 0; margin: 0; display: grid; gap: 14px; }}
  .comment {{
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 14px 16px;
    background: #fff;
  }}
  .comment-meta {{
    display: flex;
    justify-content: space-between;
    gap: 12px;
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-bottom: 8px;
  }}
  .comment-meta-main {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px 12px;
    align-items: baseline;
  }}
  .comment-actions {{
    display: inline-flex;
    gap: 8px;
    flex: 0 0 auto;
  }}
  .comment-action {{
    border: 1px solid var(--border);
    background: var(--surface);
    color: var(--text-muted);
    border-radius: 999px;
    padding: 2px 10px;
    font: inherit;
    font-size: 0.78rem;
    font-weight: 600;
    cursor: pointer;
  }}
  .comment-action:hover {{
    color: var(--accent);
    border-color: #a5c4d9;
    background: var(--accent-soft);
  }}
  .comment-action--hide:hover {{
    color: #9a6700;
    border-color: #e6c27a;
    background: #fff4e5;
  }}
  .comment-body {{ white-space: pre-wrap; word-break: break-word; }}
  .alert {{
    padding: 10px 12px;
    border-radius: 8px;
    margin-bottom: 12px;
    font-size: 0.92rem;
  }}
  .alert-error {{ background: #fdecea; color: #8a1f11; border: 1px solid #f5c2c0; }}
  .alert-success {{ background: #edf7ed; color: #1e4620; border: 1px solid #c8e6c9; }}
  .alert-info {{ background: var(--accent-soft); color: #13466a; border: 1px solid #c5dcee; }}
  .hidden {{ display: none !important; }}
  .intro-text {{
    padding: 0 10px 24px;
    color: var(--text-muted);
    font-size: 0.95rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
  }}
  .intro-text p {{ margin: 0 0 8px; }}
  .intro-text a {{ text-decoration: underline; }}
  .auth-status-inline {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-bottom: 12px;
  }}
  .auth-status-inline button {{
    background: transparent;
    border: none;
    color: var(--accent);
    cursor: pointer;
    font-size: 0.85rem;
    padding: 0;
    font-weight: 600;
  }}
  .auth-status-inline button:hover {{ text-decoration: underline; }}
  .action-panel {{
    background: var(--surface);
    border: 2px solid var(--border);
    border-radius: var(--radius);
    padding: 18px 20px;
    margin-bottom: 28px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
  }}
  .action-panel h2 {{
    margin: 0 0 12px;
    font-size: 1.05rem;
  }}
  .action-panel .auth-row {{ max-width: none; }}
  .auth-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }}
  .auth-sign-in-note {{
    margin: 0 0 12px;
    font-size: 0.9rem;
    color: var(--text-muted);
  }}
  .compose-actions {{
    display: flex;
    gap: 8px;
    margin-top: 16px;
    align-items: center;
  }}
  .comments-section {{
    margin-top: 8px;
  }}
  .comments-section h2 {{
    margin: 0 0 14px;
    font-size: 1.05rem;
  }}
  @media (max-width: 600px) {{
    .auth-grid {{ grid-template-columns: 1fr; }}
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #171411;
      --surface: #211c18;
      --text: #f2ebe1;
      --text-muted: #b9aea0;
      --accent: #7ebbed;
      --accent-soft: #1a3344;
      --border: #3a322b;
    }}
    .comment {{ background: #1a1613; }}
    .alert-error {{ background: #3a1714; color: #ffb4a9; border-color: #7f2d25; }}
    .alert-success {{ background: #142818; color: #a8d5a8; border-color: #2f5c31; }}
    .btn-primary {{ color: #102030; }}
    .auth-row input, .auth-row textarea {{
      background-color: #26201b;
      color: var(--text);
      border-color: #433931;
    }}
    .auth-row textarea:focus, .auth-row input:focus {{
      border-color: var(--accent);
      outline: none;
    }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <nav class="toolbar" aria-label="Discussion navigation">
    <div class="toolbar-main">
      <a class="btn" href="{html.escape(links['catalog'])}">&larr; All studies</a>
      <h1>Discussion — {html.escape(title)}{draft_note}</h1>
    </div>
    <div class="toolbar-end">
      <span class="toolbar-actions">
        <a class="btn btn-primary" href="{html.escape(links['read'])}">Read paper</a>
        <a class="btn" href="{html.escape(links['pdf'])}" download>Download PDF</a>
        <a class="btn" href="{html.escape(feedback)}" rel="noopener">Suggest a correction</a>
      </span>
      <button type="button" id="toolbar-auth-btn" class="btn btn-primary btn-auth">Log in</button>
    </div>
  </nav>

  <div class="intro-text" aria-labelledby="about-discussion">
    <p id="about-discussion">Use this page for questions, interpretive discussion, and general comments on <em>{html.escape(title)}</em>.</p>
    <p>For typos, citations, or section-specific corrections intended for maintainers, use <a href="{html.escape(feedback)}" rel="noopener">Suggest a correction</a> (GitHub Issues) instead.</p>
    <p class="privacy-note">Sign-in uses your email address and display name. We use them only for discussion identity and moderation. See the site <a href="{html.escape(links['catalog'])}#contribute">contribute</a> section for more.</p>
  </div>

  <div id="discuss-alert" class="alert hidden" role="status"></div>

  <section id="sign-in-panel" class="action-panel hidden" aria-labelledby="sign-in-heading">
    <h2 id="sign-in-heading">Sign in to comment</h2>
    <p class="auth-sign-in-note">Enter your email and display name. We will send a one-time sign-in link.</p>
    <form id="magic-link-form" class="auth-row">
      <div class="auth-grid">
        <label>Email<input type="email" name="email" autocomplete="email" required></label>
        <label>Display name<input type="text" name="displayName" maxlength="80" autocomplete="nickname" required></label>
      </div>
      <div class="turnstile-wrap">
        <div id="sign-in-turnstile" class="cf-turnstile" data-sitekey="{TURNSTILE_SITE_KEY}" data-action="{TURNSTILE_ACTION}"></div>
      </div>
      <div class="compose-actions">
        <button type="submit" class="btn btn-primary">Email me a sign-in link</button>
      </div>
    </form>
  </section>

  <section id="comment-panel" class="action-panel hidden" aria-labelledby="comment-heading">
    <h2 id="comment-heading">Add a comment</h2>
    <div class="auth-status-inline">
      <span>Signed in as <strong id="auth-user-label"></strong></span>
    </div>
    <form id="comment-form" class="auth-row">
      <label>Your comment<textarea name="body" maxlength="8192" required placeholder="Share a question or comment…"></textarea></label>
      <div class="compose-actions">
        <button type="submit" class="btn btn-primary">Post comment</button>
      </div>
    </form>
  </section>

  <section class="comments-section" aria-labelledby="comments-heading">
    <h2 id="comments-heading">Comments</h2>
    <ul id="comment-list" class="comments" aria-live="polite"></ul>
    <p id="comments-empty" class="hidden">No comments yet. Be the first to start the discussion.</p>
  </section>
</div>

<script src="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit"></script>
<script>
(() => {{
  const STUDY_SLUG = {slug_json};
  const STUDY_TITLE = {title_json};
  const SITE_HOST = {site_host};
  const API_FALLBACK = {json.dumps(DISCUSSIONS_API_FALLBACK)};
  const TURNSTILE_SITE_KEY = {json.dumps(TURNSTILE_SITE_KEY)};
  const TURNSTILE_ACTION = {json.dumps(TURNSTILE_ACTION)};

  const apiBase = () => (window.location.hostname === SITE_HOST ? "" : API_FALLBACK);

  const alertEl = document.getElementById("discuss-alert");
  const commentList = document.getElementById("comment-list");
  const commentsEmpty = document.getElementById("comments-empty");
  const signInPanel = document.getElementById("sign-in-panel");
  const commentPanel = document.getElementById("comment-panel");
  const magicForm = document.getElementById("magic-link-form");
  const commentForm = document.getElementById("comment-form");
  const authUserLabel = document.getElementById("auth-user-label");
  const toolbarAuthBtn = document.getElementById("toolbar-auth-btn");
  let currentSession = {{ loggedIn: false }};
  let signInTurnstileWidgetId = null;
  let signInTurnstileTimer = null;
  const DISCUSS_SEEN_KEY = "amd-discuss-seen";

  const markDiscussionSeen = (comments) => {{
    if (!Array.isArray(comments) || !comments.length) return;
    const latest = comments.reduce(
      (max, item) => Math.max(max, Number(item.createdAt) || 0),
      0,
    );
    if (!latest) return;
    try {{
      const seen = JSON.parse(localStorage.getItem(DISCUSS_SEEN_KEY) || "{{}}");
      seen[STUDY_SLUG] = Math.max(Number(seen[STUDY_SLUG] || 0), latest);
      localStorage.setItem(DISCUSS_SEEN_KEY, JSON.stringify(seen));
    }} catch {{
      // ignore storage errors
    }}
  }};

  const showAlert = (kind, message) => {{
    alertEl.className = `alert alert-${{kind}}`;
    alertEl.textContent = message;
    alertEl.classList.remove("hidden");
  }};

  const withTurnstile = (fn) => {{
    turnstile.ready(fn);
  }};

  const signInTurnstileEl = () => document.getElementById("sign-in-turnstile");

  const resetSignInTurnstileContainer = () => {{
    const wrap = signInPanel?.querySelector(".turnstile-wrap");
    if (!wrap) return;
    wrap.innerHTML = `<div id="sign-in-turnstile" class="cf-turnstile" data-sitekey="${{TURNSTILE_SITE_KEY}}" data-action="${{TURNSTILE_ACTION}}"></div>`;
  }};

  const destroySignInTurnstile = () => {{
    withTurnstile(() => {{
      if (signInTurnstileWidgetId != null) {{
        try {{
          turnstile.remove(signInTurnstileWidgetId);
        }} catch {{
          // ignore stale widget ids
        }}
        signInTurnstileWidgetId = null;
      }}
    }});
  }};

  const mountSignInTurnstile = () => {{
    if (!signInPanel || signInPanel.classList.contains("hidden")) return;
    withTurnstile(() => {{
      let widget = signInTurnstileEl();
      if (!widget) {{
        resetSignInTurnstileContainer();
        widget = signInTurnstileEl();
      }}
      if (!widget) return;
      if (signInTurnstileWidgetId != null) {{
        try {{
          turnstile.remove(signInTurnstileWidgetId);
        }} catch {{
          // ignore stale widget ids
        }}
        signInTurnstileWidgetId = null;
      }}
      signInTurnstileWidgetId = turnstile.render(widget, {{
        sitekey: TURNSTILE_SITE_KEY,
        action: TURNSTILE_ACTION,
        theme: "auto",
        "refresh-expired": "auto",
      }});
    }});
  }};

  const scheduleSignInTurnstile = () => {{
    if (signInTurnstileTimer) clearTimeout(signInTurnstileTimer);
    signInTurnstileTimer = setTimeout(() => {{
      signInTurnstileTimer = null;
      requestAnimationFrame(() => mountSignInTurnstile());
    }}, 150);
  }};

  const showSignInPanel = () => {{
    signInPanel.classList.remove("hidden");
    commentPanel.classList.add("hidden");
    destroySignInTurnstile();
    resetSignInTurnstileContainer();
    scheduleSignInTurnstile();
    signInPanel.scrollIntoView({{ behavior: "smooth", block: "start" }});
    const emailInput = magicForm.querySelector('input[name="email"]');
    if (emailInput) emailInput.focus();
  }};

  const hideSignInPanel = () => {{
    signInPanel.classList.add("hidden");
    destroySignInTurnstile();
    resetSignInTurnstileContainer();
  }};

  const showCommentPanel = () => {{
    hideSignInPanel();
    commentPanel.classList.remove("hidden");
  }};

  const hideCommentPanel = () => {{
    commentPanel.classList.add("hidden");
  }};

  const openLoginFlow = () => {{
    showSignInPanel();
  }};

  const handleLogout = async () => {{
    try {{
      await fetchJson("/api/discuss-auth/logout", {{ method: "POST", body: "{{}}" }});
      setAuthUi({{ loggedIn: false }});
      await loadComments();
      showAlert("info", "Signed out.");
    }} catch (err) {{
      showAlert("error", err.message);
    }}
  }};

  toolbarAuthBtn.addEventListener("click", () => {{
    if (currentSession.loggedIn) {{
      handleLogout();
      return;
    }}
    openLoginFlow();
  }});

  const params = new URLSearchParams(window.location.search);
  const discussError = params.get("discuss_error");
  if (discussError) {{
    showAlert("error", decodeURIComponent(discussError));
    showSignInPanel();
    params.delete("discuss_error");
    const clean = params.toString();
    history.replaceState(null, "", clean ? `?${{clean}}` : window.location.pathname);
  }}

  const fetchJson = async (path, options = {{}}) => {{
    const response = await fetch(apiBase() + path, {{
      credentials: "include",
      headers: {{ "Content-Type": "application/json", ...(options.headers || {{}}) }},
      ...options,
    }});
    const data = await response.json().catch(() => ({{}}));
    if (!response.ok) {{
      throw new Error(data.error || data.message || `Request failed (${{response.status}})`);
    }}
    return data;
  }};

  const turnstileToken = () =>
    signInTurnstileEl()?.closest("form")?.querySelector('input[name="cf-turnstile-response"]')?.value
    || magicForm.querySelector('input[name="cf-turnstile-response"]')?.value
    || "";

  const resetSignInTurnstile = () => {{
    if (signInTurnstileWidgetId != null) {{
      withTurnstile(() => {{
        try {{
          turnstile.reset(signInTurnstileWidgetId);
        }} catch {{
          destroySignInTurnstile();
          resetSignInTurnstileContainer();
          scheduleSignInTurnstile();
        }}
      }});
      return;
    }}
    scheduleSignInTurnstile();
  }};

  const formatWhen = (ms) => {{
    try {{
      return new Date(Number(ms)).toLocaleString(undefined, {{
        dateStyle: "medium",
        timeStyle: "short",
      }});
    }} catch {{
      return "";
    }}
  }};

  const renderCommentActions = (item) => {{
    const parts = [];
    if (item.canDelete) {{
      parts.push(`<button type="button" class="comment-action comment-action--delete" data-action="delete" data-comment-id="${{escapeHtml(item.id)}}">Delete</button>`);
    }}
    if (item.canHide) {{
      parts.push(`<button type="button" class="comment-action comment-action--hide" data-action="hide" data-comment-id="${{escapeHtml(item.id)}}">Hide</button>`);
    }}
    return parts.length ? `<span class="comment-actions">${{parts.join("")}}</span>` : "";
  }};

  const renderComments = (comments) => {{
    commentList.innerHTML = "";
    if (!comments.length) {{
      commentsEmpty.classList.remove("hidden");
      return;
    }}
    commentsEmpty.classList.add("hidden");
    comments.forEach((item) => {{
      const li = document.createElement("li");
      li.className = "comment";
      li.dataset.commentId = item.id;
      li.innerHTML = `
        <div class="comment-meta">
          <span class="comment-meta-main">
            <strong>${{escapeHtml(item.authorName || "Reader")}}</strong>
            <time datetime="${{item.createdAt}}">${{formatWhen(item.createdAt)}}</time>
          </span>
          ${{renderCommentActions(item)}}
        </div>
        <div class="comment-body">${{escapeHtml(item.body)}}</div>`;
      commentList.appendChild(li);
    }});
  }};

  const escapeHtml = (value) => String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

  const setAuthUi = (session) => {{
    currentSession = session || {{ loggedIn: false }};
    const loggedIn = Boolean(currentSession.loggedIn);
    if (loggedIn) {{
      authUserLabel.textContent = currentSession.displayName || currentSession.email || "Reader";
      toolbarAuthBtn.textContent = "Log out";
      toolbarAuthBtn.classList.remove("btn-primary");
      toolbarAuthBtn.setAttribute("aria-label", "Sign out of discussion");
      showCommentPanel();
    }} else {{
      toolbarAuthBtn.textContent = "Log in";
      toolbarAuthBtn.classList.add("btn-primary");
      toolbarAuthBtn.setAttribute("aria-label", "Sign in to discuss");
      hideCommentPanel();
      hideSignInPanel();
    }}
  }};

  const removeComment = async (commentId, action) => {{
    const prompt = action === "hide" ? "Hide this comment?" : "Delete this comment?";
    if (!window.confirm(prompt)) return;
    const path = action === "hide"
      ? `/api/discussions/${{encodeURIComponent(STUDY_SLUG)}}/comments/${{encodeURIComponent(commentId)}}/hide`
      : `/api/discussions/${{encodeURIComponent(STUDY_SLUG)}}/comments/${{encodeURIComponent(commentId)}}/delete`;
    await fetchJson(path, {{ method: "POST", body: "{{}}" }});
    showAlert("success", action === "hide" ? "Comment hidden." : "Comment deleted.");
    await loadComments();
  }};

  commentList.addEventListener("click", async (event) => {{
    const button = event.target.closest(".comment-action");
    if (!button) return;
    const commentId = button.dataset.commentId;
    const action = button.dataset.action;
    if (!commentId || !action) return;
    button.disabled = true;
    try {{
      await removeComment(commentId, action);
    }} catch (err) {{
      showAlert("error", err.message);
      button.disabled = false;
    }}
  }});

  const loadComments = async () => {{
    const data = await fetchJson(`/api/discussions/${{encodeURIComponent(STUDY_SLUG)}}`);
    const comments = data.comments || [];
    renderComments(comments);
    markDiscussionSeen(comments);
  }};

  const loadSession = async () => {{
    try {{
      const session = await fetchJson("/api/discuss-auth/me");
      setAuthUi(session);
      await loadComments();
    }} catch (err) {{
      setAuthUi({{ loggedIn: false }});
      showAlert("error", err.message);
    }}
  }};

  magicForm.addEventListener("submit", async (event) => {{
    event.preventDefault();
    const form = event.currentTarget;
    const email = form.email.value.trim();
    const displayName = form.displayName.value.trim();
    const turnstileTokenValue = turnstileToken();
    if (!turnstileTokenValue) {{
      scheduleSignInTurnstile();
      showAlert("error", "Complete the verification check below.");
      return;
    }}
    try {{
      const data = await fetchJson("/api/discuss-auth/magic-link", {{
        method: "POST",
        body: JSON.stringify({{
          email,
          displayName,
          turnstileToken: turnstileTokenValue,
          returnTo: window.location.href.split("#")[0],
        }}),
      }});
      showAlert("success", data.message || "Check your email for a sign-in link.");
      resetSignInTurnstile();
    }} catch (err) {{
      showAlert("error", err.message);
      resetSignInTurnstile();
    }}
  }});

  commentForm.addEventListener("submit", async (event) => {{
    event.preventDefault();
    const form = event.currentTarget;
    const body = form.body.value.trim();
    if (!body) {{
      showAlert("error", "Comment cannot be empty.");
      return;
    }}
    try {{
      await fetchJson(`/api/discussions/${{encodeURIComponent(STUDY_SLUG)}}/comments`, {{
        method: "POST",
        body: JSON.stringify({{
          body,
          title: STUDY_TITLE,
        }}),
      }});
      form.body.value = "";
      showAlert("success", "Comment posted.");
      await loadComments();
      const textarea = form.querySelector('textarea[name="body"]');
      if (textarea) textarea.focus();
    }} catch (err) {{
      showAlert("error", err.message);
    }}
  }});

  loadSession().catch((err) => showAlert("error", err.message));
}})();
</script>
</body>
</html>
"""


def write_discussion_page(row: StudyRow) -> Path | None:
    path = discussion_output_path(row)
    if path is None:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_discussion_page(row), encoding="utf-8")
    return path


def remove_discussion_page(row: StudyRow) -> None:
    path = discussion_output_path(row)
    if path and path.is_file():
        path.unlink()


def build_discussion_pages_for_rows(rows: list[StudyRow]) -> list[Path]:
    written: list[Path] = []
    for row in rows:
        if row.has_pdf:
            path = write_discussion_page(row)
            if path:
                written.append(path)
    return written


def build_all_discussion_pages() -> list[Path]:
    written: list[Path] = []
    for table in CATALOG_TABLES:
        written.extend(build_discussion_pages_for_rows(load_catalog_rows(table)))
    return written


def verify_discussion_pages() -> list[str]:
    errors: list[str] = []
    for table in CATALOG_TABLES:
        for row in load_catalog_rows(table):
            if not row.has_pdf:
                continue
            path = discussion_output_path(row)
            if path is None:
                continue
            if not path.is_file():
                errors.append(f"Missing discussion page for {row.slug}: {path.relative_to(STUDIES.parent)}")
    return errors


def main() -> int:
    written = build_all_discussion_pages()
    print(f"Wrote {len(written)} discussion page(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
