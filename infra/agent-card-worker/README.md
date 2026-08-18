# Agent Card worker (`amd-agent-card`)

Serves the [A2A Agent Card](https://a2a-protocol.org/latest/topics/agent-discovery/)
at `https://analyticmadhyasthdarshan.org/.well-known/agent-card.json`.

The canonical card remains at [`.well-known/agent-card.json`](../../.well-known/agent-card.json).
The publish script embeds that JSON and writes gitignored `src/index.js`.
Production attaches the zone Workers Route
`analyticmadhyasthdarshan.org/.well-known/agent-card.json` → `amd-agent-card`.

## Deploy

From the repository root:

```powershell
python Scripts/_publish_agent_card_snippet.py
python Scripts/_test_agent_card.py --live
```

The publish script writes `src/index.js` (gitignored), uploads Worker
`amd-agent-card`, enables the workers.dev host, and binds the zone route.
