---
name: sync-master-clean-branches
description: >-
  Safely switch a Git repository to master, fast-forward it to origin/master,
  and remove obsolete local PR branches whose work is already merged. Use when
  asked to sync or refresh master, return to the remote head, prune merged local
  PR branches, or perform both tasks. Does not discard dirty work, rewrite
  master, or delete remote or unmerged branches.
---

# Sync master and clean local PR branches

Perform only the operation the user requested: syncing `master`, cleaning local
PR branches, or both.

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

## Completion check

```powershell
git branch -vv
git status --short --branch
```

Report the updated `master` commit, every local branch removed, any branch
skipped and why, and whether the working tree is clean.
