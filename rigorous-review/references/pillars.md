# Analysis pillars

Work every pillar on every review. A pillar you skip is a pillar you cannot list in the non-findings block, and an unlisted pillar reads to the author as "not checked."

## The seven pillars

**Correctness** — Does the code do what it claims, on the inputs it will actually see? Trace the changed path end to end. Check that the predicate used to *read* state and the predicate used to *write* it agree — divergent predicates are a recurring, high-severity defect and they never look wrong locally. And check that the mechanism is not merely present but *effective* — see below.

**Maintainability** — Is the structure something the next person can change safely? Look for hidden coupling, implicit ordering requirements, and state that must be kept in sync by convention rather than by construction.

**Readability** — Does the code read the way the rest of the file reads? Match the surrounding idiom, naming, and comment density. A locally-clever construction in a plain codebase is a maintainability cost, not a win.

**Efficiency** — Only flag work that is measurably wasteful on realistic inputs: N+1 queries, repeated work inside a loop that could be hoisted, unbounded growth. Do not flag micro-optimisations.

**Security** — Authentication and authorisation on the changed path, injection surfaces, secrets in code or logs, and data exposure. Check that a security control is actually *reachable* — a safe default is worthless if a lower-precedence config layer already set the flag the other way.

**Edge cases and error handling** — Empty, single-element, and maximal inputs; null and undefined; concurrent and repeated invocation; the failure branch of every call that can fail. Ask what the user sees when it goes wrong, not just whether it is caught.

**Testability** — Is the changed behaviour covered by a test that would fail if the behaviour regressed? Coverage percentage is not the question. A test that mocks the thing under test proves nothing.

## Mechanism present is not mechanism effective

The wiring being there is not the behaviour happening. A reviewer who confirms the value reaches the right function has checked that the *plumbing* is connected, not that the *water* arrives. These are separate claims and the second is the one the change promised.

The failure is easy to miss because everything looks right: the argument is threaded correctly, the call is in the right place, the types check, the tests pass. What is missing happens at runtime — the work is scheduled and then abandoned, cancelled, or never awaited.

Ask both questions, in order, and treat them as separate:

1. **Present** — is the value threaded through and the call made on the path that needs it?
2. **Effective** — does the work that call schedules actually run to completion, and does its outcome reach whoever depends on it?

Answering 1 and stopping is the specific mistake. State which one you verified.

### Capability triage

Before sweeping, decide which of these the language and runtime under review actually have. A capability the language lacks is not a gap in your review — say so in the non-findings block and move on. A capability it *has* is a sweep you owe.

| Capability | Present when the language/runtime can… | Then check |
|---|---|---|
| **Detachable effects** | represent in-flight work as a value, or start work that outlives the statement | the handle is retained and joined before the result is relied on |
| **Cancellation** | interrupt in-flight work from outside — timeouts, abort signals, context, fiber or task interruption, shutdown | the cancellation boundary sits outside the work that must not be lost |
| **Error absorption** | catch, discard, or downgrade a failure without surfacing it | the failure path is observable at a level someone reads |
| **Delivery semantics** | retry, redeliver, ack, or commit — queues, streams, jobs, outbox tables | success is recorded only after the durable write, and replay is safe |
| **Ordering** | complete work out of submission order — concurrency, batching, parallel map | anything order-dependent is sequenced explicitly |

### Detachable effects — the recurring one

If a language lets you *obtain* a handle to in-flight work, it lets you *drop* it. That is one defect class with many spellings. Hunt the shape, not the keyword:

- work started in statement position whose result is bound to nothing
- a handle assigned to a discard binding, or to a name that is never read again
- a function whose signature cannot report completion, called where completion matters
- a background task held only by a local that goes out of scope
- a collection of handles built and never joined
- a wrapper named for "fire and forget", "background", "detached", or "async" semantics, called on a path whose correctness needs the result

The last one is the sharpest trap: a helper whose *name* documents that it discards is still a discard. A change that switches a call from an awaiting helper to a detaching one reverses the guarantee while the diff reads as a rename.

Two compounding factors turn a dropped handle from a latency question into data loss:

- **Cancellation reaches it.** If the caller can be cancelled — client timeout, request abort, shutdown, parent task interruption — ask whether that cancellation propagates into the detached work. Detaching from a *parent* is not the same as detaching from the *runtime*; work reparented to a root scope still dies when the process drains.
- **The resulting error is absorbed.** Trace where a cancellation error lands. If the handler for it logs at debug or trace, or catches and ignores, the loss is silent — and silent loss outranks loud failure on the severity ladder.

When both hold, the code claims a durable side effect and does not have one.

### Sweeping for it

These are shape questions, so they are `ast-grep` questions. Text search cannot express "bound to nothing" or "never joined" — it has no notion of syntactic position. Per `references/semantic-search.md`, run the structural sweep first and descend only if the pattern cannot be written.

Two patterns carry most of the value. Scope both to the changed files and their callees:

- **Unbound effect** — a call to a function known to return a handle, appearing where its value is discarded. Write it against the language's grammar: an expression statement, a discard binding, a lambda body whose result type is ignored.
- **Unjoined handle** — a spawn or submit whose result is assigned, with no subsequent join, await, or collect on that binding in scope. A YAML rule with `has` and `not` states this directly; chained greps do not.

Sanity-check each pattern against a known instance before trusting an empty result, per the traps in `references/semantic-search.md`. On this sweep especially, an empty result is the whole claim — and when the semantic tier is unavailable, on every sweep whose value is absence.

**Verify by execution where the runtime allows it.** Phase 5 rule 3 applies with force: drive the changed unit, cancel the caller mid-flight, and check whether the side effect landed. An input → output table showing the write missing after cancellation converts this from `Plausible` to `Confirmed`, and it is not arguable.

## Reviewer preferences

These are stylistic positions, not universal truths. Apply them; do not moralise about them.

### Functional-programming bias

Prefer immutable state, pure functions, and referential transparency. Prefer declarative constructs over imperative loops where the declarative form is at least as clear. Flag in-place mutation of a shared or caller-owned value — that is a correctness concern, not a style one. Prefer local reasoning and composition.

### Anti-over-engineering

Flag, symmetrically, in both directions:

- **Too much** — an abstraction with exactly one call site; configurability nobody asked for; error handling for a scenario that cannot occur; a layer that only forwards. If 200 lines could be 50, say so and show the 50.
- **Too little** — the same non-trivial logic duplicated across call sites, where a change to one will silently miss the others.

Neither is a nit. Both change the cost of the next change.

### Typing

Strict types. Flag `any`, unchecked casts, and assertions that suppress a real error rather than encode a real invariant. A cast is a claim; ask what proves it.

### Comments

Minimal and high-signal. A comment should explain *why* — the constraint, the trade-off, the non-obvious reason. Flag comments that restate the code, and flag missing comments only where the *why* is genuinely unrecoverable from the code.

### Tests

An implementation is incomplete without tests, and the tests must include the edge cases. Missing tests for a changed behavioural path is a finding, not a suggestion.

## What is not a finding

Scope discipline is part of the review. Do not raise:

- Improvements to code the change did not touch.
- Refactors the author did not ask for and the change does not require.
- Preferences with no consequence you can name.

If you cannot state what goes wrong, it is not a finding. Move it to the non-findings block or drop it.
