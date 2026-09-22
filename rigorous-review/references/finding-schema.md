# Finding schema

Every finding carries all eight fields. A finding missing any field is not ready to report — either complete it or drop it.

| Field | Rule |
|---|---|
| **Severity** | `Critical` / `High` / `Medium` / `Low`. See the ladder below. |
| **Pillar** | Which of the seven pillars this violates. One only — pick the primary. |
| **Location** | `path/to/file.ext:LINE` or `:START-END`. Either diff-anchored or PR-level — see below. |
| **Claim** | One sentence. What is wrong. Not what to do about it. |
| **Evidence** | The actual code, quoted. Copied from the file, not reconstructed from memory. |
| **Failure scenario** | Concrete inputs or state → the wrong outcome. Named values, not "could fail". |
| **Suggested fix** | The minimal change that resolves it. Often one line. |
| **Confidence** | `Confirmed` (verified, usually empirically) or `Plausible` (reasoned, not executed). |

## Two kinds of location

Most findings sit on a line the change touched. Some of the most serious ones do not: the change is correct in isolation and wrong because of what it now depends on. A schema that only admits diff lines cannot express those, so the reviewer either drops the finding or files it against the wrong line.

**Diff-anchored** — a line the change added or modified. The default. No extra justification needed.

**PR-level** — a line outside the diff. Allowed **only** with a **load-bearing clause**: one sentence stating what the change did that makes this previously-fine code newly decisive. Mark the location so the author can see it is not their line:

```markdown
**[High · Correctness] `src/runtime/dispatch.go:74` (outside the diff — PR-level)**
```

The load-bearing clause is what separates a real PR-level finding from a pre-existing complaint. It answers "why is this in *my* review?" Three shapes that qualify:

- **Newly reached** — the change routes a code path through this callee for the first time.
- **Newly load-bearing** — the callee was already reached, but the change makes a guarantee depend on behaviour it does not provide.
- **Newly frequent or newly scaled** — the change moves the call inside a loop, a batch, or a hot path, so a tolerable cost becomes a real one.

If you cannot write that clause, the finding is pre-existing. Move it to the non-findings block or drop it. Never use PR-level as a way to attach a wishlist to someone else's change.

## Severity ladder

Severity is about consequence, not about how interesting the bug is.

- **Critical** — Data loss or corruption, a security control that does not hold, or a break that reaches production users on the normal path.
- **High** — The feature does not do what it claims for a real user or role; silent wrong results; a failure mode with no error surfaced.
- **Medium** — Correct on the normal path, wrong or degraded on a reachable edge; missing test for a changed behavioural path.
- **Low** — Maintainability and readability costs with no behavioural consequence.

**Silent failures rank higher than loud ones.** An error the user sees is a bug; a wrong answer the user trusts is worse.

## Format

```markdown
**[High · Correctness] `src/filters/rowMatch.ts:42`**
The search predicate matches raw accessor values, so columns that render a
derived label are unsearchable.

```ts
const matches = row => String(row[col.accessor]).includes(query)
```

Searching "Approved" against a row whose `status` accessor holds `2` and whose
cell renders `Approved` returns no match. Four of the six columns named in the
acceptance criteria are affected, and the box shows an empty result rather than
an error — the user reads it as "no such record."

Fix: match against the rendered cell value, `col.render(row)`, falling back to
the accessor when no renderer is defined.

*Confidence: Confirmed — ran the exported predicate against fixture rows.*
```

Keep it in that order: header line, claim, evidence, failure scenario, fix, confidence. The author reads the header and the claim; everything after is there to be checked.

## The non-findings block

**Mandatory. Every review ends with it, including reviews with zero findings.**

Without it the author cannot distinguish "checked and clean" from "not checked", so they must re-review the change themselves — which is the whole cost the review was meant to remove.

```markdown
### Checked, no concern

- **Preflight** — install, typecheck, lint, unit, integration all exit 0 (table above).
- **Security** — new endpoint inherits the existing auth middleware; verified at
  `src/routes/index.ts:88`.
- **Edge cases** — empty and single-element inputs covered by the added tests.
- **Efficiency** — the added query is indexed on `(tenant_id, created_at)`.
```

Name what you checked and how you know. "Looks fine" is not a non-finding — it is an admission that the pillar was skipped.

If a pillar could not be checked, say that instead, and say why:

```markdown
- **Integration behaviour** — not verified; the suite requires credentials
  unavailable in this environment.
```

## Alignment with typed finding tools

Some runtimes expose a structured findings API rather than free markdown. The schema maps directly:

| This schema | Typed field |
|---|---|
| Location | `file`, `line` |
| Claim | `summary` (and a ≤60-char `short_summary`) |
| Failure scenario | `failure_scenario` |
| Pillar | `category` |
| Confidence | `verdict`: `Confirmed` → `CONFIRMED`, `Plausible` → `PLAUSIBLE` |

Evidence, severity, and the suggested fix have no typed slot — fold them into `summary` rather than dropping them. A PR-level finding keeps its real `file` and `line` — the out-of-diff ones — and carries the load-bearing clause at the front of `summary`, since the typed schema has no field for it. Do not relocate it to a diff line to make it anchor; that misdirects the author to code that is not the problem. When such a tool is available, emit through it *instead of* printing the findings as prose, not in addition.
