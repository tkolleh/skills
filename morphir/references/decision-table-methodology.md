# Decision-table verification methodology

The correctness gate for a Morphir/Elm translation of source logic. This exists because the two more obvious verification strategies both turn out not to work for this purpose:

- **`morphir-elm make`'s exit code** only confirms the Elm parses into valid IR — it says nothing about whether the IR represents the *right* behavior. A model that compiles cleanly can still be a confidently wrong translation.
- **Diffing `morphir-elm gen`'s generated output against the hand-written source** doesn't work either, because generated code always diverges textually from hand-written code even when both are behaviorally identical (see `morphir-elm-cli.md`'s note on this). A real bug and a purely mechanical difference are indistinguishable under a text diff.

The remaining option — and the one that actually verifies what matters — is: pick concrete inputs, trace them by hand through both the Elm model and the cited source code, and compare the outcomes. This is fixture-based equivalence checking, not exhaustive state-space search. It's a weaker guarantee in the abstract (an input outside the table is unverified) but it's cheap to produce, easy for a human reviewer to sanity-check line by line, and it directly answers the question that matters: "does this model behave like the source on the cases that matter."

## Building the table

For each function under verification, enumerate fixtures covering:

1. **The happy path** — the most common, unremarkable input.
2. **Every branch and guard** — each `if`/`case`/pattern-match arm in the source should have at least one fixture that exercises it.
3. **Short-circuit behavior** — if the source short-circuits (stops evaluating once an early condition determines the outcome), include a fixture where a later condition would produce a *different* result if evaluated, to prove the short-circuit is preserved in the model, not just that outputs happen to agree.
4. **Boundary and empty cases** — empty collections, zero/negative values, nulls/optionals in whichever form the source and model represent them, ties (multiple equally-valid outcomes), and anything the source's own tests already flag as an edge case worth covering.
5. **Anything already flagged as a known gap** — if a prior pass already identified an under-tested or ambiguous case, include it explicitly rather than letting it fall through the cracks again.

## Table format

For each fixture, record the input, the traced outcome through the Elm model, the traced outcome through the cited source `file:line`, and whether they agree. A minimal per-row shape:

```markdown
### Fixture: <short descriptive name>

**Input:** <concrete input values>

**Elm trace:** <the sequence of branches/guards taken in the Elm model, and the resulting output>

**Source trace:** <the sequence of branches/guards taken in the source at `path/to/File.ext:line`, and the resulting output>

**Result:** AGREE | DIVERGE — <if diverge, which side looks correct and why, or "unresolved, filed as a finding">
```

Group fixtures by function or module, and lead the report with any divergence found — a clean table of agreements is good news, but it's not the part a reviewer needs to spend their time on.

See `templates/decision-table-template.md` for a ready-to-copy skeleton.

## Handling a divergence

When a fixture's traces disagree, that's the actual finding this whole method exists to surface. Two rules govern how to handle it:

1. **Never silently adjust the Elm model to match the source without flagging it.** The instinct to "just fix the model so the table goes green" defeats the purpose — a divergence might mean the *source* has a bug that predates this exercise entirely, and quietly making the model agree with buggy source produces a model that faithfully encodes the bug, which is worse than no model at all.
2. **State which side you believe is correct, and why — but don't unilaterally resolve it as part of authoring the model.** Whether to fix the source, fix the model to match a discovered spec/intent, or leave the divergence as a documented known gap is a decision for whoever owns the source code's correctness, not something to decide silently while translating. If the project has a dedicated spec-vs-code drift/triage tool as part of its workflow, hand the divergence to it with the fixture and both traces as context, rather than re-deriving that judgment here.

A clean decision table — one where every fixture agrees — is not a stronger claim than what it actually checked. State the fixture count and coverage explicitly (which branches, which boundary cases) rather than letting "the table passed" imply exhaustiveness it doesn't have.

## Worked example (genericized)

Source (illustrative, not a real codebase):

```scala
def isEligible(account: Account, threshold: Int): Boolean = {
  if (account.isSuspended) false
  else account.balance >= threshold
}
```

Elm model:

```elm
isEligible : Account -> Int -> Bool
isEligible account threshold =
    if account.isSuspended then
        False
    else
        account.balance >= threshold
```

Fixture table:

| Fixture | Input | Elm trace | Source trace | Result |
|---|---|---|---|---|
| Happy path, eligible | `{isSuspended: False, balance: 100}`, threshold `50` | not suspended → `100 >= 50` → `True` | not suspended → `100 >= 50` → `true` | AGREE |
| Happy path, ineligible | `{isSuspended: False, balance: 10}`, threshold `50` | not suspended → `10 >= 50` → `False` | not suspended → `10 >= 50` → `false` | AGREE |
| Short-circuit on suspension | `{isSuspended: True, balance: 1000}`, threshold `50` | suspended → `False` (balance never checked) | suspended → `false` (balance never checked) | AGREE — confirms short-circuit preserved despite a balance that would otherwise pass |
| Boundary, exact threshold | `{isSuspended: False, balance: 50}`, threshold `50` | not suspended → `50 >= 50` → `True` | not suspended → `50 >= 50` → `true` | AGREE |

This table is intentionally small — a real one should cover every branch and every boundary condition the source actually has, not just four illustrative rows.
