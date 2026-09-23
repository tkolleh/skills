# Verification

A suspected defect is a hypothesis. Most hypotheses are wrong. This file is how you find out which, before the author does.

## Why this phase exists

A false finding costs more than a missed one. A missed defect costs one bug; a false finding costs the author an hour and costs you the benefit of the doubt on every finding after it. Optimise for precision.

In the review batch this skill was distilled from, four suspected defects were investigated in depth. **Three were refuted.** Every one of them would have been a false finding, and every one of them looked correct before it was tested.

## Rule 1 — Quote or drop

Every claim must quote code you actually read, from the file, at the revision under review.

No quote, no finding. This is absolute, and it is not bureaucracy — the act of going back to copy the line is what catches the finding you built on a half-remembered signature, an overload you did not know existed, or a file you inferred rather than opened.

Common failure: reasoning about a function from its call sites. Open the definition.

## Rule 2 — Refute, do not confirm

For each hypothesis, set out to **prove it wrong**. Ask "what would have to be true for this code to be correct?" and then go looking for that, in earnest.

Accept the refutation when it lands. A hypothesis you talked yourself back into is the one that ships as a false finding.

Things that refute a hypothesis:

- A guard, default, or invariant upstream that makes the bad input unreachable.
- A caller that already handles the case.
- A test that exercises exactly the path, and passes for the right reason.
- Framework or library behaviour that differs from the reasonable assumption — check the actual version resolved in this project, not the current docs.
- The behaviour being intentional, and stated as such in the PR description, a linked ticket, or a comment.

**Never state a suspected defect as fact when asking someone else — human or agent — to investigate it.** Priming produces confirmation. Ask the neutral question:

- Wrong: "Confirm that `applyFilter` drops rows when the toggle is active."
- Right: "What does `applyFilter` return for an active toggle with an empty selection? Show the code path."

When you do delegate, instruct the investigator to attempt refutation and to report a refutation as a successful outcome, not a failure to find something.

## Rule 3 — Prove behaviour empirically where you can

Reading establishes what the code *says*. Running establishes what it *does*. Where the changed unit can be driven in isolation, drive it.

The strongest finding in the source batch came from extracting a third-party filter function verbatim from the shipped bundle, driving it with realistic fixtures, and producing an exact input → output table. That converted "this looks wrong" into "here is precisely what your user sees", and it was not arguable.

How to do it:

1. Isolate the smallest unit that carries the behaviour — the exported function, the reducer, the predicate.
2. Take it **as shipped**, at the reviewed revision. Do not retype it; a transcription that fixes the bug proves nothing.

   When the unit has to be lifted into a harness — a different language, a standalone runner, an extracted function — **prove the harness is faithful before you trust a single result from it.** The repo's own test suite is the instrument: run the existing assertions for that unit through your harness and confirm they all still pass. In the run that produced this rule, a reviewer transcribed a Scala sanitiser into a Java harness and validated it by running the PR's own 93 spec assertions through it — 93 passed, 0 failed — before reporting anything. That converts every later result from "my copy behaves this way" into "the shipped code behaves this way." Without it, a transcription slip is indistinguishable from a defect, and it will be the author's first explanation.
3. Drive it with fixtures drawn from the real domain — values from tests, seed data, or the ticket's acceptance criteria. Invented inputs invite "that would never happen."
4. **Include control rows.** Alongside each input you claim is mishandled, drive a sibling you expect to be handled *correctly*, and label it. Without controls an unchanged output is ambiguous — it reads equally as a real defect or as a harness you wired up wrong, and the author will reach for the second reading first.

   ```
   input                             output              result
   SSN: 123456789                    SSN:  **            modified   <- control
   SSN = 123456789                   SSN = 123456789     UNCHANGED  <- finding
   ```

   The control redacting is what makes the finding unarguable: the harness demonstrably works, and the only thing that changed is the input.

5. Report the input → output table, not your interpretation of it.

Do not fabricate a table you did not produce. Where you cannot execute, say so and mark the finding `Plausible`.

## False-positive catalogue

Check every candidate finding against this list before it goes in the report. Anything matching is dropped or moved to non-findings.

- **Pre-existing** — the problem is on a line the change did not touch, *and* the change does not make it decisive. Real, but not this PR's. Before dropping on this rule, test it: can you write the load-bearing clause from `references/finding-schema.md` — newly reached, newly load-bearing, or newly frequent? If you can, the line is unchanged but the finding is this PR's, and it reports as PR-level. If you cannot, drop it. The rule exists to stop wishlists riding along on someone else's change, not to protect a change from the consequences of what it now depends on.
- **Compiler-catchable** — type errors, missing imports, formatting, unused symbols. The toolchain reports these better than you do; preflight already ran them. **This rule assumes a toolchain that will actually tell the author.** Before dropping on it, check that one exists and runs: a dynamic language has no compile step that catches an undefined name, and a repo with no CI has nothing that would surface it. Where preflight is something *you* had to construct, the toolchain is not reporting this — you are — so the finding stands. It also stands when the defect masks another: a test that dies on `NameError` never evaluates its assertion, so the wrong return value underneath it goes unseen.
- **Intentional** — the change in behaviour is the point of the PR, or is stated in the description or a linked ticket.
- **Explicitly silenced** — a suppression comment with a stated reason. Question a *missing* reason, not the suppression.
- **Unreachable** — a guard upstream makes the input impossible. Verify the guard; do not assume it.
- **Pedantic** — a naming or structure preference a senior engineer would not raise in a review.
- **Out of scope** — a genuine improvement to code the change did not touch.

## Two traps that survive careful review

**Green CI is not evidence of safety.** A suite proves the change is safe only where a test exercises the changed path *for the right reason*. Check whether one does. Two recurring cases: the test mocks the very layer the change modified (auth, network, clock), and the build step strips types rather than checking them, so a type error never fails anything.

**Do not persist an unverified conclusion.** Nothing goes into memory, notes, a ticket, or a handoff until it has passed this phase. A plausible-but-wrong inference written down early gets read back later as established fact — including by you.
