#!/usr/bin/env python3
"""Guard: generator scripts must write tracked files through write_text_lf.

AGENTS.md section 8 requires every file in the repository to use LF, and says
the scripts that write files "must emit LF". Nothing enforced it, and the
scripts did not: `Path.write_text` uses text mode, which translates "\\n" to
"\\r\\n" on Windows. A single `python Scripts/_build_studies_index.py` therefore
rewrote 29 tracked files -- every `discussion.html`, `Studies/README.md`, the
issue template -- with CRLF and no content change. `.gitattributes` normalized
them back on commit, so the repository never carried CRLF, but until then
`git status` listed 29 modified files that buried the real diff.

CI runs on Linux, where text mode does not translate newlines, so this bug was
invisible to every automated check and only cost the Windows maintainers. That
is why this test reads the *source* rather than testing behaviour at runtime:
a runtime test would pass on Linux no matter how the writes were spelled.

`_common.write_text_lf` writes bytes (no translation) and skips the write when
the content is unchanged, so rebuilds leave both content and mtimes alone.

To add a deliberate exception, put `# lf-exempt: <reason>` on the call line or
the line just above it. Two exist today, both legitimate: the PDF text cache
invalidates on mtime so it must be rewritten every time, and social-card
rendering writes into a TemporaryDirectory that never reaches the repository.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent

# Kwargs Path.write_text actually accepts. A `.write_text()` call carrying any
# other keyword belongs to some other object -- the deck-notes PDF writer calls
# `tw.write_text(page, color=GOLD)` on a canvas -- and is not a file write.
PATH_WRITE_TEXT_KWARGS = {"encoding", "errors", "newline"}

EXEMPT_MARKER = "# lf-exempt:"


def _statement_is_exempt(source_lines: list[str], node: ast.AST) -> bool:
    """True when the call, or the line just above it, carries the marker.

    These calls are already near the line-length limit, so the reason usually
    reads better on its own line above than as a trailing comment.
    """
    start = getattr(node, "lineno", 0)
    end = getattr(node, "end_lineno", start)
    return any(
        EXEMPT_MARKER in source_lines[i - 1]
        for i in range(start - 1, end + 1)
        if 0 < i <= len(source_lines)
    )


def _is_text_mode_open(node: ast.Call) -> bool:
    """True for `open(..., "w")` and friends in text mode."""
    func = node.func
    name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
    if name != "open":
        return False
    mode = None
    if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
        mode = node.args[1].value
    for kw in node.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
            mode = kw.value.value
    if not isinstance(mode, str) or "b" in mode:
        return False
    return any(ch in mode for ch in "wxa")


def check_file(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    lines = source.split("\n")
    problems: list[str] = []

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [f"{path.name}:{exc.lineno}: could not parse -- {exc.msg}"]

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        kwargs = {kw.arg for kw in node.keywords if kw.arg}

        if isinstance(node.func, ast.Attribute) and node.func.attr == "write_text":
            if not kwargs <= PATH_WRITE_TEXT_KWARGS:
                continue  # not Path.write_text
            if "newline" in kwargs or _statement_is_exempt(lines, node):
                continue
            problems.append(
                f"{path.name}:{node.lineno}: Path.write_text() without newline= "
                f"-- use write_text_lf(path, text) from _common"
            )
            continue

        if _is_text_mode_open(node):
            if "newline" in kwargs or _statement_is_exempt(lines, node):
                continue
            problems.append(
                f"{path.name}:{node.lineno}: open(..., 'w') in text mode without "
                f"newline='\\n' -- writes CRLF on Windows"
            )

    return problems


def scan() -> list[str]:
    problems: list[str] = []
    for path in sorted(SCRIPTS.glob("*.py")):
        # Tests write fixtures into temp dirs, never into the repository.
        if path.name.startswith("_test_"):
            continue
        problems.extend(check_file(path))
    return problems


def main() -> int:
    problems = scan()
    if problems:
        print("Generated-file writes that can emit CRLF on Windows:\n")
        for problem in problems:
            print(f"  {problem}")
        print(
            f"\n{len(problems)} problem(s). Use write_text_lf() from _common, or "
            f"mark a deliberate exception with '{EXEMPT_MARKER} <reason>'."
        )
        return 1
    print("Generated-file write check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
