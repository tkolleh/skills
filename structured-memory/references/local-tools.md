# Local Memory Tools: Capability Map

Three distinct memory systems are available in this environment. They are not interchangeable — each has a different scope, data model, and reliability profile. Route information to the right one; don't default to whichever is closest at hand.

## 1. Local file-based auto-memory (Claude Code harness feature)

Governed by the user's global `~/.claude/CLAUDE.md`. Materializes as Markdown files under `~/.claude/projects/<project-slug>/memory/`, one directory per working-directory slug — this makes it **project-scoped by default**, not cross-project.

**Four memory types**, chosen by what's being recorded:
- `user` — durable facts about the user's role, expertise, and preferences (informs *how* to explain things, not *what* to do).
- `feedback` — corrections and confirmations of approach ("don't do X", "yes, keep doing Y"). Structure the body as: the rule, then a **Why:** line (the incident or reasoning behind it), then a **How to apply:** line (when it kicks in).
- `project` — ongoing work, decisions, and motivations not derivable from the code or git history itself. Same **Why:**/**How to apply:** structure; these decay faster than feedback memories since project state changes quickly.
- `reference` — pointers into external systems (a Jira project, a Slack channel, a dashboard URL) rather than facts themselves.

**File format**: one memory per file, YAML frontmatter (`name`, `description`, `metadata.type`), then body content. Files link to each other with `[[other-memory-name]]` — the link target is the `name:` frontmatter field, not the filename. A `[[link]]` to a memory that doesn't exist yet is not an error; it marks something worth writing later.

**`MEMORY.md`** is the always-loaded index — one line per memory, under ~150 characters, format `- [Title](file.md) — one-line hook`. It is a pointer list only; memory content never goes directly into `MEMORY.md`, and entries past line 200 are truncated from context.

**Explicit exclusions** — never save these here (or anywhere) because they're cheaply re-derivable from the current state of the world: code patterns/conventions/architecture/file paths (re-read the code), git history or blame (run `git log`), debugging fix recipes (the fix is in the code diff; the commit message has the why), anything already in a CLAUDE.md, and ephemeral in-progress task state (that belongs in a plan or task list, not memory).

Before recommending anything from a memory file, verify the fact still holds — a memory naming a specific function, flag, or file path is a claim about the state of the world *when it was written*, not a live guarantee.

## 2. openmemory MCP server

A separate, standalone memory service (independent of the Claude Code harness) reached via `mcp__openmemory__*` tools. Its natural scope is **cross-project** — nothing in its data model is tied to a working directory.

**Data model**: memories live in a hierarchical semantic graph (HSG) with five sectors — `episodic`, `procedural`, `semantic`, `emotional`, `reflective` — assigned automatically by the store call based on content, not chosen by the caller. A single memory can appear in multiple sectors. Two storage modes exist: `contextual` (free-text HSG storage, the default, retrieved by semantic similarity) and `factual` (a temporal knowledge graph of `subject`–`predicate`–`object` triples with a `valid_from` timestamp, retrieved by pattern-matching subject/predicate/object). `type: "both"` writes to both stores from one call.

Each memory carries `salience` (a relevance/importance weight, boosted over time by `openmemory_reinforce`) and `decay_lambda` (how fast salience fades — lower values decay slower). Query with `openmemory_query`: `type: "contextual"` for semantic search, `"factual"` for triple-pattern lookups, `"unified"` for both at once.

**Confirmed operational constraint — not a hypothesis, verified empirically**: `openmemory_store` silently corrupts content that spans more than one clause or sentence. The failure is not truncation at a fixed length — a 130-character single run-on string can survive intact while a 90-character two-sentence input loses its second sentence, and some multi-sentence inputs come back completely empty rather than partial. The one pattern that reliably survives is **one atomic proposition per `store` call** — a single short sentence expressing exactly one fact, with no compound clauses. There is no way to detect the corruption from the `store` call's own return value (it reports success either way); the only reliable check is to call `openmemory_get` on the returned id immediately after every store and compare content byte-for-byte against what was sent. If a multi-fact memory needs recording, decompose it into N separate `store` calls up front rather than writing one long entry and hoping it survives — retrying the same long content tends to fail the same way.

## 3. serena MCP server

Reached via `mcp__serena__*` tools (`list_memories`, `read_memory`, `write_memory`, `edit_memory`, `delete_memory`, `rename_memory`, plus `onboarding` and `initial_instructions` for session setup). Its memory model is deliberately simple: named, project-scoped text files with no sectors, no decay, no salience, and no cross-project semantic search. It behaves like a lightweight project-local key-value note store, not a semantic memory graph.

Per this environment's global configuration, serena has two distinct jobs that don't overlap with the other two stores:
- It is the designated tool for **all task-management operations** — active work breakdown, in-flight subtask state, session-to-session continuity on a specific piece of work. This is explicitly *not* what the local auto-memory or openmemory are for; those are for durable facts and lessons, not live task state.
- It is the **first stop before fetching any external documentation** — check serena memories, then openmemory, and only fall back to a live fetch (Context7, web) if nothing recent (under about a week old) is already recorded. This ordering exists because both memory stores are cheaper and faster than a live fetch, and serena's simpler, purely-textual retrieval is assumed to be the fastest of the two to check first.

## Decision table

| Information to remember | Store | Why |
|---|---|---|
| "This specific worktree-sharing rollout uses hook X, hit incident Y" | Local auto-memory, `project` type | Tied to one project's ongoing work; decays as the project evolves; not useful to a different codebase |
| "The user always wants terse commit messages, no trailing summary" | Local auto-memory, `user` or `feedback` type | About this user's standing preference, applies within this Claude Code install across their projects, but is a harness-level (not cross-tool) concept |
| "`trash -l` hides dotfiles from its listing on any machine with this CLI" | openmemory, `contextual` | A durable fact about a tool's real-world behavior, true regardless of which project or repo triggers it |
| "The internal deploy CLI silently skips any migration whose changelog folder name contains `stage`/`prod`" | openmemory, `contextual` | Internal-tool behavior fact that would burn time again on a *different* service using the same internal tool — cross-project within the tool's blast radius |
| "Subtask 3 of the current feature is blocked on subtask 2" | serena, task-management memory | Live, in-progress task state for the current unit of work — not a durable lesson, and not scoped to "cross-project" at all |
| "Docs for library X fetched 2 days ago say Y" | serena (checked first) or openmemory, whichever already holds it | Recent-enough cached documentation; re-check before re-fetching live, per the check-memory-first rule |
| "Function `foo()` at file.py:42 does the parsing" | None of the three | Derivable by re-reading the code; do not memorize file:line facts that rot the moment the file changes |
