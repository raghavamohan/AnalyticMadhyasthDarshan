# OpenCode / ZCode configuration

- **Agent rules:** [AGENTS.md](../AGENTS.md) at the repository root (source of truth).
- **Rule mirrors:** `.cursor/rules/*.mdc` — loaded via `opencode.json` → `instructions`.
- **Skills:** `.opencode/skills/` junction → `.agents/skills/` (canonical skill sources).

After editing `AGENTS.md` or `.agents/skills/**/SKILL.md`, regenerate and verify all
mirrors instead of editing `.cursor/` copies by hand:

```powershell
python Scripts/_sync_agent_rules.py
python Scripts/_sync_agent_rules.py --check
```
