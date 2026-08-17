# Decision table: <function/module name>

Model: `src/<path/to/Module>.elm`
Source: `<path/to/Source.ext>` (function `<name>`, starting line `<N>`)

See `../decision-table-methodology.md` for the full methodology this table follows.

## Coverage checklist

- [ ] Happy path
- [ ] Every branch/guard in the source
- [ ] Short-circuit behavior (if the source short-circuits)
- [ ] Boundary/empty cases (empty collections, zero/negative values, nulls/optionals, ties)
- [ ] Any previously-flagged known gap

## Fixtures

### Fixture: <short descriptive name>

**Input:** <concrete input values>

**Elm trace:** <branches/guards taken, resulting output>

**Source trace:** <branches/guards taken in the source, resulting output>

**Result:** AGREE | DIVERGE — <if diverge: which side looks correct and why, or "unresolved, filed as a finding">

---

<!-- repeat one "### Fixture" block per row -->

## Summary

- Fixtures traced: <N>
- Agreements: <N>
- Divergences: <N> — <one line each, or "none">
- Open findings: <N> — <one line each, or "none">
