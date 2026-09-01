#!/usr/bin/env python3
"""Run the Scripts/ test suites that CI enforces.

Discovery is a **denylist**, not an allowlist, and that is the whole point. Every
suite here passed on the day it was written, but only four of twenty-one were
wired into a workflow — the rest were enforced by nothing and nobody noticed,
because adding a test file to `Scripts/` did not add it to CI. Inverting the
default fixes the class of bug rather than the instance: a new `_test_*.py` is
enforced the moment it lands, and skipping one is a deliberate act that has to be
written down here with a reason.

Held suites are still **printed on every run**. A skip that scrolls past silently
is indistinguishable from coverage.

Usage (from the repository root):

    python Scripts/_run_test_suites.py           # what CI enforces
    python Scripts/_run_test_suites.py --all     # including the held suites
    python Scripts/_run_test_suites.py --list    # show what would run, run nothing
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
BASE = SCRIPTS.parent

# Suites deliberately left out of the enforced set, each with the reason it is
# held. These are not broken — they pass. They are withheld because failing them
# would not mean the same thing as failing the others, and that judgement belongs
# to a maintainer rather than to a green tick.
HELD: dict[str, str] = {
    "_test_study_html_layout.py": (
        "pins the reader's exact CSS and toolbar structure, so a deliberate "
        "restyle fails it; enforcing means every design change updates an "
        "assertion in the same commit"
    ),
    "_test_analyze_jeevan_pass_three.py": (
        "asserts frozen results (122 members, residual 34) parsed from a tracked "
        "research note in The-Epistemology-of-Coexistence; editing that study's "
        "note would fail CI repo-wide. Also ~18s, most of the suite's runtime"
    ),
    "_test_analyze_jeevan_pass_four.py": (
        "chained onto pass three's committed CSVs and its 122-record invariant"
    ),
    "_test_validate_jeevan_pass_five.py": (
        "chained onto pass four's coverage register"
    ),
}


def discover() -> list[Path]:
    return sorted(SCRIPTS.glob("_test_*.py"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--all",
        action="store_true",
        help="also run the held suites listed in HELD",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="print the enforced and held sets, then exit without running",
    )
    args = parser.parse_args()

    suites = discover()
    if not suites:
        print("No Scripts/_test_*.py suites found; discovery is broken.")
        return 1

    selected = [p for p in suites if args.all or p.name not in HELD]
    held = [p for p in suites if p.name in HELD and not args.all]

    # Names in HELD that no longer exist mean a rename left a stale reason behind,
    # and would silently drop the suite's replacement out of the held set.
    stale = sorted(set(HELD) - {p.name for p in suites})
    if stale:
        print("Stale entries in HELD (no such suite): " + ", ".join(stale))
        return 1

    if held:
        print(f"Held out of the enforced set ({len(held)}):")
        for path in held:
            print(f"  - {path.name}: {HELD[path.name]}")
        print()

    if args.list:
        print(f"Would run ({len(selected)}):")
        for path in selected:
            print(f"  - {path.name}")
        return 0

    failures: list[str] = []
    for path in selected:
        print(f"== {path.name}")
        result = subprocess.run(
            [sys.executable, str(path)],
            cwd=BASE,
            check=False,
        )
        if result.returncode != 0:
            failures.append(path.name)

    print()
    if failures:
        print(f"{len(failures)} of {len(selected)} suite(s) FAILED:")
        for name in failures:
            print(f"  - {name}")
        return 1
    print(f"All {len(selected)} enforced suite(s) passed. {len(held)} held.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
