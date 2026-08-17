# Translating Allium specs into Alloy models

Allium and Alloy answer different questions about the same spec: `allium check` confirms a spec parses and is internally consistent; an Alloy model of the same spec asks whether a *specific property* holds across every state the spec's rules can reach. Translating from one to the other is not mechanical — three Allium semantics quietly produce a weaker model than the spec actually states if carried across without adjustment.

## Checking the source spec first

Before translating, run `allium check` against **every** spec file in the checked set together, not one at a time:

```bash
allium check .allium/some-domain.allium .allium/another-domain.allium
```

Checking a single file in isolation emits spurious `allium.use.unresolvedPath` warnings for anything it depends on from another file, and hides genuine cross-file findings. The output is **concatenated JSON objects, one per file — not a single JSON document.** A plain `json.load()` on the combined output fails with "Extra data" partway through; parse it with a streaming decoder instead (e.g. Python's `json.JSONDecoder().raw_decode()` in a loop over the output, advancing past each decoded object).

## Trap 1 — `use` does not import value types

`use "parent.allium"` pulls in the parent spec's entities and rules, but **not its `value` type declarations.** A child spec that references a value type like `UUID` or a domain-specific ID type defined only in the parent fails `allium.type.undefinedReference` — the `use` looked like it should have covered this, and didn't.

When translating a child spec's obligation into Alloy: either re-declare the needed value type locally in the child before translating, or fall back to a plain `String`-equivalent Alloy signature if the value type's internal structure doesn't matter for the property being checked. Also watch for the inverse problem — an entity declared in both the parent and the child spec collides; don't carry both into the same Alloy model as if they were distinct.

## Trap 2 — untyped trigger parameters and unused refs are silently accepted

Only four things count as a "reference" to a declared entity or definition, for Allium's own unused-reference checking:
- A field type on another declaration
- A `.created()` call
- A join lookup (`Entity{...}`)
- A `with` relationship

Trigger parameters, loop iteration variables, and `exposes:` clauses do **not** count as references — so a trigger parameter that's declared but never actually used downstream, or an entity only ever touched via one of these four excluded forms, will not raise `allium.entity.unused`/`allium.definition.unused` even when it should. Don't treat "no unused-ref warning" as proof a declaration is load-bearing to the property being modeled.

More importantly: **trigger parameters are untyped**, by the checker's own admission — there's no automated way to catch a `provides:` argument passed in the wrong position. When a trigger parameter feeds into the property being translated to Alloy, hand-verify its type and position against the trigger's declaration before encoding it into the model. A translation that trusts an untyped, positionally-matched parameter can silently model a different value than the spec actually passes.

## Trap 3 — adding a status value needs its own Witness rules

If a spec's obligation depends on a status/state enum, adding a new value to that enum requires adding a corresponding `rule WitnessXToY` declaration for every transition into and out of it. Skipping this produces two warnings per missing value — `allium.status.unreachableValue`, and `allium.status.noExit` as a downstream consequence of the first — and, more importantly for this skill's purposes, means the state machine as declared doesn't actually admit reaching or leaving that value. An Alloy model built from a spec with this gap will faithfully reproduce an under-connected state graph; check the Witness rules are complete for every status value the property touches before trusting an `UNSAT` that depends on reachability.

(A `allium.deferred.missingLocationHint` warning has no known satisfying syntax — `-- see:`, `in`, `from`, and `at` all either fail to parse or don't resolve. Leave it as a stated warning and use a trailing `-- path` comment instead of chasing a fix; this is unrelated to the Alloy translation but shows up in the same `allium check` output and shouldn't be mistaken for something the translation needs to solve.)

## Prior convention for organizing the bridge

Earlier work on this exact bridge (spec → Alloy model) settled on a convention worth reusing rather than reinventing per-project:

- Model files live under `.allium/alloy/<name>.als`, one file per obligation or closely related group of obligations, gitignored (they're generated/derived from the spec, not hand-authored source of truth).
- A small runner script (`.allium/alloy/run-alloy.py`, also gitignored) drives the batched invocation from Phase C of the main skill.
- Annotate each `check`/`run` command with an `-- @expect UNSAT` (or `SAT`) comment marker in the `.als` source, and diff the actual verdict against it — this turns "did the property hold" into "did it hold *and match what we expected it to*," catching the case where a model technically runs but checks a different, weaker property than intended.

## Weeding-rule vs. distillation-rule distinction

If the obligation under translation came from a **target-state spec** (one written to describe intended behavior, cited against file:line anchors in the actual code), check it against those citations directly. If it came from a **distilled spec** (one extracted by observing actual current behavior), check it against actual runtime behavior instead. Conflating the two — checking a target-state spec's Alloy model as though it were describing current behavior, or vice versa — produces divergences that aren't real divergences, just a category mismatch between what kind of spec was being modeled. Confirm which kind of spec is in scope during Phase A, before translating.
