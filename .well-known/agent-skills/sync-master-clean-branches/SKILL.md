---
name: sync-master-clean-branches
description: >-
  Safely switch a Git repository to master, fast-forward it to origin/master,
  remove obsolete local PR branches whose work is already merged, and clean up generated study/application
  PDFs. Use when
  asked to sync or refresh master, return to the remote head, prune merged local
  PR branches, or perform a full sync and cleanup. Preserves reference-library
  files, the repository-local tmp directory, dirty source work, and remote or unmerged branches.
---

# Sync master, clean local PR branches and generated output

A full invocation of this skill includes syncing `master`, cleaning merged local
PR branches and deleting local
generated PDFs under `Studies/` and `Applications/`. If the user explicitly
requests only syncing or only branch cleanup, perform only that operation. A
full cleanup request authorizes the PDF removal described
below; show the exact targets and proceed without asking for routine
confirmation. Preserve the repository-root `tmp/` contents; temporary stashing
with restoration is allowed, but deleting them as cleanup is not.

## Safety invariants

- Inspect the working tree before switching branches. Untracked files under
  the repository-root `tmp/` directory may remain during sync or be temporarily
  stashed without further confirmation. Any tracked
  changes, including under `tmp/`, or untracked paths outside `tmp/` block sync:
  do not stash, commit, reset, discard, or carry those changes onto `master`
  without the user's direction.
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

Apply the clean-tree gate with one exception: untracked paths under the exact
repository-root `tmp/` directory do not block sync. Use
`git status --porcelain --untracked-files=all` when individual paths are needed
to distinguish this exception from other changes. Prefer leaving `tmp/` in
place. When needed for sync, a temporary stash of its untracked files is
authorized:

```powershell
git stash push --include-untracked -m "sync-master: preserve tmp" -- tmp/
```

Apply the gate for other changes before stashing. Keep the pathspec scoped to
`tmp/`; do not use a repository-wide stash or include ignored files with
`--all`. Record the newly created stash's exact object ID and verify creation
succeeded before proceeding; do not mistake an older stash for a new one.
Restore that exact stash with `git stash apply <stash-object-id>` after the
sync attempt, including when sync fails. Drop only the matching stash entry
after verifying all saved files were restored. If restoration conflicts, keep
the stash and report its ID and the remaining conflict; do not overwrite files
or discard the saved copy.

Do not delete `tmp/` as cleanup, stage its files for commit, or add ignore rules
for it. If Git still refuses a switch or pull because preserved files would be
overwritten, stop and report the conflict without forcing the operation.

## Sync master

For a clean working tree, or one containing only untracked `tmp/` files:

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
changed paths other than any preserved untracked `tmp/` files.

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

If a PDF is locked or permission is denied, leave the affected target
in place and report it. Do not close applications, alter permissions, or
substitute a different deletion method to bypass an approval rejection. Continue
independent cleanup and report any remaining generated output accurately.

## Completion check

```powershell
git branch -vv
git status --short --branch
```

Repeat the PDF inventory to confirm which eligible files remain. Report the
updated `master` commit, any preserved untracked `tmp/` files and their stash
restoration status (including any retained stash ID), local branches and PDFs
removed, skipped branches or PDFs and their reasons, and whether the working
tree is clean. If untracked `tmp/` files remain, report them explicitly rather
than calling the working tree clean. Ignored PDFs do not affect Git's clean status; do not use a clean
status as proof they were removed.
