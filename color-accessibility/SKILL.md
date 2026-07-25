---
name: color-accessibility
description: >-
  Trigger on: check contrast, WCAG contrast, accessible colors, readable text color,
  fix low-contrast, dimmed text color, palette accessibility, pastel color, textcolor
  for background, make this color readable, UI theme contrast, Neovim highlight contrast.
  Evaluate, fix, and generate accessible fg/bg pairs with the pastel CLI and
  color-accessibility/main.py (WCAG AA/AAA). Use whenever the user changes colors for
  UI, CSS, terminal, or editor themes — do not guess contrast; measure it.
license: MIT
compatibility: "pastel, python3"
metadata:
  audience: developers
  domain: color-accessibility
  version: "2.0.0"
  tools: "pastel, python3, main.py"
---

# Color Accessibility

Prove every fg/bg pair with math before shipping colors. pastel has **no** contrast
subcommand — use main.py in this skill directory for ratios; use pastel for
manipulation (textcolor, mix, darken, lighten, format).

## When to use / not use

- **Use:** contrast checks, picking text on a fill, fixing failing pairs, dimmed/inactive
  text, theme palette audit.
- **Do not use:** brand-only palette vibes with no readability ask; full diagram authoring
  (use diagram — it has its own contrast step).

Work phases **in order**. Do not skip. Do not invent ratios from memory.

## Prerequisites

```bash
pastel --version    # required on PATH
python3 color-accessibility/main.py --help
```

If pastel is missing: tell the user to install (brew install pastel or
cargo install pastel) and STOP.

Resolve main.py relative to this skill directory (or the path you loaded the skill from).

## Thresholds (default)

| Role | Min ratio | Notes |
|------|-----------|--------|
| Normal text / UI labels | **4.5:1** (AA) | Prefer **7:1** (AAA) when easy |
| Large text (>=18pt / 14pt bold) | **3:1** (AA) | Pass --large-text |
| Dimmed / inactive | Still >= **3:1** vs bg; **strictly below** active text ratio | Hierarchy without illegibility |

Deeper WCAG notes: load references/wcag.md only if large-text, non-text UI, or AAA is disputed.

## Phase 1 — Capture pairs

1. List every fg/bg (or fill/font-color) pair the user cares about as hex or named colors.
2. Completion: each pair has explicit fg and bg strings (no "something light gray").

## Phase 2 — Measure (required)

For each pair:

```bash
python3 main.py contrast --fg '<fg>' --bg '<bg>'
# large text:
python3 main.py contrast --fg '<fg>' --bg '<bg>' --large-text
```

- Exit 0 + "status":"success" -> meets default min.
- Exit 1 + "status":"fail" -> record ratio and continue to Phase 3.
- "status":"error" -> report reason and STOP (or fix input colors).

Optimal black/white fg for a background only:

```bash
python3 main.py textcolor --bg '<bg>'
# equivalent core: pastel textcolor '<bg>' | pastel format hex
```

Completion: every pair has a JSON result with ratio, level, passes_aa.

## Phase 3 — Fix failures

Do **not** hand-pick hex. Prefer:

```bash
python3 main.py fix --fg '<fg>' --bg '<bg>' --adjust auto --min-ratio 4.5
```

- auto: try pastel textcolor on bg first; else nudge fg lightness.
- Prefer the textcolor / high-ratio result (often black or white, frequently AAA).
  Do **not** scrape the nearest gray that barely clears 4.5:1 unless the user
  asked to preserve a gray look.
- --adjust fg|bg when the user freezes one side.
- Re-run contrast on the returned pair.fg / pair.bg.

Manual pastel knobs (when fix is wrong for the aesthetic):

```bash
pastel darken 0.1 '<color>' | pastel format hex
pastel lighten 0.15 '<color>' | pastel format hex
pastel desaturate 0.2 '<color>' | pastel format hex
```

Completion: every required pair passes_aa (or user explicitly accepted a documented exception).

## Phase 4 — Dimmed / mixed roles

Inactive text = mix fg toward bg in a perceptual space (default Lab):

```bash
python3 main.py mix-dim --fg '<active_fg>' --bg '<bg>' --fraction 0.6
# fraction = pastel --fraction = how much of the *base fg* is kept (0-1)
```

Then contrast the mixed color vs bg. If < 3:1, raise --fraction (keep more fg) or fix via Phase 3.

Completion: dim color hex + ratio; dim ratio < active ratio when both exist.

## Phase 5 — Deliver

1. Emit final hex pairs (and ratios) in the user's target format (CSS, Lua hl, JSON, table).
2. Cite measured ratios next to each pair (e.g. 12.8:1 AAA).
3. Never claim WCAG pass without a Phase 2 (or post-fix) main.py result in this turn.

Completion: user-ready snippet + no unverified pairs.

## Commands cheat sheet

| Goal | Command |
|------|---------|
| Ratio | python3 main.py contrast --fg ... --bg ... |
| Best fg | python3 main.py textcolor --bg ... |
| Auto-fix | python3 main.py fix --fg ... --bg ... --adjust auto |
| Dim mix | python3 main.py mix-dim --fg ... --bg ... --fraction 0.6 |
| Hex normalize | pastel format hex '<color>' |

## Edge cases

- **Transparent / alpha:** flatten onto the real background first; do not contrast alpha hex alone.
- **Gradient text:** check against the lightest and darkest stops under the glyphs.
- **Syntax themes:** active vs comment/dimmed both need Phase 2; comments still >= 3:1.
- **diagram skill:** for D2 class fills, diagram/main.py check-contrast is enough inside diagram work.

## Non-examples (do not load this skill alone)

- "Draw a C4 diagram of our services" -> diagram
- "What is the complementary hue of blue?" -> plain pastel complement is enough unless readability is in scope
