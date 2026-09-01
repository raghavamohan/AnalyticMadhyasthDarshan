#!/usr/bin/env python3
"""Tests for the commit-artifacts composite action's shell.

This action is the only part of CI that writes to a branch, and nothing
exercises it. It is referenced by study-pr.yml, which runs only on a labelled
study pull request, and by proposal-approved.yml, which runs only when an issue
is labelled -- so an edit to it otherwise reaches the default branch with no CI
having run it at all. study-pr.yml compounds that by resolving the action as
`@master`, meaning even a real study pull request tests the merged copy rather
than the branch's.

These tests extract the step's own script out of action.yml and drive it against
a throwaway repository with a local bare remote, so the push path is real rather
than mocked.

Run from the repository root:

    python Scripts/_test_commit_artifacts.py
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
BASE = SCRIPTS.parent
ACTION = BASE / ".github" / "actions" / "commit-artifacts" / "action.yml"

THIS_REPO = "owner/repo"
FORK_REPO = "contributor/fork"


def extract_run_script() -> str:
    """Pull the `run: |` block out of action.yml without a YAML parser.

    PyYAML is not in requirements.txt and nothing else in Scripts/ needs it;
    adding a dependency for one test is a worse trade than handling the block
    scalar's indentation here.
    """
    lines = ACTION.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.strip() not in ("run: |", "run: |-"):
            continue
        indent = len(line) - len(line.lstrip())
        body = []
        for rest in lines[index + 1:]:
            if rest.strip() and (len(rest) - len(rest.lstrip())) <= indent:
                break
            body.append(rest[indent + 2:])
        return "\n".join(body) + "\n"
    raise AssertionError(f"no `run: |` block found in {ACTION}")


def step_script() -> str:
    """The step's script with the composite-action inputs already substituted."""
    text = extract_run_script()
    assert "${{ inputs.paths }}" in text, "paths input no longer interpolated"
    assert "${{ inputs.message }}" in text, "message input no longer interpolated"
    return text.replace("${{ inputs.paths }}", "Studies").replace(
        "${{ inputs.message }}", "ci: regenerate study artifacts"
    )


def _git(cwd: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    )
    return done.stdout.strip()


def run_case(
    head_repo: str, *, dirty: bool, branch: str = ""
) -> tuple[int, str, bool, dict[str, str]]:
    """Run the step once.

    ``head_repo`` is what GitHub would put in HEAD_REPO -- the empty string for
    any event with no pull_request payload. ``dirty`` decides whether CI is
    treated as having regenerated something. ``branch`` is the composite action's
    ``branch`` input: empty pushes the checked-out branch, non-empty commits onto
    a new branch and pushes that instead.

    Returns the exit status, the combined output, whether ``main`` moved on the
    remote, and the step outputs the script wrote to GITHUB_OUTPUT.
    """
    tmp = Path(tempfile.mkdtemp(prefix="commit-artifacts-"))
    try:
        remote = tmp / "remote.git"
        work = tmp / "work"
        (work / "Studies").mkdir(parents=True)
        subprocess.run(
            ["git", "init", "-q", "--bare", str(remote)], check=True, capture_output=True
        )
        _git(work, "init", "-q", "-b", "main")
        _git(work, "config", "user.email", "ci@example.invalid")
        _git(work, "config", "user.name", "ci")
        (work / "Studies" / "artifact.txt").write_text("base\n", encoding="utf-8")
        _git(work, "add", "-A")
        _git(work, "commit", "-qm", "base")
        _git(work, "remote", "add", "origin", str(remote))
        _git(work, "push", "-q", "-u", "origin", "main")
        before = _git(work, "rev-parse", "origin/main")

        if dirty:
            (work / "Studies" / "artifact.txt").write_text("regenerated\n", encoding="utf-8")

        output_file = tmp / "github_output"
        output_file.touch()
        done = subprocess.run(
            ["bash", "-c", step_script()],
            cwd=work,
            capture_output=True,
            text=True,
            env={
                "PATH": __import__("os").environ["PATH"],
                "HOME": str(tmp),
                "HEAD_REPO": head_repo,
                "THIS_REPO": THIS_REPO,
                "BRANCH": branch,
                "GITHUB_OUTPUT": str(output_file),
            },
        )
        after = _git(work, "rev-parse", "origin/main")
        # Last write wins, matching how Actions collapses repeated output keys.
        outputs: dict[str, str] = {}
        for line in output_file.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                key, _, value = line.partition("=")
                outputs[key] = value
        if branch:
            remote_branches = _git(work, "ls-remote", "--heads", "origin")
            outputs["_remote_has_branch"] = str(f"refs/heads/{branch}" in remote_branches)
        return done.returncode, done.stdout + done.stderr, before != after, outputs
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_same_repo_pull_request_still_pushes() -> None:
    code, out, pushed, outputs = run_case(THIS_REPO, dirty=True)
    assert code == 0, out
    assert pushed, "a same-repo pull request must still get its artifacts committed"
    assert outputs.get("pushed") == "true", outputs


def test_fork_pull_request_with_stale_artifacts_fails_with_guidance() -> None:
    """The push would 403; say what to run instead of dying on the raw error."""
    code, out, pushed, _outputs = run_case(FORK_REPO, dirty=True)
    assert code == 1, out
    assert not pushed, "nothing may reach the remote from a fork run"
    assert FORK_REPO in out, out
    assert "Studies/artifact.txt" in out, "must name the files left stale"
    assert "_regenerate_pdf.py" in out, "must say what to run locally"
    assert "::error" in out, "must surface as an annotation, not just log text"


def test_fork_pull_request_with_correct_artifacts_passes() -> None:
    """A fork contributor who already regenerated must not be failed.

    This is why the fork branch sits after the empty-diff check rather than
    before it: reaching it has to mean the branch really is stale.
    """
    code, out, pushed, outputs = run_case(FORK_REPO, dirty=False)
    assert code == 0, out
    assert not pushed
    assert "No generated file changes to commit." in out, out
    assert outputs.get("pushed") == "false", outputs


def test_event_without_pull_request_payload_still_pushes() -> None:
    """proposal-approved.yml runs on `issues`, where HEAD_REPO is empty."""
    code, out, pushed, outputs = run_case("", dirty=True)
    assert code == 0, out
    assert pushed, "the issues-triggered bootstrap commit must still be pushed"
    assert outputs.get("pushed") == "true", outputs


def test_branch_input_pushes_a_new_branch_and_leaves_the_base_alone() -> None:
    """The bootstrap path: land on a side branch, never on the base directly.

    proposal-approved.yml cannot push to master -- the ruleset requires a pull
    request and github-actions[bot] has no bypass -- so it commits onto a branch
    and opens a PR instead. The base must be untouched.
    """
    code, out, base_moved, outputs = run_case(
        "", dirty=True, branch="ci/bootstrap-proposal-42"
    )
    assert code == 0, out
    assert not base_moved, "the base branch must not move when branch: is set"
    assert outputs.get("_remote_has_branch") == "True", out
    assert outputs.get("pushed") == "true", outputs


def test_branch_input_with_nothing_to_commit_pushes_no_branch() -> None:
    """No stray branch, and `pushed` says so, so the caller can skip the PR step."""
    code, out, base_moved, outputs = run_case(
        "", dirty=False, branch="ci/bootstrap-proposal-43"
    )
    assert code == 0, out
    assert not base_moved
    assert outputs.get("_remote_has_branch") == "False", out
    assert outputs.get("pushed") == "false", outputs


def main() -> int:
    if shutil.which("bash") is None:
        print("bash not available; skipping commit-artifacts shell tests.")
        return 0
    tests = [
        obj
        for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]
    failed = 0
    for test in tests:
        try:
            test()
        except Exception as exc:  # noqa: BLE001 - test harness boundary
            failed += 1
            print(f"FAIL {test.__name__}: {type(exc).__name__}: {exc}")
        else:
            print(f"ok   {test.__name__}")
    if failed:
        print(f"\n{failed} test(s) failed.")
        return 1
    print(f"\nAll {len(tests)} test(s) passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
