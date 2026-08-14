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
3. Drive it with fixtures drawn from the real domain — values from tests, seed data, or the ticket's acceptance criteria. Invented inputs invite "that would never happen."
4. Report the input → output table, not your interpretation of it.

Do not fabricate a table you did not produce. Where you cannot execute, say so and mark the finding `Plausible`.

## False-positive catalogue

Check every candidate finding against this list before it goes in the report. Anything matching is dropped or moved to non-findings.

- **Pre-existing** — the problem is on a line the change did not touch. Real, but not this PR's.
- **Compiler-catchable** — type errors, missing imports, formatting, unused symbols. The toolchain reports these better than you do; preflight already ran them.
- **Intentional** — the change in behaviour is the point of the PR, or is stated in the description or a linked ticket.
- **Explicitly silenced** — a suppression comment with a stated reason. Question a *missing* reason, not the suppression.
- **Unreachable** — a guard upstream makes the input impossible. Verify the guard; do not assume it.
- **Pedantic** — a naming or structure preference a senior engineer would not raise in a review.
- **Out of scope** — a genuine improvement to code the change did not touch.

## Two traps that survive careful review

**Green CI is not evidence of safety.** A suite proves the change is safe only where a test exercises the changed path *for the right reason*. Check whether one does. Two recurring cases: the test mocks the very layer the change modified (auth, network, clock), and the build step strips types rather than checking them, so a type error never fails anything.

**Do not persist an unverified conclusion.** Nothing goes into memory, notes, a ticket, or a handoff until it has passed this phase. A plausible-but-wrong inference written down early gets read back later as established fact — including by you.
