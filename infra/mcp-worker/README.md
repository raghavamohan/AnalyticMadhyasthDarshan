# MCP Server Card worker (`amd-mcp`)

Serves the [SEP-1649](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1649)
MCP Server Card at
`https://analyticmadhyasthdarshan.org/.well-known/mcp/server-card.json`
and a thin Streamable HTTP runtime at `/mcp`, plus `GET /api/studies`,
`GET /api/studies/{slug}`, `GET /api/glossary`, `GET /api/start-here`, and
`GET /api/cite/{slug}`.

The canonical card remains at [`.well-known/mcp/server-card.json`](../../.well-known/mcp/server-card.json).
The Worker source is [`src/runtime.js`](src/runtime.js); the publish script
prepends the embedded card JSON and `Studies/start-here.json`, then writes
gitignored `src/index.js`.

Read-only tools: `search_studies`, `list_studies`, `get_study`,
`get_study_outline`, `get_glossary`, `get_start_here`, `get_cite`.
Resources: `studies://catalog-all`, `studies://glossary`, `studies://feed`,
`studies://start-here`, and `studies://study/{slug}` for canonical markdown.
There are no write tools. DNS-AID does not publish `_mcp._agents`.

The zone API token can upload this Worker. Production attaches zone Workers
Routes (`/.well-known/mcp/*`, `/mcp*`, `/api/studies*`, `/api/glossary*`,
`/api/start-here*`, `/api/cite*`) so apex requests run
the Worker without a workers.dev redirect. `--apply-redirect` now binds those
routes and keeps only the homepage 301.

## Deploy

Changes to the Server Card, Start Here data, runtime, or publisher are generated
and checked on pull requests, then deployed automatically after merge to
`master` by `agent-publications.yml`. The post-deploy job verifies the live card,
MCP runtime, and exact canonical Start Here response.

For an intentional manual deployment from the repository root:

```powershell
python Scripts/_publish_mcp_server_card.py
python Scripts/_test_mcp_server_card.py --live
python Scripts/_test_studies_api.py --live
```

Pass `--generate-only` to the publisher to write and syntax-check the gitignored
bundle without Cloudflare credentials or a deployment.
