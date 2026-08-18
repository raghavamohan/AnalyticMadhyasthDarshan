const ORIGIN = "https://analyticmadhyasthdarshan.org";
const GITHUB_RAW =
  "https://raw.githubusercontent.com/raghavamohan/AnalyticMadhyasthDarshan/master";
const PROTOCOL_VERSIONS = ["2025-06-18", "2025-03-26", "2024-11-05"];
const DEFAULT_PROTOCOL = PROTOCOL_VERSIONS[0];
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
          "User-Agent": "amd-mcp-catalog-fetch/1.1",
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
        slug: { type: "string", description: "Catalog directory name, for example The-Ontology-of-Coexistence." },
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

async function callTool(name, args) {
  const input = args && typeof args === "object" ? args : {};
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
  if (name === "get_study") {
    const slug = input.slug;
    if (!slug) {
      return {
        isError: true,
        content: [{ type: "text", text: "slug is required" }],
      };
    }
    const match = rows.find((row) => row.slug === slug);
    if (!match) {
      return {
        isError: true,
        content: [{ type: "text", text: `No catalog row for slug ${slug}` }],
      };
    }
    return textResult(studySummary(match));
  }
  return {
    isError: true,
    content: [{ type: "text", text: `Unknown tool: ${name}` }],
  };
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
        version: "1.1.0",
      },
      instructions:
        "Read-only catalog tools. Cite markdown as the source of truth. Write APIs are for humans; see /auth.md.",
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

  if (method === "resources/read") {
    const uri = params.uri;
    const item = RESOURCES.find((entry) => entry.uri === uri);
    if (!item) {
      return rpcError(id, -32602, `Unknown resource: ${uri}`);
    }
    try {
      const data = await fetchJson(item.path);
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
    return new Response("Not Found", { status: 404, headers: CORS_HEADERS });
  },
};
