# Session Note templates

Load when composing Phase E. Apply Concision. No Task Matrix.

## Create (save #1)

```markdown
---
title: <Descriptive Title>
date: <YYYY-MM-DD HH:MM:SS>
tags: [<note-key-lowercase-when-issue>]
---

# <Note Key> | <Title>

> **BLUF:** <1–2 sentences, current truth>

## Executive Summary & Key Outcomes

- **Primary Goal:** …
- **Result:** …
- **Core Decision:** …

## Key Findings & Invariants

| Category | Finding | Impact/Next |
|----------|---------|-------------|
| … | … | … |

## Visual

<!-- Optional: fenced d2/mermaid and/or metric tables. Omit section if N/A. -->

<details>
<summary>Deep Context</summary>

- Files, commands, logs for this create session only.

</details>

## Related

- [[journals/daily/YYYY_MM_DD|<Daily title>]]
<!-- Optional real wikilinks only; never invent titles -->
```

**Wikilink syntax — resolve by path, not title:** zk resolves `[[...]]` by filename/path,
not by note title (title-text-only links produce dead links that goto-definition and
`zk list --broken-links` will flag). Always write `[[relative/path/without/extension|Display Title]]`,
never `[[Display Title]]` alone. Get the exact path from a source already resolved this run
(Phase C/D/H's `zk new`/`zk daily` output, or `zk list --format link -m "<query>"` to confirm) —
never hand-guess a slug or title text into a link target.

Rules on create:

- Issue-key Note Key → include it in `tags` (lowercase).
- Slug Note Key → do **not** invent an issue tag.
- **No** `## Update:` section.
- Deep Context is top-level under the Living Head, then **frozen**.

## Update (save #2+)

1. **Replace** the entire Living Head (frontmatter through Visual; keep Related current).
2. **Leave untouched:** frozen create Deep Context and every prior `## Update:` body.
3. **Append** one new delta at the bottom:

```markdown
## Update: YYYY-MM-DD

- <what this session did / changed — delta only>
- <optional one-liner session intent>
- <new fences if historical; not a second full findings table>

<details>
<summary>Deep Context (this session)</summary>

- Files, commands, logs for this session only.

</details>
```

## Forbidden in either template

- Task Matrix / standing task checklist section
- Base64 embeds, separate asset writes from save-zk
- Second full Key Findings table inside an Update
- Invented `[[wikilinks]]`
- Title-only `[[wikilinks]]` (e.g. `[[Some Note Title]]`) — always `[[path|Title]]`
