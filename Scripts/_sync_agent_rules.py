"""Sync AGENTS.md rule sections and skills to Cursor/OpenCode mirrors.

Source of truth:
  - Rules: AGENTS.md sections 1–5 → .cursor/rules/*.mdc (OpenCode via opencode.json)
  - Skills: .agents/skills/ → .cursor/skills/ (.opencode/skills/ is a junction to .agents/skills/)

Run from repo root after editing AGENTS.md or .agents/skills/:

    python Scripts/_sync_agent_rules.py
    python Scripts/_sync_agent_rules.py --check
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
AGENTS = REPO / "AGENTS.md"
RULES_DIR = REPO / ".cursor" / "rules"
AGENTS_SKILLS = REPO / ".agents" / "skills"
CURSOR_SKILLS = REPO / ".cursor" / "skills"
OPENCODE_SKILLS = REPO / ".opencode" / "skills"

SECTION_PATTERN = re.compile(
    r"^## (\d+)\. (.+?) *\*\((?:always applies|applies when[^)]+)\)\*\s*$",
    re.MULTILINE,
)

MDC_CONFIG: dict[int, dict[str, str]] = {
    1: {
        "file": "study-edited-on.mdc",
        "description": 'Keep the "Edited on" field current whenever a study is changed',
        "globs": "Studies/*/*.md",
        "alwaysApply": "true",
        "title": 'Keep "Edited on" current in Studies',
        "section_ref": "§1",
        "extra_globs": "",
    },
    2: {
        "file": "studies-index-readme-sync.mdc",
        "description": "Keep Studies/index.html and Studies/README.md in sync",
        "globs": "Studies/index.html,Studies/README.md",
        "alwaysApply": "false",
        "title": "Keep Studies/index.html and Studies/README.md in sync",
        "section_ref": "§2",
        "extra_globs": "",
    },
    3: {
        "file": "md-to-pdf.mdc",
        "description": "Convert study markdown to PDF using the repo's internal scripts only",
        "globs": (
            "Studies/*/*.md,Scripts/_regenerate_pdf.py,Scripts/_convert_to_pdf.py,"
            "Scripts/_html_to_pdf.js,Scripts/_verify_pdf_diagrams.py,"
            "Scripts/_verify_pdf_fenced_code.py"
        ),
        "alwaysApply": "false",
        "title": "Markdown to PDF — use internal scripts only",
        "section_ref": "§3",
        "extra_globs": "",
    },
    4: {
        "file": "study-prose-style.mdc",
        "description": "Scholarly essay prose for Studies — no AI scaffold tags or signposting",
        "globs": "Studies/*/*.md",
        "alwaysApply": "true",
        "title": "Study prose style — scholarly essay, not AI scaffold",
        "section_ref": "§4",
        "extra_globs": "",
    },
    5: {
        "file": "study-standpoint-scope.mdc",
        "description": "Standpoint and scope section for topical Studies",
        "globs": "Studies/*/*.md",
        "alwaysApply": "true",
        "title": "Standpoint and scope — topical studies",
        "section_ref": "§5",
        "extra_globs": "",
    },
}


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def extract_sections(text: str) -> dict[int, str]:
    matches = list(SECTION_PATTERN.finditer(text))
    sections: dict[int, str] = {}
    for i, match in enumerate(matches):
        num = int(match.group(1))
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[num] = text[start:end].strip()
    return sections


def agents_body_to_mdc(body: str, section_num: int) -> str:
    out = body
    out = re.sub(r"^#### ", "### ", out, flags=re.MULTILINE)
    out = re.sub(r"^### ", "## ", out, flags=re.MULTILINE)
    out = re.sub(
        r"\[[^\]]*§(\d+)[^\]]*\]\([^)]+\)",
        r"[AGENTS.md](../AGENTS.md) §\1",
        out,
    )
    out = re.sub(r"\]\(Studies/", "](../Studies/", out)
    out = re.sub(
        r"\. Cursor mirror:\n`\.cursor/rules/[^`\n]+`\.\n",
        ".\n",
        out,
    )
    out = re.sub(
        r"\. Cursor mirror: `\.cursor/rules/[^`\n]+`\.\n",
        ".\n",
        out,
    )
    if section_num == 1:
        out = out.replace(
            "using the pipeline in [AGENTS.md](../AGENTS.md) §3\n   (never ad-hoc converters)",
            "using the pipeline in [AGENTS.md](../AGENTS.md) §3\n   (Cursor mirror: `md-to-pdf.mdc`; never ad-hoc converters)",
        )
    if section_num == 3:
        out = out.replace(
            "When a study markdown file under `Studies/` needs a PDF,",
            "When a study markdown file under `Studies/<Slug>/` needs a PDF,",
        )
        out = out.replace(
            "```powershell\npython Scripts/_convert_to_pdf.py Studies/<Slug>/<Slug>.md --watermark Draft\n"
            "node Scripts/_html_to_pdf.js Studies/<Slug>/<Slug>.html\n"
            "Remove-Item Studies/<Slug>/<Slug>.html\n```",
            "```powershell\npython Scripts/_convert_to_pdf.py Studies/<Slug>/<Slug>.md\n"
            "node Scripts/_html_to_pdf.js Studies/<Slug>/<Slug>.html Draft\n"
            "python Scripts/_verify_pdf_diagrams.py Studies/<Slug>/<Slug>.md Studies/<Slug>/<Slug>.pdf\n"
            "python Scripts/_verify_pdf_fenced_code.py Studies/<Slug>/<Slug>.md Studies/<Slug>/<Slug>.pdf\n"
            "Remove-Item Studies/<Slug>/<Slug>.html\n```",
        )
    return out.strip()


def render_mdc(section_num: int, body: str) -> str:
    cfg = MDC_CONFIG[section_num]
    mdc_body = agents_body_to_mdc(body, section_num)
    return (
        "---\n"
        f"description: {cfg['description']}\n"
        f"globs: {cfg['globs']}\n"
        f"alwaysApply: {cfg['alwaysApply']}\n"
        "---\n\n"
        f"# {cfg['title']}\n\n"
        f"> **Source of truth:** [AGENTS.md](../AGENTS.md) {cfg['section_ref']}. "
        "Keep this file in sync when editing.\n\n"
        f"{mdc_body}\n"
    )


def sync_rules() -> list[str]:
    text = AGENTS.read_text(encoding="utf-8")
    sections = extract_sections(text)
    missing = [n for n in MDC_CONFIG if n not in sections]
    if missing:
        raise SystemExit(f"AGENTS.md missing sections: {missing}")

    written: list[str] = []
    for num, cfg in MDC_CONFIG.items():
        path = RULES_DIR / cfg["file"]
        path.write_text(render_mdc(num, sections[num]), encoding="utf-8", newline="\n")
        written.append(str(path.relative_to(REPO)))
    return written


def sync_skills() -> list[str]:
    if not AGENTS_SKILLS.is_dir():
        raise SystemExit(f"Missing skills directory: {AGENTS_SKILLS}")

    # .opencode/skills/ is a junction to .agents/skills/ — do not write there.
    if OPENCODE_SKILLS.exists() and OPENCODE_SKILLS.resolve() != AGENTS_SKILLS.resolve():
        raise SystemExit(
            f".opencode/skills/ should junction to .agents/skills/; "
            f"resolved to {OPENCODE_SKILLS.resolve()}"
        )

    CURSOR_SKILLS.mkdir(parents=True, exist_ok=True)
    for skill_dir in sorted(AGENTS_SKILLS.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            continue
        target_dir = CURSOR_SKILLS / skill_dir.name
        target_dir.mkdir(parents=True, exist_ok=True)
        content = skill_file.read_text(encoding="utf-8")
        (target_dir / "SKILL.md").write_text(normalize_text(content), encoding="utf-8", newline="\n")

    return [str(CURSOR_SKILLS.relative_to(REPO))]


def expected_rules() -> dict[Path, str]:
    text = AGENTS.read_text(encoding="utf-8")
    sections = extract_sections(text)
    missing = [n for n in MDC_CONFIG if n not in sections]
    if missing:
        raise SystemExit(f"AGENTS.md missing sections: {missing}")
    expected: dict[Path, str] = {}
    for num, cfg in MDC_CONFIG.items():
        path = RULES_DIR / cfg["file"]
        expected[path] = render_mdc(num, sections[num])
    return expected


def check_rules() -> list[str]:
    errors: list[str] = []
    for path, content in expected_rules().items():
        if not path.exists():
            errors.append(f"missing {path.relative_to(REPO)}")
            continue
        actual = path.read_text(encoding="utf-8")
        if normalize_text(actual) != normalize_text(content):
            errors.append(f"stale {path.relative_to(REPO)} (run _sync_agent_rules.py)")
    return errors


def check_skills() -> list[str]:
    errors: list[str] = []
    if not AGENTS_SKILLS.is_dir():
        return [f"missing {AGENTS_SKILLS.relative_to(REPO)}"]

    for skill_dir in sorted(AGENTS_SKILLS.iterdir()):
        if not skill_dir.is_dir():
            continue
        source = skill_dir / "SKILL.md"
        if not source.is_file():
            continue
        target = CURSOR_SKILLS / skill_dir.name / "SKILL.md"
        expected = normalize_text(source.read_text(encoding="utf-8"))
        if not target.exists():
            errors.append(f"missing {target.relative_to(REPO)}")
            continue
        actual = normalize_text(target.read_text(encoding="utf-8"))
        if actual != expected:
            errors.append(f"stale {target.relative_to(REPO)} (run _sync_agent_rules.py)")

    for extra in sorted(CURSOR_SKILLS.glob("*/SKILL.md")) if CURSOR_SKILLS.is_dir() else []:
        name = extra.parent.name
        if not (AGENTS_SKILLS / name / "SKILL.md").is_file():
            errors.append(f"orphan {extra.relative_to(REPO)} (remove or add to .agents/skills/)")

    return errors


def check_sync() -> None:
    errors = check_rules() + check_skills()
    if errors:
        raise SystemExit(
            "Agent rules/skills mirrors are out of sync:\n"
            + "\n".join(f"  - {e}" for e in errors)
            + "\nRun: python Scripts/_sync_agent_rules.py"
        )


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        check_sync()
        print("OK: agent rules and skills mirrors are in sync")
        return

    rules = sync_rules()
    skills = sync_skills()
    print("Synced rules:")
    for path in rules:
        print(f"  {path}")
    print("Synced skills to:")
    for path in skills:
        print(f"  {path}/")
    print("  (.opencode/skills/ junction -> .agents/skills/ - no copy needed)")
    check_sync()
    print("OK: verify passed")


if __name__ == "__main__":
    main()
