---
name: smart-init
description: "Trigger on: init, CLAUDE.md, AGENTS.md, setup repo, onboard, generate docs, project documentation for agents, bootstrap, new project setup. Evidence-guided AGENTS.md generator that makes AI coding agent runs ~28% faster and ~16% cheaper by eliminating exploratory navigation. Always produces a tool-agnostic root AGENTS.md plus a thin CLAUDE.md that imports it via `@AGENTS.md`, per Anthropic's documented memory-import convention."
license: MIT
compatibility: opencode
metadata:
  audience: developers
---

You are generating or updating this repository's root `AGENTS.md` — the canonical, tool-agnostic
agent context file — plus a root `CLAUDE.md` that imports it. This makes future coding-agent runs
faster and cheaper (reduce exploratory navigation and repeated inference). Optimize for: concise,
accurate, actionable, and easy to maintain.

## Research Background

This command implements findings from "On the Impact of AGENTS.md Files on the Efficiency of AI Coding Agents" (Lulla et al., 2026):
- ~28.6% lower median wall-clock time with AGENTS.md present
- ~16.6% lower median output token consumption
- Key mechanism: upfront repo structure/conventions reduce exploratory navigation and re-planning loops

## Why Two Files

`AGENTS.md` is the tool-agnostic contract, shared by every AI coding agent (Claude Code, Cursor,
Copilot, Windsurf, Devin, Cline, OpenCode). `CLAUDE.md` is Claude Code's own memory file — Claude
Code reads `CLAUDE.md` natively and does **not** fall back to `AGENTS.md` on its own. Anthropic's
documented bridge (`code.claude.com/docs/en/memory`) is a literal import line:

```markdown
@AGENTS.md

## Claude Code
Use plan mode for changes under `src/billing/`.
```

The `@AGENTS.md` line must be bare text on its own line, outside any code fence — import parsing
skips fenced code blocks and inline code spans, so a markdown link like `[@AGENTS.md](AGENTS.md)`
or a prose mention does not trigger the import. Never substitute a prose link for the literal
import line.

Never propose a plain `ln -s AGENTS.md CLAUDE.md` symlink instead of the import — a symlinked
`CLAUDE.md` cannot also carry a `## Claude Code` section, and this skill always adds one.

## User Focus (optional)

$ARGUMENTS

## Context Discovery (keep small)

Repo root:
!`git rev-parse --show-toplevel 2>/dev/null || pwd`

Git remote (used for enterprise repo detection):
!`git remote get-url origin 2>/dev/null || echo "no remote"`

Candidate build/config files (if present):
!`ls -1 package.json pnpm-lock.yaml yarn.lock bun.lockb pyproject.toml poetry.lock requirements.txt setup.cfg setup.py go.mod Cargo.toml Makefile Justfile pom.xml build.gradle build.gradle.kts composer.json Gemfile .tool-versions .nvmrc .ruby-version .python-version nx.json turbo.json lerna.json rush.json pnpm-workspace.yaml 2>/dev/null | head -25`

Existing agent context files (any of these may already carry the content AGENTS.md should own):
!`found=0; for f in AGENTS.md CLAUDE.md .cursorrules .cursor/rules .github/copilot-instructions.md .windsurfrules .devin/guidelines.md .clinerules; do if [ -e "$f" ]; then found=1; echo "--- $f ---"; head -50 "$f"; fi; done; [ "$found" -eq 0 ] && echo "No existing agent context files found"; true`

## Hard Constraints (token/time hygiene)

- Do NOT paste large lockfiles or massive file trees into the chat.
- Prefer reading a few "source of truth" files over scanning the entire repo.
- Do NOT invent commands. Only document commands you can confirm exist (e.g., from package scripts, Makefile targets, tooling configs) or clearly label as "if applicable".
- Keep `AGENTS.md` short enough to be read quickly (aim: 80-180 lines; no giant paragraphs).
- Keep `CLAUDE.md` genuinely thin: the import line, a `## Claude Code` heading, and only
  Claude-specific content (see "Claude Code Section" below). Never re-derive or duplicate
  `AGENTS.md`'s full content there.

## Task

1. Locate the repository root (use the value above) and target `AGENTS.md` at that root as the
   canonical file.
2. **Detect prior state** from the Context Discovery output above:
   - **Case A — `AGENTS.md` exists, `CLAUDE.md` is already a thin import**: update `AGENTS.md`
     in place (preserve project-specific details; remove duplicates; keep headings stable). Leave
     `CLAUDE.md`'s import line untouched; only touch its `## Claude Code` section if needed.
   - **Case B — `AGENTS.md` exists, `CLAUDE.md` is missing or is a full/duplicate document**:
     rewrite `CLAUDE.md` down to the import + `## Claude Code` section (see template below). Do
     not ask for extra confirmation beyond the normal edit approval — this is expected skill
     behavior, not a special case.
   - **Case C — no `AGENTS.md`, but `CLAUDE.md` (or another tool's rule file: `.cursorrules`,
     `.github/copilot-instructions.md`, `.windsurfrules`, `.devin/guidelines.md`, `.clinerules`)
     already holds substantive tool-agnostic content**: migrate that content into a new
     `AGENTS.md` verbatim where still accurate, then rewrite `CLAUDE.md` to the thin import
     template. Do this as one pass; the standard edit-approval prompt is the only gate.
   - **Case D — nothing exists**: generate both files from scratch.
3. Build `AGENTS.md` around the highest-impact categories shown to matter in practice:
   - **Project description** (what this repo is, what it's for)
   - **Architecture + project structure** (where to look; key directories; entrypoints)
   - **Conventions + best practices** (style, patterns, do/don't)
   - **Workflow commands** (setup/build/test/lint/format) because they prevent wasted cycles
4. If this is an **enterprise/internal repo** (see Enterprise-Specific Section below), add the enterprise integration sections to `AGENTS.md`.

## Required Output Format (AGENTS.md template)

Use this structure. Keep tight, bullet-first:

```markdown
# AGENTS.md

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

## Required Output Format (CLAUDE.md template)

```markdown
@AGENTS.md

## Claude Code
<!-- Claude Code-specific mechanics only: MCP/tool preferences, plan-mode triggers, -->
<!-- Claude Code settings quirks. Do NOT restate AGENTS.md content here except the -->
<!-- reinforced high-stakes rules below. -->
- <!-- e.g. "Prefer the `metals-mcp` compile-file/get-usages tools over grep for Scala symbols" -->

<!-- Reinforced from AGENTS.md (duplication here is deliberate: CLAUDE.md is the file Claude -->
<!-- Code actually loads, so the highest-stakes rules must not depend on the import firing) -->
- Never run destructive commands (force-push, hard reset, branch deletion, production
  deploys) without explicit human confirmation.
- Do NOT commit secrets, credentials, or PII.
<!-- Add other AGENTS.md rules here ONLY if they are genuinely high-stakes (data loss, -->
<!-- security, compliance) — do not reinforce routine style/convention rules. -->
```

Only include a rule in the reinforced list if it is genuinely high-stakes (irreversible actions,
credentials/PII/secrets, compliance). Routine conventions (formatting, naming, import order)
belong only in `AGENTS.md` — reinforcing those in `CLAUDE.md` defeats the point of the split.

## Monorepo Detection and Rule

**Detection signals** -- if any of these files exist at the repo root, treat as a monorepo:
- `nx.json` (Nx)
- `turbo.json` (Turborepo)
- `lerna.json` (Lerna)
- `rush.json` (Rush)
- `pnpm-workspace.yaml` (pnpm workspaces)
- `workspaces` field in `package.json`

When detected as a monorepo:
- Keep root `AGENTS.md` (with root `CLAUDE.md` importing it) as the "global contract".
- List workspace/package locations and how to navigate them.
- Mention where per-package instructions live (e.g., `packages/*/AGENTS.md`), if any already exist.
- Document the workspace-aware commands (e.g., `nx run`, `turbo run`, `pnpm --filter`).
- Do NOT create nested `AGENTS.md`/`CLAUDE.md` pairs for individual packages unless the user
  focus ($ARGUMENTS) explicitly asks for "split/nested" — this restraint applies regardless of
  file naming; it is an anti-sprawl rule, not specific to the old single-file scheme.

## Enterprise-Specific Section (Internal/Private Repos Only)

**Detection**: The git remote URL points to a private enterprise Sourcegraph instance or internal Git host (not github.com/gitlab.com/bitbucket.org).

When an enterprise repo is detected, append these sections to the `AGENTS.md` template after "Gotchas" and before "When You're Stuck":

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
2. Ensure `AGENTS.md` is short enough to be read quickly (80-180 lines target; enterprise repos may reach 220).
3. Ensure it's internally consistent (one way to run tests, one formatter path, etc.).
4. If updating an existing file, preserve any project-specific details that are still accurate.
5. Ensure `CLAUDE.md` contains the bare `@AGENTS.md` import line outside any code fence, a
   `## Claude Code` heading, and nothing that duplicates routine `AGENTS.md` content.
6. **Run the command validation check** (see below).

## Post-Generation Validation

After writing `AGENTS.md` and `CLAUDE.md`, verify that documented commands actually exist. Run:

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

Cross-check the output against every command in the "Common Commands" table. Flag any command in `AGENTS.md` that does not appear in the script/target list and either remove it or mark it with `<!-- UNVERIFIED -->`.

## Deliverables

1. Create or update `AGENTS.md` at the repo root.
2. Create or update `CLAUDE.md` at the repo root as a thin `@AGENTS.md` import with a
   `## Claude Code` section.
3. Run the post-generation validation and fix any mismatches.
4. Reply with a brief summary:
   - New files created vs. existing files updated vs. migrated from a prior single-file/other-tool format
   - Which sections were added/modified in `AGENTS.md`
   - What was placed in `CLAUDE.md`'s `## Claude Code` section and why (Claude-specific vs. reinforced high-stakes rule)
   - Any sections that need human review (e.g., unverified commands, enterprise sections with placeholders)
