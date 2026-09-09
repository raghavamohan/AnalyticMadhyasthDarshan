"""Resumable proposal bootstrap; all Git writes stay on its own PR."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def command(*args: str) -> str:
    result = subprocess.run(args, cwd=BASE, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"{args[0]} failed")
    return result.stdout.strip()


def gh(*args: str):
    return json.loads(command("gh", *args) or "null")


def output(name: str, value: str) -> None:
    if path := os.environ.get("GITHUB_OUTPUT"):
        with open(path, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(f"{name}={value}\n")


def assert_approved(issue: dict) -> None:
    if issue.get("state") != "open" or "proposal-approved" not in {item["name"] for item in issue.get("labels", [])}:
        raise ValueError("Proposal must still be open and proposal-approved.")


def status(repo: str, sha: str, state: str, description: str) -> None:
    command("gh", "api", "--method", "POST", f"repos/{repo}/statuses/{sha}",
            "-f", f"state={state}", "-f", "context=verify", "-f", f"description={description}",
            "-f", f"target_url=https://github.com/{repo}/actions/workflows/studies-index-check.yml")


def prepare(repo: str, issue_number: int, branch: str) -> None:
    assert_approved(gh("api", f"repos/{repo}/issues/{issue_number}"))
    try:
        settings = gh("api", f"repos/{repo}/actions/permissions/workflow")
    except RuntimeError as error:
        # GITHUB_TOKEN has no Administration permission. The PR-create endpoint
        # remains authoritative when this settings read is forbidden.
        if '403' not in str(error):
            raise
        settings = None
        print('Workflow token cannot read administrative settings; PR creation will enforce the repository policy.')
    if settings is not None and not settings.get("can_approve_pull_request_reviews"):
        raise ValueError("Enable Actions 'Allow GitHub Actions to create and approve pull requests' in repository settings before bootstrap.")
    registry = json.loads((BASE / "Studies/proposal-registry.json").read_bytes())
    existing = next((row for row in registry.get('proposals', []) if str(row.get('issueNumber')) == str(issue_number)), None)
    if existing:
        rows = [row for path in (BASE / 'Studies').glob('catalog-*.json') if path.name != 'catalog-all.json' for row in json.loads(path.read_bytes())]
        catalog = next((row for row in rows if row.get('slug') == existing.get('slug')), None)
        if not catalog or existing.get('phase') not in {'pre-catalog', 'catalog-draft', 'catalog-released', 'published', 'catalog'}:
            raise ValueError('Existing proposal metadata is incomplete or retired; reconcile it before retrying.')
        if existing['phase'] == 'pre-catalog' and catalog.get('status') != 'ongoing':
            raise ValueError('Proposal phase and catalog status disagree.')
        # Also recovers a run interrupted after merge but before dispatch.
        command('gh', 'workflow', 'run', 'publish-site.yml', '--repo', repo, '--ref', 'master',
                '-f', f'source_sha={command("git", "rev-parse", "HEAD")}')
        output("complete", "true")
        return
    prs = gh("pr", "list", "--repo", repo, "--head", branch, "--state", "all", "--json", "number,state")
    if any(pr["state"] == "CLOSED" for pr in prs) and not any(pr["state"] == "OPEN" for pr in prs):
        raise ValueError("The bootstrap PR was closed without merging; maintainer review is required before retry.")
    remote = command("git", "ls-remote", "--heads", "origin", f"refs/heads/{branch}")
    if remote:
        command("git", "fetch", "origin", f"refs/heads/{branch}")
        command("git", "switch", "-c", branch, "FETCH_HEAD")
        command("git", "merge", "--no-edit", "origin/master")
    else:
        command("git", "switch", "-c", branch)
    output("complete", "false")


def verify_merge(repo: str, issue_number: int, branch: str) -> None:
    assert_approved(gh("api", f"repos/{repo}/issues/{issue_number}"))
    # A resumed branch may contain a new base-merge commit with no dirty files.
    # Publish that head even when the generated-artifact action was a no-op.
    command('git', 'push', '-u', 'origin', 'HEAD')
    prs = gh("pr", "list", "--repo", repo, "--head", branch, "--state", "open", "--json", "number")
    if not prs:
        try:
            command("gh", "pr", "create", "--repo", repo, "--base", "master", "--head", branch,
                    "--title", f"Prepare Planned workspace for proposal #{issue_number}",
                    "--body", f"Approved proposal: #{issue_number}\n\nCatalog and proposal metadata only; no public reader or PDF.")
        except RuntimeError as error:
            raise RuntimeError("Could not create the bootstrap PR. Check Actions 'Allow GitHub Actions to create and approve pull requests'. The prepared branch is retained. " + str(error)) from error
        prs = gh('pr', 'list', '--repo', repo, '--head', branch, '--state', 'open', '--json', 'number')
    number = str(prs[0]['number'])
    sha = command("git", "rev-parse", "HEAD")
    status(repo, sha, "pending", "Waiting for bootstrap verification.")
    try:
        command("gh", "workflow", "run", "studies-index-check.yml", "--repo", repo,
                "--ref", branch, "-f", f"report_sha={sha}")
        deadline = time.monotonic() + 1200
        while time.monotonic() < deadline:
            states = gh("api", f"repos/{repo}/commits/{sha}/statuses")
            check = next((item for item in states if item["context"] == "verify"), None)
            if check and check["state"] == "success":
                break
            if check and check["state"] in {"failure", "error"}:
                raise RuntimeError("Bootstrap verification failed; inspect the verify status on its PR.")
            time.sleep(5)
        else:
            raise RuntimeError("Bootstrap verification timed out.")
    except Exception:
        status(repo, sha, "failure", "Bootstrap verification did not complete.")
        raise
    assert_approved(gh("api", f"repos/{repo}/issues/{issue_number}"))
    command("gh", "pr", "merge", number, "--repo", repo, "--merge", "--delete-branch", "--match-head-commit", sha)
    merged = gh("pr", "view", number, "--repo", repo, "--json", "mergeCommit")["mergeCommit"]["oid"]
    command("gh", "workflow", "run", "publish-site.yml", "--repo", repo, "--ref", "master", "-f", f"source_sha={merged}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["prepare", "verify-merge"])
    parser.add_argument("--issue", type=int, required=True)
    args = parser.parse_args()
    if args.issue <= 0:
        raise SystemExit("Issue number must be positive.")
    repo = os.environ["GITHUB_REPOSITORY"]
    (prepare if args.mode == "prepare" else verify_merge)(repo, args.issue, f"ci/bootstrap-proposal-{args.issue}")
