const ORIGIN = "https://analyticmadhyasthdarshan.org";
const GITHUB_RAW =
  "https://raw.githubusercontent.com/raghavamohan/AnalyticMadhyasthDarshan/master";
const PROTOCOL_VERSIONS = ["2025-06-18", "2025-03-26", "2024-11-05"];
const DEFAULT_PROTOCOL = PROTOCOL_VERSIONS[0];
const CITATION_AUTHOR = "Raghav Mohan";
const SLUG_RE = /^[A-Za-z0-9-]+$/;
const CATALOG_SOURCES = [
  ["/Studies/catalog-topical.json", "topical"],
  ["/Studies/catalog-formal.json", "formal"],
  ["/Studies/catalog-applied.json", "applied"],
];
const RESOURCES = [
  {
    uri: "studies://catalog-all",
    name: "Unified study catalog",
    mimeType: "application/json",
    path: "/Studies/catalog-all.json",
  },
  {
    uri: "studies://glossary",
    name: "Shared glossary",
    mimeType: "application/json",
    path: "/Studies/glossary.json",
  },
  {
    uri: "studies://feed",
    name: "Study change feed",
    mimeType: "application/feed+json",
    path: "/Studies/feed.json",
  },
  {
    uri: "studies://start-here",
    name: "Recommended reading path",
    mimeType: "application/json",
    path: "/Studies/start-here.json",
  },
];
const RESOURCE_TEMPLATES = [
  {
    uriTemplate: "studies://study/{slug}",
    name: "Study markdown",
    description:
      "Canonical markdown for one published study. Replace {slug} with the catalog directory name.",
    mimeType: "text/markdown",
  },
];

const CORS_HEADERS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET, HEAD, POST, OPTIONS",
  "access-control-allow-headers":
    "content-type, mcp-session-id, mcp-protocol-version, accept",
  "access-control-expose-headers": "mcp-session-id, mcp-protocol-version",
};

const CARD_HEADERS = {
  "content-type": "application/json",
  "cache-control": "public, max-age=3600",
  etag: `"${CARD_ETAG}"`,
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET, HEAD, OPTIONS",
};

function jsonHeaders(extra) {
  return {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
    ...CORS_HEADERS,
    ...(extra || {}),
  };
}

function jsonResponse(status, payload, extraHeaders) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: jsonHeaders(extraHeaders),
  });
}

function emptyResponse(status, extraHeaders) {
  return new Response(null, {
    status,
    headers: { ...CORS_HEADERS, ...(extraHeaders || {}) },
  });
}

function absoluteFromStudies(href) {
  if (!href) {
    return null;
  }
  if (href.startsWith("../")) {
    return `${ORIGIN}/${href.slice(3)}`;
  }
  if (href.startsWith("http://") || href.startsWith("https://")) {
    return href;
  }
  return `${ORIGIN}/Studies/${href}`;
}

function normalizeRow(row, collection) {
  const copy = { ...row };
  if (!copy.collection) {
    copy.collection = collection || row.collection || "topical";
  }
  copy.htmlUrl = absoluteFromStudies(row.html);
  copy.pdfUrl = absoluteFromStudies(row.pdf);
  copy.mdUrl = absoluteFromStudies(row.md);
  return copy;
}

function matchesQuery(entry, query) {
  if (!query) {
    return true;
  }
  const haystack = [
    entry.slug,
    entry.title,
    entry.description,
    entry.category,
    Array.isArray(entry.categories) ? entry.categories.join(" ") : "",
  ]
    .join(" ")
    .toLowerCase();
  return haystack.indexOf(String(query).toLowerCase()) !== -1;
}

async function fetchJson(path) {
  const urls = [`${ORIGIN}${path}`, `${GITHUB_RAW}${path}`];
  let lastError = null;
  for (const url of urls) {
    try {
      const response = await fetch(url, {
        headers: {
          Accept: "application/json",
          "User-Agent": "amd-mcp-catalog-fetch/1.2",
        },
      });
      if (!response.ok) {
        lastError = new Error(`${url} returned HTTP ${response.status}`);
        continue;
      }
      const data = await response.json();
      return data;
    } catch (err) {
      lastError = err;
    }
  }
  throw lastError || new Error(`failed to fetch ${path}`);
}

async function fetchText(urls) {
  let lastError = null;
  for (const url of urls) {
    if (!url) {
      continue;
    }
    try {
      const response = await fetch(url, {
        headers: {
          Accept: "text/markdown, text/plain, */*",
          "User-Agent": "amd-mcp-catalog-fetch/1.2",
        },
      });
      if (!response.ok) {
        lastError = new Error(`${url} returned HTTP ${response.status}`);
        continue;
      }
      return await response.text();
    } catch (err) {
      lastError = err;
    }
  }
  throw lastError || new Error("failed to fetch markdown");
}

async function loadCatalogs() {
  try {
    const rows = await fetchJson("/Studies/catalog-all.json");
    if (Array.isArray(rows)) {
      return rows.map((row) => normalizeRow(row, row.collection));
    }
  } catch (_err) {
    // Fall back to the three collection files if catalog-all is not live yet.
  }
  const parts = await Promise.all(
    CATALOG_SOURCES.map(async ([path, collection]) => {
      try {
        const rows = await fetchJson(path);
        if (!Array.isArray(rows)) {
          return [];
        }
        return rows.map((row) => normalizeRow(row, collection));
      } catch (_err) {
        return [];
      }
    })
  );
  return parts.flat();
}

function filterStudies(rows, input) {
  const query = input && input.query != null ? input.query : input && input.q;
  const collection = input && input.collection;
  const status = input && input.status;
  const slug = input && input.slug;
  return rows.filter((row) => {
    if (collection && row.collection !== collection) {
      return false;
    }
    if (status && row.status !== status) {
      return false;
    }
    if (slug && row.slug !== slug) {
      return false;
    }
    return matchesQuery(row, query);
  });
}

function findStudy(rows, slug) {
  return rows.find((row) => row.slug === slug) || null;
}

function studySummary(row) {
  return {
    slug: row.slug,
    title: row.title,
    collection: row.collection,
    status: row.status,
    category: row.category,
    description: row.description,
    updated: row.updated || null,
    htmlUrl: row.htmlUrl,
    pdfUrl: row.pdfUrl,
    mdUrl: row.mdUrl,
  };
}

function markdownUrls(row) {
  const urls = [];
  if (row.mdUrl) {
    urls.push(row.mdUrl);
  }
  if (row.md) {
    urls.push(`${GITHUB_RAW}/Studies/${row.md}`);
    if (String(row.md).startsWith("../")) {
      urls.push(`${GITHUB_RAW}/${String(row.md).slice(3)}`);
    }
  }
  if (row.slug) {
    urls.push(`${ORIGIN}/Studies/${row.slug}/${row.slug}.md`);
    urls.push(`${GITHUB_RAW}/Studies/${row.slug}/${row.slug}.md`);
    urls.push(`${ORIGIN}/Applications/${row.slug}/${row.slug}.md`);
    urls.push(`${GITHUB_RAW}/Applications/${row.slug}/${row.slug}.md`);
  }
  return [...new Set(urls.filter(Boolean))];
}

function extractOutline(markdown) {
  const lines = String(markdown || "").split(/\r?\n/);
  const outline = [];
  let inFence = false;
  for (const line of lines) {
    if (/^```/.test(line)) {
      inFence = !inFence;
      continue;
    }
    if (inFence) {
      continue;
    }
    const match = /^(#{2,3})\s+(.+?)\s*#*\s*$/.exec(line);
    if (!match) {
      continue;
    }
    outline.push({
      level: match[1].length,
      heading: match[2].replace(/\*+/g, "").trim(),
    });
  }
  return outline;
}

async function loadStudyMarkdown(row) {
  if (!row || (!row.md && !row.mdUrl)) {
    return null;
  }
  return fetchText(markdownUrls(row));
}

async function studyDetail(row) {
  const summary = studySummary(row);
  if (!row.md && !row.mdUrl) {
    return { ...summary, outline: [] };
  }
  try {
    const markdown = await loadStudyMarkdown(row);
    return { ...summary, outline: extractOutline(markdown) };
  } catch (_err) {
    return { ...summary, outline: [] };
  }
}

function citationDate(updated) {
  if (!updated) {
    return null;
  }
  const match = String(updated).match(/^(\w+ \d+, \d{4})/);
  return match ? match[1] : String(updated);
}

function citePayload(row) {
  const summary = studySummary(row);
  const url = summary.mdUrl || summary.htmlUrl || `${ORIGIN}/Studies/${row.slug}/`;
  const date = citationDate(row.updated);
  const status = row.status || "ongoing";
  const parts = [CITATION_AUTHOR, `*${row.title}*`, status];
  if (date) {
    parts.push(date);
  }
  return {
    ...summary,
    author: CITATION_AUTHOR,
    editedOn: row.updated || null,
    url,
    citation: `${parts.join(", ")}. ${url}`,
  };
}

function matchesGlossaryTerm(term, query) {
  if (!query) {
    return true;
  }
  const needle = String(query).toLowerCase();
  const haystack = [
    term.id,
    term.display,
    term.definition,
    Array.isArray(term.match) ? term.match.join(" ") : "",
  ]
    .join(" ")
    .toLowerCase();
  return haystack.indexOf(needle) !== -1;
}

function studyRef(rows, slug, extra) {
  const row = findStudy(rows, slug);
  const base = row
    ? studySummary(row)
    : {
        slug,
        title: null,
        collection: null,
        status: null,
        category: null,
        description: null,
        updated: null,
        htmlUrl: null,
        pdfUrl: null,
        mdUrl: null,
      };
  return { ...base, ...(extra || {}) };
}

async function loadStartHere() {
  if (typeof START_HERE !== "undefined") {
    return START_HERE;
  }
  return fetchJson("/Studies/start-here.json");
}

async function startHerePayload(rows) {
  const path = await loadStartHere();
  const stages = (path.stages || []).map((stage) => ({
    number: stage.number,
    domain: stage.domain,
    question: stage.question,
    reason: stage.reason,
    core: studyRef(rows, stage.core && stage.core.slug, {
      role: stage.core && stage.core.role,
    }),
    related: (stage.related || []).map((item) => studyRef(rows, item.slug)),
  }));
  const parallel = path.parallelTrack || {};
  return {
    title: path.title,
    intro: path.intro,
    stages,
    parallelTrack: {
      label: parallel.label || null,
      question: parallel.question || null,
      reason: parallel.reason || null,
      studies: (parallel.studies || []).map((item) => studyRef(rows, item.slug)),
    },
  };
}

const TOOLS = [
  {
    name: "search_studies",
    description:
      "Search Analytic Madhyasth Darshan studies by title, slug, description, or category. Returns matching catalog rows with HTML, PDF, and Markdown URLs.",
    inputSchema: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description: "Search text to match against title, slug, description, and category.",
        },
        collection: {
          type: "string",
          enum: ["topical", "formal", "applied"],
          description: "Limit results to one catalog collection.",
        },
        status: {
          type: "string",
          enum: ["ongoing", "draft", "released"],
        },
      },
      additionalProperties: false,
    },
  },
  {
    name: "list_studies",
    description: "List catalog rows, optionally filtered by collection or status.",
    inputSchema: {
      type: "object",
      properties: {
        collection: {
          type: "string",
          enum: ["topical", "formal", "applied"],
        },
        status: {
          type: "string",
          enum: ["ongoing", "draft", "released"],
        },
      },
      additionalProperties: false,
    },
  },
  {
    name: "get_study",
    description: "Return one catalog row by slug, including HTML, PDF, and Markdown URLs.",
    inputSchema: {
      type: "object",
      properties: {
        slug: {
          type: "string",
          description: "Catalog directory name, for example The-Ontology-of-Coexistence.",
        },
      },
      required: ["slug"],
      additionalProperties: false,
    },
  },
  {
    name: "get_study_outline",
    description:
      "Return ## and ### headings from a published study's markdown so an agent can jump to sections without fetching the full paper.",
    inputSchema: {
      type: "object",
      properties: {
        slug: {
          type: "string",
          description: "Catalog directory name, for example The-Ontology-of-Coexistence.",
        },
      },
      required: ["slug"],
      additionalProperties: false,
    },
  },
  {
    name: "get_glossary",
    description:
      "Search the shared studies glossary by id, display form, match aliases, or definition text.",
    inputSchema: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description: "Optional substring. Omit to return every term.",
        },
      },
      additionalProperties: false,
    },
  },
  {
    name: "get_start_here",
    description:
      "Return the recommended reading path (human, existence, knowledge, value, living) with catalog slugs and one-line reasons.",
    inputSchema: {
      type: "object",
      properties: {},
      additionalProperties: false,
    },
  },
  {
    name: "get_cite",
    description:
      "Return a suggested citation line for one study from catalog title, status, Edited-on, and markdown URL.",
    inputSchema: {
      type: "object",
      properties: {
        slug: {
          type: "string",
          description: "Catalog directory name, for example The-Ontology-of-Coexistence.",
        },
      },
      required: ["slug"],
      additionalProperties: false,
    },
  },
];

function textResult(payload) {
  return {
    content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
    structuredContent: payload,
  };
}

function toolError(message) {
  return {
    isError: true,
    content: [{ type: "text", text: message }],
  };
}

async function callTool(name, args) {
  const input = args && typeof args === "object" ? args : {};
  if (name === "search_studies" || name === "list_studies" || name === "get_study") {
    const rows = await loadCatalogs();
    if (name === "search_studies") {
      const matches = filterStudies(rows, input);
      return textResult({
        query: input.query || "",
        collection: input.collection || "all",
        count: matches.length,
        studies: matches.map(studySummary),
      });
    }
    if (name === "list_studies") {
      const matches = filterStudies(rows, input);
      return textResult({
        collection: input.collection || "all",
        status: input.status || "all",
        count: matches.length,
        studies: matches.map(studySummary),
      });
    }
    const slug = input.slug;
    if (!slug) {
      return toolError("slug is required");
    }
    const match = findStudy(rows, slug);
    if (!match) {
      return toolError(`No catalog row for slug ${slug}`);
    }
    return textResult(studySummary(match));
  }
  if (name === "get_study_outline") {
    const slug = input.slug;
    if (!slug) {
      return toolError("slug is required");
    }
    const rows = await loadCatalogs();
    const match = findStudy(rows, slug);
    if (!match) {
      return toolError(`No catalog row for slug ${slug}`);
    }
    return textResult(await studyDetail(match));
  }
  if (name === "get_glossary") {
    const glossary = await fetchJson("/Studies/glossary.json");
    const terms = Array.isArray(glossary.terms) ? glossary.terms : [];
    const query = input.query || input.q || "";
    const matches = terms.filter((term) => matchesGlossaryTerm(term, query));
    return textResult({
      query,
      count: matches.length,
      terms: matches,
    });
  }
  if (name === "get_start_here") {
    const rows = await loadCatalogs();
    return textResult(await startHerePayload(rows));
  }
  if (name === "get_cite") {
    const slug = input.slug;
    if (!slug) {
      return toolError("slug is required");
    }
    const rows = await loadCatalogs();
    const match = findStudy(rows, slug);
    if (!match) {
      return toolError(`No catalog row for slug ${slug}`);
    }
    return textResult(citePayload(match));
  }
  return toolError(`Unknown tool: ${name}`);
}

function rpcError(id, code, message) {
  return { jsonrpc: "2.0", id, error: { code, message } };
}

function rpcResult(id, result) {
  return { jsonrpc: "2.0", id, result };
}

function negotiateProtocol(requested) {
  if (requested && PROTOCOL_VERSIONS.includes(requested)) {
    return requested;
  }
  return DEFAULT_PROTOCOL;
}

function parseStudyResourceUri(uri) {
  const prefix = "studies://study/";
  if (!uri || !uri.startsWith(prefix)) {
    return null;
  }
  const slug = decodeURIComponent(uri.slice(prefix.length));
  return SLUG_RE.test(slug) ? slug : null;
}

async function handleRpc(message) {
  if (!message || message.jsonrpc !== "2.0" || typeof message.method !== "string") {
    return rpcError(message && "id" in message ? message.id : null, -32600, "Invalid Request");
  }
  const id = "id" in message ? message.id : undefined;
  const method = message.method;
  const params = message.params || {};

  if (id === undefined) {
    return null;
  }

  if (method === "initialize") {
    const protocolVersion = negotiateProtocol(params.protocolVersion);
    return rpcResult(id, {
      protocolVersion,
      capabilities: {
        tools: { listChanged: false },
        resources: { listChanged: false },
      },
      serverInfo: CARD.serverInfo || {
        name: "Analytic Madhyasth Darshan",
        version: "1.2.0",
      },
      instructions:
        "Read-only catalog tools. Cite markdown as the source of truth. Use get_study_outline or studies://study/{slug} for headings and paper text. Write APIs are for humans; see /auth.md.",
    });
  }

  if (method === "ping") {
    return rpcResult(id, {});
  }

  if (method === "tools/list") {
    return rpcResult(id, { tools: TOOLS });
  }

  if (method === "tools/call") {
    const name = params.name;
    if (!name) {
      return rpcError(id, -32602, "tools/call requires params.name");
    }
    try {
      const result = await callTool(name, params.arguments || {});
      return rpcResult(id, result);
    } catch (err) {
      return rpcError(id, -32603, String(err && err.message ? err.message : err));
    }
  }

  if (method === "resources/list") {
    return rpcResult(id, {
      resources: RESOURCES.map((item) => ({
        uri: item.uri,
        name: item.name,
        mimeType: item.mimeType,
      })),
    });
  }

  if (method === "resources/templates/list") {
    return rpcResult(id, { resourceTemplates: RESOURCE_TEMPLATES });
  }

  if (method === "resources/read") {
    const uri = params.uri;
    const slug = parseStudyResourceUri(uri);
    if (slug) {
      try {
        const rows = await loadCatalogs();
        const match = findStudy(rows, slug);
        if (!match) {
          return rpcError(id, -32602, `Unknown resource: ${uri}`);
        }
        if (!match.md && !match.mdUrl) {
          return rpcError(id, -32602, `No markdown yet for slug ${slug}`);
        }
        const markdown = await loadStudyMarkdown(match);
        return rpcResult(id, {
          contents: [
            {
              uri,
              mimeType: "text/markdown",
              text: markdown,
            },
          ],
        });
      } catch (err) {
        return rpcError(id, -32603, String(err && err.message ? err.message : err));
      }
    }
    const item = RESOURCES.find((entry) => entry.uri === uri);
    if (!item) {
      return rpcError(id, -32602, `Unknown resource: ${uri}`);
    }
    try {
      const data =
        item.uri === "studies://start-here"
          ? await loadStartHere()
          : await fetchJson(item.path);
      return rpcResult(id, {
        contents: [
          {
            uri,
            mimeType: item.mimeType,
            text: JSON.stringify(data),
          },
        ],
      });
    } catch (err) {
      return rpcError(id, -32603, String(err && err.message ? err.message : err));
    }
  }

  return rpcError(id, -32601, `Method not found: ${method}`);
}

function respondCard(request) {
  if (request.method === "OPTIONS") {
    return emptyResponse(204, CARD_HEADERS);
  }
  if (request.method === "HEAD") {
    return emptyResponse(200, CARD_HEADERS);
  }
  return new Response(CARD_BODY, { status: 200, headers: CARD_HEADERS });
}

async function handleMcp(request) {
  if (request.method === "OPTIONS") {
    return emptyResponse(204);
  }
  if (request.method !== "POST") {
    return emptyResponse(405, { allow: "POST, OPTIONS" });
  }
  let payload;
  try {
    payload = await request.json();
  } catch (_err) {
    return jsonResponse(400, rpcError(null, -32700, "Parse error"));
  }
  if (Array.isArray(payload)) {
    const results = [];
    for (const message of payload) {
      const result = await handleRpc(message);
      if (result) {
        results.push(result);
      }
    }
    if (!results.length) {
      return emptyResponse(202);
    }
    return jsonResponse(200, results);
  }
  const result = await handleRpc(payload);
  if (!result) {
    return emptyResponse(202);
  }
  return jsonResponse(200, result);
}

async function handleStudiesApi(request) {
  if (request.method === "OPTIONS") {
    return emptyResponse(204);
  }
  if (request.method !== "GET" && request.method !== "HEAD") {
    return emptyResponse(405, { allow: "GET, HEAD, OPTIONS" });
  }
  const url = new URL(request.url);
  const input = {
    q: url.searchParams.get("q") || url.searchParams.get("query") || "",
    collection: url.searchParams.get("collection") || "",
    status: url.searchParams.get("status") || "",
    slug: url.searchParams.get("slug") || "",
  };
  try {
    const rows = await loadCatalogs();
    const matches = filterStudies(rows, input);
    const body = {
      query: input.q,
      collection: input.collection || "all",
      status: input.status || "all",
      slug: input.slug || null,
      count: matches.length,
      studies: matches.map(studySummary),
    };
    if (request.method === "HEAD") {
      return emptyResponse(200, jsonHeaders());
    }
    return jsonResponse(200, body);
  } catch (err) {
    return jsonResponse(502, { error: String(err && err.message ? err.message : err) });
  }
}

async function handleStudyBySlug(request, slug) {
  if (request.method === "OPTIONS") {
    return emptyResponse(204);
  }
  if (request.method !== "GET" && request.method !== "HEAD") {
    return emptyResponse(405, { allow: "GET, HEAD, OPTIONS" });
  }
  if (!SLUG_RE.test(slug)) {
    return jsonResponse(400, { error: "invalid slug" });
  }
  try {
    const rows = await loadCatalogs();
    const match = findStudy(rows, slug);
    if (!match) {
      return jsonResponse(404, { error: `No catalog row for slug ${slug}` });
    }
    const body = await studyDetail(match);
    if (request.method === "HEAD") {
      return emptyResponse(200, jsonHeaders());
    }
    return jsonResponse(200, body);
  } catch (err) {
    return jsonResponse(502, { error: String(err && err.message ? err.message : err) });
  }
}

async function handleGlossary(request) {
  if (request.method === "OPTIONS") {
    return emptyResponse(204);
  }
  if (request.method !== "GET" && request.method !== "HEAD") {
    return emptyResponse(405, { allow: "GET, HEAD, OPTIONS" });
  }
  const url = new URL(request.url);
  const query = url.searchParams.get("q") || url.searchParams.get("query") || "";
  try {
    const glossary = await fetchJson("/Studies/glossary.json");
    const terms = Array.isArray(glossary.terms) ? glossary.terms : [];
    const matches = terms.filter((term) => matchesGlossaryTerm(term, query));
    const body = { query, count: matches.length, terms: matches };
    if (request.method === "HEAD") {
      return emptyResponse(200, jsonHeaders());
    }
    return jsonResponse(200, body);
  } catch (err) {
    return jsonResponse(502, { error: String(err && err.message ? err.message : err) });
  }
}

async function handleStartHere(request) {
  if (request.method === "OPTIONS") {
    return emptyResponse(204);
  }
  if (request.method !== "GET" && request.method !== "HEAD") {
    return emptyResponse(405, { allow: "GET, HEAD, OPTIONS" });
  }
  try {
    const rows = await loadCatalogs();
    const body = await startHerePayload(rows);
    if (request.method === "HEAD") {
      return emptyResponse(200, jsonHeaders());
    }
    return jsonResponse(200, body);
  } catch (err) {
    return jsonResponse(502, { error: String(err && err.message ? err.message : err) });
  }
}

async function handleCite(request, slug) {
  if (request.method === "OPTIONS") {
    return emptyResponse(204);
  }
  if (request.method !== "GET" && request.method !== "HEAD") {
    return emptyResponse(405, { allow: "GET, HEAD, OPTIONS" });
  }
  if (!SLUG_RE.test(slug)) {
    return jsonResponse(400, { error: "invalid slug" });
  }
  try {
    const rows = await loadCatalogs();
    const match = findStudy(rows, slug);
    if (!match) {
      return jsonResponse(404, { error: `No catalog row for slug ${slug}` });
    }
    const body = citePayload(match);
    if (request.method === "HEAD") {
      return emptyResponse(200, jsonHeaders());
    }
    return jsonResponse(200, body);
  } catch (err) {
    return jsonResponse(502, { error: String(err && err.message ? err.message : err) });
  }
}

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";
    if (path === "/.well-known/mcp/server-card.json" || path === "/.well-known/mcp.json") {
      return respondCard(request);
    }
    if (path === "/mcp") {
      return handleMcp(request);
    }
    if (path === "/api/studies") {
      return handleStudiesApi(request);
    }
    const studyMatch = path.match(/^\/api\/studies\/([A-Za-z0-9-]+)$/);
    if (studyMatch) {
      return handleStudyBySlug(request, studyMatch[1]);
    }
    if (path === "/api/glossary") {
      return handleGlossary(request);
    }
    if (path === "/api/start-here") {
      return handleStartHere(request);
    }
    const citeMatch = path.match(/^\/api\/cite\/([A-Za-z0-9-]+)$/);
    if (citeMatch) {
      return handleCite(request, citeMatch[1]);
    }
    return new Response("Not Found", { status: 404, headers: CORS_HEADERS });
  },
};
