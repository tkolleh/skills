# Worked examples (load on demand)

Placeholders: `KEY`, `PROJ`, names — substitute from user context / `jira me` / config. Never ship real company keys in skill text.

## Read

```bash
# Auth / identity
jira me

# Single issue
jira issue view KEY --plain
jira issue view KEY --raw | jq '{key, status: .fields.status.name, summary: .fields.summary, assignee: .fields.assignee.displayName}'

# My open issues in default project
jira issue list -a"$(jira me)" -s~Done --plain --columns key,status,summary,priority --paginate 0:50

# Another project
jira issue list -pPROJ -s"In Progress" --plain --columns key,assignee,summary

# JQL across projects
jira issue list -q'project IS NOT EMPTY AND assignee = currentUser() AND updated >= -3d' --plain --columns key,status,summary

# Current sprint (board must be configured)
jira sprint list --current --plain --columns key,status,summary,assignee
```

## Write (after user confirm)

```bash
# Create in default project
jira issue create -tTask -s"Renew TLS cert" -b"Expires Friday" --no-input

# Create in other project
jira issue create -pPROJ -tBug -s"Null deref on save" -yHigh -b"Steps…" --no-input

# Edit summary
jira issue edit KEY -s"Renew TLS cert (prod)" --no-input

# Comment with wiki conversion
md='Fixed in `abc1234`. **Please verify** on staging.'
body=$(printf '%s\n' "$md" | pandoc -f gfm -t jira)
jira issue comment add KEY "$body" --no-input

# Assign to self / other / unassign
jira issue assign KEY "$(jira me)"
jira issue assign KEY "Jane Doe"
jira issue assign KEY x

# Transition
jira issue move KEY "In Progress"
jira issue move KEY Done --comment "Shipped in 1.4.2"
```

## Branch → key

Branch `feat/PROJ-123-retry-backoff` → active key `PROJ-123` → `jira issue view PROJ-123 --plain`.

## Failure handling examples

- Missing CLI: tell user to install `ankitpokhrel/jira-cli`.
- `jira me` fails: `jira init` (or fix `JIRA_API_TOKEN` / config path).
- `unknown flag: --list` on move: skill bug — use status name only.
- Empty list: report empty; suggest broadening filter or wrong `-p`.
