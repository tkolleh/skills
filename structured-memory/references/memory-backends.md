# Memory Backends: Capability Map

Memory backends in this environment fall into up to three roles. Not every environment has all three — some collapse project-notes and durable-memory into a single store, or have no dedicated task-tracking store at all. Figure out which roles actually exist wherever this skill runs before assuming all three do; route information to the right one, don't default to whichever is closest at hand.

## Role 1: Project- or workspace-scoped notes

A file-based memory store, typically materializing as Markdown files scoped to one working directory or project — this makes it **project-scoped by default**, not cross-project.

**Four common memory types**, chosen by what's being recorded:
- `user` — durable facts about the user's role, expertise, and preferences (informs *how* to explain things, not *what* to do).
- `feedback` — corrections and confirmations of approach ("don't do X", "yes, keep doing Y"). Structure the body as: the rule, then a **Why:** line (the incident or reasoning behind it), then a **How to apply:** line (when it kicks in).
- `project` — ongoing work, decisions, and motivations not derivable from the code or git history itself. Same **Why:**/**How to apply:** structure; these decay faster than feedback memories since project state changes quickly.
- `reference` — pointers into external systems (a Jira project, a Slack channel, a dashboard URL) rather than facts themselves.

**File format**: one memory per file, YAML frontmatter (`name`, `description`, `metadata.type`), then body content. Files link to each other with `[[other-memory-name]]` — the link target is the `name:` frontmatter field, not the filename. A `[[link]]` to a memory that doesn't exist yet is not an error; it marks something worth writing later.

**An always-loaded index file** is a common pattern for this role — one line per memory, under ~150 characters, format `- [Title](file.md) — one-line hook`. It is a pointer list only; memory content never goes directly into the index, and entries past some line-count budget are truncated from context.

One concrete example of this shape: Claude Code's project auto-memory, which stores these as markdown files with YAML frontmatter under a per-project directory, indexed by an always-loaded `MEMORY.md`.

**Explicit exclusions** — never save these here (or anywhere) because they're cheaply re-derivable from the current state of the world: code patterns/conventions/architecture/file paths (re-read the code), git history or blame (run `git log`), debugging fix recipes (the fix is in the code diff; the commit message has the why), anything already in a project's standing instructions doc, and ephemeral in-progress task state (that belongs in a plan or task list, not memory).

Before recommending anything from a memory file, verify the fact still holds — a memory naming a specific function, flag, or file path is a claim about the state of the world *when it was written*, not a live guarantee.

## Role 2: Durable cross-project memory

A separate, standalone memory service, independent of any single project or workspace. Its natural scope is **cross-project** — nothing in its data model is tied to a working directory.

**Common data model shape**: memories retrieved primarily by semantic similarity search, sometimes alongside a structured fact/triple mode (subject–predicate–object records with a validity timestamp) for pattern-matched lookups. Individual memories may carry an importance or salience weight that can be boosted over time (e.g. on repeated relevance) and a decay rate governing how fast that weight fades absent reinforcement.

**Observed failure mode, name-checked because it's real and costly**: at least one production memory backend (`openmemory`, via its `store` call) has been empirically confirmed to silently corrupt multi-clause writes — dropped clauses, spliced fragments, or emptied content — with the call reporting success regardless of whether the write actually landed intact. The corruption boundary is not a simple length limit: a 130-character single run-on sentence can survive intact while a 90-character two-sentence input loses its second sentence, and some multi-sentence inputs come back completely empty rather than partial. The one pattern that reliably survives is **one atomic proposition per write** — a single short sentence expressing exactly one fact, with no compound clauses. There is no way to detect the corruption from the write call's own return value; the only reliable check is to read the memory back immediately after every write and compare content byte-for-byte against what was sent. If a multi-fact memory needs recording, decompose it into N separate writes up front rather than writing one long entry and hoping it survives — retrying the same long content tends to fail the same way. Treat this as a standing risk with any durable-memory backend you haven't personally verified, not as a quirk unique to the one tool where it was first confirmed.

## Role 3: Task-tracking state

A lightweight, project-scoped store for live, in-flight work — named text notes with no sectors, no decay, and no cross-project semantic search. It behaves like a simple key-value note store for the current unit of work, not a semantic memory graph.

This role typically has two distinct jobs that don't overlap with the other two:
- **All task-management operations** — active work breakdown, in-flight subtask state, session-to-session continuity on a specific piece of work. This is explicitly *not* what project notes or durable memory are for; those are for durable facts and lessons, not live task state.
- **The first stop before fetching any external documentation** — check task-tracking state, then durable memory, and only fall back to a live fetch (docs search, web) if nothing recent (under about a week old) is already recorded. This ordering exists because both memory stores are cheaper and faster than a live fetch, and this role's simpler, purely-textual retrieval is typically the fastest of the two to check first.

## Decision table

| Information to remember | Store | Why |
|---|---|---|
| "This specific worktree-sharing rollout uses hook X, hit incident Y" | Project-scoped notes | Tied to one project's ongoing work; decays as the project evolves; not useful to a different codebase |
| "The user always wants terse commit messages, no trailing summary" | Project-scoped notes | About this user's standing preference, applies across their projects within this agent setup, but is a setup-level (not cross-tool) concept |
| "`trash -l` hides dotfiles from its listing on any machine with this CLI" | Durable cross-project memory | A durable fact about a tool's real-world behavior, true regardless of which project or repo triggers it |
| "The internal deploy CLI silently skips any migration whose changelog folder name contains `stage`/`prod`" | Durable cross-project memory | Internal-tool behavior fact that would burn time again on a *different* service using the same internal tool — cross-project within the tool's blast radius |
| "Subtask 3 of the current feature is blocked on subtask 2" | Task-tracking state | Live, in-progress task state for the current unit of work — not a durable lesson, and not scoped to "cross-project" at all |
| "Docs for library X fetched 2 days ago say Y" | Task-tracking state (checked first) or durable memory, whichever already holds it | Recent-enough cached documentation; re-check before re-fetching live, per the check-memory-first rule |
| "Function `foo()` at file.py:42 does the parsing" | None of the three | Derivable by re-reading the code; do not memorize file:line facts that rot the moment the file changes |
