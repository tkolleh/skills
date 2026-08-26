---
name: scala
description: "Enforces required tool order for Scala/Java projects. Compile/test: use the `bloop` CLI directly (bloop compile, bloop test) — never `sbt compile`/`sbt test`. Search/navigate: scalex first, then ast-grep, then a semantic/LSP-aware tool if one is available, then grep/ripgrep as last resort — this order is unconditional, even for single-file lookups. Trigger on: \"compile this\", \"run the tests\", \"bloop compile\", \"sbt test\", \"build the project\", \"find where X is defined\", \"who implements this trait\", \"find usages of\", \"search this Scala codebase\", or any Scala/Java compile, test, or code-search request."
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: scala-tooling
  tags: "scala, java, bloop, scalex, ast-grep, code-search, compile, test"
  tools: "bloop, scalex, ast-grep, grep"
---

## What this skill enforces

Two hard rules for working in Scala/Java projects, both aimed at the same problem: generic,
language-agnostic tool defaults (`sbt compile`, `grep`) are slow or semantically blind compared to
Scala-aware tools that already exist in this environment. Following the generic default "because
it's obvious" silently produces slower feedback loops or missed call sites — this skill exists so
that doesn't happen by default.

1. **Compilation and testing MUST go through the `bloop` CLI directly.**
2. **Code search/navigation MUST follow this fallback order: scalex → ast-grep → semantic/LSP tool
   (if available) → grep.** This order is unconditional — it applies even when you already know
   which file to look in.

This skill is agent-agnostic: it names capabilities (a Scala symbol-intelligence CLI, a structural
pattern-matching CLI, an optional semantic/LSP layer) rather than assuming one specific host's
plugin or MCP ecosystem. Use whichever concrete tool your environment provides for each role —
see the invocation notes under each tool below for how that resolves in Claude Code specifically.

## Compile and test: bloop only

Use `bloop compile <project>` and `bloop test <project>` directly. Do **not** use
`sbt compile` / `sbt test` for this purpose, and do not rely on Metals to trigger a build
implicitly.

**Why:** Bloop runs a persistent build server with warm incremental-compilation state. `sbt`
reloads its JVM and rebuilds its build graph on every invocation. Once the Bloop daemon is warm,
per-module compile feedback is dramatically faster than a cold `sbt` cycle — a from-scratch
project compile through a healthy Bloop daemon has been measured at ~74s on this class of project,
versus multi-minute `sbt` cycles when the daemon state is stale or absent.

**Precondition — check before running anything:**

```bash
which bloop
```

If this returns nothing, **stop and report it** rather than silently falling back to `sbt`:

```
bloop CLI not found on PATH. Install it with:
  cs install bloop        # latest
  cs install bloop:X.Y.Z  # pinned — check .bloop/*.json or the project's Metals/Bloop config
                          # for the version this project's daemon expects
```

Do not auto-install without asking — this changes the user's environment.

**Documented exception:** plain `sbt` is still correct for running a specific test *suite* via
`testOnly`, and for `scalafmtOnly`. This skill does not relitigate that — it only replaces
`sbt compile`/`sbt test` for the whole-module/green-gate case.

**Known gotcha:** a cold Bloop daemon can make a compile exceed two minutes and appear to hang or
get backgrounded. That's expected behavior on a cold start, not a failure — let it finish rather
than killing and retrying.

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

**Do not `which scalex` as a precondition check.** Unlike `bloop`, scalex typically has no bare
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

If your environment exposes a semantic-code or LSP-backed tool (e.g. Claude Code's `serena` MCP
server, which is Metals-backed for Scala — `find_referencing_symbols`, `find_implementations`,
`get_diagnostics_for_file`), use it when you need something neither scalex nor ast-grep can give,
because neither does real type-checking:

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
