# acli jira (load when the active instance requires OAuth)

`acli` is Atlassian's official CLI (https://acli.atlassian.com) — a different tool from
jira-cli, with different command grammar, for Jira Cloud tenants that enforce OAuth 2.0
and reject classic API-token Basic/Bearer auth. Never guess acli flags by analogy to
jira-cli; the shapes below are verified against `acli jira <command> --help`.

Placeholders: `KEY`, `PROJ`, `TYPE` — substitute from user context. Never ship real
project keys, tenant hostnames, or personal emails/usernames in skill text.

## Prerequisites (fail fast)

```bash
command -v acli >/dev/null || { echo "acli missing — install from https://acli.atlassian.com"; exit 1; }
acli jira auth status >/dev/null 2>&1 || { echo "acli not authenticated — run: acli auth login && acli jira auth login"; exit 1; }
```

Auth is two separate steps: `acli auth login` (global Atlassian profile) then
`acli jira auth login` (per-app grant for Jira specifically). Do not re-run either if
`acli jira auth status` already shows an authenticated account — treat re-auth as a
user-requested action, not something to do proactively.

If multiple accounts are logged in, `acli jira auth switch` changes the active one —
confirm with the user before switching if a request could plausibly target either.

## Key structural difference from jira-cli

jira-cli takes the issue key **positionally** (`jira issue view KEY`). acli's `workitem`
subcommands take it as a **named flag that accepts a comma-separated list, a JQL query,
or a filter ID** — `--key`, `--jql`, or `--filter` are interchangeable inputs across
create/edit/assign/transition/delete. This makes acli write commands **bulk-oriented by
default**: `acli jira workitem transition --jql "..." --status "Done"` can move every
issue matching a query in one call. Treat any acli write that uses `--jql` or `--filter`
(instead of a specific `--key`) as a bulk change requiring explicit confirmation of the
query/filter and its expected match count — check with `--count` or a `search` first
when the blast radius isn't obvious.

## Phase 2 equivalent — Read

| Goal | Command |
|------|---------|
| Auth / identity | `acli jira auth status` |
| Search (JQL) | `acli jira workitem search --jql "..." --limit N` (human-readable table) |
| Search (JSON) | `acli jira workitem search --jql "..." --json` |
| Search (CSV) | `acli jira workitem search --jql "..." --csv` |
| Count only | `acli jira workitem search --jql "..." --count` |
| Paginate all | `acli jira workitem search --jql "..." --paginate` |
| By saved filter | `acli jira workitem search --filter FILTER_ID` |
| Open in browser | `acli jira workitem search --jql "..." --web` |
| View one item | `acli jira workitem view KEY` (key is positional here, unlike other workitem subcommands) |
| View one item (JSON) | `acli jira workitem view KEY --json` |
| Specific fields only | `acli jira workitem view KEY --fields summary,comment` |
| List comments | `acli jira workitem comment list KEY` |
| Boards | `acli jira board search` / `acli jira board view BOARD_ID` |
| Sprints on a board | `acli jira board list-sprints BOARD_ID` |
| Work items in a sprint | `acli jira sprint list-workitems SPRINT_ID` |
| Projects visible to user | `acli jira project list` |

**Rules**
- Default search field set is `issuetype,key,assignee,priority,status,summary` — override with `-f/--fields` only when the user needs specific fields.
- `--json` is the JSON flag here (not `--raw` as in jira-cli) — do not mix the two tools' flag names.
- Do not dump full JSON into chat; extract with `jq` if needed.

## Phase 3 equivalent — Write (confirm first, extra caution on JQL/filter targeting)

**Confirm with the user before any create, edit, comment, assign, transition, or delete.**
For any write using `--jql` or `--filter` (as opposed to an explicit `--key`), confirm the
**exact query and expected scope** — these can affect many issues in one call. `-y/--yes`
suppresses acli's own confirmation prompt; do not pass it until the user has already
confirmed in this conversation.

| Action | Command |
|--------|---------|
| Create | `acli jira workitem create --project PROJ --type TYPE --summary "..." --description "..."` |
| Create under a parent | add `--parent PARENT_KEY` |
| Edit (by key) | `acli jira workitem edit --key "KEY-1,KEY-2" --summary "..."` |
| Edit (by JQL — bulk) | `acli jira workitem edit --jql "project = PROJ AND ..." --assignee "user@example.com" --yes` |
| Comment | `acli jira workitem comment create --key KEY --body "..."` (also accepts `--jql`/`--filter` — bulk caution applies; `--body-file` for longer bodies) |
| Assign | `acli jira workitem assign --key KEY --assignee "user@example.com"` · self: `--assignee "@me"` · default assignee: `--assignee "default"` · unassign: `--remove-assignee` |
| Transition | `acli jira workitem transition --key KEY --status "State Name"` |
| Transition (bulk by JQL) | `acli jira workitem transition --jql "..." --status "Done" --yes` |
| Delete | `acli jira workitem delete --key KEY` — extra explicit confirm, doubly so if `--jql`/`--filter` scoped |

### Formatting

acli's `create`/`edit` accept `--description` as plain text or Atlassian Document Format
(ADF), or `--description-file` to read from a file. There is no jira-cli-style
`--template -` stdin flag; use `--description-file` for longer bodies instead of shell
quoting gymnastics. Markdown is not natively rendered — treat the same way as jira-cli's
"convert with pandoc if structure matters" guidance in `formatting.md`, targeting ADF/plain
text as the output instead of Jira wiki markup.

### Transitions

`--status` takes the workflow's transition/status name string, same caveat as jira-cli:
not a global enum, not something to invent. On failure, surface the error and ask the user
for the exact name shown in the Jira UI rather than guessing synonyms.

## Confirmation matrix

| Action | Confirm? |
|--------|----------|
| `auth status`, `search`, `view`, `comment list`, `board`/`sprint`/`project` reads | No |
| `create`, `edit` (by `--key`), `comment create`, `assign`, `transition` (by `--key`) | Yes |
| `edit`/`transition`/`assign`/`delete` scoped by `--jql` or `--filter` | Yes, explicit — confirm the query and expected match count |
| `delete` (any form) | Yes, explicit |

## Anti-patterns specific to acli

- Assuming `--raw` (jira-cli) works here — it's `--json`.
- Assuming the issue key is positional on `workitem search`/`create`/`edit`/`assign`/`transition`/`delete` — it's a named `--key` flag on all of those (only `workitem view` takes it positionally).
- Running a `--jql`/`--filter`-scoped write without checking scope first (`--count` or a plain `search`).
- Re-running `acli auth login` / `acli jira auth login` when `acli jira auth status` already shows an authenticated session.
- Guessing a flag name instead of running `acli jira <command> --help` first — this reference was built from verified `--help` output, but acli's surface is larger than what's captured here (e.g. `attachment`, `link`, `watcher`, `dashboard`, `field`, `filter`, `clone`, `archive` subcommands exist and aren't detailed above); check `--help` before using anything not listed here.
