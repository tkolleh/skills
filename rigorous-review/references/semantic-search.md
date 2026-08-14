# Semantic search during review

Grep answers "where does this string appear." Review needs "what does this change reach." Those are different questions, and text search answers the second one badly — it misses renamed bindings, re-exports, and interface implementations, and it drowns in comments and string literals.

## Tool ladder — in this order, every time

1. **`ast-grep`** — structural patterns. Matches syntax, ignoring formatting, comments, and whitespace.
2. **serena** (semantic MCP server) — symbol-level questions answered from the language server: definitions, references, implementations, diagnostics.
3. **ripgrep / plain text search** — last resort, and only for things that genuinely are text: log strings, config keys, comments, documentation.

Reaching for grep first is the single most common way a review misses a call site.

Use `ast-grep`, never `sg` — `sg` is deprecated and prints a warning instead of running your pattern.

## The questions worth asking

**Blast radius — the core review question.** For every changed function, type, or constant, find who depends on it. serena's reference lookup answers this from the language server, so it catches aliased imports and re-exports that a text search will not.

- Did every caller get updated for a changed signature?
- Did every implementer of a changed interface get updated? Use the implementations lookup, not a search for the interface name.
- Is a changed constant read anywhere that assumes the old value?

**Read the definition, not the call site.** Phase 5 forbids claims built on inference. Jump to the symbol's definition before making one — the overload, default parameter, or decorator you did not know about lives there.

**Diagnostics on changed files.** The language server's own diagnostics catch type and resolution errors on the exact files under review. This is a check on the preflight gates, not a replacement: it finds problems in files the gates might not compile in isolation.

**Pattern sweeps for the preference pillars.** `ast-grep` is the right instrument for "does this change introduce the thing we do not do here" — mutation of a caller-owned argument, a loosened type, a swallowed error, a duplicated block. Write the pattern against the language's syntax rather than grepping for a keyword.

Run these against the changed files first, then against their dependents. A sweep of the whole repo produces pre-existing hits, which are not findings.

## Traps

- **`ast-grep` is not sound on shell.** It silently misses non-standard constructs in `bash`/`zsh` sources — tab-indented function bodies, subshell-body closing parens, heredocs. A clean sweep over shell proves nothing; read those files, or fall back to text search and say you did.
- **A silent zero result is not evidence.** Zero hits can mean "no such pattern" or "the pattern did not compile against this language." Sanity-check by running the pattern against a known instance before trusting an empty sweep.
- **serena needs the project indexed and the language server running.** If symbol lookups return nothing for a symbol you can see in the file, the server is not up for that language — say so and fall back, rather than reporting "no references found" as a fact.
- **Pre-existing matches are not findings.** Scope every sweep to the changed files and their dependents.

## Allium specifications

When the repo carries `.allium` specifications, they are the authoritative statement of intended behaviour — above the PR description, which is prose and can be wrong.

- `allium check` — validate the specs parse and are structurally sound. A change that breaks its own spec is a finding.
- `allium model` — extract the domain model, to check that the change's vocabulary matches the domain's.
- `allium plan` — derive test obligations from the spec. Any obligation the change leaves untested is a testability finding with an authoritative source, not an opinion.

For spec-versus-implementation drift, use the `weed` skill — it exists for exactly this comparison. Divergence is a finding in whichever direction it runs: report whether the code or the spec is the thing that moved, and do not assume it is the code.
