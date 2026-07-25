# Jira body formatting (load on demand)

Cloud/Server wiki markup differs from Markdown. Agents should author Markdown, then convert when structure matters.

## When to convert

| Body | Action |
|------|--------|
| One short sentence, no structure | Pass plain text; skip pandoc |
| Headings, lists, links, code, tables | `pandoc -f gfm -t jira` |
| pandoc missing | Plain text only; say formatting may be flat |

## Convert

```bash
body=$(printf '%s\n' "$MARKDOWN" | pandoc -f gfm -t jira)
```

Prefer `gfm` over bare `markdown` for fenced code and strikethrough.

## Apply

```bash
# comment
jira issue comment add KEY "$body" --no-input
printf '%s\n' "$body" | jira issue comment add KEY --template -

# description on create/edit
jira issue create -tTask -s"Summary" -b"$body" --no-input
jira issue edit KEY -b"$body" --no-input
printf '%s\n' "$body" | jira issue edit KEY --template - --no-input
```

`--template -` reads stdin. Positional comment body wins over `--template` if both given.

## Quick wiki cheatsheet (if writing wiki directly)

```text
h1. Heading
* bold* _italic_
* bullet
# numbered
{code}snippet{code}
[link text|https://example.com]
```

Do not assume Markdown (`**bold**`, `# heading`) renders correctly in Jira without conversion.
