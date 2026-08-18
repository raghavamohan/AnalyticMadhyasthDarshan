import catalog from './api-catalog.json';

const CATALOG_CONTENT_TYPE =
  'application/linkset+json; profile="https://www.rfc-editor.org/info/rfc9727"';
const CATALOG_LINK =
  '</.well-known/api-catalog>; rel="api-catalog"; type="application/linkset+json"';

function apiCatalogHeaders() {
  return {
    'Content-Type': CATALOG_CONTENT_TYPE,
    Link: CATALOG_LINK,
    'Cache-Control': 'public, max-age=3600',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
  };
}

function apiCatalogResponse(method) {
  const headers = apiCatalogHeaders();
  if (method === 'OPTIONS') {
    return new Response(null, { status: 204, headers });
  }
  if (method === 'HEAD') {
    return new Response(null, { status: 200, headers });
  }
  return new Response(JSON.stringify(catalog), { status: 200, headers });
}

export default {
  fetch(request) {
    const url = new URL(request.url);
    if (url.pathname === '/.well-known/api-catalog' || url.pathname === '/.well-known/api-catalog/') {
      return apiCatalogResponse(request.method);
    }
    return new Response('Not Found', { status: 404 });
  },
};
