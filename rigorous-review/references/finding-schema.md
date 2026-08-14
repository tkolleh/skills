# Finding schema

Every finding carries all eight fields. A finding missing any field is not ready to report — either complete it or drop it.

| Field | Rule |
|---|---|
| **Severity** | `Critical` / `High` / `Medium` / `Low`. See the ladder below. |
| **Pillar** | Which of the seven pillars this violates. One only — pick the primary. |
| **Location** | `path/to/file.ext:LINE` or `:START-END`. Must be a line the change touched. |
| **Claim** | One sentence. What is wrong. Not what to do about it. |
| **Evidence** | The actual code, quoted. Copied from the file, not reconstructed from memory. |
| **Failure scenario** | Concrete inputs or state → the wrong outcome. Named values, not "could fail". |
| **Suggested fix** | The minimal change that resolves it. Often one line. |
| **Confidence** | `Confirmed` (verified, usually empirically) or `Plausible` (reasoned, not executed). |

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

Evidence, severity, and the suggested fix have no typed slot — fold them into `summary` rather than dropping them. When such a tool is available, emit through it *instead of* printing the findings as prose, not in addition.
