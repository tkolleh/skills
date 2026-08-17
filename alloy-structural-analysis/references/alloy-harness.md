# The Alloy headless harness — exact mechanics

`alloy exec` is designed to be scripted, but its defaults fight that goal in three specific ways. Each one produces a plausible-looking wrong answer rather than an error, so catch them mechanically rather than trusting a clean-looking run.

## Invocation

```bash
alloy exec -f -q -s <solver> -t json -o <output-dir> -c '<command-name-or-*>' <file>.als
```

- `-s electrod.nuxmv` — routes through Electrod → nuXmv for real temporal (LTL) model-checking. Required for any property using `always`/`eventually`/`until` or `var` fields under an unbounded trace.
- `-s minisat` (or `sat4j`, `glucose`) — the default bounded SAT backends. Fine for non-temporal structural checks; also the only thing that runs if `electrod.nuxmv` is unavailable, which produces indistinguishable-looking output (see the Temporal trap below) — don't let a fallback silently substitute for the check you meant to run.
- `-o` is resolved **relative to the current working directory, not the `.als` file's directory.** A relative `-o` from the wrong CWD silently writes results somewhere unexpected — use an absolute path.
- `-f` (force) **deletes the output directory before resolving `-c`.** If the command name in `-c` has a typo, the prior run's results are already gone by the time Alloy discovers the name doesn't match anything. Validate the command name against the file's actual `check`/`run` declarations before invoking with `-f`.
- `-t json` or `-t xml` — always use one of these, never the default Markdown/text renderer. The `.md` solution rendering drops structure needed to tell a real counterexample from a vacuous one.

## Trap 1 — exit code is always 0, except for a syntax error

SAT, UNSAT, a solver crash, a missing input file, an unmatched `-c` name, and a non-empty `-o` directory that `-f` should have cleared: all of these return exit code 0. The **only** case that returns 1 is an actual `.als` syntax error.

Never gate success on exit code. The correct success criterion is:

> `receipt.json` exists in the output directory **and** every command name you expected to check is present as a key in it.

A compile error produces no output directory at all. A solver crash produces an output directory that exists but is empty or missing the expected keys. Both look identical from an exit-code check — only inspecting `receipt.json`'s actual keys distinguishes them.

## Trap 2 — `receipt.json`'s `values` field is unsound off-scope, solver-dependent

`values` silently misreports atoms when a signature's actual model does not sit exactly at its declared scope bound — it can drop the first `scope − |sig|` atoms or invent phantom ones. This is **solver-dependent**:

- Corrupts under: `sat4j`, `glucose`, `minisat.prover`
- Complete/correct under: `minisat`, `sat4j.light`
- `skolems` (the witness bindings for a `check`'s violating instance) never exhibits this bug — trust `skolems` before `values`.

Two ways to get a trustworthy result instead of guessing which solver you're safe with:
1. Scope every signature with `exactly N Sig` rather than a bare `N Sig` upper bound, so "off-scope" can't occur.
2. Parse the `-t xml` output instead of `values` from JSON — the XML instance representation does not carry this defect.

## Trap 3 — duplicate command names silently collapse (last write wins)

`receipt.json`'s `commands` field is a **dict keyed by command name**, not a list of results. Two `check`/`run` commands sharing a name write to the same key — the second overwrites the first, even though the console output shows both having run. Nothing reports the collision.

Validate command-name uniqueness across the whole spec set **before** invoking, at the same point Phase B of the main skill already checks this. If a result count looks short, check for a name collision before assuming the check found nothing.

## Trap 4 — self-diagnose rather than assume the solver ran

Whenever a result looks suspiciously clean — instant UNSAT, no meaningful search time, or you're not certain `electrod.nuxmv` was actually invoked rather than silently falling back to the bounded default — confirm which solver binaries actually executed:

```bash
alloy -D debug exec -s electrod.nuxmv -t json -f -o <output-dir> <file>.als 2>&1 \
  | grep -i "kodkod.solvers.api.NativeCode"
```

A hit naming both the Electrod and nuXmv binaries confirms a real invocation. No hit means the result is not evidence of anything and must be reported as unverified, not as a verdict.

## The SAT/UNSAT discriminator

There is no boolean "satisfied" field. Presence of the `solution` key under a command's entry means the search produced at least one instance; absence means UNSAT (no such instance exists within the checked scope). Path into the structure:

```
commands[<CommandName>].solution[i].instances[j].{values, skolems}
```

- `solution[]` — one entry per enumerated solution (relevant when invoked with `-r N` to ask for N distinct solutions).
- `instances[j]` — one entry per state in that solution's trace (relevant for temporal/`var`-field models with more than one state).

## Modelling for a legible counterexample, not just a verdict

Phrase an assertion you intend to `check` as a **top-level universally-quantified statement** — `all x: T | <property>` — rather than an implication whose negation degenerates to an existence check:

```
-- Good: negation skolemizes as CommandName_x, naming the violating atom
check NoOrphanStage {
  all s: Stage | s in ReachableStages
}

-- Avoid: negation is "no x: T | ...", which finds A violation but names nothing
check NoOrphanStageWeak {
  SomeCondition implies (no s: Stage | s not in ReachableStages)
}
```

The first form's negation, when SAT, skolemizes the witness as `<CommandName>_<var>` — the counterexample names the specific atom that violates the property. The second form can be SAT for reasons that don't point at anything actionable.

**Read the rendered counterexample, not just the verdict.** Two authoring mistakes from prior model-building sessions are worth watching for directly:
- A single `iff` constraint over existing stages doesn't forbid orphaned atoms outside that set — add an explicit no-orphans clause if the property depends on exhaustiveness, not just consistency.
- Leaving a field like a "winner" relation unconstrained lets the solver assign it arbitrarily to satisfy the model, producing a counterexample that looks meaningful but is actually just filling in an underspecified relation. If a witness looks arbitrary, check whether the relation it turns on is actually constrained anywhere in the model.

## Temporal checking's actual failure mode

If `electrod.nuxmv` is broken or unavailable, bounded checks (`check X for N` including `var`-field lasso models) still run correctly on the default SAT backend — they just cannot express genuinely unbounded/LTL properties. The dangerous case: a trace that cannot close into a lasso under the bounded search returns **UNSAT**, which is visually indistinguishable from a proved assertion. This is exactly why Trap 4's debug-log verification matters most for temporal models — an UNSAT you haven't debug-verified might mean "proved" or might mean "the bounded search couldn't even construct a trace to check."

## Environment fix recipe (pointer only — do not re-derive)

If `alloy`, `electrod`, or `nuXmv` are ever actually missing or broken on a given machine (this skill assumes they are not, per its `compatibility` field), the exact recovery recipe — MacPorts install of `libxml2`/`gmp`/`libedit`, building Electrod from source via a local opam switch with three specific upstream dependency-pin patches, and the verified end-to-end invocation — lives in the memory file `nuxmv_macports_libs_fixed.md` from the session that first solved it. Read that file rather than re-deriving the fix from scratch.
