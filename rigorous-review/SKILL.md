---
name: rigorous-review
description: >
  Rigorous, evidence-backed code review for high-stakes changes. Trigger on:
  rigorous review, thorough review, deep review, review this PR properly,
  review before merge, high-stakes review, "is this actually safe to merge",
  regulated or compliance code review, batch-review these PRs. Every finding
  carries quoted evidence, a concrete failure scenario, and must survive an
  adversarial refutation pass; every review states what was checked and found
  clean. Use when a wrong call is expensive and a false finding costs
  credibility. Do not use for a quick pass over a small diff, for generating
  commit messages, for CI failure triage, or for reviewing your own
  work-in-progress before it is ready.
license: MIT
compatibility: "Requires git; wt (worktrunk) for review worktrees; ast-grep and a semantic code-intelligence MCP server (serena) for structural search; a memory backend (serena memories, openmemory) for reviewer preferences; allium for specification-backed intent; and the project's own test/lint/typecheck tooling. Optional: gh (Phase 7 publish), hunk plus its bundled hunk-review skill (inline placement in a live diff review)."
metadata:
  audience: developers
  workflow: code-review
  tags: "review, pull-request, quality, evidence, functional-programming"
  tools: "git, wt, ast-grep, serena, openmemory, allium, gh, hunk"
---

# Rigorous Review

Review changes the way a defect costs real money: run the project's own gates before reading a line, quote the evidence for every claim, try to disprove your own findings, and say what you checked and found clean.

A false finding costs more than a missed one. Optimise for precision.

Work the phases in order. Never skip or reorder — each depends on the one before it.

---

## Phase 0 — Load the reviewer's standard

Know what you are reviewing against before you look at anything.

1. **Read the baseline.** `references/pillars.md` — the seven pillars and the standing preferences. The floor is a strong functional-programming bias: immutability, pure functions, referential transparency, declarative over imperative, strict typing, no speculative abstraction. That floor holds whether or not memory has anything to say.
2. **Query memory for stated review preferences** — serena memories first, then openmemory, then any local memory file.
3. **Gate what you adopt.** Memory returns whatever is nearest, not whatever is relevant: a query for review preferences will surface unrelated operational facts with confident-looking scores, and low or negative relevance scores are the norm rather than a signal of subtlety. Adopt a memory only if it *states a preference about reviewing or about code style*. Discard the rest, however high it ranks. Never infer a preference from an operational fact, and never invent one.

Precedence, highest first: **the project's own documented standards** (Phase 3) → **the reviewer's stated preferences** → **the baseline**. A repo that has chosen a different idiom wins inside that repo; say so rather than relitigating it in a finding.

If memory is unavailable, proceed on the baseline and say that you did.

---

## Phase 1 — Scope the work

Establish exactly what is under review and stop guessing about identity.

1. **Target** — a PR number or URL, a branch, a commit range, or the working tree. Ask if ambiguous; do not assume the current diff.
2. **Isolate the change in its own worktree before touching anything** — preflight installs and codegen must never churn files the user is editing. `wt` ([worktrunk](https://worktrunk.dev)) resolves a PR in one step:
   ```bash
   wt switch pr:<number> --no-cd    # GitHub; mr:<number> GitLab; or a branch name
   wt list --format json            # recover the worktree path
   ```
   `--no-cd` because a shell's `cd` does not survive between tool calls. Take the path from `wt list` and target every later command at it explicitly — `git -C <path>`.
3. **Refresh the base ref before computing anything.** A stale local base silently inflates a diff — one change in the source batch read as +767 lines when the true delta was +140.
   ```bash
   git -C <worktree> fetch origin --prune
   git -C <worktree> diff --stat origin/<base>...<head>
   ```
   Report the true changed-line count; every later scope judgement rests on it.
4. **Resolve the acting identity from the forge, not from git config.** `user.email` locally is frequently not the account that reviews. Filtering "PRs I have not reviewed" on the wrong identity marks everything unreviewed:
   ```bash
   gh api user --jq .login
   ```
5. **Filter a batch on objective criteria only** — open, not draft, no blocking label, within the stated window, not already reviewed by the identity from step 4. Never on how interesting a change looks. One worktree per PR, so a failed install cannot contaminate the next review.

Completion: you can state the target, its worktree path, its base, the true changed-line count, and the acting identity.

---

## Phase 2 — Preflight (before reading any code)

Run the project's own verification gates first. This is the highest-yield phase and the one most reviewers skip — in the source batch it caught the single most important defect, a typecheck failure, before any human reading happened.

**Discover the commands. Never assume them.** `npm run preflight` is not a universal command, and neither is `npm`. Probe the task runners, then the language manifests, then CI — a Rust or Go repo often has only a manifest and a workflow, and probing for `package.json` alone reports "no gates" for a project with a full suite. Probes, the CI-template trap, and per-ecosystem fallbacks: `references/preflight.md`.

Then:

1. Run each discovered gate **inside the Phase 1 worktree**, in the project's own order — install, codegen, typecheck, lint, unit, integration, build.
2. **Log every step's exit code in a table**, including the ones that passed. Passing gates are non-findings you have earned.
3. **A failing gate is the finding.** Report it with the command and its output, and continue the review — do not stop, the author needs the rest too.
4. **Read the churn before discarding it.** Install and codegen steps rewrite files. Check what moved:
   ```bash
   git -C <worktree> status --porcelain
   ```
   A lockfile or generated file that changes when you run the project's own install or codegen is a finding: the committed artifact is out of sync with its source. Do not silently throw it away.
5. **Tear the worktree down when the review is reported**, not before — the findings cite it:
   ```bash
   wt remove <branch> --foreground
   ```
   `wt remove` refuses a dirty worktree; that refusal is the step-4 signal arriving late, so inspect before reaching for `-f`. Use `--force` only once you have accounted for the churn, and `--reap` if a gate left a dev server or watcher running. Keep the worktree if the user asks to inspect it — say where it is.

The user's own checkout is never touched at any point. That is the guarantee the worktree buys, and it is worth stating in the report.

If no gates are discoverable, say so plainly and mark the review as unverified-by-tooling. Do not invent a command.

---

## Phase 3 — Gather intent

You cannot judge whether code is correct until you know what it was meant to do.

Read, in this order: the PR description; linked tickets and their **acceptance criteria**; commit messages; prior review threads — and specifically **which earlier concerns are still unaddressed at head**; and the repo's own standards (`CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `docs/`). Project standards outrank your preferences; cite the file when you invoke one.

**Where the repo carries `.allium` specifications, they outrank the PR description.** A description is prose and can be wrong; the spec is the checked statement of intended behaviour. Run `allium check` to confirm the specs are sound, `allium model` for the domain vocabulary, and `allium plan` to derive the change's test obligations — an untested obligation is a testability finding with an authoritative source rather than an opinion. For spec-versus-code drift use the `weed` skill, and report which side moved rather than assuming it was the code.

**State the premise the change rests on, then check it is still true.** One change in the source batch was blocked on an upstream dependency described as missing that had in fact landed nine days earlier — the repo had simply pinned an older tag. A stale premise invalidates the change and every review of it.

Completion: you can state the intended behaviour in one sentence and list the acceptance criteria it must satisfy.

---

## Phase 4 — Analyse

Work all seven pillars — correctness, maintainability, readability, efficiency, security, edge cases and error handling, testability — against the standard from Phase 0. Full checklist: `references/pillars.md`.

**Search structurally, not textually.** Grep answers "where does this string appear"; review needs "what does this change reach", and text search answers that badly — it misses aliased imports, re-exports, and interface implementations. Use, in this order: **`ast-grep`** for structural patterns, **serena** for symbol-level questions the language server can answer, and plain text search only for things that genuinely are text. Never `sg` — it is deprecated.

Three searches earn their cost on every review:

- **Blast radius** — for each changed symbol, find its references and, for a changed interface, its implementations. Did every dependent get updated?
- **Definitions** — jump to the definition of anything you intend to claim about. Reasoning from call sites is where false findings come from.
- **Preference sweeps** — pattern-match the changed files for the things this codebase does not do: caller-owned mutation, loosened types, swallowed errors, duplicated logic.

Scope sweeps to the changed files and their dependents; repo-wide hits are pre-existing, not findings. Queries, traps, and the language-server caveats: `references/semantic-search.md`.

Check each acceptance criterion from Phase 3 against the code that implements it. A criterion no code satisfies is a finding regardless of whether the gates passed.

**Green gates are not evidence of safety.** Ask whether a test exercises the changed path *for the right reason*. Two recurring cases: the test mocks the exact layer the change touched, and the build strips types instead of checking them.

---

## Phase 5 — Verify (load-bearing — never skip)

Every candidate finding is a hypothesis, and most hypotheses are wrong. Three rules; mechanics and the false-positive catalogue in `references/verification.md`.

1. **Quote or drop.** Every claim quotes code you actually opened, at the reviewed revision. No quote, no finding.
2. **Refute, do not confirm.** Ask what would have to be true for the code to be *correct*, then go looking for it in earnest — an upstream guard, a handling caller, a passing test, actual library behaviour at the resolved version. Accept the refutation when it lands. Of four suspected defects investigated this way in the source batch, three were refuted; all three would have shipped as false findings.
3. **Prove behaviour empirically where the unit can be driven.** Take the function as shipped — do not retype it — drive it with fixtures from the real domain, and report the input → output table rather than your reading of it. Where you cannot execute, mark the finding `Plausible`.

Run every surviving candidate against the false-positive catalogue. Then drop anything whose consequence you cannot state in a sentence.

**Persist nothing until it has passed this phase** — no memory writes, no ticket comments, no handoff notes. A plausible-but-wrong inference written down early gets read back later as fact.

---

## Phase 6 — Report

Eight required fields per finding, ordered header → claim → evidence → failure scenario → fix → confidence. Schema and worked example: `references/finding-schema.md`.

Register: **state the bug, show the fix, stop.** No compliments before or after. No nits. Every finding says the concern *and why it matters*.

Order findings by severity, and severity by consequence — silent wrong answers outrank loud failures.

**End every review with the non-findings block, including reviews with zero findings.** Name each pillar you checked and how you know it is clean. Without it the author cannot tell "checked" from "skipped", and must re-review the change themselves — which is the entire cost the review existed to remove. If a pillar could not be checked, say that and say why.

If the runtime provides a structured findings tool, emit through it *instead of* prose, not in addition. Field mapping is in `references/finding-schema.md`.

### Inline placement in a live diff review (optional)

When a Hunk session is live on this change, place the anchorable findings beside the code too — an *additional* surface, never a replacement. Two rules decide whether it helps:

- **Partition before you submit.** Comments anchor to a file and line inside the loaded review, and the batch is validated as a whole — one finding aimed outside the review rejects every other with it. Read the session's file and hunk structure first.
- **Never reload the session to make a finding fit.** That swaps what the user is reading. Ask.

The preflight table, the non-findings block, whole-change findings, and findings whose evidence sits outside the diff never anchor — they go in the report regardless. Detection, degradation, schema mapping: `references/hunk.md`.

---

## Phase 7 — Publish (opt-in)

**Only on explicit request.** Never post as a side effect of being asked to review.

Show the user the exact body, every inline comment with its file and line, and the review event. Get approval for that content — approval to "post it" is not approval for comments they have not read. Default to a `COMMENT` event; never choose `APPROVE` or `REQUEST_CHANGES` on the user's behalf.

After posting, **verify server-side**. The transcript is not evidence: a body can land while inline comments are silently rejected for out-of-range lines. Read back the review state and the inline-comment count, compare against what you intended, and report the actual numbers. Commands, permalink format, and multi-forge notes: `references/publishing.md`.

---

## Fan-out mode (opt-in)

The default path is a single reviewer and uses no agent tooling. Only when the user explicitly asks for a batch or a multi-lens review, fan out one reviewer per change or per pillar.

Two rules if you do: give each reviewer a **neutral** question, never a suspected defect stated as fact — priming produces confirmation; and instruct each to treat a refutation as a successful result rather than a failure to find something. Merge findings only after each has passed Phase 5 independently.

---

## Anti-patterns

- Reaching for text search before `ast-grep` and the semantic server, and missing an aliased or re-exported call site
- Trusting an empty `ast-grep` sweep, or any sweep over shell sources, as proof of absence
- Adopting an unrelated memory as a review preference because it ranked highly
- Priming a reviewer with a suspected defect — biases toward confirming it
- Running preflight in the user's checkout instead of a dedicated review worktree
- Relying on `cd` persisting between commands instead of passing the worktree path explicitly
- Discarding preflight churn without reading it, or forcing a worktree removal to get past it
- Reviewing against a stale base ref, inflating the diff
- Treating green CI as proof the changed path is safe
- Hardcoding one project's verification command instead of discovering it
- Reporting a finding without quoted evidence, or without a stated consequence
- Reviewing lines the change did not touch
- Posting without reading the result back from the API
- Reloading or navigating a live diff session the user is reading, to make a finding fit
- Treating inline notes as a substitute for the report, or submitting a comment batch without checking each finding anchors inside the loaded review
- Leaving lockfile or worktree churn behind after preflight
- Persisting an unverified conclusion to memory or notes
- Padding a review with nits, or opening it with a compliment
