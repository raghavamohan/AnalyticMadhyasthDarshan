---
name: sync-master-clean-branches
description: >-
  Safely switch a Git repository to master, fast-forward it to origin/master,
  remove obsolete local PR branches whose work is already merged, remove the
  repository-local tmp directory, and clean up generated study/application
  PDFs. Use when
  asked to sync or refresh master, return to the remote head, prune merged local
  PR branches, or perform a full sync and cleanup. Preserves reference-library
  files, dirty source work, and remote or unmerged branches.
---

# Sync master, clean local PR branches and generated output

A full invocation of this skill includes syncing `master`, cleaning merged local
PR branches, removing the repository-root `tmp/` directory, and deleting local
generated PDFs under `Studies/` and `Applications/`. If the user explicitly
requests only syncing or only branch cleanup, perform only that operation. A
full cleanup request authorizes the temporary-output and PDF removal described
below; show the exact targets and proceed without asking for routine
confirmation.

## Safety invariants

- Inspect the working tree before switching branches. The exact repository-root
  `tmp/` directory is disposable output during a full invocation: verify its
  resolved path, show its contents, delete it, and inspect the tree again. If
  anything else is dirty, do not stash, commit, reset, discard, or carry the
  changes onto `master` without the user's direction.
- Update `master` with a fast-forward only. If it has diverged from
  `origin/master`, stop and report the divergence; do not reset or rebase it.
- Never infer that an upstream marked `[gone]` is safe to delete: first confirm
  the local branch is merged into the updated `master`.
- Exclude `master` and every branch checked out in any worktree.
- Delete local branches only. Do not delete remote branches unless the user asks
  for that separately.
- Use `git branch -d`, not `git branch -D`. Report branches that safe deletion
  refuses instead of forcing their removal.
- Every `.pdf` file anywhere under `Studies/` and `Applications/` is generated
  output in this repository and may be deleted during a full invocation,
  regardless of Git tracking or filename-to-source naming. Never delete PDFs in
  `References/`, other worktrees, or elsewhere in the repository under this
  rule.

## Inspect the repository

Run from the repository root:

```powershell
git status --short --branch
git remote -v
git worktree list --porcelain
git for-each-ref refs/heads --format="%(refname:short)|%(upstream:short)|%(upstream:track)|%(objectname:short)|%(subject)"
```

Confirm that `origin/master` exists. A clean status prints only the branch line;
any additional path is an uncommitted change that must be preserved.

For a full invocation, inspect and remove the exact repository-root `tmp/`
directory before applying the clean-tree gate. Resolve both the repository root
and the target to absolute paths, require the target to equal `<repo>/tmp`, and
refuse a symbolic link, junction, or other reparse point. Use native PowerShell
file operations and do not interpret `/tmp` as an operating-system temporary
directory. Re-run `git status --short --branch` afterward. Any remaining changed
path blocks branch switching until the user decides how to handle it.

## Sync master

For a clean working tree:

```powershell
git switch master
git pull --ff-only origin master
```

If `master` is already checked out, proceed directly to the fast-forward pull.
Do not substitute a normal merge pull.

Verify the result:

```powershell
git status --short --branch
git log -1 --oneline --decorate
```

The status should show `master...origin/master` with no ahead/behind count and no
changed paths.

## Clean obsolete local PR branches

Refresh remote-tracking state before deciding which branches are stale:

```powershell
git fetch --prune origin
git branch --merged master --format="%(refname:short)"
git worktree list --porcelain
git branch -vv
```

Build an exact candidate list from local branches that satisfy all of these:

1. The branch appears in `git branch --merged master`.
2. It is not `master` or another intentionally long-lived branch.
3. It is not checked out in any worktree.
4. Its name, upstream, or known merged PR establishes that it is a short-lived
   PR branch rather than a persistent local integration branch.

Show or state the exact candidates before deleting them. Delete each candidate
with safe deletion:

```powershell
git branch -d <branch-name>
```

Do not force-delete branches absent from `git branch --merged master`, including
squash-merged or rebased branches. Report them separately so the user can decide
whether their remaining commits are disposable.

## Clean generated PDFs

After the sync and branch cleanup, discover every `.pdf` file recursively under
`Studies/` and `Applications/`. Do not rely on ordinary `git status` or
`git clean -fd`: generated PDFs are normally ignored, and the cleanup contract
also covers any accidentally tracked PDF in these two roots.

An eligible PDF must be a regular local file whose resolved absolute path stays
inside the current repository's `Studies/` or `Applications/` root. Do not
follow or delete symbolic links, junctions, or other reparse points; skip any
file with a reparse point in its directory ancestry. Source-name checks and Git
tracking checks are intentionally unnecessary because repository policy defines
all PDFs in these roots as generated artifacts.

Show the exact eligible paths, then remove only those files. This covers study
papers, slides PDFs, presenter-notes PDFs, generated companion-note PDFs, and
generated PDFs in nested study/application subdirectories. Preserve Markdown,
HTML, PPTX, figures, notes, and everything outside the two PDF roots. Local
deletion does not delete the published PDFs in Cloudflare R2.

On Windows, use native PowerShell file operations with verified absolute literal
paths, for example `Remove-Item -LiteralPath <verified-pdf-path> -ErrorAction Stop`.
Delete files individually; do not use recursive directory removal or a blanket
`git clean -fdx`, which would also remove unrelated ignored data and settings.

If `tmp/` or a PDF is locked or permission is denied, leave the affected target
in place and report it. Do not close applications, alter permissions, or
substitute a different deletion method to bypass an approval rejection. Continue
independent cleanup and report any remaining generated output accurately.

## Completion check

```powershell
git branch -vv
git status --short --branch
```

Repeat the PDF inventory to confirm which eligible files remain. Report the
updated `master` commit, whether `tmp/` was removed, local branches and PDFs
removed, skipped branches or PDFs and their reasons, and whether the working
tree is clean. Ignored PDFs do not affect Git's clean status; do not use a clean
status as proof they were removed.
