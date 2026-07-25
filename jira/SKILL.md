---
name: jira
description: >
  Manage Jira issues, sprints, and epics with the jira CLI (ankitpokhrel/jira-cli).
  Trigger on: jira, jira-cli, ticket, issue key (e.g. PROJ-123), epic, sprint,
  transition/move ticket, comment on ticket, assign ticket, JQL, create bug/story,
  "what's on my board", "my open issues". Use when the user wants to find, read,
  create, update, transition, comment on, assign, or link Jira work items — or
  list sprints/epics — via CLI. Do not use for Todoist, GitHub Issues, Linear, or
  generic project planning with no Jira involvement.
license: MIT
compatibility: "Requires jira CLI (https://github.com/ankitpokhrel/jira-cli) authenticated via `jira init`. Optional: jq, pandoc (gfm→jira)."
metadata:
  audience: developers
  workflow: project-management
  tools: "jira, jq, pandoc"
---

# Jira CLI

Bridge natural language to `jira` (jira-cli). Portable across users, projects, Cloud/Server/DC — never hardcode project keys, usernames, servers, or board IDs.

Work phases in order for each request. Skip only phases marked optional when their precondition is unmet.

## Prerequisites (fail fast)

```bash
command -v jira >/dev/null || { echo "jira CLI missing — install ankitpokhrel/jira-cli"; exit 1; }
jira me >/dev/null 2>&1 || { echo "jira not authenticated — run: jira init"; exit 1; }
```

On failure: report the exact fix (`brew install jira-cli` / `jira init`) and STOP. Do not invent issue keys or statuses.

Optional tools: `jq` (JSON field extract), `pandoc` (Markdown→Jira wiki for descriptions/comments). If missing, prefer `--plain` text or pass simple plain text bodies.

## Phase 1 — Resolve context

Establish **active issue key**, **project**, and **acting user** before writes.

1. **Issue key** — Prefer explicit key in the user message (`[A-Z][A-Z0-9]+-\d+`). Else parse current git branch (`feat/PROJ-123-…`, `PROJ-123-…`). Else search (Phase 2). Never invent keys.
2. **Project** — Explicit `-p KEY` / user text wins. Else default from config (`jira` uses `~/.config/.jira/.config.yml`, override with `JIRA_CONFIG_FILE`). For another project always pass `-p KEY` or JQL `project = KEY`.
3. **User** — `ME=$(jira me)` for "me" / "my". Assignees accept email or exact display name; self-assign: `jira issue assign KEY "$(jira me)"`.
4. **Session memory (optional)** — If a memory tool exists, read/write active key as `JIRA_ACTIVE_KEY`. If none, keep the key in conversation only. Do not require serena/openmemory.

Completion: you can name the target key and/or project, or you are about to search with an explicit JQL/filter plan.

## Phase 2 — Read (prefer structured output)

| Goal | Command |
|------|---------|
| View one issue | `jira issue view KEY --plain` (human) or `jira issue view KEY --raw` (JSON) |
| List / search | `jira issue list [flags] --plain` or `--raw` |
| My open work | `jira issue list -a"$(jira me)" -s~Done --plain --columns key,status,summary,priority` |
| Recent | `jira issue list --history --plain` |
| Cross-project JQL | `jira issue list -q'project IS NOT EMPTY AND …' --plain` |
| Sprint issues | `jira sprint list --current --plain` (needs board in config) |
| Epics | `jira epic list --table --plain` |

**Rules**
- Use `--plain` or `--raw` in agents — never the interactive TUI.
- There is **no** `--output json`. JSON is `--raw`.
- Default list is **project-scoped** to config project. Broaden with `-p` or `-q`.
- Paginate: `--paginate 0:50` (max 100/page).
- With `--raw` + `jq`, extract only needed fields. List items look like `{key, fields:{summary,status:{name},assignee:{displayName},issueType:{name},…}}`. View `--raw` uses standard Jira API issue JSON (`fields.status.name`, etc.).
- Do not dump full JSON into chat.

Common list flags: `-tType` `-sStatus` (repeatable; `-s~Done` = not Done) `-aAssignee` `-rReporter` `-yPriority` `-lLabel` `-q'JQL'` `--updated week`.

Deep JQL: load `references/jql.md` only if needed.

## Phase 3 — Write (confirm first)

**Confirm with the user before any create, edit, comment, assign, transition, delete, or bulk change.** One confirmation can cover a stated batch. Reads need no confirmation.

Always pass non-interactive flags where available (`--no-input` on create/edit/comment).

| Action | Command |
|--------|---------|
| Create | `jira issue create -tTYPE -s"Summary" -b"Body" --no-input` (`-pKEY` if not default) |
| Edit | `jira issue edit KEY -s"…" -b"…" --no-input` |
| Comment | `jira issue comment add KEY "body"` or `--template -` / `--template FILE` |
| Assign | `jira issue assign KEY "email-or-name"` or `KEY "$(jira me)"` · unassign: `KEY x` |
| Transition | `jira issue move KEY "State Name"` |
| Delete | `jira issue delete KEY` — extra explicit confirm |

### Formatting (descriptions / comments)

Jira wiki ≠ Markdown. If body has headings, lists, or code and `pandoc` exists:

```bash
body=$(printf '%s\n' "$MARKDOWN" | pandoc -f gfm -t jira)
jira issue comment add KEY "$body" --no-input
# or: printf '%s\n' "$body" | jira issue comment add KEY --template -
```

Else use short plain text (no reliance on MD rendering). Details: `references/formatting.md`.

### Transitions (no `--list` flag)

`jira issue move` has **no** `--list`. Target state is the **transition name** for that workflow (instance-specific).

1. Read current status: `jira issue view KEY --plain` (or `--raw` → `.fields.status.name`).
2. Prefer the exact state name the user asked for (quote spaces: `"In Progress"`).
3. On error, show the CLI error, suggest common names (`In Progress`, `Done`, `To Do`, `Backlog`) or ask the user for the exact workflow transition — do not invent transition IDs.
4. Optional: comment while moving: `jira issue move KEY "Done" --comment "…"`.

Details: `references/transitions.md`.

## Phase 4 — Report

After each mutating command: state key, action, new status/assignee if known. On failure: paste the CLI error, what you tried, and the next safe step. Never claim success without a successful command exit.

## Anti-patterns

- Inventing issue keys, projects, or statuses
- Interactive TUI (`jira issue list` without `--plain`/`--raw`)
- `jira issue move KEY --list` (invalid flag)
- `--output json` (use `--raw`)
- Hardcoding one company's project/board/username into commands
- Bulk edit/delete without confirmation
- Dumping raw multi-issue JSON into the user chat

## Examples

**User:** "my open tickets"
→ `jira issue list -a"$(jira me)" -s~Done --plain --columns key,status,summary,priority --paginate 0:50`

**User:** "show ACME-42"
→ `jira issue view ACME-42 --plain`

**User:** "comment on ACME-42: fixed in abc123" (after confirm)
→ pandoc (if needed) then `jira issue comment add ACME-42 "…" --no-input`

**User:** "move ACME-42 to In Progress" (after confirm)
→ `jira issue move ACME-42 "In Progress"`

**User:** "bugs in project OPS filed by me last week"
→ `jira issue list -pOPS -tBug -r"$(jira me)" --created week --plain --columns key,status,summary`

More: `references/examples.md`.
