# Session Context, lookup, and Daily back-link

## Session Context (Phase B inputs)

**In-scope (this session):**

- Serena / OpenCode / agent memories created or updated in-session
- Markdown or allium files touched this session
- New or updated diagram/chart source (`.d2`, mermaid fences, metric tables)
- Decisions and outcomes stated in-session
- Branch name, open PR, tracker issue metadata when available

**Out of scope:**

- Whole-repo `docs/` crawl
- Secrets, tokens, credentials, PII
- Unrelated historical notes not referenced this session

Mark each source **present** or **unavailable**. Never abort the run because one source is missing.

## Note Lookup (Phase C)

1. Prefer tag search on the issue key (frontmatter `tags`).
2. Fallback: filename contains the key under the Session Note Location (typically `$ZK_NOTEBOOK_DIR/projects`).
3. Hit table:
   - **0** → create
   - **1** → update that path
   - **>1** → update **most recently modified**; do not ask; do not merge files
4. Issue-key identity requires the key as a frontmatter tag on write.

Example probes (adapt to local zk version):

```bash
# Tag-first (preferred when supported)
zk list --tag "<issue-key-lowercase>" -f path 2>/dev/null

# Filename fallback
find "$ZK_NOTEBOOK_DIR/projects" -name "*<KEY>*" -type f 2>/dev/null
```

## Create plumbing (Phase H)

- One **Session Note Location** / zk group for all keys — key-agnostic (Jira, GitHub, or slug).
- Prefer `zk new` parameterized with the human Note Key + title.
- If `zk new` fails: write markdown under the notebook projects path; report **fallback** in Phase I.

## Daily Note (Phases D + H)

```bash
zk daily
```

- Resolve path only via `zk daily` (or mark unavailable). Never invent a daily path.
- After a successful Session Note write, append **one** back-link line, e.g.:

  `- Session Note updated: [[Note-Key Title]]` or created variant.

- **Primary / best-effort:** Session Note success + Daily fail → keep Session Note, **warn**. Session Note fail → skip Daily.
- Do not roll back a good Session Note because Daily failed.

## Visual inputs

Prefer fences already in Session Context. Else draft minimal in-note fence or metric table. No asset files, no base64, no required diagram/visualize CLI.
