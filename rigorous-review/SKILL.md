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
compatibility: "Requires git; gh with REST and GraphQL access to the forge (Phase 3 prior-findings ledger — GraphQL is required for thread resolved-state, and an enterprise host needs a literal GH_HOST prefix on every call); wt (worktrunk) for review worktrees; ast-grep and a semantic code-intelligence MCP server (serena) for structural search; a memory backend (serena memories, openmemory) for reviewer preferences; allium for specification-backed intent; and the project's own test/lint/typecheck tooling. Optional: hunk plus its bundled hunk-review skill (inline placement in a live diff review)."
metadata:
  audience: developers
  workflow: code-review
  tags: "review, pull-request, quality, evidence, functional-programming"
  tools: "git, wt, ast-grep, serena, openmemory, allium, gh, hunk"
---

# Rigorous Review

Review changes the way a defect costs real money: run the project's own gates before reading a line, quote the evidence for every claim, try to disprove your own findings, and say what you checked and found clean. A false finding costs more than a missed one. Optimise for precision. Work the phases in order.

Copy this checklist into your working notes and check phases off as their completion criteria are met — every skipped phase in this skill's failure history was skipped silently, never decided against:

```
Review Progress:
- [ ] 0 Standard   — baseline read; memory queried and gated
- [ ] 1 Scope      — worktree resolved (dedicated, or the one exception verified);
                     reviewed SHA == forge head; true changed-line count known
- [ ] 2 Preflight  — gates discovered and run in the worktree; exit codes tabled; churn read
- [ ] 3 Intent     — acceptance criteria + repo-rule assertions extracted; ledger built;
                     open-thread count stated with confirmed/refuted/unverifiable split
- [ ] 4 Analyse    — every changed file read whole at the pinned SHA; five sweeps run,
                     tool named per sweep
- [ ] 5 Verify     — every finding quoted, refutation attempted, probed where drivable
- [ ] 6 Report     — findings by consequence; non-findings block; verdict preconditions met
- [ ] 7 Publish    — only on explicit request, verified server-side after posting
```

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
2. **Every review runs in a dedicated review worktree, with exactly one exception.** Preflight installs and codegen must never churn files the user is editing, and every file you read must be at the revision under review — a separate worktree buys both. The one exception: the directory the review was invoked from is already a checkout of the PR's branch, **at the PR's head, with a clean tree**. Check all three before claiming it:
   ```bash
   git -C <invocation-dir> branch --show-current      # must equal the PR's headRefName
   git -C <invocation-dir> rev-parse HEAD             # must equal headRefOid from the forge
   git -C <invocation-dir> status --porcelain         # must be empty
   ```
   Branch name alone is not enough — a checkout on the right branch but behind the head, or carrying uncommitted edits, reviews a revision that is not the PR. If any check fails, fall through to a separate worktree; never advance or clean the user's checkout to make it qualify.

   **Creating the review worktree.** First resolve a local repo for the PR: the invocation directory if it is a clone of the PR's repo, else a known local clone, else a fresh clone into scratch space. Then:
   - Where `wt` ([worktrunk](https://worktrunk.dev)) manages that repo **and no existing worktree already holds the PR's branch**, it resolves a PR in one step:
     ```bash
     wt switch pr:<number> --no-cd    # GitHub; mr:<number> GitLab; or a branch name
     wt list --format json            # recover the worktree path
     ```
     `--no-cd` because a shell's `cd` does not survive between tool calls.
   - **If any worktree already holds the PR's branch, do not commandeer it — it is someone's working copy.** `wt switch` and `git worktree add <branch>` both route to or collide with that checkout, which may be stale and may carry uncommitted work. In the run that produced this rule, the author's `FRD-8171` worktree sat one commit behind the forge head at review time. Create a detached review worktree pinned at the exact head instead:
     ```bash
     git -C <repo> fetch origin <base> 'refs/pull/<number>/head' --prune   # GitHub; GitLab: refs/merge-requests/<number>/head
     git -C <repo> worktree add --detach <repo>/../<name>.review-pr<number> <headRefOid>
     ```
     Detached-at-SHA also removes a whole class of stale-head errors: the worktree cannot silently drift, and step 3's head check passes by construction.

   **Review the source in that worktree and nowhere else.** Every later command — diffs, file reads, structural sweeps, preflight gates — targets the worktree path explicitly (`git -C <path>`, absolute paths for readers and search tools). A file read from the invocation directory, an editor buffer, or another checkout is a different revision wearing the same name.
3. **Confirm the worktree is at the revision under review.** A supplied or reused worktree may sit behind the PR — the base can be fresh while the head is stale, and nothing in the diff announces it. Resolve the forge's head and compare:
   ```bash
   gh pr view <number> --json headRefOid --jq .headRefOid
   git -C <worktree> rev-parse HEAD
   ```
   If they differ, stop and say so before computing any diff. Either advance the worktree, or review the forge head from object storage and materialise it for the search tools (see `references/semantic-search.md`). Report the commit you actually reviewed. In the test that produced this rule the supplied worktree was 21 commits and five review rounds behind; every core file had changed in the gap, and three findings would have described code that later commits already fixed.
4. **Refresh the base ref before computing anything, and pass `--no-ext-diff`.** A stale local base silently inflates a diff — one change in the source batch read as +767 lines when the true delta was +140.
   ```bash
   git -C <worktree> fetch origin --prune
   git -C <worktree> diff --no-ext-diff --stat origin/<base>...<head>
   ```
   `--no-ext-diff` is a flag on `diff`, so it goes **after** the subcommand — `git -C <path> --no-ext-diff diff` fails with `unknown option`. Pass it on every diff you read.

   It is needed because a user's global `diff.external` (difftastic, delta, and friends) replaces unified diff output with a side-by-side render that has **no `+`/`-` markers at all** — added lines become indistinguishable from context, and nothing announces the substitution. It is configured globally on many developer machines, so the failure follows you into every repo. A review built on that output is guessing which lines are new; that is the one input the whole review rests on. Report the true changed-line count.
5. **Resolve the acting identity from the forge, not from git config.** `user.email` locally is frequently not the account that reviews. Filtering "PRs I have not reviewed" on the wrong identity marks everything unreviewed:
   ```bash
   gh api user --jq .login
   ```
6. **Filter a batch on objective criteria only** — open, not draft, no blocking label, within the stated window, not already reviewed by the identity from step 5. Never on how interesting a change looks. One worktree per PR, so a failed install cannot contaminate the next review.

Completion: you can state the target, its worktree path, its base, **the commit you actually reviewed and whether it matches the PR head**, the true changed-line count, and the acting identity.

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

Read, in this order: the PR description; linked tickets and their **acceptance criteria**; commit messages; prior review threads (the ledger, step below); and the repo's own standards (`CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `docs/`). Project standards outrank your preferences; cite the file when you invoke one.

**Turn the repo's documented gotchas into checkable assertions.** A standards file is not only precedence for resolving conflicts you happen to notice — its gotchas, invariants, and "always/never" statements are findings the maintainers already wrote for you, pre-verified and citable. Reading them as background and moving on is how a change violates a rule the repo states in plain text.

For each rule you find, write down the assertion and check it against the diff:

| Doc says | Assertion | Checked how |
|---|---|---|
| "always wrap X in Y" | no changed call to X outside Y | structural sweep for X, inspect enclosing form |
| "never call A from B" | no new A call inside B | structural sweep scoped to B |
| "Z must run before W" | ordering holds on every changed path | read the changed path |

Sweep structurally, per `references/semantic-search.md` — these assertions are shape claims and text search cannot settle them. A violation is a finding whose authority is the repo's own document: cite file and line, the way an acceptance criterion is cited. Rules the change does not touch go in the non-findings block as checked.

Where the repo carries machine-checkable rules — `ast-grep` rule files, custom lint rules, CI policy checks — run them rather than re-deriving them by eye, and say which ran. A rule configured as non-blocking still reports; a warning the author did not see is still a finding.

**Where the repo carries `.allium` specifications, they outrank the PR description.** A description is prose and can be wrong; the spec is the checked statement of intended behaviour. Run `allium check` to confirm the specs are sound, `allium model` for the domain vocabulary, and `allium plan` to derive the change's test obligations — an untested obligation is a testability finding with an authoritative source rather than an opinion. For spec-versus-code drift use the `weed` skill, and report which side moved rather than assuming it was the code.

**State the premise the change rests on, then check it is still true.** One change in the source batch was blocked on an upstream dependency described as missing that had in fact landed nine days earlier — the repo had simply pinned an older tag. A stale premise invalidates the change and every review of it.

### The prior-findings ledger

On any change that has been reviewed before — by you, a colleague, or another agent — build a ledger before analysing. Long-lived branches accumulate rounds, and a fix that landed in round two can be undone in round four by a merge, a refactor, or a rename, with nothing in the diff announcing it.

**Fetch the threads before you read the diff. This is a command, not a reading habit.** Enumerate them; do not sample the ones the diff reminds you of. A review that states a merge position without this step is not a rigorous review — see the open-threads gate below.

**No single call returns the prior findings.** A PR stores review prose in three collections that do not overlap, and the one most reviewers reach for is the one most likely to be empty. `gh pr view --json reviews` returns only top-level summary bodies — it silently omits every inline comment, which is where findings actually live. On the PR behind the gate below, 30 of 44 review bodies were empty and **zero** findings appeared in them, while 27 sat in the inline comments. It succeeds, returns well-formed JSON, and shows nothing: a silent partial success, more dangerous than an error because a 404 makes you look again and a stub body does not.

Query all three — inline comments, review bodies, issue-level discussion — plus the GraphQL thread query that carries `isResolved`, which REST does not expose at all. `--paginate` every one; the default page of 30 dropped 57% of that PR's history with no signal. On an enterprise forge each call needs a literal `GH_HOST=<host>` prefix, or `gh api` returns **404, not an empty list**.

**Commands, the three-collection table, the pagination reconciliation, and the failure modes each source has: `references/ledger.md`. Read it before building the ledger.**

Three properties of the data shape how you must handle it:

- **Key the ledger on thread identity** — the root comment's `databaseId` — never on a line. An outdated thread reports `line: null`, so line-keyed merging drops exactly the threads that have survived the most rounds.
- **Two threads on the same line are usually two defects.** Co-location is not duplication; collapsing them hides a live defect behind a fix that looks complete.
- **`resolved=false, outdated=true` is the dangerous quadrant**, not a stale one: a finding the author replied "Done" to but never resolved, on code that has since moved. It is still open.


Then resolve each against **head**, not against the reply that closed it:

| Status | Meaning | Action |
|---|---|---|
| **Unaddressed** | never fixed | carry forward, note it has persisted N rounds |
| **Addressed** | fixed and still holds at head | non-findings block, so the author sees it was re-checked |
| **Regressed** | fixed, then undone | report — see below |
| **Over-corrected** | fixed as asked, and the fix introduced a new defect | report at regression severity; name the origin thread and quote what was requested, so the author does not revert into the original bug |
| **Refuted at head** | no longer holds because it was wrong, not because it was fixed | say so explicitly and show the evidence; otherwise the original reviewer re-raises it |
| **Superseded** | the code it described is gone | say so; do not carry it |

**A regression is worse than the original defect and is reported at higher severity.** Everyone believes it is fixed: the thread is resolved, the author has moved on, and the reviewer who confirmed the fix will not look again. Say explicitly that it was fixed and has come back, name the commit that fixed it and the one that undid it, and re-verify at head under the usual quote-or-drop rule.

The same reasoning carries an **over-correction** — thread resolved, author moved on, requesting reviewer believes it landed — so it takes the same elevated severity. Do not file one as a regression: nothing was undone, and filing it that way points the author at a revert that reintroduces the original bug. Name the earlier request that produced it, quote what was asked for, and say how the fix must be *narrowed* rather than reversed.

**Refutation belongs in the ledger too.** A prior finding that turns out to be wrong on the merits is a result worth recording, not a silence. Say so explicitly and show the evidence — otherwise the reviewer who raised it reads the omission as an oversight and raises it again next round.

An author's reply is not evidence. "Done", a resolved thread, and a commit message naming the fix are all claims about an earlier revision. Verify at head.

### The open-threads gate

**Another reviewer's unresolved finding is a blocking input to your verdict, not context you may skim.** Before stating any merge position — and *especially* before anything that reads as approval — every thread with `isResolved=false` must be accounted for, by name, with a status at head.

Account for each one in one of three ways. Silence is the one option that misleads, because the author cannot distinguish it from agreement:

| | What you must show |
|---|---|
| **Confirmed** | it reproduces at head — quote the evidence, carry it into your report at its own severity |
| **Refuted** | it does not hold at head — show why, per Phase 5 rule 2 |
| **Unverifiable** | you could not settle it — say so, and say what blocked you |

Then state the count explicitly: *"N threads open at head; C confirmed, R refuted, U unverifiable."* A review that cannot produce that line has not finished Phase 3.

**Unverifiable is an honest answer and it absorbs scale.** A long-running branch can carry dozens of unresolved-but-outdated threads written against code that has since been rewritten. Settling each one needs the original reviewer's intent, not just the diff, and "the code moved" is not the same as "the finding was answered" — so classify them as unverifiable in a batch and say why, rather than either inventing resolutions or letting the count stop you reviewing. Spend the individual effort on the threads still anchored to current lines; those are the ones the author can act on today.

Before setting the batch aside, read it once for **structural claims that outlive the code they were filed against** — an argument about irreversibility, ordering, or a durability guarantee often still holds after the function it described was rewritten, and it frequently sets the severity of what you found yourself.

The forge also carries a one-field summary of where review stands. It is not a substitute for the thread list, but disagreeing with it silently is a mistake worth catching early:

```bash
GH_HOST=<forge-host> gh api graphql -f query='
{ repository(owner:"<owner>", name:"<repo>") {
    pullRequest(number:<n>) { reviewDecision } } }' --jq '.data.repository.pullRequest.reviewDecision'
```

**Approving over an unresolved thread you have not addressed is the failure this gate exists to prevent.** Not because the other reviewer is right — they may well be wrong, and refuting them is a first-class outcome — but because an approval is read as a judgement on everything open at that commit. Approving without looking tells the author a finding was weighed when it was not, and it retires a thread that no one will reopen.

This rule exists because of a specific failure. On a 29-commit, 9-round PII-redaction PR, a review using this skill approved at head `<sha>` and retracted ten minutes later. At that commit **27 of 41 threads were `isResolved=false`** — seven of them still anchored to current lines, the rest unresolved and outdated — and the approval had engaged with none of them. All seven anchored findings then proved real on execution: SSNs and dates of birth leaking unredacted to an analytics topic, and ordinary audit text irreversibly corrupted at a sanitizer that never retains the original.

The analysis was never the weak point — the same skill confirmed four of them against the regex source within minutes of finally looking. It approved because nothing made it look first. One GraphQL query would have caught every one.

Two aggravating patterns to recognise in yourself, both present in that review:

- **The nit at the verdict.** The approval's one substantive remark was that the PR description was stale. When the most severe thing you have to say at approval time is a documentation nit, that is not a clean PR — it is an unread thread list.
- **Rounds as reassurance.** Nine rounds of fixes read as evidence of convergence. On a change of this shape they are the opposite: each round narrowed a regex and opened a new gap, which is why round nine still leaked. Prior review effort is not a substitute for checking head, and a long fix history is a reason to check harder.

Completion: you can state the intended behaviour in one sentence, list the acceptance criteria it must satisfy, name the repo-documented rules the change is subject to, give the status at head of every prior finding, and state the open-thread count with its confirmed/refuted/unverifiable split.

---

## Phase 4 — Analyse

Work all seven pillars — correctness, maintainability, readability, efficiency, security, edge cases and error handling, testability — against the standard from Phase 0. Full checklist: `references/pillars.md`.

**Read the whole source file before analysing it. The diff is a pointer to where to look, never the thing you review.** Open every changed file in full, at the exact revision under review, and read the code the changed lines sit inside — the enclosing function, its callers in that file, the constructor or factory the type flows through, the invariants declared at the top. A hunk shows you what moved; it cannot show you what the moved code now means.

This is not the same claim as the PR-level finding rule in `references/finding-schema.md`. That rule says an out-of-diff *line* may be reported when the change made it decisive. This says you cannot know whether it did without having read it. The rule presupposes the reading.

The cost of skipping it is not a missed nit. On the PR behind Phase 3's gate, the diff showed a scrubber being wired into a pipeline — routine, and it reads as an improvement. What made two of those findings **Critical rather than High** sat ~120 lines above the diff, untouched:

```scala
object AuditActionReason {
  def apply(value: String): AuditActionReason = new AuditActionReason(sanitizePII(value))
}
```

A private constructor and a single factory that sanitises on the way in and retains nothing. That one fact converts "this regex over-redacts" into "this irreversibly destroys audit records", and no amount of staring at the diff would surface it.

Three specific traps, all of which look like a clean review from inside the hunk:

- **Reviewing the wrong revision.** Pin the SHA explicitly and read the file at it — `git -C <worktree> show <sha>:<path>`, or fetch from object storage when you have no worktree (`references/semantic-search.md`). A file read from a branch name, from a stale worktree, or from your editor's buffer is a different file, and nothing in the text says so.
- **Reviewing the wrong file.** A generated, vendored, or re-exported symbol has a real definition elsewhere; the diff names the path it was edited at, not the path that defines behaviour.
- **Reading only the changed files.** The callee a change newly depends on is usually unchanged, so it appears in no diff — which is exactly why the inbound-blast-radius sweep below exists.

When a file is genuinely too large to read whole, say so and name what you read instead — the enclosing type, the call graph around the change. An unread region you do not declare reads to the author as a region you checked.

**Search structurally, not textually — this is a requirement, not a preference.** Grep answers "where does this string appear"; review needs "what does this change reach", and text search answers that badly — it misses aliased imports, re-exports, and interface implementations, and it cannot express a question about syntactic position or nesting at all. Use, in this order, descending only when the step above cannot express the query: **`ast-grep`** for structural patterns, **serena** for symbol-level questions the language server can answer, and plain text search only for things that genuinely are text. Invoke it as `ast-grep`, not `sg` — on some installations `sg` is a deprecated alias that warns instead of running. A language-specific skill's tool order wins for that language and is still structural-first.

Report which tool answered each sweep, and justify every fall-back to text search. It matters most where the sweep's value is proving *absence*: an empty grep result is not evidence, because grep's misses are invisible.

Five searches earn their cost on every review:

- **Outbound blast radius** — for each changed symbol, find its references and, for a changed interface, its implementations. Did every dependent get updated?
- **Inbound blast radius** — for each call the change adds, re-routes, or moves, open the **callee** and name the guarantee now being assumed: completion, durability, ordering, totality, atomicity. Does it provide it? The callee is usually unchanged, so no dependents sweep will surface it and it will not appear in the diff — these are PR-level findings and need the load-bearing clause.
- **Definitions** — jump to the definition of anything you intend to claim about, including **generated and vendored code**. Reasoning from call sites is where false findings come from, and a generated type's real variants are where an exhaustive-looking match turns out not to be.
- **Effect lifetime** — where the language has detachable effects or cancellation, sweep the changed paths for work that is started and abandoned, and for cancellation that reaches a side effect that must not be lost. Capability triage and the patterns: `references/pillars.md`.
- **Preference sweeps** — pattern-match the changed files for the things this codebase does not do: caller-owned mutation, loosened types, swallowed errors, duplicated logic. Include the assertions extracted from the repo's own standards in Phase 3.

Scope sweeps to the changed files, their dependents, and **the callees the change newly depends on**. Unrelated repo-wide hits are pre-existing, not findings. Queries, traps, and the language-server caveats: `references/semantic-search.md`.

Check each acceptance criterion from Phase 3 against the code that implements it. A criterion no code satisfies is a finding regardless of whether the gates passed.

**Distinguish mechanism present from mechanism effective.** Confirming a value is threaded to the right call proves the plumbing is connected, not that the water arrives. Ask both, and state which you verified: is the call made on the path that needs it, *and* does the work it schedules run to completion with its outcome reaching whoever depends on it? Stopping at the first is the specific way a correct-looking diff fails to do what it promised. Capability triage — which of detachable effects, cancellation, error absorption, delivery semantics, and ordering this language actually has — is in `references/pillars.md`.

**Green gates are not evidence of safety.** Ask whether a test exercises the changed path *for the right reason*. Three recurring cases: the test mocks the exact layer the change touched, the build strips types instead of checking them, and the test asserts the call happened rather than that its effect landed.

Completion: you can name every file you read in full and the revision you read it at, name any file you could not read whole and what you read instead, and say which tool answered each of the five sweeps.

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

### Stating a verdict

A verdict is a claim about the whole change, so it carries the whole review's evidence. This applies wherever the verdict appears — a posted `APPROVE`, or a sentence in chat saying the change looks safe to merge. Users act on the sentence exactly as they would on the button.

Before writing one, state these three lines. If you cannot, you do not have a verdict yet, and saying so is the honest output:

1. **Gates** — every preflight command and its exit code.
2. **Open threads** — the count from the Phase 3 gate, with its confirmed/refuted/unverifiable split, and each confirmed one named.
3. **Head** — the commit you reviewed, and that it matches the forge head now. A verdict on a superseded commit is worse than none; re-check at the moment you state it, since the author may have pushed while you were reading.

**Never volunteer approval.** Report findings and let the user decide. The strongest thing to offer unasked is "no findings survived verification at `<sha>`", which is a statement about your review rather than a judgement on the change — and it is only available when the open-thread count is zero or every open thread is accounted for.

Stating "looks good to merge" while another reviewer's finding sits unresolved and unexamined is the failure documented in Phase 3. If you are going to disagree with an open finding, disagree with it explicitly and show the refutation — never by omission.

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

**Agreement between reviewers is not evidence.** Never promote, upgrade, or retain a finding because several reviewers converged on it — panels of dozens of agents, adversarial ones included, have unanimously endorsed defects that did not exist. The only things that promote a finding are a quote from the reviewed revision, a failing gate, or an executed probe. A finding every reviewer raised and none could evidence is dropped exactly like a finding one reviewer raised and could not evidence.

---

## Anti-patterns

- Reaching for text search before `ast-grep` and the semantic server, and missing an aliased or re-exported call site
- Falling back to text search without saying so, or using it for a question about syntactic position or nesting that only a structural pattern can express
- Trusting an empty `ast-grep` sweep, or any sweep over shell sources, as proof of absence
- Checking only who depends on the change, never what the change now depends on
- Stopping at "the value is threaded through" without checking the effect it schedules actually completes
- Reading the repo's standards as background instead of extracting checkable assertions from them
- Treating a resolved thread, a "done" reply, or a fix commit as proof a prior finding still holds at head
- Reading prior review prose from `gh pr view --json reviews` alone, and taking a stub summary body as proof the review was empty
- Fetching review data without `--paginate`, and reading the first 30 of 69 comments as the whole history
- Letting a missing `GH_HOST` 404 stand in for "this PR has no prior comments"
- Keying a findings ledger on line numbers, so outdated threads reporting `line: null` drop out silently
- Stating a verdict — approving, or saying it looks safe to merge — while another reviewer's thread is unresolved and unexamined
- Treating many prior review rounds as evidence of convergence rather than as a reason to check head harder
- Offering a fix snippet precise enough to be pasted verbatim, without having compiled or tested it
- Piping an empirical probe into a build tool's interactive REPL and reading its silent no-op as a clean run, instead of a scratch test under the project's own runner
- Leaving probe scaffolding behind in the review worktree after the table is captured
- Refusing a finding solely because its line is outside the diff, when the change is what made that line decisive
- Adopting an unrelated memory as a review preference because it ranked highly
- Priming a reviewer with a suspected defect — biases toward confirming it
- Running preflight in the user's checkout instead of a dedicated review worktree
- Reviewing in the invocation directory on branch-name match alone, without confirming it sits at the PR head with a clean tree
- Commandeering an existing worktree that holds the PR's branch — someone's working copy — instead of creating a detached review worktree at the head SHA
- Relying on `cd` persisting between commands instead of passing the worktree path explicitly
- Discarding preflight churn without reading it, or forcing a worktree removal to get past it
- Reviewing against a stale base ref, inflating the diff
- Treating green CI as proof the changed path is safe
- Accepting "the gates pass" from the requester without reading the commit's actual status, when one API call settles it
- Reading a pending check as a passing one, or a review bot's green status as evidence it actually reviewed this commit
- Hardcoding one project's verification command instead of discovering it
- Reporting a finding without quoted evidence, or without a stated consequence
- Reviewing lines the change did not touch
- Reviewing the diff hunks instead of the source file they sit in, so the context that sets severity is never read
- Reading a changed file from a branch name, a stale worktree, or an editor buffer rather than at the pinned revision under review
- Leaving part of a file unread without saying so, which the author reads as checked
- Posting without reading the result back from the API
- Reloading or navigating a live diff session the user is reading, to make a finding fit
- Treating inline notes as a substitute for the report, or submitting a comment batch without checking each finding anchors inside the loaded review
- Leaving lockfile or worktree churn behind after preflight
- Persisting an unverified conclusion to memory or notes
- Padding a review with nits, or opening it with a compliment
