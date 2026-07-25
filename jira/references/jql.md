# JQL and list filters (load on demand)

Use CLI flags when they express the need. Drop to `-q'JQL'` for joins the flags cannot express. Default list scope is the **configured project**; cross-project queries need explicit `project` in JQL or `-p`.

## Flag → intent (jira-cli)

| Intent | Flag / pattern |
|--------|----------------|
| Type | `-tBug` `-tStory` `-tEpic` (names are instance-specific) |
| Status equals | `-s"In Progress"` |
| Status not | `-s~Done` |
| Assignee | `-a"$(jira me)"` or `-a"Jane Doe"` · unassigned: `-ax` |
| Reporter | `-r"$(jira me)"` |
| Priority | `-yHigh` |
| Label | `-lbackend` (repeatable) |
| Text text | positional: `jira issue list "login timeout" --plain` |
| Created/updated | `--created week` `--updated -7d` `--created-after 2026-01-01` |
| Watched / recent | `-w` / `--history` |
| Parent / epic child | `-P PARENT-KEY` |
| Raw JQL | `-q'assignee = currentUser() AND sprint in openSprints()'` |
| Pagination | `--paginate 0:50` (max 100 per page) |

## JQL snippets (portable)

Prefer `currentUser()` in JQL over hardcoding usernames.

```text
assignee = currentUser() AND resolution = Unresolved
assignee = currentUser() AND status != Done ORDER BY updated DESC
reporter = currentUser() AND created >= -7d
project = OPS AND issuetype = Bug AND status = "In Progress"
text ~ "payment retry" AND project = BILL
sprint in openSprints() AND assignee = currentUser()
filter = "My Open Bugs"
project IS NOT EMPTY AND updated >= -1d
key = PROJ-123
```

## Multi-project / multi-user

- Another project: `jira issue list -pOTHER --plain …` or `-q'project = OTHER AND …'`.
- All accessible projects: `-q'project IS NOT EMPTY AND …'` (can be slow — tighten filters).
- Someone else's queue: `-a"Exact Display Name"` or email; do not guess.
- Config default user is whatever `jira me` returns after `jira init` — never embed a personal login in skill text.

## Output discipline

```bash
jira issue list -a"$(jira me)" -s~Done --plain --columns key,status,summary,priority --paginate 0:50
jira issue list -q'key = PROJ-123' --raw | jq '.[0] | {key, summary: .fields.summary, status: .fields.status.name, assignee: .fields.assignee.displayName}'
```

No `--output json`. JSON = `--raw`.
