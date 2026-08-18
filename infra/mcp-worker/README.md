# MCP Server Card worker (`amd-mcp`)

Serves the [SEP-1649](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1649)
MCP Server Card at
`https://analyticmadhyasthdarshan.org/.well-known/mcp/server-card.json`
and a thin Streamable HTTP runtime at `/mcp`, plus `GET /api/studies`.

The canonical card remains at [`.well-known/mcp/server-card.json`](../../.well-known/mcp/server-card.json).
The Worker source is [`src/runtime.js`](src/runtime.js); the publish script
prepends the embedded card JSON and writes gitignored `src/index.js`.

Read-only tools: `search_studies`, `list_studies`, `get_study`.
Resources: `studies://catalog-all`, `studies://glossary`, `studies://feed`.
There are no write tools. DNS-AID does not publish `_mcp._agents`.

The zone API token can upload this Worker. Production attaches zone Workers
Routes (`/.well-known/mcp/*`, `/mcp*`, `/api/studies*`) so apex requests run
the Worker without a workers.dev redirect. `--apply-redirect` now binds those
routes and keeps only the homepage 301.

## Deploy

From the repository root:

```powershell
python Scripts/_publish_mcp_server_card.py
python Scripts/_test_mcp_server_card.py --live
python Scripts/_test_studies_api.py --live
```
