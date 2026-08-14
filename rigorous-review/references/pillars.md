# Analysis pillars

Work every pillar on every review. A pillar you skip is a pillar you cannot list in the non-findings block, and an unlisted pillar reads to the author as "not checked."

## The seven pillars

**Correctness** — Does the code do what it claims, on the inputs it will actually see? Trace the changed path end to end. Check that the predicate used to *read* state and the predicate used to *write* it agree — divergent predicates are a recurring, high-severity defect and they never look wrong locally.

**Maintainability** — Is the structure something the next person can change safely? Look for hidden coupling, implicit ordering requirements, and state that must be kept in sync by convention rather than by construction.

**Readability** — Does the code read the way the rest of the file reads? Match the surrounding idiom, naming, and comment density. A locally-clever construction in a plain codebase is a maintainability cost, not a win.

**Efficiency** — Only flag work that is measurably wasteful on realistic inputs: N+1 queries, repeated work inside a loop that could be hoisted, unbounded growth. Do not flag micro-optimisations.

**Security** — Authentication and authorisation on the changed path, injection surfaces, secrets in code or logs, and data exposure. Check that a security control is actually *reachable* — a safe default is worthless if a lower-precedence config layer already set the flag the other way.

**Edge cases and error handling** — Empty, single-element, and maximal inputs; null and undefined; concurrent and repeated invocation; the failure branch of every call that can fail. Ask what the user sees when it goes wrong, not just whether it is caught.

**Testability** — Is the changed behaviour covered by a test that would fail if the behaviour regressed? Coverage percentage is not the question. A test that mocks the thing under test proves nothing.

## Reviewer preferences

These are stylistic positions, not universal truths. Apply them; do not moralise about them.

### Functional-programming bias

Prefer immutable state, pure functions, and referential transparency. Prefer declarative constructs over imperative loops where the declarative form is at least as clear. Flag in-place mutation of a shared or caller-owned value — that is a correctness concern, not a style one.

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
