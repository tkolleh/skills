# Transitions and write safety (load on demand)

## Hard facts (jira-cli)

- Command: `jira issue move ISSUE-KEY STATE`
- Aliases: `transition`, `mv`
- **There is no `jira issue move --list`.** That flag does not exist (unknown flag error).
- `STATE` is a workflow **transition/status name** string for that issue's workflow — not a global enum, not a numeric ID you invent.
- Flags: `--comment "…"`, `-a assignee`, `-R resolution`, `--web`. No `--no-input` on move.

## Safe procedure

1. Confirm intent with the user (target key + target state).
2. Read current status: `jira issue view KEY --plain` or `--raw` → `.fields.status.name`.
3. Run: `jira issue move KEY "Exact State Name"`.
4. On success: re-view or trust CLI success message; report new state.
5. On failure: surface stderr. Typical causes: wrong name, no permission, transition unavailable from current status, required field on transition.

## Recovery when the name is wrong

1. Do not retry random synonyms in a loop.
2. Ask the user for the exact transition as shown in the Jira UI for that issue, **or** try one obvious quoted variant they used ("In Progress" vs "In progress") once.
3. Optional advanced (auth token already used by CLI; only if user wants): Jira REST  
   `GET /rest/api/2/issue/{KEY}/transitions` — parse `.transitions[].name`. Prefer documenting the ask-user path so the skill stays CLI-first and portable.

## Confirmation matrix

| Action | Confirm? |
|--------|----------|
| list / view / me / serverinfo | No |
| create / edit / comment / assign / move / link | Yes |
| delete / bulk change | Yes, explicit |

One user "yes" may cover a clearly listed batch (e.g. three named comments).

## Multi-project writes

Pass `-p PROJECT` on create when not using the config default. Issue keys already encode project (`OPS-9`); move/edit/comment take the key and do not need `-p` for routing, but list/create defaults still follow config project.
