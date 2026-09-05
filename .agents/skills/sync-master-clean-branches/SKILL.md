---
name: sync-master-clean-branches
description: >-
  Safely switch a Git repository to master, fast-forward it to origin/master,
  remove obsolete local PR branches whose work is already merged, and clean up
  uncommitted generated study/application PDFs. Use when
  asked to sync or refresh master, return to the remote head, prune merged local
  PR branches, or perform a full sync and cleanup. Preserves tracked PDFs,
  reference-library files, dirty source work, and remote or unmerged branches.
---

# Sync master, clean local PR branches and generated PDFs

A full invocation of this skill includes syncing `master`, cleaning merged local
PR branches, and removing eligible local generated PDFs. If the user explicitly
requests only syncing or only branch cleanup, perform only that operation. A
full cleanup request authorizes the eligible PDF removal described below; show
the candidates and proceed without asking for routine confirmation.

## Safety invariants

- Inspect the working tree before switching branches. If it is dirty, do not
  stash, commit, reset, discard, or carry the changes onto `master` without the
  user's direction.
- Update `master` with a fast-forward only. If it has diverged from
  `origin/master`, stop and report the divergence; do not reset or rebase it.
- Never infer that an upstream marked `[gone]` is safe to delete: first confirm
  the local branch is merged into the updated `master`.
- Exclude `master` and every branch checked out in any worktree.
- Delete local branches only. Do not delete remote branches unless the user asks
  for that separately.
- Use `git branch -d`, not `git branch -D`. Report branches that safe deletion
  refuses instead of forcing their removal.
- PDF cleanup is limited to regenerable, uncommitted `.pdf` files directly inside
  `Studies/<Slug>/` and `Applications/<Slug>/` in the current worktree. Never
  delete PDFs in `References/`, other worktrees, or elsewhere in the repository
  under this rule. Preserve PDFs tracked in the index or HEAD, both before
  switching branches and after syncing master.

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

Before switching, retain the PDF paths tracked by the index and HEAD as a
protected set for the later cleanup. This also protects a staged addition or a
PDF tracked on the starting branch but absent from master. Use Git's path output
without lossy parsing of quoted names (for example, NUL-delimited output).

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

## Clean uncommitted generated PDFs

After the sync and branch cleanup, discover PDFs in both the ordinary untracked
and ignored sets. Study/application PDFs are intentionally ignored, so ordinary
`git status` or `git clean -fd` alone will miss them. For inspection:

```powershell
git ls-files --others --exclude-standard -- 'Studies/*/*.pdf' 'Applications/*/*.pdf'
git ls-files --others --ignored --exclude-standard -- 'Studies/*/*.pdf' 'Applications/*/*.pdf'
```

Filter these results to files directly inside a study/application directory;
Git pathspecs can also match deeper paths. An eligible PDF must satisfy all of
these conditions:

1. It is a regular local `.pdf` file, outside the protected set captured before
   switching, and absent from both the current Git index and HEAD. Recheck its
   tracking status immediately before removal.
2. A tracked authoring source explains how to regenerate it: a same-stem `.md`
   or `.pptx`, or, for `<Deck>-notes.pdf`, the corresponding `<Deck>.pptx`.
   Preserve a PDF with no such source and report it as an ambiguous original.
3. Its resolved absolute path stays inside the current repository's permitted
   study/application directory. Skip symbolic links, junctions, or other reparse
   points in the file or its directory ancestry.

Show the exact eligible paths, then remove only those files. This covers study
papers, slides PDFs, presenter-notes PDFs, and generated companion-note PDFs.
Preserve their Markdown, HTML, PPTX, figures, and notes sources. Local deletion
does not delete the published PDFs in Cloudflare R2.

On Windows, use native PowerShell file operations with verified absolute literal
paths, for example `Remove-Item -LiteralPath <verified-pdf-path> -ErrorAction Stop`.
Delete files individually; do not use recursive directory removal or a blanket
`git clean -fdx`, which would also remove unrelated ignored data and settings.

If a PDF is locked or permission is denied, leave it in place and report the
specific file. Do not close applications, alter permissions, or substitute a
different deletion method to bypass an approval rejection. Continue independent
cleanup and report any remaining PDFs accurately.

## Completion check

```powershell
git branch -vv
git status --short --branch
```

Repeat the PDF inventory to confirm which eligible files remain. Report the
updated `master` commit, local branches and PDFs removed, skipped branches or
PDFs and their reasons, and whether the working tree is clean. Ignored PDFs do
not affect Git's clean status; do not use a clean status as proof they were removed.
