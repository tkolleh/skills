---
name: zk-merge
description: "Summarizes current session consolidating memories, tasks, and key findings into a Zettelkasten note."
license: MIT
compatibility: opencode
metadata:
  audience: developers
  tools: "zk, gh, zk, serena, worktrunk, allium"
---

# zk-merge

## When to use

Use when the user asks to remove and/or close worktrees, merging notes, completing tasks, archiving to zk, or capturing results of an extended working session.

Collect context from common locations such as `.opencode/`, `AGENT_CONTEXT.md`, `.serena`, `docs/`, diagrams, and newly added markdown files. The context **must be relevant to recent completed work**. Write a summary to a single well-organized Zettelkasten note keyed to a issue tracker key e.g. Jira issue key, github issue id, or a session summary (<= 8 words).


## Step 1: Identify an issue key or summarize

## Step 2: Review memory and docs

Check serena memories, opencode memories, or other memories added during the session for relevant context. Review any new markdown files added to the project during the session, as well as any diagrams created or updated. Review any newly added allium files added.

## Step 3: Check for an Existing zk Note

```bash
find "$ZK_NOTEBOOK_DIR/projects" -name "<JIRA-KEY>_*.md" 2>/dev/null
```

- **Found** → note the path; you will **append** to it.
- **Not found** → you will **create** a new note.


## Step 4: Parse content

Summarize each file found — extract what matters for future reference, not a verbatim copy. For all diagrams, reference from assets directory with relative path, do not embed as base64 or inline.:
  - `.d2`
  - Mermaid
  - Binary images (`.png`, `.svg`)

Note that the memory filename reflects the topic.


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
