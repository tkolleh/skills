---
name: jira
description: Manage Jira issues, sprints, and epics using the Jira CLI. Handles context retention and Markdown-to-JiraWiki formatting.
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: project-management
  tools:
    - jira
    - jq
    - pandoc
    - serena
---

## What I do
I act as an intelligent bridge between natural language and the Jira CLI. I allow you to find, read, update, transition, and comment on tickets. Crucially, I maintain state across conversation turns (remembering which ticket we are discussing) and ensure complex text is correctly formatted for Jira's rendering engine.

## When to use me
Use this skill when:
- You are asked to use Jira or jira-cli.
- You need to **find** a ticket based on keywords, status, or assignee.
- You need to **read** the details of a specific issue.
- You need to **transition** a ticket (e.g., "Move this to Done").
- You need to **update** fields or **comment** on an issue.
- The user references "tickets," "issues," "epics," or "sprints."

## Instructions

### 1. Context Retrieval & Management

Before executing any Jira command, you must establish the "Active Issue."
* **Check Memory**: Query `serena` or `openmemory` for a `JIRA_ISSUE` node linked to the current session via `DISCUSSING`.
* **Check Environment**: Look for an issue key in the current git branch name (e.g., `feat/PROJ-123-login`).
* **Search**: If no context exists, use JQL to find the issue.
* **Persist**: Once an issue is identified/discussed, store it in memory immediately.
    * *Pattern*: `(Session) -[DISCUSSING]-> (JIRA_ISSUE {key: "PROJ-123"})`

### 2. Reading Issues (The JSON Rule)

**NEVER** use `jira issue view` directly, as the output is often unstructured text.
* **Command**: Use `jira issue list --raw` with a specific JQL query and JSON output.
* **Parsing**: Pipe the output to `jq` to extract exactly what you need.
    ```bash
    jira issue list -q "key = PROJ-123" --plain --output json | jq '.[0] | {key: .key, summary: .fields.summary, status: .fields.status.name, description: .fields.description}'
    ```

### 3. Transitions (Safety First)
Never guess a transition ID or name. Statuses are workflows, not just strings.
1.  **List Transitions**: `jira issue move PROJ-123 --list`
2.  **Execute**: Use the specific ID or exact name found in step 1.

### 4. Handling Text Formatting (Markdown vs. Wiki)

Jira uses a specific Wiki markup, not standard Markdown. When updating descriptions or comments:
* **Convert**: Use `pandoc` to convert the user's Markdown input into Jira-compatible syntax.
    ```bash
    echo "# Header\n- List item" | pandoc -f gfm -t jira
    ```
* **Apply**: Use the output string in your `jira` command.

## Best Practices

* **Precision JQL**: Avoid broad searches. Use `project = 'PROJ' AND text ~ 'search term'` to limit scope.
* **No Hallucinations**: Never invent issue keys (e.g., PROJ-000). If the key is unknown, search for it.
* **Privacy**: Do not dump full JSON payloads into the chat. Extract only relevant fields (Summary, Status, Assignee, Description) using `jq`.
* **Safety**: Ask for confirmation before destructive actions (deleting issues or bulk edits).

## Examples

### Search for a bug reported by a specific user

```bash
jira issue list -q "project = ACME AND reporter = currentUser() AND issuetype = Bug" --plain --output json | jq '.[] | .key + ": " + .fields.summary'

```

### Comment on the active issue (Context: PROJ-123)

```bash
# 1. Convert comment to Jira format
formatted_comment=$(echo "Fixed in commit \`a1b2c3d\`." | pandoc -f gfm -t jira)

# 2. Post comment
jira issue comment add PROJ-123 "$formatted_comment"

```

### Move a ticket to "Done"

```bash
# 1. Check available transitions
jira issue move PROJ-123 --list

# 2. Execute transition (assuming 'Done' is a valid transition)
jira issue move PROJ-123 "Done"

```
