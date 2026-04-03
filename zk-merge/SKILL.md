---
name: zk-merge
description: "Consolidates Serena memories and task findings into a Zettelkasten note keyed to a Jira issue. Use when merging notes, archiving to zk, or capturing results of a Jira-linked work session. Never deletes or overwrites existing content."
license: MIT
compatibility: opencode
metadata:
  audience: developers
  tools: zk
---

# zk-merge

Collect context from common locations such as `.opencode/`, `AGENT_CONTEXT.md`, `.serena`, `docs/`, diagrams, and newly added markdown files. And tasks, diagrams, and Serena memories from the current project. The context **must** be relevant to recent changes. Then write them into a single well-organized Zettelkasten note keyed to a todo/issue tracker key e.g. Jira issue key.


## Step 1: Identify an issue Key

- Check the user's message for a key matching `[A-Z]+-\d+` (e.g. `PROJ-2264`, `ACME-7707`).
- Check recent commit messages for the same pattern.
- If none provided, check the current git branch:

```bash
git rev-parse --abbrev-ref HEAD
```

Parse the branch name with the same pattern. If a key is found, confirm it with the user before continuing. If none found, ask the user to provide one.


## Step 2: Find the Project Root

```bash
git rev-parse --show-toplevel
```

All `.opencode/` and `.serena/` reads are relative to this root. Call this `$PROJECT_ROOT`.


## Step 3: Check for an Existing zk Note

```bash
find "$ZK_NOTEBOOK_DIR/projects" -name "<JIRA-KEY>_*.md" 2>/dev/null
```

- **Found** → note the path; you will **append** to it.
- **Not found** → you will **create** a new note.


### 4a. Parse content

Summarize each file found — extract what matters for future reference, not a verbatim copy.

For diagrams:
- `.d2` → embed in fenced block
- Mermaid (`.mmd`, inline in `.md`) → embed in fenced block
- Binary images (`.png`, `.svg`) → reference by filename and original relative path only

### 4b. Serena memories (read in priority order)


| Path | Type | Priority |
|------|------|----------|
| `~/.serena/memories/**/*.md` | General learnings, cross-project patterns | Highest |
| `$PROJECT_ROOT/.serena/memories/**/*.md` | Project-specific context | Medium |


For each memory file, note the filename (it reflects the topic), extract points relevant to this Jira issue, and skip files clearly unrelated to the task.


## Step 5: Compose the Note

### New note structure

```markdown
---
title: <Descriptive Title>
date: <MM-DD-YYYY> <HH:MM:SS>
tags: [<issue-key-lowercase>]
---

# <Issue-Key> | <Descriptive Title>

## Context

<Synthesized from findings — key architectural facts, contracts, infra notes>

## Tasks

### <Task Name>

**Status:**
**Objective:**
**Complexity:**

## Diagrams

<Embed diagram source blocks or reference binary files by path>

## Summary

- <Key finding or decision 1>
- <Key finding or decision 2>
- <Key finding or decision 3>
```

### Append structure (existing note)

Add at the **bottom** of the file:

```markdown

---

## Update: <YYYY-MM-DD>

### Context

<New context items not already present in the note>

### Diagrams

<New diagrams added this session>

### Session Summary

- <general insights>
- <What changed or was decided this session — 3-5 bullets>
```


## Step 6: Write the Note

### Creating a new note

Use the existing `jira` zk group:

```bash
zk new --group jira --extra jirakey="<JIRA-KEY>" "<Descriptive Title>"
```

This creates `$ZK_NOTEBOOK_DIR/projects/<Issue-KEY>_<slug-title>.md` using the `jira.md` template.
After `zk new` creates the file, write your composed content into it (replacing the empty `{{content}}` placeholder).

### Appending to an existing note

Append the composed update section to the bottom of the existing file. Do not touch any content above.


## Safety Rules

These are non-negotiable:

- **Never overwrite** existing note content — only append.
- **Never delete** any file (.opencode, .serena, or zk note).
- **Never truncate** a note that already exists.
- If content might already be present in the note, add it with `<!-- possibly duplicate — review -->` rather than skipping it.


## Content Formatting

- **Tables** for task/subtask lists — more scannable than prose
- **Bold** key decisions so they stand out when skimming
- **ISO dates** (`YYYY-MM-DD`) for all timestamps in the body; use the jira template's `format-date` in frontmatter
- **Fenced code blocks** for diagrams (never inline)
- **Short bullets** for memory items — one insight per bullet
