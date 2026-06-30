#!/usr/bin/env python3
"""Generate per-study discussion.html pages plus shared discussion assets."""
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
    has_approved_proposal_stub,
    load_catalog_rows,
)

FEEDBACK_ISSUES_URL = "https://github.com/raghavamohan/AnalyticMadhyasthDarshan/issues/new"
TURNSTILE_SITE_KEY = "0x4AAAAAADoBfrNV5lPeJQWO"
TURNSTILE_ACTION = "turnstile-spin-v1"
DISCUSSIONS_API_FALLBACK = "https://amd-discussions.raghavamohan.workers.dev"

# Bump when discuss.css / discuss.js change so the cached shared assets refresh.
ASSET_VERSION = "2"

ASSETS_DIRNAME = "assets"
DISCUSS_CSS_NAME = "discuss.css"
DISCUSS_JS_NAME = "discuss.js"


def assets_dir() -> Path:
    return STUDIES / ASSETS_DIRNAME


def feedback_href(title: str) -> str:
    issue_title = quote(f"Study feedback: {title}")
    return f"{FEEDBACK_ISSUES_URL}?template=study-feedback.yml&title={issue_title}"


def discussion_output_path(row: StudyRow) -> Path | None:
    if row.table == StudyTable.APPLIED:
        return APPLICATIONS / row.slug / "discussion.html"
    return STUDIES / row.slug / "discussion.html"


def _relative_links(row: StudyRow) -> dict[str, str | None]:
    has_read = row.has_pdf or has_approved_proposal_stub(row.slug)
    if row.table == StudyTable.APPLIED:
        return {
            "catalog": "../../Studies/index.html",
            "read": f"{row.slug}.html" if has_read else None,
            "pdf": f"{row.slug}.pdf" if has_read else None,
            "assets": "../../Studies/assets",
        }
    return {
        "catalog": "../index.html",
        "read": f"{row.slug}.html" if has_read else None,
        "pdf": f"{row.slug}.pdf" if has_read else None,
        "assets": "../assets",
    }


def _canonical_url(row: StudyRow) -> str:
    base = site_base_url().rstrip("/")
    if row.table == StudyTable.APPLIED:
        return f"{base}/Applications/{row.slug}/discussion.html"
    return f"{base}/Studies/{row.slug}/discussion.html"


def _toolbar_paper_links(links: dict[str, str | None]) -> str:
    if not links.get("read") or not links.get("pdf"):
        return ""
    return (
        f'          <a class="discuss-toolbar-link" href="{html.escape(links["read"])}">Read paper</a>\n'
        f'          <a class="discuss-toolbar-link discuss-toolbar-download" href="{html.escape(links["pdf"])}" download>PDF</a>\n'
    )


def _submission_portal_href(row: StudyRow) -> str:
    if row.table == StudyTable.APPLIED:
        return "../../Studies/submit.html"
    return "../submit.html"


def _contributing_href(row: StudyRow) -> str:
    if row.table == StudyTable.APPLIED:
        return "../../CONTRIBUTING.md"
    return "../../CONTRIBUTING.md"


def _discussion_header_note(row: StudyRow, feedback: str) -> str:
    if row.status == StudyStatus.ONGOING:
        return (
            f'<p class="discuss-header-note" id="about-discussion">Questions and comments on this planned study. '
            f"Sign-in uses your email for posting identity only.</p>"
        )
    return (
        f'<p class="discuss-header-note" id="about-discussion">Questions and comments on this study. '
        f'Maintainer corrections via <a href="{html.escape(feedback)}" rel="noopener">GitHub Issues</a>. '
        f"Sign-in uses your email for posting identity only.</p>"
    )


def _approved_proposal_callout(row: StudyRow, links: dict[str, str | None]) -> str:
    title = display_title(row)
    submit_href = html.escape(_submission_portal_href(row))
    read_href = html.escape(links["read"] or f"{row.slug}.html")
    pdf_href = html.escape(links["pdf"] or f"{row.slug}.pdf")
    return f"""
  <section class="planned-callout" aria-labelledby="planned-callout-heading">
    <h2 id="planned-callout-heading">Approved proposal</h2>
    <p>An approved study proposal for <strong>{html.escape(title)}</strong> is available to read. The full analytic paper is not yet in the catalog as Draft; use the proposal to see scope, questions, and planned comparisons.</p>
    <p><a href="{read_href}">Read the proposal</a> &middot; <a href="{pdf_href}" download>Download proposal PDF</a> &middot; <a href="{submit_href}">My Submissions</a> to submit the full draft when ready.</p>
    <p>Use the comments below to discuss scope, sources, and comparisons before the full study is written.</p>
  </section>
"""


def _planned_study_callout(row: StudyRow) -> str:
    title = display_title(row)
    submit_href = html.escape(_submission_portal_href(row))
    contributing_href = html.escape(_contributing_href(row))
    return f"""
  <section class="planned-callout" aria-labelledby="planned-callout-heading">
    <h2 id="planned-callout-heading">Help shape this study</h2>
    <p>This paper is <strong>planned but not yet written</strong>. We are soliciting proposals from contributors who would like to author <strong>{html.escape(title)}</strong>.</p>
    <p>Use the comments below to discuss the <strong>scope</strong> of the study: which questions it should answer, what to include or leave out, which primary texts matter most, and how it should compare with other traditions. Your input here helps define the paper before anyone writes it.</p>
    <p>If you want to take on the study, follow our submission process on <a href="{submit_href}">My Submissions</a> &mdash; sign in with GitHub, propose the study, and wait for maintainer approval before submitting a draft. Read the study format in <a href="{contributing_href}">CONTRIBUTING.md</a> before you start.</p>
  </section>
"""


DISCUSS_CSS = """:root {
  --bg: #f7f3ec;
  --surface: #fffdf9;
  --text: #2a241c;
  --text-muted: #5c5348;
  --accent: #1f5f8b;
  --accent-soft: #e8f1f8;
  --border: #ddd3c4;
  --radius: 10px;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Segoe UI", system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.55;
}
a { color: var(--accent); }
.wrap { max-width: 820px; margin: 0 auto; padding: 16px 20px 48px; }
.discuss-header { margin-bottom: 16px; }
.discuss-toolbar {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 13px;
  margin: 0 0 10px;
  padding: 10px 14px;
  border: 1px solid #d8d2c8;
  border-radius: 8px;
  background: rgba(247, 244, 239, 0.92);
  -webkit-backdrop-filter: blur(8px);
  backdrop-filter: blur(8px);
}
.discuss-toolbar-row {
  display: grid;
  align-items: center;
  gap: 8px 14px;
  grid-template-columns: minmax(0, 1fr) minmax(0, auto) minmax(0, 1fr);
}
.discuss-toolbar-back { grid-column: 1; justify-self: start; min-width: 0; }
.discuss-toolbar-actions {
  grid-column: 3;
  justify-self: end;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 8px 12px;
  min-width: 0;
  text-align: right;
}
.discuss-toolbar-feedback { font-size: 12px; font-weight: 600; white-space: nowrap; }
.discuss-toolbar-download { min-width: 0; text-align: right; }
.discuss-toolbar-title {
  grid-column: 2;
  justify-self: center;
  text-align: center;
  margin: 0;
  min-width: 0;
  font-size: 14px;
  font-weight: 700;
  color: #2c241c;
  line-height: 1.35;
}
.discuss-toolbar-link { color: #1a5276; text-decoration: none; font-weight: 600; }
.discuss-toolbar-link:hover { color: #13405c; }
.discuss-toolbar-link:focus-visible { outline: 2px solid #1a5276; outline-offset: 2px; }
.discuss-toolbar-download::after { content: " \\2193"; font-weight: 700; }
.discuss-header-note { margin: 0; font-size: 0.82rem; color: var(--text-muted); line-height: 1.45; }
.btn-sm { padding: 5px 11px; font-size: 0.85rem; }
.btn-tiny { padding: 5px 11px; font-size: 0.82rem; }
.btn-auth { cursor: pointer; font: inherit; flex-shrink: 0; }
.btn {
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
  cursor: pointer;
  font-family: inherit;
}
.btn-primary { background: var(--accent); border-color: var(--accent); color: #fff; }
.btn:hover { filter: brightness(0.97); }
.btn:disabled { opacity: 0.55; cursor: not-allowed; }
.status-badge {
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
}
.status-badge--draft { background: #fff4e5; color: #9a6700; }
.status-badge--planned { background: #f5ebe0; color: #8b6914; }
.planned-callout {
  margin: 0 0 20px;
  padding: 18px 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 4px solid #b45309;
  border-radius: var(--radius);
}
.planned-callout h2 { margin: 0 0 10px; font-size: 1.05rem; color: #92400e; }
.planned-callout p { margin: 0 0 10px; font-size: 0.95rem; color: var(--text); }
.planned-callout p:last-child { margin-bottom: 0; }
.auth-row { display: grid; gap: 10px; max-width: 420px; }
.auth-row label { display: grid; gap: 4px; font-size: 0.9rem; font-weight: 600; }
.auth-row input, .auth-row textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font: inherit;
}
.auth-row textarea { min-height: 120px; resize: vertical; }
.turnstile-wrap { margin: 10px 0; min-height: 65px; }
.comments { list-style: none; padding: 0; margin: 0; display: grid; gap: 14px; }
.comment {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px 16px;
  background: #fff;
}
.comment.is-new { box-shadow: 0 0 0 2px var(--accent-soft); }
.comment-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 8px;
}
.comment-meta-main { display: flex; flex-wrap: wrap; gap: 8px 12px; align-items: baseline; }
.comment-permalink { color: var(--text-muted); text-decoration: none; font-weight: 700; opacity: 0.5; }
.comment-permalink:hover { color: var(--accent); opacity: 1; }
.comment-actions { display: inline-flex; gap: 8px; flex: 0 0 auto; }
.comment-action {
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-muted);
  border-radius: 999px;
  padding: 2px 10px;
  font: inherit;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
}
.comment-action:hover { color: var(--accent); border-color: #a5c4d9; background: var(--accent-soft); }
.comment-action--hide:hover { color: #9a6700; border-color: #e6c27a; background: #fff4e5; }
.comment-body { white-space: pre-wrap; word-break: break-word; }
.comment-body a { color: var(--accent); }
.comment-body code {
  font-family: Consolas, "Courier New", monospace;
  font-size: 0.9em;
  background: var(--accent-soft);
  padding: 1px 5px;
  border-radius: 4px;
}
.comment-children {
  list-style: none;
  margin: 14px 0 0;
  padding: 0 0 0 16px;
  border-left: 2px solid var(--border);
  display: grid;
  gap: 14px;
}
.comment-reply { margin-top: 12px; }
.reply-form { display: grid; gap: 8px; }
.reply-form textarea {
  width: 100%;
  min-height: 80px;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font: inherit;
  resize: vertical;
}
.new-divider {
  list-style: none;
  text-align: center;
  font-size: 0.74rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #b45309;
  margin: 2px 0;
  position: relative;
}
.new-divider span { background: var(--bg); padding: 0 10px; position: relative; z-index: 1; }
.new-divider::before {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  border-top: 1px solid #e6c27a;
}
.comments-list-actions { margin-top: 16px; text-align: center; }
.skeleton-comment {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px 16px;
  background: var(--surface);
}
.skeleton-line {
  height: 10px;
  border-radius: 4px;
  background: var(--border);
  opacity: 0.6;
  margin: 8px 0;
  animation: skeleton-pulse 1.2s ease-in-out infinite;
}
.skeleton-line.short { width: 32%; }
@keyframes skeleton-pulse { 0%, 100% { opacity: 0.35; } 50% { opacity: 0.7; } }
.alert { padding: 10px 12px; border-radius: 8px; margin-bottom: 12px; font-size: 0.92rem; }
.alert-error { background: #fdecea; color: #8a1f11; border: 1px solid #f5c2c0; }
.alert-success { background: #edf7ed; color: #1e4620; border: 1px solid #c8e6c9; }
.alert-info { background: var(--accent-soft); color: #13466a; border: 1px solid #c5dcee; }
.hidden { display: none !important; }
.action-panel {
  background: var(--surface);
  border: 2px solid var(--border);
  border-radius: var(--radius);
  padding: 14px 16px;
  margin-bottom: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
}
.action-panel h2 { margin: 0 0 10px; font-size: 1rem; }
.action-panel .auth-row { max-width: none; }
.auth-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.auth-sign-in-note { margin: 0 0 12px; font-size: 0.9rem; color: var(--text-muted); }
.compose-actions { display: flex; gap: 8px; margin-top: 16px; align-items: center; }
.comments-section { margin-top: 8px; }
.comments-section h2 { margin: 0 0 12px; font-size: 1rem; }
@media (max-width: 640px) {
  .discuss-toolbar-row { grid-template-columns: 1fr 1fr; }
  .discuss-toolbar-back { grid-column: 1; }
  .discuss-toolbar-actions { grid-column: 1 / -1; justify-self: stretch; justify-content: flex-end; }
  .discuss-toolbar-title { grid-column: 1 / -1; white-space: normal; }
  .discuss-toolbar-feedback { white-space: normal; }
}
@media (max-width: 600px) {
  .auth-grid { grid-template-columns: 1fr; }
}
@media (prefers-reduced-motion: reduce) {
  .skeleton-line { animation: none; }
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #171411;
    --surface: #211c18;
    --text: #f2ebe1;
    --text-muted: #b9aea0;
    --accent: #7ebbed;
    --accent-soft: #1a3344;
    --border: #3a322b;
  }
  .comment { background: #1a1613; }
  .alert-error { background: #3a1714; color: #ffb4a9; border-color: #7f2d25; }
  .alert-success { background: #142818; color: #a8d5a8; border-color: #2f5c31; }
  .btn-primary { color: #102030; }
  .auth-row input, .auth-row textarea, .reply-form textarea {
    background-color: #26201b;
    color: var(--text);
    border-color: #433931;
  }
  .auth-row textarea:focus, .auth-row input:focus, .reply-form textarea:focus {
    border-color: var(--accent);
    outline: none;
  }
  .discuss-toolbar { background: rgba(26, 24, 21, 0.92); border-color: #423b33; }
  .discuss-toolbar-link { color: #7ebbed; }
  .discuss-toolbar-link:hover { color: #b8daf3; }
  .discuss-toolbar-title { color: #f5f1ec; }
  .planned-callout { background: #211c18; border-color: #3a322b; border-left-color: #d97706; }
  .planned-callout h2 { color: #fcd34d; }
  .new-divider { color: #f0c78a; }
  .new-divider::before { border-top-color: #6b4518; }
}
"""


DISCUSS_JS = r"""(() => {
  const cfg = window.AMD_DISCUSS || {};
  const STUDY_SLUG = cfg.slug;
  const STUDY_TITLE = cfg.title;
  const SITE_HOST = cfg.siteHost;
  const API_FALLBACK = cfg.apiFallback;
  const TURNSTILE_SITE_KEY = cfg.turnstileSiteKey;
  const TURNSTILE_ACTION = cfg.turnstileAction;
  const PAGE_SIZE = 50;

  const apiBase = () => (window.location.hostname === SITE_HOST ? "" : API_FALLBACK);

  const alertEl = document.getElementById("discuss-alert");
  const commentList = document.getElementById("comment-list");
  const commentsEmpty = document.getElementById("comments-empty");
  const loadMoreWrap = document.getElementById("load-more-wrap");
  const loadMoreBtn = document.getElementById("load-more");
  const signInPanel = document.getElementById("sign-in-panel");
  const commentPanel = document.getElementById("comment-panel");
  const magicForm = document.getElementById("magic-link-form");
  const commentForm = document.getElementById("comment-form");
  const toolbarAuthBtn = document.getElementById("toolbar-auth-btn");
  let currentSession = { loggedIn: false };
  let signInTurnstileWidgetId = null;
  let signInTurnstileTimer = null;
  let allComments = [];
  let nextOffset = 0;
  let hasMore = false;
  let initialLastSeen = null;
  const DISCUSS_SEEN_KEY = "amd-discuss-seen";
  const DISPLAY_NAME_KEY = "amd-discuss-name";

  const readDiscussSeenMap = () => {
    try {
      return JSON.parse(localStorage.getItem(DISCUSS_SEEN_KEY) || "{}");
    } catch {
      return {};
    }
  };

  const lastSeenForSlug = () => Number(readDiscussSeenMap()[STUDY_SLUG] || 0);

  const markDiscussionSeen = (comments) => {
    if (!Array.isArray(comments) || !comments.length) return;
    const latest = comments.reduce(
      (max, item) => Math.max(max, Number(item.createdAt) || 0),
      0,
    );
    if (!latest) return;
    try {
      const seen = readDiscussSeenMap();
      seen[STUDY_SLUG] = Math.max(Number(seen[STUDY_SLUG] || 0), latest);
      localStorage.setItem(DISCUSS_SEEN_KEY, JSON.stringify(seen));
    } catch {
      // ignore storage errors
    }
  };

  const showAlert = (kind, message) => {
    alertEl.className = `alert alert-${kind}`;
    alertEl.textContent = message;
    alertEl.classList.remove("hidden");
  };

  const withTurnstile = (fn) => {
    turnstile.ready(fn);
  };

  const signInTurnstileEl = () => document.getElementById("sign-in-turnstile");

  const resetSignInTurnstileContainer = () => {
    const wrap = signInPanel?.querySelector(".turnstile-wrap");
    if (!wrap) return;
    wrap.innerHTML = `<div id="sign-in-turnstile" class="cf-turnstile" data-sitekey="${TURNSTILE_SITE_KEY}" data-action="${TURNSTILE_ACTION}"></div>`;
  };

  const destroySignInTurnstile = () => {
    withTurnstile(() => {
      if (signInTurnstileWidgetId != null) {
        try {
          turnstile.remove(signInTurnstileWidgetId);
        } catch {
          // ignore stale widget ids
        }
        signInTurnstileWidgetId = null;
      }
    });
  };

  const mountSignInTurnstile = () => {
    if (!signInPanel || signInPanel.classList.contains("hidden")) return;
    withTurnstile(() => {
      let widget = signInTurnstileEl();
      if (!widget) {
        resetSignInTurnstileContainer();
        widget = signInTurnstileEl();
      }
      if (!widget) return;
      if (signInTurnstileWidgetId != null) {
        try {
          turnstile.remove(signInTurnstileWidgetId);
        } catch {
          // ignore stale widget ids
        }
        signInTurnstileWidgetId = null;
      }
      signInTurnstileWidgetId = turnstile.render(widget, {
        sitekey: TURNSTILE_SITE_KEY,
        action: TURNSTILE_ACTION,
        theme: "auto",
        "refresh-expired": "auto",
      });
    });
  };

  const scheduleSignInTurnstile = () => {
    if (signInTurnstileTimer) clearTimeout(signInTurnstileTimer);
    signInTurnstileTimer = setTimeout(() => {
      signInTurnstileTimer = null;
      requestAnimationFrame(() => mountSignInTurnstile());
    }, 150);
  };

  const showSignInPanel = () => {
    signInPanel.classList.remove("hidden");
    commentPanel.classList.add("hidden");
    destroySignInTurnstile();
    resetSignInTurnstileContainer();
    scheduleSignInTurnstile();
    signInPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    const emailInput = magicForm.querySelector('input[name="email"]');
    if (emailInput) emailInput.focus();
  };

  const hideSignInPanel = () => {
    signInPanel.classList.add("hidden");
    destroySignInTurnstile();
    resetSignInTurnstileContainer();
  };

  const showCommentPanel = () => {
    hideSignInPanel();
    commentPanel.classList.remove("hidden");
  };

  const hideCommentPanel = () => {
    commentPanel.classList.add("hidden");
  };

  const openLoginFlow = () => {
    showSignInPanel();
  };

  const handleLogout = async () => {
    try {
      await fetchJson("/api/discuss-auth/logout", { method: "POST", body: "{}" });
      setAuthUi({ loggedIn: false });
      renderComments();
    } catch (err) {
      showAlert("error", err.message);
    }
  };

  toolbarAuthBtn.addEventListener("click", () => {
    if (currentSession.loggedIn) {
      handleLogout();
      return;
    }
    openLoginFlow();
  });

  const params = new URLSearchParams(window.location.search);
  const discussError = params.get("discuss_error");
  if (discussError) {
    showAlert("error", decodeURIComponent(discussError));
    showSignInPanel();
    params.delete("discuss_error");
    const clean = params.toString();
    history.replaceState(null, "", clean ? `?${clean}` : window.location.pathname);
  }

  const fetchJson = async (path, options = {}) => {
    const response = await fetch(apiBase() + path, {
      credentials: "include",
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || data.message || `Request failed (${response.status})`);
    }
    return data;
  };

  const turnstileToken = () =>
    signInTurnstileEl()?.closest("form")?.querySelector('input[name="cf-turnstile-response"]')?.value
    || magicForm.querySelector('input[name="cf-turnstile-response"]')?.value
    || "";

  const resetSignInTurnstile = () => {
    if (signInTurnstileWidgetId != null) {
      withTurnstile(() => {
        try {
          turnstile.reset(signInTurnstileWidgetId);
        } catch {
          destroySignInTurnstile();
          resetSignInTurnstileContainer();
          scheduleSignInTurnstile();
        }
      });
      return;
    }
    scheduleSignInTurnstile();
  };

  const formatWhen = (ms) => {
    try {
      return new Date(Number(ms)).toLocaleString(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      });
    } catch {
      return "";
    }
  };

  const escapeHtml = (value) => String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

  const renderMarkdown = (raw) => {
    let text = escapeHtml(raw == null ? "" : raw);
    const codes = [];
    text = text.replace(/`([^`]+)`/g, (m, code) => {
      codes.push(code);
      return `\u0000CODE${codes.length - 1}\u0000`;
    });
    text = text.replace(
      /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
      (m, label, url) => `<a href="${url}" target="_blank" rel="noopener nofollow">${label}</a>`,
    );
    text = text.replace(
      /(^|[\s(])(https?:\/\/[^\s<]+)/g,
      (m, pre, url) => `${pre}<a href="${url}" target="_blank" rel="noopener nofollow">${url}</a>`,
    );
    text = text.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    text = text.replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, "$1<em>$2</em>");
    text = text.replace(/(^|[^_])_([^_\n]+)_(?!_)/g, "$1<em>$2</em>");
    text = text.replace(/\u0000CODE(\d+)\u0000/g, (m, i) => `<code>${codes[Number(i)]}</code>`);
    return text;
  };

  const commentActionButtons = (item) => {
    const parts = [];
    if (currentSession.loggedIn) {
      parts.push(`<button type="button" class="comment-action comment-action--reply" data-action="reply" data-comment-id="${escapeHtml(item.id)}">Reply</button>`);
    }
    if (item.canDelete) {
      parts.push(`<button type="button" class="comment-action comment-action--delete" data-action="delete" data-comment-id="${escapeHtml(item.id)}">Delete</button>`);
    }
    if (item.canHide) {
      parts.push(`<button type="button" class="comment-action comment-action--hide" data-action="hide" data-comment-id="${escapeHtml(item.id)}">Hide</button>`);
    }
    return parts.join("");
  };

  const buildTree = (comments) => {
    const byId = new Map();
    comments.forEach((c) => byId.set(c.id, { ...c, children: [] }));
    const roots = [];
    byId.forEach((node) => {
      const parent = node.parentId ? byId.get(node.parentId) : null;
      if (parent) {
        parent.children.push(node);
      } else {
        roots.push(node);
      }
    });
    return roots;
  };

  const renderCommentNode = (node, lastSeen) => {
    const isNew = lastSeen && Number(node.createdAt) > lastSeen;
    const idAttr = escapeHtml(node.id);
    const actions = commentActionButtons(node);
    const actionsHtml = actions ? `<span class="comment-actions">${actions}</span>` : "";
    const childrenHtml = node.children.length
      ? `<ul class="comment-children">${node.children.map((c) => renderCommentNode(c, lastSeen)).join("")}</ul>`
      : "";
    return `<li class="comment${isNew ? " is-new" : ""}" id="c-${idAttr}" data-comment-id="${idAttr}">
        <div class="comment-meta">
          <span class="comment-meta-main">
            <strong>${escapeHtml(node.authorName || "Reader")}</strong>
            <time datetime="${node.createdAt}">${formatWhen(node.createdAt)}</time>
            <a class="comment-permalink" href="#c-${idAttr}" aria-label="Permalink to this comment" title="Permalink">#</a>
          </span>
          ${actionsHtml}
        </div>
        <div class="comment-body">${renderMarkdown(node.body)}</div>
        <div class="comment-reply hidden" data-reply-for="${idAttr}"></div>
        ${childrenHtml}
      </li>`;
  };

  const updateLoadMore = () => {
    if (!loadMoreWrap) return;
    loadMoreWrap.classList.toggle("hidden", !hasMore);
  };

  const showCommentsSkeleton = () => {
    commentsEmpty.classList.add("hidden");
    commentList.setAttribute("aria-busy", "true");
    commentList.innerHTML = Array.from({ length: 3 }).map(() =>
      `<li class="skeleton-comment" aria-hidden="true"><div class="skeleton-line short"></div><div class="skeleton-line"></div><div class="skeleton-line"></div></li>`
    ).join("");
  };

  const renderComments = () => {
    commentList.removeAttribute("aria-busy");
    if (!allComments.length) {
      commentList.innerHTML = "";
      commentsEmpty.classList.remove("hidden");
      updateLoadMore();
      return;
    }
    commentsEmpty.classList.add("hidden");
    const lastSeen = initialLastSeen || 0;
    const roots = buildTree(allComments);
    const anyOld = roots.some((n) => Number(n.createdAt) <= lastSeen);
    const html = [];
    let dividerPlaced = false;
    roots.forEach((node) => {
      if (lastSeen && anyOld && !dividerPlaced && Number(node.createdAt) > lastSeen) {
        html.push(`<li class="new-divider"><span>New since your last visit</span></li>`);
        dividerPlaced = true;
      }
      html.push(renderCommentNode(node, lastSeen));
    });
    commentList.innerHTML = html.join("");
    updateLoadMore();
  };

  const setAuthUi = (session) => {
    currentSession = session || { loggedIn: false };
    const loggedIn = Boolean(currentSession.loggedIn);
    if (loggedIn) {
      toolbarAuthBtn.textContent = "Log out";
      toolbarAuthBtn.classList.remove("btn-primary");
      toolbarAuthBtn.setAttribute("aria-label", "Sign out of discussion");
      showCommentPanel();
    } else {
      toolbarAuthBtn.textContent = "Log in";
      toolbarAuthBtn.classList.add("btn-primary");
      toolbarAuthBtn.setAttribute("aria-label", "Sign in to discuss");
      hideCommentPanel();
      hideSignInPanel();
    }
  };

  const removeComment = async (commentId, action) => {
    const prompt = action === "hide" ? "Hide this comment?" : "Delete this comment?";
    if (!window.confirm(prompt)) return;
    const path = action === "hide"
      ? `/api/discussions/${encodeURIComponent(STUDY_SLUG)}/comments/${encodeURIComponent(commentId)}/hide`
      : `/api/discussions/${encodeURIComponent(STUDY_SLUG)}/comments/${encodeURIComponent(commentId)}/delete`;
    await fetchJson(path, { method: "POST", body: "{}" });
    showAlert("success", action === "hide" ? "Comment hidden." : "Comment deleted.");
    await loadComments();
  };

  const openReply = (commentId) => {
    commentList.querySelectorAll(".comment-reply").forEach((el) => {
      if (el.dataset.replyFor !== commentId) {
        el.classList.add("hidden");
        el.innerHTML = "";
      }
    });
    const box = commentList.querySelector(`.comment-reply[data-reply-for="${commentId}"]`);
    if (!box) return;
    if (!box.classList.contains("hidden") && box.innerHTML) {
      box.classList.add("hidden");
      box.innerHTML = "";
      return;
    }
    box.innerHTML = `<form class="reply-form">
        <textarea name="body" maxlength="8192" required placeholder="Write a reply&hellip;"></textarea>
        <div class="compose-actions">
          <button type="submit" class="btn btn-primary btn-tiny">Post reply</button>
          <button type="button" class="btn btn-tiny reply-cancel">Cancel</button>
        </div>
      </form>`;
    box.classList.remove("hidden");
    const ta = box.querySelector("textarea");
    if (ta) ta.focus();
  };

  commentList.addEventListener("click", async (event) => {
    const cancel = event.target.closest(".reply-cancel");
    if (cancel) {
      const box = cancel.closest(".comment-reply");
      if (box) {
        box.classList.add("hidden");
        box.innerHTML = "";
      }
      return;
    }
    const button = event.target.closest(".comment-action");
    if (!button) return;
    const commentId = button.dataset.commentId;
    const action = button.dataset.action;
    if (!commentId || !action) return;
    if (action === "reply") {
      openReply(commentId);
      return;
    }
    button.disabled = true;
    try {
      await removeComment(commentId, action);
    } catch (err) {
      showAlert("error", err.message);
      button.disabled = false;
    }
  });

  const postComment = (body, parentId) =>
    fetchJson(`/api/discussions/${encodeURIComponent(STUDY_SLUG)}/comments`, {
      method: "POST",
      body: JSON.stringify({ body, title: STUDY_TITLE, parentId: parentId || null }),
    });

  commentList.addEventListener("submit", async (event) => {
    const form = event.target.closest(".reply-form");
    if (!form) return;
    event.preventDefault();
    const box = form.closest(".comment-reply");
    const parentId = box ? box.dataset.replyFor : null;
    const body = form.body.value.trim();
    if (!body) {
      showAlert("error", "Reply cannot be empty.");
      return;
    }
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.disabled = true;
    try {
      await postComment(body, parentId);
      showAlert("success", "Reply posted.");
      await loadComments();
    } catch (err) {
      showAlert("error", err.message);
      if (submitBtn) submitBtn.disabled = false;
    }
  });

  const loadComments = async ({ append = false } = {}) => {
    if (!append) {
      nextOffset = 0;
      allComments = [];
      showCommentsSkeleton();
    } else if (loadMoreBtn) {
      loadMoreBtn.disabled = true;
    }
    try {
      const data = await fetchJson(
        `/api/discussions/${encodeURIComponent(STUDY_SLUG)}?limit=${PAGE_SIZE}&offset=${nextOffset}`,
      );
      const batch = data.comments || [];
      if (initialLastSeen === null) initialLastSeen = lastSeenForSlug();
      allComments = append ? allComments.concat(batch) : batch;
      nextOffset += batch.length;
      hasMore = batch.length === PAGE_SIZE;
      renderComments();
      markDiscussionSeen(allComments);
    } finally {
      if (loadMoreBtn) loadMoreBtn.disabled = false;
    }
  };

  if (loadMoreBtn) {
    loadMoreBtn.addEventListener("click", () => {
      loadComments({ append: true }).catch((err) => showAlert("error", err.message));
    });
  }

  const loadSession = async () => {
    try {
      const session = await fetchJson("/api/discuss-auth/me");
      setAuthUi(session);
      await loadComments();
    } catch (err) {
      setAuthUi({ loggedIn: false });
      showAlert("error", err.message);
    }
  };

  const savedName = (() => {
    try {
      return localStorage.getItem(DISPLAY_NAME_KEY) || "";
    } catch {
      return "";
    }
  })();
  if (savedName) {
    const nameInput = magicForm.querySelector('input[name="displayName"]');
    if (nameInput) nameInput.value = savedName;
  }

  magicForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const email = form.email.value.trim();
    const displayName = form.displayName.value.trim();
    const turnstileTokenValue = turnstileToken();
    if (!turnstileTokenValue) {
      scheduleSignInTurnstile();
      showAlert("error", "Complete the verification check below.");
      return;
    }
    try {
      const data = await fetchJson("/api/discuss-auth/magic-link", {
        method: "POST",
        body: JSON.stringify({
          email,
          displayName,
          turnstileToken: turnstileTokenValue,
          returnTo: window.location.href.split("#")[0],
        }),
      });
      try {
        localStorage.setItem(DISPLAY_NAME_KEY, displayName);
      } catch {
        // ignore storage errors
      }
      showAlert("success", data.message || "Check your email for a sign-in link.");
      resetSignInTurnstile();
    } catch (err) {
      showAlert("error", err.message);
      resetSignInTurnstile();
    }
  });

  commentForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const body = form.body.value.trim();
    if (!body) {
      showAlert("error", "Comment cannot be empty.");
      return;
    }
    try {
      await postComment(body, null);
      form.body.value = "";
      showAlert("success", "Comment posted.");
      await loadComments();
      const textarea = form.querySelector('textarea[name="body"]');
      if (textarea) textarea.focus();
    } catch (err) {
      showAlert("error", err.message);
    }
  });

  loadSession().catch((err) => showAlert("error", err.message));
})();
"""


def render_discussion_page(row: StudyRow) -> str:
    title = display_title(row)
    links = _relative_links(row)
    status_note = ""
    if row.status == StudyStatus.DRAFT:
        status_note = ' <span class="status-badge status-badge--draft">Draft</span>'
    elif row.status == StudyStatus.ONGOING:
        status_note = ' <span class="status-badge status-badge--planned">Planned</span>'
    feedback = feedback_href(title)
    paper_links = _toolbar_paper_links(links)
    header_note = _discussion_header_note(row, feedback)
    if row.status == StudyStatus.ONGOING and has_approved_proposal_stub(row.slug):
        planned_callout = _approved_proposal_callout(row, links)
    elif row.status == StudyStatus.ONGOING:
        planned_callout = _planned_study_callout(row)
    else:
        planned_callout = ""

    assets = links["assets"]
    css_href = html.escape(f"{assets}/{DISCUSS_CSS_NAME}?v={ASSET_VERSION}")
    js_href = html.escape(f"{assets}/{DISCUSS_JS_NAME}?v={ASSET_VERSION}")
    canonical = _canonical_url(row)
    description = f"Reader discussion for the study \u201c{title}\u201d on AnalyticMadhyasthDarshan.org."

    config_json = json.dumps(
        {
            "slug": row.slug,
            "title": title,
            "siteHost": site_base_url().replace("https://", "").replace("http://", "").rstrip("/"),
            "apiFallback": DISCUSSIONS_API_FALLBACK,
            "turnstileSiteKey": TURNSTILE_SITE_KEY,
            "turnstileAction": TURNSTILE_ACTION,
        },
        ensure_ascii=False,
    )
    ld_json = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "DiscussionForumPosting",
            "headline": f"Discussion: {title}",
            "url": canonical,
            "about": title,
            "isPartOf": {
                "@type": "WebSite",
                "name": "AnalyticMadhyasthDarshan.org",
                "url": site_base_url().rstrip("/") + "/",
            },
        },
        ensure_ascii=False,
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>Discussion &mdash; {html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="canonical" href="{html.escape(canonical)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="AnalyticMadhyasthDarshan.org">
<meta property="og:title" content="Discussion &mdash; {html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:url" content="{html.escape(canonical)}">
<meta name="twitter:card" content="summary">
<script type="application/ld+json">
{ld_json}
</script>
<link rel="stylesheet" href="{css_href}">
</head>
<body>
<div class="wrap">
  <header class="discuss-header">
    <nav class="discuss-toolbar" aria-label="Discussion navigation">
      <div class="discuss-toolbar-row">
        <a class="discuss-toolbar-link discuss-toolbar-back" href="{html.escape(links['catalog'])}">&larr; Studies</a>
        <h1 class="discuss-toolbar-title">{html.escape(title)}{status_note}</h1>
        <span class="discuss-toolbar-actions">
{paper_links}          <a class="discuss-toolbar-link discuss-toolbar-feedback" href="{html.escape(feedback)}" rel="noopener">Suggest correction</a>
          <button type="button" id="toolbar-auth-btn" class="btn btn-sm btn-auth btn-primary">Log in</button>
        </span>
      </div>
    </nav>
    {header_note}
  </header>

  <div id="discuss-alert" class="alert hidden" role="status"></div>
{planned_callout}
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
    <form id="comment-form" class="auth-row">
      <label>Your comment<textarea name="body" maxlength="8192" required placeholder="Share a question or comment&hellip;"></textarea></label>
      <div class="compose-actions">
        <button type="submit" class="btn btn-primary">Post comment</button>
      </div>
    </form>
  </section>

  <section class="comments-section" aria-labelledby="comments-heading">
    <h2 id="comments-heading">Comments</h2>
    <ul id="comment-list" class="comments" aria-live="polite"></ul>
    <p id="comments-empty" class="hidden">No comments yet. Be the first to start the discussion.</p>
    <div id="load-more-wrap" class="comments-list-actions hidden">
      <button type="button" id="load-more" class="btn">Load more comments</button>
    </div>
  </section>
</div>

<script src="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit"></script>
<script>window.AMD_DISCUSS = {config_json};</script>
<script src="{js_href}"></script>
</body>
</html>
"""


def write_shared_assets() -> list[Path]:
    target = assets_dir()
    target.mkdir(parents=True, exist_ok=True)
    css_path = target / DISCUSS_CSS_NAME
    js_path = target / DISCUSS_JS_NAME
    css_path.write_text(DISCUSS_CSS, encoding="utf-8")
    js_path.write_text(DISCUSS_JS, encoding="utf-8")
    return [css_path, js_path]


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
        path = write_discussion_page(row)
        if path:
            written.append(path)
    return written


def build_all_discussion_pages() -> list[Path]:
    write_shared_assets()
    written: list[Path] = []
    for table in CATALOG_TABLES:
        written.extend(build_discussion_pages_for_rows(load_catalog_rows(table)))
    return written


def verify_discussion_pages() -> list[str]:
    errors: list[str] = []
    css_path = assets_dir() / DISCUSS_CSS_NAME
    js_path = assets_dir() / DISCUSS_JS_NAME
    if not css_path.is_file():
        errors.append(f"Missing shared discussion stylesheet: {css_path.relative_to(STUDIES.parent)}")
    if not js_path.is_file():
        errors.append(f"Missing shared discussion script: {js_path.relative_to(STUDIES.parent)}")
    for table in CATALOG_TABLES:
        for row in load_catalog_rows(table):
            path = discussion_output_path(row)
            if path is None:
                continue
            if not path.is_file():
                errors.append(f"Missing discussion page for {row.slug}: {path.relative_to(STUDIES.parent)}")
    return errors


def main() -> int:
    written = build_all_discussion_pages()
    print(f"Wrote shared discussion assets to {assets_dir().relative_to(STUDIES.parent)}.")
    print(f"Wrote {len(written)} discussion page(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
