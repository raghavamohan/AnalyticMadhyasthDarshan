# OpenCode / ZCode configuration

- **Agent rules:** [AGENTS.md](../AGENTS.md) at the repository root (source of truth).
- **Rule mirrors:** `.cursor/rules/*.mdc` — loaded via `opencode.json` → `instructions`.
- **Skills:** `.opencode/skills/` junction → `.agents/skills/` (add, remove, status, manage studies).

When editing agent rules, update `AGENTS.md` and the matching `.mdc` file in the same commit.
