import { GENERATED_PDF_KEYS } from "./generated-pdf-keys.js";

const ALLOWED_KEYS = new Set(GENERATED_PDF_KEYS);
const PDF_CONTENT_TYPE = "application/pdf";

function objectKey(pathname) {
  try {
    const key = decodeURIComponent(pathname.replace(/^\/+/, ""));
    if (key.includes("\\") || (!key.startsWith("Studies/") && !key.startsWith("Applications/"))) {
      return null;
    }
    return key;
  } catch {
    return null;
  }
}

function isPdfPath(key) {
  return key !== null && key.toLowerCase().endsWith(".pdf");
}

function baseHeaders(object) {
  const headers = new Headers();
  object.writeHttpMetadata(headers);
  headers.set("Content-Type", PDF_CONTENT_TYPE);
  headers.set("ETag", object.httpEtag);
  headers.set("Accept-Ranges", "bytes");
  headers.set("Access-Control-Allow-Origin", "*");
  headers.set("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS");
  headers.set("X-Content-Type-Options", "nosniff");
  headers.set("X-AMD-PDF-Origin", "r2");
  if (object.customMetadata?.sha256) {
    headers.set("X-AMD-PDF-SHA256", object.customMetadata.sha256);
  }
  if (object.uploaded instanceof Date) {
    headers.set("Last-Modified", object.uploaded.toUTCString());
  }
  return headers;
}

function errorResponse(status, message, extraHeaders = {}) {
  return new Response(message, {
    status,
    headers: {
      "Cache-Control": "no-store",
      "Content-Type": "text/plain; charset=utf-8",
      "X-Content-Type-Options": "nosniff",
      ...extraHeaders,
    },
  });
}

function etagMatches(header, etag) {
  if (!header) return false;
  return header.split(",").some((candidate) => {
    const value = candidate.trim();
    return value === "*" || value === etag || value.replace(/^W\//, "") === etag;
  });
}

function headPreconditionStatus(request, object) {
  const ifMatch = request.headers.get("If-Match");
  if (ifMatch && !etagMatches(ifMatch, object.httpEtag)) return 412;
  const ifNoneMatch = request.headers.get("If-None-Match");
  if (etagMatches(ifNoneMatch, object.httpEtag)) return 304;

  const uploaded = object.uploaded instanceof Date ? object.uploaded.getTime() : NaN;
  const unmodifiedSince = Date.parse(request.headers.get("If-Unmodified-Since") || "");
  if (Number.isFinite(uploaded) && Number.isFinite(unmodifiedSince) && uploaded > unmodifiedSince) {
    return 412;
  }
  const modifiedSince = Date.parse(request.headers.get("If-Modified-Since") || "");
  if (!ifNoneMatch && Number.isFinite(uploaded) && Number.isFinite(modifiedSince) && uploaded <= modifiedSince) {
    return 304;
  }
  return 200;
}

function conditionalFailureStatus(request) {
  return request.headers.has("If-None-Match") || request.headers.has("If-Modified-Since")
    ? 304
    : 412;
}

function rangeHeaders(headers, object) {
  if (!object.range) {
    headers.set("Content-Length", String(object.size));
    return 200;
  }
  const offset = Number(object.range.offset);
  const length = Number(object.range.length);
  if (!Number.isFinite(offset) || !Number.isFinite(length) || length <= 0) {
    throw new RangeError("R2 returned an invalid range");
  }
  headers.set("Content-Length", String(length));
  headers.set("Content-Range", `bytes ${offset}-${offset + length - 1}/${object.size}`);
  return 206;
}

async function servePdf(request, env, key) {
  if (request.method === "OPTIONS") {
    return new Response(null, {
      status: 204,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
        "Access-Control-Allow-Headers": "Range, If-Match, If-None-Match, If-Modified-Since, If-Unmodified-Since",
        "Access-Control-Max-Age": "86400",
      },
    });
  }
  if (request.method !== "GET" && request.method !== "HEAD") {
    return errorResponse(405, "Method Not Allowed", { Allow: "GET, HEAD, OPTIONS" });
  }

  if (request.method === "HEAD") {
    const object = await env.GENERATED_PDFS.head(key);
    if (object === null) return errorResponse(404, "Generated PDF not published");
    const headers = baseHeaders(object);
    headers.set("Content-Length", String(object.size));
    return new Response(null, { status: headPreconditionStatus(request, object), headers });
  }

  let object;
  try {
    object = await env.GENERATED_PDFS.get(key, {
      onlyIf: request.headers,
      range: request.headers,
    });
  } catch (error) {
    if (request.headers.has("Range")) {
      const existing = await env.GENERATED_PDFS.head(key);
      if (existing === null) return errorResponse(404, "Generated PDF not published");
      return errorResponse(416, "Requested range not satisfiable", {
        "Content-Range": `bytes */${existing.size}`,
        "Accept-Ranges": "bytes",
      });
    }
    throw error;
  }
  if (object === null) return errorResponse(404, "Generated PDF not published");

  const headers = baseHeaders(object);
  if (!("body" in object)) {
    return new Response(null, { status: conditionalFailureStatus(request), headers });
  }
  try {
    const status = rangeHeaders(headers, object);
    return new Response(object.body, { status, headers });
  } catch (error) {
    if (error instanceof RangeError) {
      return errorResponse(416, "Requested range not satisfiable", {
        "Content-Range": `bytes */${object.size}`,
        "Accept-Ranges": "bytes",
      });
    }
    throw error;
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const key = objectKey(url.pathname);
    if (!isPdfPath(key)) {
      if (url.hostname.endsWith(".workers.dev")) return errorResponse(404, "Not Found");
      return fetch(request);
    }
    if (!ALLOWED_KEYS.has(key)) return errorResponse(404, "Generated PDF not published");
    return servePdf(request, env, key);
  },
};

export { etagMatches, headPreconditionStatus, objectKey, rangeHeaders, servePdf };
