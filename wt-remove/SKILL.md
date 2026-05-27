---
name: wt-remove
description: "Consolidate key findings using /zk-merge then close the current branch and remove the worktree."
argument-hint: "What is the purpose of this session?"
license: MIT
compatibility: opencode
metadata:
  audience: developers
  tools: "zk, gh, zk, serena, worktrunk, allium"
---

Consolidate key findings using `zk-merge` skill. Sync any allium files that were created or modified as part of this session back to the main branch directory (allium files are git ignored). Use `worktrunk` to list worktrees and identify the one associated with the current branch. Then, close the worktree and remove it from the filesystem.

If the user passed arguments, treat them as a brief summary of the purpose of this session.
