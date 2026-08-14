# Inline placement in a live Hunk session

[Hunk](https://hunk.dev) is a terminal diff reviewer whose live sessions accept agent-authored inline notes. When one is open on the change under review, findings can sit beside the code instead of only in a report.

**This file covers only the review-specific policy — when to place, what to place, and how to degrade.** For the CLI itself — session selection, navigation, the full comment command surface, error strings — use the `hunk-review` skill, which ships with Hunk and is generated from its source, so it never drifts from the installed version. Do not restate its commands here or guess at flags; load it.

## The constraint that shapes everything

Hunk notes are **hunk-anchored**. Every note needs a file path plus exactly one line or hunk target, and the file must be in the loaded review — a file outside it is refused.

There is **no review-body surface**. Hunk has no equivalent of a pull request's review body.

So these never anchor, and belong in the terminal report regardless of whether a session is open:

- The preflight gate table.
- The non-findings block.
- Whole-change findings — a false premise, a stale dependency claim, an acceptance criterion nothing implements.
- Findings whose evidence lives in a file the change did not touch. The unreachable-secure-default case is the common one: the overriding config layer is usually not in the diff.

**The terminal report is always emitted in full.** Inline notes are an addition to it, never a substitute — a user who scrolled past a hunk must still get the finding.

## Partition before submitting

Batch application validates the **entire batch** before mutating the session. One finding aimed at a file outside the review rejects every other finding with it.

So: read the session's file and hunk structure first, then split the findings.

1. Detect the session for this repo. Confirm it is loaded on the change you actually reviewed — a session open on a different branch or commit is not the same review.
2. Read its file and hunk structure. Do **not** pull the raw patch text; you have already read the code in Phase 4 and it only inflates context.
3. Anchorable = the finding's file appears in that structure. Everything else stays report-only.
4. Submit the anchorable set as **one batch**, not one call per finding.

If the batch is still rejected, report the error and fall back to the terminal report. Do not retry by dropping findings one at a time until something sticks.

## Mapping a finding to a note

| Finding field | Note field |
|---|---|
| Severity + pillar | Prefix on the summary — `[High · Correctness] …` |
| Claim | `summary` — keep it a real sentence; it is the list view and the fallback |
| Evidence + failure scenario + fix | `rationale` |
| — | `author` — label every note `rigorous-review` so the user can list and clear them as a set |
| Location | the file plus the new-side line, old-side line, or hunk number |

Anchor to the **new** side unless the finding is specifically about removed code.

Focus the viewport at most once, on the highest-severity finding. Focusing repeatedly yanks the user's view around.

Tell the user afterwards how many notes were placed, how many were report-only and why, and that the notes are theirs to clear.

## Session states and how to degrade

Never let any of these stop the review. The report is the deliverable; inline placement is a bonus.

| State | How it presents | Do |
|---|---|---|
| Hunk not installed | the binary is absent | Say nothing. Terminal report only. |
| No session for this repo | non-zero exit, "no active session matches" | Report normally. Offer to place notes if they open Hunk on this change. |
| Session exists but the daemon is unreachable | "no active sessions" while Hunk is visibly running | A sandbox is blocking loopback. Retry with escalated permission — do not conclude there is no session. |
| Several sessions on one repo | "multiple active sessions match" | Ask which; do not guess. |
| Session loaded on other content | its file list does not overlap the reviewed diff | **Ask before reloading.** Reloading replaces what the user is reading. Default to report-only. |
| Session matches | clean exit, files overlap | Partition and submit one batch. |

Two detection traps:

- **Branch on the exit code, not the output.** The JSON flag does not produce JSON on the error path — it prints a plain-text message, so a parser will throw on the very case you are testing for.
- **A live session is not proof of the right content.** Check the file list against the diff you reviewed before placing anything.

## Do not

- Reload, navigate, or clear anything without being asked — the session is the user's workspace, not yours.
- Launch the TUI. Hunk's interactive commands belong to the user; agents drive live sessions only.
- Place a note you would not have put in the report. A surface that is cheap to write into is not a reason to lower the bar — the false-positive cost is the same.
- Suppress a finding from the report because it was placed inline.
