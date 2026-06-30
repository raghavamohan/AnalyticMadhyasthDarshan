(() => {
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
