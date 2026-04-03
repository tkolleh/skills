---
name: smart-init
description: "Trigger on: init, CLAUDE.md, AGENTS.md, setup repo, onboard, generate docs, project documentation for agents, bootstrap, new project setup. Evidence-guided AGENTS.md/CLAUDE.md generator that makes AI coding agent runs ~28% faster and ~16% cheaper by eliminating exploratory navigation."
license: MIT
compatibility: opencode
metadata:
  audience: developers
---

You are generating or updating this repository's root `CLAUDE.md` (or `AGENTS.md` for OpenCode compatibility) to make future coding-agent runs faster and cheaper (reduce exploratory navigation and repeated inference). Optimize for: concise, accurate, actionable, and easy to maintain.

## Research Background

This command implements findings from "On the Impact of AGENTS.md Files on the Efficiency of AI Coding Agents" (Lulla et al., 2026):
- ~28.6% lower median wall-clock time with AGENTS.md present
- ~16.6% lower median output token consumption
- Key mechanism: upfront repo structure/conventions reduce exploratory navigation and re-planning loops

## User Focus (optional)

$ARGUMENTS

## Context Discovery (keep small)

Repo root:
!`git rev-parse --show-toplevel 2>/dev/null || pwd`

Git remote (used for enterprise repo detection):
!`git remote get-url origin 2>/dev/null || echo "no remote"`

Candidate build/config files (if present):
!`ls -1 package.json pnpm-lock.yaml yarn.lock bun.lockb pyproject.toml poetry.lock requirements.txt setup.cfg setup.py go.mod Cargo.toml Makefile Justfile pom.xml build.gradle build.gradle.kts composer.json Gemfile .tool-versions .nvmrc .ruby-version .python-version nx.json turbo.json lerna.json rush.json pnpm-workspace.yaml 2>/dev/null | head -25`

Existing CLAUDE.md or AGENTS.md (if any):
!`head -50 CLAUDE.md 2>/dev/null || head -50 AGENTS.md 2>/dev/null || echo "No existing CLAUDE.md or AGENTS.md"`

## Hard Constraints (token/time hygiene)

- Do NOT paste large lockfiles or massive file trees into the chat.
- Prefer reading a few "source of truth" files over scanning the entire repo.
- Do NOT invent commands. Only document commands you can confirm exist (e.g., from package scripts, Makefile targets, tooling configs) or clearly label as "if applicable".
- Keep the file short enough to be read quickly (aim: 80-180 lines; no giant paragraphs).

## Task

1. Locate the repository root (use the value above) and target `CLAUDE.md` at that root.
2. If `CLAUDE.md` or `AGENTS.md` already exists, UPDATE it (preserve project-specific details; remove duplicates; keep headings stable).
3. Build the document around the highest-impact categories shown to matter in practice:
   - **Project description** (what this repo is, what it's for)
   - **Architecture + project structure** (where to look; key directories; entrypoints)
   - **Conventions + best practices** (style, patterns, do/don't)
   - **Workflow commands** (setup/build/test/lint/format) because they prevent wasted cycles
4. If this is an **enterprise/internal repo** (see Enterprise-Specific Section below), add the enterprise integration sections.

## Required Output Format (CLAUDE.md template)

Use this structure. Keep tight, bullet-first:

```markdown
# CLAUDE.md

## Project Overview
<!-- 3-6 lines; no marketing; what this repo is and does -->

## Repo Map
<!-- Key directories/files; 6-12 bullets max; include entrypoints -->
- `src/` - ...
- `tests/` - ...

## Setup
<!-- Exact commands; include version managers if present; note working directory expectations -->
- Prerequisites: ...
- Install: `...`

## Common Commands
<!-- Only verified commands; prefer: install, build, test, lint, typecheck, format -->
<!-- Add "quick" vs "full" if the repo has both -->
| Command | Purpose |
|---------|---------|
| `...`   | ...     |

## Coding Conventions
<!-- Formatters/linters; naming; error handling; patterns to follow/avoid; 6-12 bullets -->
- ...

## Change Workflow
<!-- Small checklist: make change -> run checks -> update tests -> keep diffs small -->
1. Make your change
2. Run `...` to verify
3. Update/add tests
4. Keep diffs small and focused
5. Do NOT commit secrets or credentials

## Gotchas
<!-- Env vars, codegen, migrations, CI quirks; only if real; 3-8 bullets -->
- ...

## When You're Stuck
<!-- Cost-control + alignment rules -->
- Ask 1 targeted question instead of guessing
- If commands fail due to environment/tooling, report the exact error and STOP rather than looping
- Prefer the smallest reproducible check that validates the change
- When uncertain about architectural decisions, ask before implementing
```

## Monorepo Detection and Rule

**Detection signals** -- if any of these files exist at the repo root, treat as a monorepo:
- `nx.json` (Nx)
- `turbo.json` (Turborepo)
- `lerna.json` (Lerna)
- `rush.json` (Rush)
- `pnpm-workspace.yaml` (pnpm workspaces)
- `workspaces` field in `package.json`

When detected as a monorepo:
- Keep root `CLAUDE.md` as the "global contract".
- List workspace/package locations and how to navigate them.
- Mention where per-package instructions live (e.g., `packages/*/CLAUDE.md`).
- Document the workspace-aware commands (e.g., `nx run`, `turbo run`, `pnpm --filter`).
- Do NOT create many nested `CLAUDE.md` files unless the user focus ($ARGUMENTS) explicitly asks for "split/nested".

## Enterprise-Specific Section (Internal/Private Repos Only)

**Detection**: The git remote URL points to a private enterprise Sourcegraph instance or internal Git host (not github.com/gitlab.com/bitbucket.org).

When an enterprise repo is detected, append these sections to the CLAUDE.md template after "Gotchas" and before "When You're Stuck":

```markdown
## Service Integration (Enterprise)
<!-- Populate by inspecting the repo; leave placeholder if not discoverable -->

### IDL Contracts
- IDL repo: search Sourcegraph for this service's namespace in the organization's contract/IDL repository
- Local generated path: `src/main/scala/.../generated/` or similar
- Regeneration command: `...`

### Message Topics
<!-- List topics this service produces to or consumes from (e.g., Kafka, Pub/Sub) -->
| Topic | Direction | Schema |
|-------|-----------|--------|
| `...` | produce/consume | `...` |

### Service Dependencies
<!-- Upstream and downstream services; discover via IDL imports or Sourcegraph -->
- Upstream: ...
- Downstream: ...

### Deployment Pipeline
<!-- Deployment system (e.g., ArgoCD, Harness, etc.); include pipeline name if discoverable -->
- Pipeline: ArgoCD / other
- Environments: dev -> staging -> production
- Config repo: infrastructure-bootstrap repo (if applicable)
```

Populate these sections using:
1. Inspect the repo's build files and source tree for IDL/messaging references.
2. Use Sourcegraph (`src search`) to find cross-repo references to this service.
3. Mark any section you cannot verify with `<!-- NEEDS HUMAN REVIEW -->`.

## Verification Steps Before Finishing

1. Ensure every command you list is discoverable from repo config (package scripts, Makefile/Justfile targets, documented tool config) or clearly scoped ("if using X...").
2. Ensure the file is short enough to be read quickly (80-180 lines target; enterprise repos may reach 220).
3. Ensure it's internally consistent (one way to run tests, one formatter path, etc.).
4. If updating an existing file, preserve any project-specific details that are still accurate.
5. **Run the command validation check** (see below).

## Post-Generation Validation

After writing `CLAUDE.md`, verify that documented commands actually exist. Run:

```bash
# Validate package.json scripts (if present)
if [ -f package.json ]; then
  echo "=== package.json scripts ==="
  node -e "const p=require('./package.json'); console.log(Object.keys(p.scripts||{}).join('\n'))"
fi

# Validate Makefile targets (if present)
if [ -f Makefile ]; then
  echo "=== Makefile targets ==="
  grep -E '^[a-zA-Z_-]+:' Makefile | sed 's/:.*//'
fi

# Validate Justfile recipes (if present)
if [ -f Justfile ]; then
  echo "=== Justfile recipes ==="
  just --list 2>/dev/null || grep -E '^[a-zA-Z_-]+:' Justfile | sed 's/:.*//'
fi
```

Cross-check the output against every command in the "Common Commands" table. Flag any command in `CLAUDE.md` that does not appear in the script/target list and either remove it or mark it with `<!-- UNVERIFIED -->`.

## Deliverables

1. Create or update `CLAUDE.md` at the repo root.
2. Run the post-generation validation and fix any mismatches.
3. Reply with a brief summary:
   - New file created vs. existing file updated
   - Which sections were added/modified
   - Any sections that need human review (e.g., unverified commands, enterprise sections with placeholders)
