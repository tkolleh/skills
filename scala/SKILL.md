---
name: scala
description: "Enforces required tool order for Scala/Java projects. Compile/test: use the sbt server directly (a warm, long-running `sbt` shell session, or sbt's own BSP interface with `defaultBspToBuildTool = true`) — never Bloop, in any form, as the CLI or as the BSP backend. Search/navigate: scalex first, then ast-grep, then a semantic/LSP-aware tool if one is available, then grep/ripgrep as last resort — this order is unconditional, even for single-file lookups. Trigger on: \"compile this\", \"run the tests\", \"sbt compile\", \"sbt test\", \"build the project\", \"find where X is defined\", \"who implements this trait\", \"find usages of\", \"search this Scala codebase\", or any Scala/Java compile, test, or code-search request."
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: scala-tooling
  tags: "scala, java, sbt, scalex, ast-grep, code-search, compile, test"
  tools: "sbt, scalex, ast-grep, grep"
---

## What this skill enforces

Two hard rules for working in Scala/Java projects, both aimed at the same problem: generic,
language-agnostic tool defaults (a cold `sbt` invocation per command, `grep`) are slow or
semantically blind compared to Scala-aware tools and usage patterns that already exist in this
environment. Following the generic default "because it's obvious" silently produces slower
feedback loops or missed call sites — this skill exists so that doesn't happen by default.

1. **Compilation and testing MUST go through a warm sbt server, never Bloop — not the `bloop`
   CLI, and not Bloop acting as the BSP backend.**
2. **Code search/navigation MUST follow this fallback order: scalex → ast-grep → semantic/LSP tool
   (if available) → grep.** This order is unconditional — it applies even when you already know
   which file to look in.

This skill is agent-agnostic: it names capabilities (a Scala symbol-intelligence CLI, a structural
pattern-matching CLI, an optional semantic/LSP layer) rather than assuming one specific host's
plugin or MCP ecosystem. Use whichever concrete tool your environment provides for each role —
see the invocation notes under each tool below for how that resolves in Claude Code specifically.

## Compile and test: sbt server, always — never Bloop in any form

Use a long-running `sbt` shell session for `compile` and `test`. If your editor/agent integration
drives BSP instead, it must talk to **sbt's own BSP server**, not Bloop's. Do **not** shell out to
the `bloop` CLI, and do **not** enable, install, or rely on a Bloop build server for this project
— including as a BSP backend selected implicitly because it happened to be running. This is
unconditional: there is no case where falling back to Bloop is acceptable.

**Why:** Bloop compiles *files*, not sbt *tasks* — it silently misses anything produced by an
sbt task override (generated sources, sbt-plugin-driven codegen) because it never runs the task
that would produce them. It also runs as a single daemon shared across the whole machine, whose
JVM flags and version are fixed by whichever client starts it first and silently ignored
thereafter for everyone else — across multiple worktrees this produces cross-branch cache
contention and hard-to-diagnose OOMs that present as "not enough heap." None of that exists with
the sbt server: staying inside one warm `sbt` shell session (rather than invoking `sbt <task>`
fresh from the command line each time) avoids sbt's own JVM-startup and build-graph-reload cost,
which is the actual source of "cold sbt is slow" — not a reason to reach for Bloop.

**Precondition — check before running anything:**

```bash
which sbt
```

If this returns nothing, **stop and report it** rather than guessing at an install path.

**How to stay warm:** open one `sbt` shell per project/worktree and issue `compile`/`test`/
`testOnly` inside it, rather than invoking `sbt compile` etc. as a new process each time.

**If your agent or editor integration talks BSP:** it must be configured with
`defaultBspToBuildTool = true` (or the equivalent setting for your client) so that BSP requests
route to sbt's own BSP server, not Bloop's. Verify this setting rather than assuming it — a client
that falls back to Bloop when this is unset or false will silently reintroduce every problem
described above. This is not a preference between two acceptable options; Bloop-as-BSP-backend is
prohibited the same as the `bloop` CLI is.

**Documented exception:** none needed — `testOnly` and `scalafmtOnly` were already the sbt-shell
path; this skill now applies uniformly to compile, test, and those subcommands.

## Search and navigate: ordered, unconditional fallback

Before any Scala/Java symbol lookup, usage search, "does this pattern appear elsewhere" check, or
"where is X defined" question — **even inside a single file whose location you already know** —
work through these tools in order. Do not skip ahead to grep or a bare file read on the theory
that a lookup is "too simple" to need them; that shortcut has produced missed call sites before
(Scala's implicits, extension methods, and type hierarchies are exactly the things a plain text
search misses).

### 1. scalex — primary

`scalex` is a Scalameta-based Scala/Java code-intelligence CLI (find definition/implementations/
usages/imports/members) — a real semantic parser, not regex or a generic grammar, and it needs no
compile step or build server. Reach for it first for:

- `scalex def <symbol>` — find where something is defined
- `scalex impl <trait>` — find implementations
- `scalex refs <symbol>` — find all usages, categorized (extended-by, imported-by, used-as-type,
  usage, comment)
- `scalex imports <symbol>` — dependency/import graph
- `scalex members <symbol>` — list members of a class/trait/object

**Invocation:** in Claude Code, this is available as the `scalex:scalex` plugin skill — load it
for exact syntax (it resolves to a versioned bootstrap script, not a bare `scalex` binary on
PATH). In OpenCode or any other host, use whatever local `scalex` skill/plugin/CLI installation is
configured; if none is installed, say so explicitly rather than silently skipping to ast-grep.

**Do not `which scalex` as a precondition check.** Unlike `sbt`, scalex typically has no bare
PATH binary — it's resolved via a plugin/skill bootstrap, so a `which scalex` will often report
"not found" even when scalex is fully available. Treating that as "scalex unavailable, fall
through to ast-grep" is a false negative, not a legitimate fallback trigger. The only reliable
precondition is trying the actual scalex invocation for your host and seeing what happens.

**When scalex won't answer it:** it only indexes top-level declarations in git-tracked
`.scala`/`.java` files. If a symbol is local to a method body, a function parameter, a pattern
binding, in a file with parse errors, or not yet `git add`ed, scalex will report "not found" —
that's the signal to fall through to ast-grep, not a dead end.

### 2. ast-grep — structural fallback

Use the `ast-grep` skill (or the `sg`/`ast-grep` CLI directly if no skill wrapper exists in your
host) when the question is about a **code shape** rather than a **named symbol** (e.g. "find all
`Try { }` blocks", "find every `case class` with more than 5 fields"), or when scalex returned
"not found" for a reason listed above. ast-grep matches AST structure via tree-sitter, ignoring
formatting differences, and works without any indexing step.

### 3. Semantic/LSP tool — compiler-accurate confirmation (if available)

If your environment exposes `start_metals_mcp` (start_metals_mcp is a shell function), which is Metals-backed for Scala — `find_referencing_symbols`, `find_implementations`, `get_diagnostics_for_file`, you must **use it** because neither scalex nor ast-grep does real type-checking:

- Implicit/given resolution (which instance the compiler actually selects)
- Type alias resolution across files
- Cross-package ambiguous-name disambiguation (two packages both defining `Config`)
- Compiler diagnostics for a file

This tier is genuinely optional — if no such tool is configured in your host, skip straight to
step 4 rather than blocking on it. There is no separate standalone Metals CLI step to run; where
this capability exists, it's exposed through a broader tool (an MCP server, an LSP client), not a
dedicated Metals binary.

### 4. grep / ripgrep — last resort only

Use plain `grep`/`ripgrep` only when all the tools above have been exhausted or are unavailable,
or for files outside Scala/Java entirely (config, docs, build scripts). A plain file read is fine
once a location has already been confirmed by one of the tools above — it is not a substitute for
the confirmation step itself.

## Relationship to other codebase-search conventions

A host or project may already have its own general codebase-search rule (e.g. ast-grep → semantic
tool → ripgrep) for non-Scala languages. For Scala/Java specifically, this skill's order —
**scalex first** — supersedes that default: scalex's Scalameta-based symbol resolution is more
precise than tree-sitter pattern matching for named-symbol questions, which are the majority of
Scala navigation asks. ast-grep remains the right tool the moment the question shifts from "where
is X" to "find code shaped like this."
