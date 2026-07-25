# WCAG contrast reference (load on demand)

Source of truth for thresholds used by this skill. Prefer this file over memory when
large-text, non-text UI, or AAA level is disputed.

## Relative luminance and ratio

WCAG 2.x contrast ratio for two relative luminances L1 (lighter) and L2 (darker):

```
(L1 + 0.05) / (L2 + 0.05)
```

This skill obtains L via `pastel format luminance <color>` and computes the ratio in
`main.py contrast`. Range is 1:1 (identical) to 21:1 (black on white).

## Text contrast (SC 1.4.3 Contrast Minimum / 1.4.6 Enhanced)

| Content | AA min | AAA min |
|---------|--------|---------|
| Normal text | 4.5:1 | 7:1 |
| Large text | 3:1 | 4.5:1 |

**Large text** (WCAG): at least 18pt (typically 24px) regular, or 14pt (typically 18.66px)
bold. UI that is not large stays on the normal-text row.

Pass `--large-text` to `main.py` when the large-text row applies.

## Non-text contrast (SC 1.4.11)

UI components and graphical objects needed to understand content: **3:1** against adjacent
colors. Skill default for "dimmed but still a control" follows this floor unless the user
only cares about decoration.

## Skill policy defaults

| Role | Default min | Rationale |
|------|-------------|-----------|
| Body / labels / code | 4.5:1 | AA normal text |
| Prefer when cheap | 7:1 | AAA normal text |
| Dimmed inactive text | >= 3:1 and < active ratio | Legible hierarchy |
| Icons / borders as UI | 3:1 | SC 1.4.11 |

## What pastel does and does not do

| Need | Tool |
|------|------|
| Black or white readable fg for a bg | `pastel textcolor` / `main.py textcolor` |
| Perceptual mix, lighten, darken | `pastel mix|lighten|darken` |
| WCAG contrast **ratio** | **`main.py contrast` only** — pastel has no `contrast` subcommand |
| Auto repair to a min ratio | `main.py fix` |

## Colorblind simulation (optional)

Not a substitute for contrast ratios. When the user asks about CVD:

```bash
pastel colorblind deuteranopia '<color>' | pastel format hex
pastel colorblind protanopia '<color>' | pastel format hex
pastel colorblind tritanopia '<color>' | pastel format hex
```

Still re-check contrast of the simulated pair if you are designing for CVD + WCAG together.

## Delivery checklist

1. Measured ratio present for every shipped pair.
2. Level (AA/AAA/fail) matches the role row above.
3. No claim of pass without a `main.py` JSON result from the current turn.
