(() => {
  const COMMENTS_LOADING_HTML = "<li class=\"comments-loading\"><span class=\"amd-wait\"><svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 240 240\" aria-hidden=\"true\" focusable=\"false\"><path class=\"goal\" d=\"M120 36H163Q204 36 204 77V120\" transform=\"rotate(0 120 120)\" fill=\"none\" stroke=\"var(--amd-icon,#1A5276)\" stroke-width=\"20\"/><path class=\"goal\" d=\"M120 36H163Q204 36 204 77V120\" transform=\"rotate(90 120 120)\" fill=\"none\" stroke=\"var(--amd-accent,#B47B46)\" stroke-width=\"20\"/><path class=\"goal\" d=\"M120 36H163Q204 36 204 77V120\" transform=\"rotate(180 120 120)\" fill=\"none\" stroke=\"var(--amd-icon,#1A5276)\" stroke-width=\"20\"/><path class=\"goal\" d=\"M120 36H163Q204 36 204 77V120\" transform=\"rotate(270 120 120)\" fill=\"none\" stroke=\"var(--amd-accent,#B47B46)\" stroke-width=\"20\"/><circle cx=\"120\" cy=\"120\" r=\"22\" fill=\"var(--amd-accent,#B47B46)\" stroke=\"none\"/></svg><span class=\"amd-wait-label\">Loading comments&hellip;</span></span></li>";
  const cfg = window.AMD_DISCUSS || {};
  const STUDY_SLUG = cfg.slug;
  const STUDY_TITLE = cfg.title;
  const SITE_HOST = cfg.siteHost;
  const API_FALLBACK = cfg.apiFallback;
  const TURNSTILE_SITE_KEY = cfg.turnstileSiteKey;
  const TURNSTILE_ACTION = cfg.turnstileAction;
  const PAGE_SIZE = 50;
  const AUTH_CACHE_KEY = "amd-discuss-auth-v1";

  const apiBase = () => (window.location.hostname === SITE_HOST ? "" : API_FALLBACK);

  const alertEl = document.getElementById("discuss-alert");
  const commentList = document.getElementById("comment-list");
  const commentsEmpty = document.getElementById("comments-empty");
  const commentsError = document.getElementById("comments-error");
  const commentsRetry = document.getElementById("comments-retry");
  const loadMoreWrap = document.getElementById("load-more-wrap");
  const loadMoreBtn = document.getElementById("load-more");
  const signInPanel = document.getElementById("sign-in-panel");
  const commentPanel = document.getElementById("comment-panel");
  const magicForm = document.getElementById("magic-link-form");
  const commentForm = document.getElementById("comment-form");
  const toolbarAuthBtn = document.getElementById("toolbar-auth-btn");
  const bootstrapSession = window.__amdDiscussAuthBootstrap;
  let currentSession = bootstrapSession && typeof bootstrapSession.loggedIn === "boolean"
    ? { loggedIn: bootstrapSession.loggedIn, isAdmin: Boolean(bootstrapSession.isAdmin) }
    : { loggedIn: false };
  let signInTurnstileWidgetId = null;
  let signInTurnstileTimer = null;
  let turnstileLoadPromise = null;
  let allComments = [];
  let nextOffset = 0;
  let hasMore = false;
  let initialLastSeen = null;
  const DISCUSS_SEEN_KEY = "amd-discuss-seen";
  const DISPLAY_NAME_KEY = "amd-discuss-name";
  let draftOwner = '', drafts = null, authVerified = false;
  const unsavedDrafts = new Set();
  let guestId = new URLSearchParams(location.search).get('discuss_draft');
  if (!/^[a-f0-9-]{36}$/i.test(guestId || '')) {
    try { guestId = sessionStorage.getItem('amd-discuss-guest'); } catch (_) {}
    if (!/^[a-f0-9-]{36}$/i.test(guestId || '')) guestId = crypto.randomUUID();
  }
  try { sessionStorage.setItem('amd-discuss-guest', guestId); } catch (_) {}
  const guestOwner = 'guest:' + guestId;
  const draftStatus = document.getElementById('discussion-draft-status');
  const draftList = document.getElementById('discussion-draft-list');
  const draftStore = () => drafts || (drafts = AMDDiscussionDrafts.create(localStorage, STUDY_SLUG));
  const saveDraft = (parent = '', body = commentForm.body.value) => {
    if (!authVerified || !draftOwner) return;
    try { draftStore().put(draftOwner, parent, body); unsavedDrafts.delete(parent); draftStatus.textContent = 'Saved in this browser. Sign-in never posts your text automatically.'; }
    catch (error) { unsavedDrafts.add(parent); draftStatus.textContent = error.message + ' Download your text before leaving.'; throw error; }
  };
  const saveVisibleDrafts = () => {
    saveDraft();
    commentList.querySelectorAll('.reply-form').forEach(form => saveDraft(form.closest('.comment-reply').dataset.replyFor, form.body.value));
  };
  const paintDrafts = () => {
    draftList.replaceChildren();
    if (!authVerified) return;
    try {
      const owned = draftStore().list(draftOwner);
      const guests = currentSession.loggedIn ? draftStore().list(guestOwner) : [];
      for (const row of [...owned, ...guests]) {
        const button = document.createElement('button'); button.type = 'button'; button.className = 'btn btn-tiny';
        button.textContent = (row.owner === guestOwner && currentSession.loggedIn ? 'Recover pre-sign-in ' : 'Recover saved ') + (row.parent ? 'reply' : 'comment');
        button.onclick = () => {
          if (!confirm('Recover this text into the current composer? Confirm it belongs to you. Download any current text first.')) return;
          try {
            if (row.parent) { openReply(row.parent, true); const form = commentList.querySelector(`.comment-reply[data-reply-for="${CSS.escape(row.parent)}"] .reply-form`); if (!form) throw new Error('Load the original comment before recovering this reply.'); form.body.value = row.body; }
            else { commentForm.body.value = row.body; commentForm.body.focus(); }
            saveDraft(row.parent, row.body);
            if (row.owner !== draftOwner) draftStore().put(row.owner, row.parent, '');
            paintDrafts();
          } catch (error) { showAlert('error', error.message); }
        };
        draftList.append(button, ' ');
      }
    } catch (error) { draftStatus.textContent = error.message; }
  };
  commentForm.addEventListener('input', () => { try { saveDraft(); } catch (_) {} });
  commentList.addEventListener('input', event => { const form = event.target.closest('.reply-form'); if (form) { try { saveDraft(form.closest('.comment-reply').dataset.replyFor, form.body.value); } catch (_) {} } });
  addEventListener('pagehide', () => { try { saveVisibleDrafts(); } catch (_) {} });
  addEventListener('beforeunload', event => { if (unsavedDrafts.size) { event.preventDefault(); event.returnValue = ''; } });
  document.getElementById('discussion-download-draft').onclick = () => {
    const text = [commentForm.body.value, ...Array.from(commentList.querySelectorAll('.reply-form')).map(form => 'Reply to ' + form.closest('.comment-reply').dataset.replyFor + '\n' + form.body.value)].join('\n\n');
    const url = URL.createObjectURL(new Blob([text], {type:'text/plain'}));
    const a = document.createElement('a'); a.href = url; a.download = STUDY_SLUG + '-discussion-draft.txt'; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  const readStudy = document.getElementById("discuss-read-study");
  if (readStudy && /^#[^#\s]+$/.test(location.hash)) {
    try {
      const url = new URL(readStudy.getAttribute("href") || readStudy.href, location.href);
      url.hash = location.hash;
      readStudy.href = url.pathname + url.search + url.hash;
    } catch {
      // Keep the unhashed study link if the current location cannot be parsed.
    }
  }

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

  // fetch() rejects with "Failed to fetch" / "Load failed" / "NetworkError"
  // depending on the browser. None of those mean anything to a reader, and the
  // only useful advice is the same in every case.
  const readableError = (err) => {
    const raw = (err && err.message) || "";
    if (!raw || err instanceof TypeError || /failed to fetch|networkerror|load failed|network request failed/i.test(raw)) {
      return "Could not reach the discussion service. Check your connection and try again.";
    }
    return raw;
  };

  const showAlert = (kind, message) => {
    alertEl.className = `alert alert-${kind}`;
    alertEl.textContent = message;
    alertEl.classList.remove("hidden");
  };

  const loadTurnstile = () => {
    if (window.turnstile) return Promise.resolve(window.turnstile);
    if (!turnstileLoadPromise) {
      turnstileLoadPromise = new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
        script.async = true;
        script.dataset.discussTurnstile = "true";
        script.onload = () => window.turnstile
          ? resolve(window.turnstile)
          : reject(new Error("Could not load the verification check. Check your connection and try again."));
        script.onerror = () => reject(new Error("Could not load the verification check. Check your connection and try again."));
        document.head.appendChild(script);
      }).catch((err) => {
        turnstileLoadPromise = null;
        throw err;
      });
    }
    return turnstileLoadPromise;
  };

  const signInTurnstileEl = () => document.getElementById("sign-in-turnstile");

  const resetSignInTurnstileContainer = () => {
    const wrap = signInPanel?.querySelector(".turnstile-wrap");
    if (!wrap) return;
    wrap.innerHTML = `<div id="sign-in-turnstile" class="cf-turnstile" data-sitekey="${TURNSTILE_SITE_KEY}" data-action="${TURNSTILE_ACTION}"></div>`;
  };

  const destroySignInTurnstile = () => {
    const turnstile = window.turnstile;
    if (!turnstile) {
      signInTurnstileWidgetId = null;
      return;
    }
    if (signInTurnstileWidgetId == null) return;
    try {
      turnstile.remove(signInTurnstileWidgetId);
    } catch {
      // ignore stale widget ids
    }
    signInTurnstileWidgetId = null;
  };

  const mountSignInTurnstile = () => {
    if (!signInPanel || signInPanel.classList.contains("hidden")) return;
    loadTurnstile().then((turnstile) => {
      if (signInPanel.classList.contains("hidden")) return;
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
    }).catch((err) => showAlert("error", readableError(err)));
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
      saveVisibleDrafts();
      await fetchJson("/api/discuss-auth/logout", { method: "POST", body: "{}" });
      setAuthUi({ loggedIn: false });
      await loadComments();
    } catch (err) {
      showAlert("error", readableError(err));
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
    showAlert("error", discussError);
    showSignInPanel();
    params.delete("discuss_error");
    const clean = params.toString();
    history.replaceState(null, "", clean ? `?${clean}` : window.location.pathname);
  }

  const fetchJson = async (path, options = {}) => {
    const commentWrite = options.method === 'POST' && path.endsWith('/comments');
    let response;
    try { response = await fetch(apiBase() + path, {
      credentials: "include",
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    }); } catch (error) {
      if (commentWrite) throw new Error('Could not confirm whether your comment was posted. Your text is kept. Reload the comments and check before posting again.');
      throw error;
    }
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      if (response.status === 401) {
        try { saveVisibleDrafts(); } catch (_) {}
        toolbarAuthBtn.textContent = 'Sign in with email';
        currentSession = {loggedIn:false};
        showSignInPanel();
      }
      const message = typeof data.error === "string" ? data.error : data.error?.message || data.message;
      const retryAfter = response.headers.get("Retry-After");
      const guidance = response.status === 429 && retryAfter
        ? ` Retry after ${retryAfter} seconds.`
        : "";
      throw new Error((message || `Request failed (${response.status})`) + guidance + (commentWrite && response.status >= 500 ? ' Check the comments before posting again; your text is kept.' : ''));
    }
    return data;
  };

  const turnstileToken = () =>
    signInTurnstileEl()?.closest("form")?.querySelector('input[name="cf-turnstile-response"]')?.value
    || magicForm.querySelector('input[name="cf-turnstile-response"]')?.value
    || "";

  const resetSignInTurnstile = () => {
    if (signInTurnstileWidgetId != null) {
      const turnstile = window.turnstile;
      if (!turnstile) {
        signInTurnstileWidgetId = null;
        scheduleSignInTurnstile();
        return;
      }
      try {
        turnstile.reset(signInTurnstileWidgetId);
      } catch {
        destroySignInTurnstile();
        resetSignInTurnstileContainer();
        scheduleSignInTurnstile();
      }
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

  const showCommentsLoading = () => {
    commentsEmpty.classList.add("hidden");
    if (commentsError) commentsError.classList.add("hidden");
    commentList.setAttribute("aria-busy", "true");
    commentList.innerHTML = COMMENTS_LOADING_HTML;
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
    paintDrafts();
  };

  const setAuthUi = (session) => {
    const nextOwner = session?.loggedIn && session.userId ? 'user:' + session.userId : guestOwner;
    if (authVerified && draftOwner !== nextOwner) {
      try { saveVisibleDrafts(); } catch (error) { showAlert('error', error.message); return; }
      commentForm.body.value = '';
      commentList.querySelectorAll('.comment-reply').forEach(box => { box.innerHTML = ''; box.classList.add('hidden'); });
    }
    currentSession = session || { loggedIn: false };
    const changed = !authVerified || draftOwner !== nextOwner;
    draftOwner = nextOwner; authVerified = true;
    if (changed) {
      try { const row = draftStore().get(draftOwner); if (row && !commentForm.body.value) commentForm.body.value = row.body; }
      catch (error) { draftStatus.textContent = error.message; }
    }
    paintDrafts();
    const loggedIn = Boolean(currentSession.loggedIn);
    document.documentElement.dataset.discussAuth = loggedIn ? "signed-in" : "signed-out";
    try {
      sessionStorage.setItem(AUTH_CACHE_KEY, JSON.stringify({
        loggedIn,
        isAdmin: loggedIn ? Boolean(currentSession.isAdmin) : false,
        checkedAt: Date.now(),
      }));
    } catch {
      // storage can be unavailable
    }
    if (loggedIn) {
      toolbarAuthBtn.textContent = "Sign out of discussions";
      toolbarAuthBtn.classList.remove("btn-primary");
      toolbarAuthBtn.setAttribute("aria-label", "Sign out of discussion");
      showCommentPanel();
    } else {
      toolbarAuthBtn.textContent = "Sign in with email";
      toolbarAuthBtn.classList.add("btn-primary");
      toolbarAuthBtn.setAttribute("aria-label", "Sign in to discuss");
      commentPanel.classList.remove("hidden");
      hideSignInPanel();
    }
    commentForm.querySelector('button[type="submit"]').textContent = loggedIn ? 'Post comment' : 'Sign in to post';
  };

  const removeComment = async (commentId, action) => {
    const prompt = action === "hide" ? "Hide this comment?" : "Delete this comment?";
    if (!window.confirm(prompt)) return;
    const path = action === "hide"
      ? `/api/discussions/${encodeURIComponent(STUDY_SLUG)}/comments/${encodeURIComponent(commentId)}/hide`
      : `/api/discussions/${encodeURIComponent(STUDY_SLUG)}/comments/${encodeURIComponent(commentId)}/delete`;
    const comment = allComments.find((item) => item.id === commentId);
    if (!comment || !Number.isSafeInteger(Number(comment.updatedAt))) {
      throw new Error("Reload the discussion before changing this comment.");
    }
    await fetchJson(path, {
      method: "POST",
      body: JSON.stringify({sourceUpdatedAt: Number(comment.updatedAt)}),
    });
    showAlert("success", action === "hide" ? "Comment hidden." : "Comment deleted.");
    await loadComments();
  };

  const openReply = (commentId, force = false) => {
    try { saveVisibleDrafts(); } catch (error) { showAlert('error', error.message); return; }
    commentList.querySelectorAll(".comment-reply").forEach((el) => {
      if (el.dataset.replyFor !== commentId) {
        el.classList.add("hidden");
        el.innerHTML = "";
      }
    });
    const box = commentList.querySelector(`.comment-reply[data-reply-for="${CSS.escape(commentId)}"]`);
    if (!box) return;
    if (!force && !box.classList.contains("hidden") && box.innerHTML) {
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
    try { const row = draftStore().get(draftOwner, commentId); if (row && ta) ta.value = row.body; } catch (error) { showAlert('error', error.message); }
    if (ta) ta.focus();
  };

  commentList.addEventListener("click", async (event) => {
    const cancel = event.target.closest(".reply-cancel");
    if (cancel) {
      try { saveVisibleDrafts(); } catch (error) { showAlert('error', error.message); return; }
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
      showAlert("error", readableError(err));
      button.disabled = false;
    }
  });

  const postComment = async (body, parentId) => {
    const verified = await fetchJson('/api/discuss-auth/me');
    if (!verified.loggedIn || 'user:' + verified.userId !== draftOwner) {
      setAuthUi(verified);
      throw new Error('Discussion sign-in changed. Your draft stays with its original account. Sign in to that account to continue.');
    }
    return fetchJson(`/api/discussions/${encodeURIComponent(STUDY_SLUG)}/comments`, {
      method: "POST",
      body: JSON.stringify({ body, title: STUDY_TITLE, parentId: parentId || null }),
    });
  };

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
    if (submitBtn?.disabled) return;
    if (submitBtn) submitBtn.disabled = true;
    form.body.readOnly = true;
    try {
      saveDraft(parentId, form.body.value);
      if (!currentSession.loggedIn) { showSignInPanel(); return; }
      await postComment(body, parentId);
      form.body.value = '';
      try { draftStore().put(draftOwner, parentId, ''); } catch (_) { /* Keep a newer draft written in another tab. */ }
      showAlert("success", "Reply posted.");
      await loadComments();
    } catch (err) {
      showAlert("error", readableError(err));
    } finally {
      if (submitBtn) submitBtn.disabled = false;
      form.body.readOnly = false;
    }
  });

  const loadComments = async ({ append = false } = {}) => {
    try { saveVisibleDrafts(); } catch (error) { showAlert('error', error.message); return; }
    if (!append) {
      nextOffset = 0;
      allComments = [];
      showCommentsLoading();
    } else if (loadMoreBtn) {
      loadMoreBtn.disabled = true;
    }
    try {
      const data = await fetchJson(
        `/api/discussions/${encodeURIComponent(STUDY_SLUG)}?limit=${PAGE_SIZE}&offset=${nextOffset}`,
      );
      if (data.viewer && typeof data.viewer.loggedIn === "boolean") {
        setAuthUi(data.viewer);
      } else {
        // Keep the page compatible while an older Worker deployment is still
        // serving the comments response during rollout.
        try {
          setAuthUi(await fetchJson("/api/discuss-auth/me"));
        } catch {
          setAuthUi({ loggedIn: false });
        }
      }
      const batch = data.comments || [];
      if (initialLastSeen === null) initialLastSeen = lastSeenForSlug();
      allComments = append ? allComments.concat(batch) : batch;
      nextOffset += batch.length;
      hasMore = typeof data.meta?.hasMore === "boolean" ? data.meta.hasMore : batch.length === PAGE_SIZE;
      renderComments();
      markDiscussionSeen(allComments);
      if (commentsError) commentsError.classList.add("hidden");
    } catch (err) {
      if (commentList && !append) {
        commentList.innerHTML = "";
        commentList.removeAttribute("aria-busy");
      }
      if (commentsEmpty) commentsEmpty.classList.add("hidden");
      if (commentsError) commentsError.classList.remove("hidden");
      throw err;
    } finally {
      if (loadMoreBtn) loadMoreBtn.disabled = false;
    }
  };

  if (commentsRetry) {
    commentsRetry.addEventListener("click", () => {
      loadComments().catch((err) => showAlert("error", readableError(err)));
    });
  }

  if (loadMoreBtn) {
    loadMoreBtn.addEventListener("click", () => {
      loadComments({ append: true }).catch((err) => showAlert("error", readableError(err)));
    });
  }

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
      saveVisibleDrafts();
      const returnUrl = new URL(location.href);
      returnUrl.searchParams.delete('discuss_error');
      returnUrl.searchParams.set('discuss_draft', guestId);
      const data = await fetchJson("/api/discuss-auth/magic-link", {
        method: "POST",
        body: JSON.stringify({
          email,
          displayName,
          turnstileToken: turnstileTokenValue,
          returnTo: returnUrl.href,
        }),
      });
      try {
        localStorage.setItem(DISPLAY_NAME_KEY, displayName);
      } catch {
        // ignore storage errors
      }
      showAlert("success", data.message || "Check your email for a sign-in link.");
      paintDrafts();
      resetSignInTurnstile();
    } catch (err) {
      showAlert("error", readableError(err));
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
    const button = form.querySelector('button[type="submit"]');
    if (button.disabled) return;
    button.disabled = true;
    form.body.readOnly = true;
    try {
      saveDraft();
      if (!currentSession.loggedIn) { showSignInPanel(); return; }
      await postComment(body, null);
      form.body.value = "";
      try { draftStore().put(draftOwner, '', ''); } catch (_) { /* Keep a newer draft written in another tab. */ }
      showAlert("success", "Comment posted.");
      await loadComments();
      const textarea = form.querySelector('textarea[name="body"]');
      if (textarea) textarea.focus();
    } catch (err) {
      showAlert("error", readableError(err));
    } finally {
      button.disabled = false;
      form.body.readOnly = false;
    }
  });

  addEventListener('pageshow', event => { if (event.persisted) loadComments().catch(error => showAlert('error', readableError(error))); });
  document.addEventListener('visibilitychange', () => { if (!document.hidden && authVerified) loadComments().catch(error => showAlert('error', readableError(error))); });
  loadComments().catch((err) => showAlert("error", readableError(err)));
})();
