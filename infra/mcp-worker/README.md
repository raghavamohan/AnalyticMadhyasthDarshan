# MCP Server Card worker (`amd-mcp`)

Serves the [SEP-1649](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1649)
MCP Server Card at
`https://analyticmadhyasthdarshan.org/.well-known/mcp/server-card.json`.

The canonical file is [`.well-known/mcp/server-card.json`](../../.well-known/mcp/server-card.json).
The Worker embeds that JSON so the well-known URI returns HTTP 200 with
`application/json` before GitHub Pages has the tree.

The zone API token can upload this Worker but cannot create a Workers Route, so
production currently 302-redirects `/.well-known/mcp/*` to
`https://amd-mcp.raghavamohan.workers.dev` (managed by
`python Scripts/_cloudflare_performance.py --apply-redirect`). When a token with
Workers Routes Edit is available, attach

`analyticmadhyasthdarshan.org/.well-known/mcp/*` → `amd-mcp`

and remove that redirect.

The advertised Streamable HTTP transport is `/mcp`. This Worker publishes the
discovery card; it does not run an MCP session runtime.

## Deploy

From the repository root:

```powershell
python Scripts/_publish_mcp_server_card.py
python Scripts/_test_mcp_server_card.py --live
```

The publish script writes `src/index.js` (gitignored), uploads Worker `amd-mcp`,
enables the workers.dev host, and upserts the redirect.
