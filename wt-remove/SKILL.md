---
name: wt-remove
description: "Sync untracked session artifacts to the target worktree, consolidate key findings using /zk-merge, then close the current branch and remove the worktree. Pass an optional argument summarising the purpose of this session."
license: MIT
compatibility: opencode
metadata:
  audience: developers
  tools: "zk, gh, serena, worktrunk, allium"
---

Consolidate key findings using `zk-merge` skill. Then sync untracked files that carry session knowledge to the primary worktree before closing.

If the user passed arguments, treat them as a brief summary of the purpose of this session.

## Step 1 — Consolidate findings

Run the `zk-merge` skill to capture key decisions, patterns, and learnings from this session into the Zettelkasten.

## Step 2 — Sync untracked session artifacts

Git worktrees share a `.git` object store but have independent working trees. Untracked (git-ignored) files — docs, tooling config, specs — exist only in the worktree's filesystem and are lost when the worktree is removed unless explicitly synced.

### 2a. Discover untracked files

Run `git status --short` in the current worktree and collect all `??` entries.

### 2b. Resolve the destination

The destination is the repo's primary worktree (typically `main` or `master`). Resolve it with:

```bash
git worktree list --porcelain \
  | awk '/^worktree/{p=$2} /^branch refs\/heads\/(main|master)$/{print p; exit}'
```

### 2c. Categorize and copy

Use the table below to decide what to sync. For each **Sync** entry, check whether the destination already has the file. Only copy if the source is newer or the destination is absent. Use `cp -r` — never `mv`.

| Pattern | Action | Reason |
|---------|--------|--------|
| `docs/**` | Sync if newer or absent | Project documentation built during the session |
| `.claude/settings.local.json` | Sync if newer or absent | Accumulated permission allowlist |
| `*.allium`, `docs/**/*.allium` | Sync if newer or absent | Allium specs (git-ignored by design) |
| `.opencode/context/**` | Sync if newer or absent | Context-discovery artifacts |
| `.claude/scheduled_tasks.lock` | Skip | Ephemeral harness lock; meaningless outside this session |
| `target/`, `*.class`, `*.jar` | Skip | Build output |
| Any other `**/.git/**` | Skip | Internal git state |

If there are untracked files not covered by the table, use judgment: does the file carry knowledge or tooling state that another session would want? If yes, sync it; if it's ephemeral runtime state, skip it.

## Step 3 — Identify and remove the worktree

Use `worktrunk` (`wt list`) to identify the worktree associated with the current branch. Then close it:

```bash
wt remove <worktree-path>   # or: git worktree remove <path>
```

Confirm the worktree directory no longer exists after removal.
