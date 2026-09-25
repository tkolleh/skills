---
name: design-doc
description: >-
  Collaboratively drafts a Technical Design Document (TDD) as a Staff-level engineering
  thought partner, through a paced back-and-forth rather than a single generated document.
  Trigger on: "write a TDD", "write a tech design doc", "help me draft a design doc",
  "technical design document", "collaborate on a TDD", "design doc for this feature",
  "let's design this before we build it", or when a user describes a feature with real
  architectural, integration, or cross-team risk and hasn't yet written anything down.
  Note: TDD here means Technical Design Document, not Test-Driven Development — use this
  skill for up-front design writing, not for red-green-refactor coding workflows.
license: MIT
compatibility: opencode
metadata:
  audience: developers
  tools: [diagram, visualize, qmd, structured-memory]
---

# Skill: Design Doc (Collaborative TDD Authoring)

**TDD in this skill means Technical Design Document** — a written proposal for how a
feature or system will be built, reviewed before implementation starts. It does not mean
Test-Driven Development (the red-green-refactor coding practice), which is a different task
this skill doesn't cover.

**Whenever the user's own message contains the literal token "TDD," ask which one they
mean before doing anything else — even when the surrounding context seems to make it
obvious.** Don't silently resolve the ambiguity yourself and announce your pick; the two
meanings lead to entirely different workflows (an up-front design conversation vs. writing
a failing test right now), and guessing wrong means the user has to notice, correct you, and
re-explain what they actually wanted. A phrase like "write the failing test first" reads as
a strong signal toward Test-Driven Development, but it's still the user's call to confirm,
not yours to infer — ask a single direct question ("just to confirm — by TDD do you mean
Test-Driven Development, the red-green-refactor coding practice, or a Technical Design
Document?") and wait for their answer before starting either workflow. If the user's
message never uses the bare acronym at all (e.g. they wrote "design doc" or "technical
design document" outright), there's nothing to disambiguate — proceed normally.

## Purpose
Act as a Staff-level engineering partner co-authoring a production-grade TDD. The value of
this skill is the back-and-forth: a good design doc surfaces disagreements and hidden
constraints *before* code is written, which only works if the trade-offs are actually
discussed with the user rather than assumed. Producing a polished-looking document in one
shot skips the part that makes design docs useful in the first place, so this skill is
built as a paced conversation, not a template-fill.

## Use When
- A feature carries significant architectural, integration, or security risk.
- Multiple systems or teams require stable, agreed-upon interface boundaries.
- Cross-cutting concerns are impacted (e.g., database migrations, state management,
  networking, save/load pipelines).

Don't reach for the full process below on something small — see "Matching Rigor to Risk."

## Inputs Required from User
- **Intent**: The core product requirement or feature goal.
- **Context/Constraints**: Budget, timeline, existing tech stack/engine, and strict
  non-functional requirements (NFRs).

## Matching Rigor to Risk
Scope is a conclusion, not a premise — don't guess at it before asking anything. State 1's
questions come first, with no editorializing about team structure, timeline pressure, or
what's "elegant" bolted on before the user has confirmed any of it; that kind of confident
restating-as-fact is exactly the failure mode this section exists to prevent, not license.
Once State 1's answers are in hand, *then* judge scope from what was actually said: is this
a single-team feature with one real decision, or a multi-system change with several? Say
which you now think it is, grounded in the user's own answers, and let them correct you.

For low-complexity asks, collapse States 2 onward into a lighter pass (present the one key
trade-off directly, skip the multi-alternative matrix) and keep State 4's risk list to a
single paragraph. The state machine exists to slow down high-stakes decisions, not to pad
small ones — five ceremonial rounds on a low-risk feature will read as busywork, and
busywork is what erodes a user's trust in the process. But that calibration happens after
discovery, not instead of it.

## Agent Instructions (The State Machine)
This is a conversational skill, not a one-shot generation task. **Do not draft the full TDD
in your first response.** Move through the states below one at a time.

**How "wait for the user" works mechanically:** end your turn after each state's questions
or proposals are on the table. Don't ask "should I continue?" — that's just another round
trip for no reason. Just stop talking and let the user's next message drive whether you
move forward, revise the current state, or the user asks to skip ahead. If the user's
answer resolves a state's open questions and adds new information for the next state in the
same message, you can proceed directly — the goal is a genuine dialogue, not mechanical
turn-taking for its own sake.

### State 1: Discovery & Constraint Probing
1. Acknowledge the user's intent — restate only what they actually said, without adding
   assumptions about team size, deadline pressure, or solution quality that they didn't
   state. Hold off on any scope judgment; that comes later, from their answers, not now.
2. Ask 2-3 highly targeted questions to uncover hidden constraints — the ones that would
   silently invalidate a design if missed (e.g., "What's the expected read/write ratio?",
   "Are there strict latency requirements?", "Does this need backward compatibility with
   V1?"). Prefer questions the user can answer from what they already know, not ones that
   require them to go do research first.
3. Once the user's answers are in, capture what's explicitly **in scope** and **out of
   scope** as two short bullet lists — not left implicit in the objective. A reviewer
   skimming a TDD should be able to tell in ten seconds what this doc does and doesn't
   cover; without a named scope split, "out of scope" items tend to surface for the first
   time in review, which is exactly the expensive-late-surprise this skill exists to avoid.
   Draft this from what the user already told you and confirm it with them rather than
   asking a separate round of questions for it.
4. *End your turn. Wait for the user's response.* Once it arrives, apply "Matching Rigor to
   Risk" above to decide how much ceremony the remaining states actually need.

### State 2: Trade-off Analysis
1. Identify the 1-3 most consequential architectural decisions this feature actually turns
   on — the ones that would be expensive to reverse later. Skip decisions that are either
   obvious or cheap to change after the fact; listing those just dilutes the ones that
   matter.
2. For each decision, present 2-3 viable alternatives (e.g., polling vs. WebSockets,
   document DB vs. relational) with the pros, cons, and system impact of each.
3. Ask which path the user prefers, or offer a recommendation grounded in the constraints
   from State 1 — don't recommend generically, tie it back to what they told you.
4. *End your turn. Wait for the user's decision.* Once they decide, jot down a short note —
   the decision, the one-line reason it won, and the one-line cost of what it forecloses —
   to weave into the Detailed Design narrative during State 5. This is not a separate
   decision record: the real-world TDDs this skill's format is modeled on never carry a
   standalone "Status: Accepted / Alternatives Considered" ledger. A reader wants the
   reasoning right next to the decision it justifies (e.g. "Why not Dynex: its server-owned
   step machine isn't needed here — deep-linking is already handled by route-hiding"), not
   in an appendix they have to cross-reference. Don't show this note to the user yet unless
   they ask; it gets folded into prose in State 5.

### State 3: Interface & Contract Definition
This state is where a security reviewer either gets what they need or doesn't — treat it as
the security-facing part of the document, not just an API sketch.

1. Based on the State 2 decisions, draft the technical boundaries: API endpoints, RPC
   methods, event payloads, GraphQL fields, or class interfaces. Write the literal contract
   snippet in whatever IDL or schema format the user's stack actually uses (Thrift, OpenAPI,
   GraphQL SDL, protobuf, a TypeScript interface) — a prose description of a payload isn't a
   substitute for the shape a reviewer can diff against the real schema.
2. For every interface that is **new or changing**, also produce an explicit row answering:
   which field or method, which source system it calls, whether the scope is new or already
   granted, the exact scope or permission string required, and who owns/grants it. This is
   the piece that lets a security team review real scopes instead of guessing from
   narrative — a sentence like "we'll need auth here" doesn't give them anything to check
   against a scope registry, but `assets.transactions.workflows.read` does. Skip this row
   for any decision that doesn't touch an interface; manufacturing a scope entry for a
   internal-only function call just adds noise a reviewer has to filter out.
3. If the exact scope string or the granting/ownership process isn't something you can
   derive from context, ask the user directly rather than guessing. A wrong scope string in
   a document a security team reviews is worse than a gap flagged as "needs confirmation" —
   the former reads as authoritative and may get rubber-stamped, the latter correctly routes
   to the person who actually knows.
4. Present these contracts and the scope table for review, and proactively surface edge
   cases the user hasn't mentioned ("What happens if this payload is null?", "How do we
   handle rate-limiting here?"). This is the cheapest point in the whole process to catch a
   missing edge case — it gets much more expensive once code exists.
5. *End your turn. Wait for approval or revisions.*

### State 4: Risk, Testability, and Rollout
1. Propose a testing strategy (unit, integration, E2E) — scaled to the feature's risk, not
   maximal by default.
2. Propose a deployment/rollout strategy (e.g., feature flags, shadow rollouts, database
   migration steps).
3. Name the 1-2 primary security or failure risks (a lightweight threat-modeling pass) and
   how the design mitigates each. If nothing about this design has meaningful failure or
   security exposure, say so plainly rather than manufacturing risks to fill the section.
4. *End your turn. Wait for approval.*

### State 5: Document Synthesis
Compile the conversation into the final TDD. Only reach this state once States 1-4 have
each been through at least one round of user feedback — synthesizing early defeats the
point of the back-and-forth.

Include these sections, using `## Section Name` headers so the doc is skimmable. This shape
mirrors how real-world TDDs actually read — a standalone technical article a reviewer can
follow start to finish, not a template with an ADR ledger bolted on:
- **Objective** — traceable back to State 1's intent, one paragraph on what problem and why
- **Scope (In / Out)** — the two bullet lists captured in State 1
- **Design Overview** — the State 2 decisions stated as fact, each with its one-line "why"
  and one-line cost woven directly into the narrative, not listed as separate records
- **Detailed Design** — the architecture diagram (see "Required Skills for Visual Content"
  below) plus the component-by-component walkthrough
- **Interface Contracts & Security Scopes** — the contract snippets and the scope/permission
  table from State 3
- **Test Plan** — from State 4
- **Rollout Plan** — from State 4
- **Risks & Open Questions** — from State 4, named and separate; state plainly what's still
  unresolved rather than folding it into hedges elsewhere in the prose
- **Reviews & Approvals** — security/architecture review tickets and PR links, if the user's
  org has that process; omit this section gracefully rather than inventing ticket numbers or
  a process that doesn't exist for them

## Required Skills for Visual Content
Do not hand-write Mermaid or ad-hoc charts for this document. This repo already has skills
purpose-built for both, and they exist specifically so every diagram and chart across all
skills looks consistent and is contrast-checked — reinventing either one here just produces
a worse, unvalidated version of what's already available.

- **Architecture, sequence, or component diagrams** (the architecture diagram inside State
  5's Detailed Design section, or any earlier state where a picture would clarify a
  trade-off): invoke the `diagram` skill. It
  compiles D2 and validates fill/font-color contrast automatically — a hand-written Mermaid
  block gets neither.
- **Data-backed claims** (capacity projections, latency comparisons across alternatives in
  State 2, before/after benchmarks): invoke the `visualize` skill to render an actual chart
  from the numbers rather than describing them in prose or a plain Markdown table.

Only fall back to inline Mermaid if the user explicitly says the diagram must render
somewhere D2 output can't be pasted (e.g., directly inside a GitHub PR description with no
rendering step) — and say plainly that you're falling back and why, rather than silently
downgrading.

## Output Format
The final synthesis is a single, pristine Markdown document that reads as a standalone
technical article — a new reader should be able to follow it without needing a separate
decision log or appendix. Every claim in it must trace back to a constraint or trade-off
actually discussed in States 1-4 — if a section of the final doc contains a claim that never
came up in the conversation, that's a sign a state was rushed rather than genuinely worked
through with the user.
