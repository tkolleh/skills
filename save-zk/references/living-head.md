# Living Head boundaries

The Living Head is the only region a save may **fully replace** so the top of the note always reflects current truth.

## May replace every run

1. YAML frontmatter: `title`, `date`, `tags` (keep/ensure issue-key tag when Note Key is an issue id)
2. `# <Note Key> | <Title>`
3. `> **BLUF:** …` (Living BLUF — five-second entry point)
4. **Executive Summary & Key Outcomes** (Primary Goal / Result / Core Decision)
5. **Key Findings & Invariants** — markdown **table only** (Category | Finding | Impact/Next); full table replaced each save
6. **Visual** (optional) — current `d2`/`mermaid` fences and/or metric tables; omit or clear when N/A
7. **Related** links list (refresh to real targets; Daily link required when Daily resolved)

## Must not touch

| Region | Rule |
|--------|------|
| Create-time Deep Context `<details>` | Frozen after first write |
| Prior `## Update: YYYY-MM-DD` bodies | Never edit, delete, or reorder |
| Other notebook files | Out of scope except Daily back-link attempt |
| Session source files | Never delete |

## Not in Living Head

- Task Matrix (not a template section at all)
- Full-file rewrite
- Merging sibling Session Notes

## Update append rules

- First create: **no** Update section
- Save #2+: append **one** new Update with **session delta** only — not a second full findings table
- New Deep Context for later sessions lives **inside** that Update's `<details>` only

## Safety if unsure

- Prefer append over replace outside Living Head
- Mark possible duplicates: `<!-- possibly duplicate — review -->`
