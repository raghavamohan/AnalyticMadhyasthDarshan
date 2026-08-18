/**
 * WebMCP tools for Analytic Madhyasth Darshan.
 * https://webmachinelearning.github.io/webmcp/
 *
 * Feature-detects document.modelContext (current spec) and
 * navigator.modelContext (earlier drafts / Chrome EPP). Registers catalog
 * search, retrieval, and navigation tools on page load, retrying until the
 * API appears. Abort the controller to unregister — WebMCP has no unregisterTool().
 */
(function registerAmdWebMcp() {
  "use strict";

  var controller = new AbortController();
  var registerOpts = { signal: controller.signal };
  var registered = false;
  var retryTimer = null;
  var RETRY_MS = 250;
  var RETRY_LIMIT = 40;
  var SITE = "https://analyticmadhyasthdarshan.org";
  var CATALOGS = [
    { collection: "topical", url: "/Studies/catalog-topical.json" },
    { collection: "formal", url: "/Studies/catalog-formal.json" },
    { collection: "applied", url: "/Studies/catalog-applied.json" },
  ];
  var PAGES = {
    catalog: "/Studies/index.html",
    "api-docs": "/api-docs.html",
    auth: "/auth.md",
    submissions: "/Studies/submit.html",
    "api-catalog": "/.well-known/api-catalog",
    "agent-card": "/.well-known/agent-card.json",
  };
  var catalogCache = null;

  function modelContext() {
    if (navigator.modelContext && typeof navigator.modelContext.registerTool === "function") {
      return navigator.modelContext;
    }
    if (document.modelContext && typeof document.modelContext.registerTool === "function") {
      return document.modelContext;
    }
    return null;
  }

  function registerTool(tool) {
    if (navigator.modelContext && typeof navigator.modelContext.registerTool === "function") {
      return navigator.modelContext.registerTool(tool, registerOpts);
    }
    return document.modelContext.registerTool(tool, registerOpts);
  }

  function textResult(value) {
    var text = typeof value === "string" ? value : JSON.stringify(value, null, 2);
    return { content: [{ type: "text", text: text }] };
  }

  function origin() {
    return (location && location.origin) || SITE;
  }

  function absoluteFromStudies(relative) {
    if (!relative) {
      return null;
    }
    if (/^https?:\/\//i.test(relative)) {
      return relative;
    }
    return new URL(relative, origin() + "/Studies/").href;
  }

  function matchesQuery(entry, query) {
    if (!query) {
      return true;
    }
    var haystack = [
      entry.slug,
      entry.title,
      entry.description,
      entry.category,
      Array.isArray(entry.categories) ? entry.categories.join(" ") : "",
    ]
      .join(" ")
      .toLowerCase();
    return haystack.indexOf(query.toLowerCase()) !== -1;
  }

  function applyCatalogSearch(query) {
    var input = document.getElementById("q");
    if (!input) {
      return false;
    }
    input.value = query;
    input.dispatchEvent(new Event("input", { bubbles: true }));
    return true;
  }

  function loadCatalogs() {
    if (catalogCache) {
      return Promise.resolve(catalogCache);
    }
    return Promise.all(
      CATALOGS.map(function (source) {
        return fetch(source.url)
          .then(function (res) {
            if (!res.ok) {
              return [];
            }
            return res.json();
          })
          .then(function (rows) {
            if (!Array.isArray(rows)) {
              return [];
            }
            return rows.map(function (row) {
              var copy = Object.assign({}, row);
              copy.collection = source.collection;
              copy.htmlUrl = absoluteFromStudies(row.html);
              copy.pdfUrl = absoluteFromStudies(row.pdf);
              return copy;
            });
          })
          .catch(function () {
            return [];
          });
      })
    ).then(function (parts) {
      catalogCache = parts.flat();
      return catalogCache;
    });
  }

  function registerAll() {
    registerTool({
      name: "search_studies",
      description:
        "Search Analytic Madhyasth Darshan studies by title, slug, description, or category. " +
        "Returns matching catalog rows with HTML and PDF URLs. On the studies catalog page, also applies the search box.",
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
        },
        required: ["query"],
        additionalProperties: false,
      },
      annotations: { readOnlyHint: true },
      execute: function (input) {
        var query = (input && input.query) || "";
        var collection = input && input.collection;
        applyCatalogSearch(query);
        return loadCatalogs().then(function (rows) {
          var matches = rows.filter(function (row) {
            if (collection && row.collection !== collection) {
              return false;
            }
            return matchesQuery(row, query);
          });
          return textResult({
            query: query,
            collection: collection || "all",
            count: matches.length,
            studies: matches,
          });
        });
      },
    });

    registerTool({
      name: "list_studies",
      description:
        "List studies in the public catalogs (topical, formal, applied). " +
        "Optionally filter by collection and status (ongoing, draft, or released).",
      inputSchema: {
        type: "object",
        properties: {
          collection: {
            type: "string",
            enum: ["topical", "formal", "applied"],
            description: "Catalog collection to list. Omit to include all three.",
          },
          status: {
            type: "string",
            enum: ["ongoing", "draft", "released"],
            description: "Lifecycle status to include.",
          },
        },
        additionalProperties: false,
      },
      annotations: { readOnlyHint: true },
      execute: function (input) {
        var collection = input && input.collection;
        var status = input && input.status;
        return loadCatalogs().then(function (rows) {
          var matches = rows.filter(function (row) {
            if (collection && row.collection !== collection) {
              return false;
            }
            if (status && row.status !== status) {
              return false;
            }
            return true;
          });
          return textResult({
            collection: collection || "all",
            status: status || "all",
            count: matches.length,
            studies: matches.map(function (row) {
              return {
                slug: row.slug,
                title: row.title,
                collection: row.collection,
                status: row.status,
                category: row.category,
                htmlUrl: row.htmlUrl,
                pdfUrl: row.pdfUrl,
              };
            }),
          });
        });
      },
    });

    registerTool({
      name: "get_study",
      description:
        "Retrieve one study from the public catalogs by slug, including title, status, " +
        "description, and absolute HTML/PDF URLs when a document exists.",
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
      annotations: { readOnlyHint: true },
      execute: function (input) {
        var slug = ((input && input.slug) || "").trim();
        if (!slug) {
          return textResult({ error: "slug is required" });
        }
        return loadCatalogs().then(function (rows) {
          var study = rows.find(function (row) {
            return row.slug === slug;
          });
          if (!study) {
            return textResult({ error: "study not found", slug: slug });
          }
          return textResult(study);
        });
      },
    });

    registerTool({
      name: "open_study",
      description:
        "Navigate this tab to a study HTML page (default) or PDF by catalog slug.",
      inputSchema: {
        type: "object",
        properties: {
          slug: {
            type: "string",
            description: "Catalog directory name, for example The-Ontology-of-Coexistence.",
          },
          format: {
            type: "string",
            enum: ["html", "pdf"],
            description: "Document to open. Defaults to html.",
          },
        },
        required: ["slug"],
        additionalProperties: false,
      },
      annotations: { readOnlyHint: false },
      execute: function (input) {
        var slug = ((input && input.slug) || "").trim();
        var format = (input && input.format) || "html";
        return loadCatalogs().then(function (rows) {
          var study = rows.find(function (row) {
            return row.slug === slug;
          });
          if (!study) {
            return textResult({ error: "study not found", slug: slug });
          }
          var href = format === "pdf" ? study.pdfUrl : study.htmlUrl;
          if (!href) {
            return textResult({
              error: "no " + format + " document for this study",
              slug: slug,
              status: study.status,
            });
          }
          location.assign(href);
          return textResult({ opened: href, slug: slug, format: format });
        });
      },
    });

    registerTool({
      name: "open_page",
      description:
        "Navigate this tab to a site page: studies catalog, API docs, Auth.md, " +
        "submissions portal, RFC 9727 api-catalog, or A2A Agent Card.",
      inputSchema: {
        type: "object",
        properties: {
          page: {
            type: "string",
            enum: Object.keys(PAGES),
            description: "Which site page to open.",
          },
        },
        required: ["page"],
        additionalProperties: false,
      },
      annotations: { readOnlyHint: false },
      execute: function (input) {
        var page = input && input.page;
        var path = PAGES[page];
        if (!path) {
          return textResult({
            error: "unknown page",
            page: page,
            known: Object.keys(PAGES),
          });
        }
        var href = origin() + path;
        location.assign(href);
        return textResult({ opened: href, page: page });
      },
    });
  }

  function stopRetry() {
    if (retryTimer !== null) {
      clearInterval(retryTimer);
      retryTimer = null;
    }
  }

  function tryRegister() {
    if (registered || controller.signal.aborted) {
      return true;
    }
    if (!modelContext()) {
      return false;
    }
    try {
      registerAll();
      registered = true;
      stopRetry();
      return true;
    } catch (err) {
      console.warn("WebMCP registration failed", err);
      return false;
    }
  }

  if (!tryRegister()) {
    var attempts = 0;
    retryTimer = setInterval(function () {
      attempts += 1;
      if (tryRegister() || attempts >= RETRY_LIMIT) {
        stopRetry();
      }
    }, RETRY_MS);
  }

  window.addEventListener("pageshow", function () {
    tryRegister();
  });

  window.addEventListener(
    "pagehide",
    function () {
      stopRetry();
      controller.abort();
    },
    { once: true }
  );
})();
