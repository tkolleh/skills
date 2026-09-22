# Semantic search during review

Grep answers "where does this string appear." Review needs "what does this change reach." Those are different questions, and text search answers the second one badly — it misses renamed bindings, re-exports, and interface implementations, and it drowns in comments and string literals.

## Tool ladder — in this order, every time

1. **`ast-grep`** — structural patterns. Matches syntax, ignoring formatting, comments, and whitespace.
2. **serena** (semantic MCP server) — symbol-level questions answered from the language server: definitions, references, implementations, diagnostics.
3. **ripgrep / plain text search** — last resort, and only for things that genuinely are text: log strings, config keys, comments, documentation.

**This ordering is a requirement, not a preference.** Start every code question at step 1 and descend only when the step above cannot express it. Descending is a decision you must be able to justify: say in the report which tool answered each sweep, and when you fell back to text search, say why the structural form could not express the query. "It was quicker" is not a reason.

Reaching for grep first is the single most common way a review misses a call site.

Where a language-specific skill defines its own tool order for this repo — the `scala` skill is one — that order wins for that language, and it is still structural-first. Project standards outrank this file; text-search-first never does.

Prefer `ast-grep`. On some installations `sg` is a deprecated alias that warns instead of running your pattern; on others it is a working shim for the same binary. Use `ast-grep` so the command is unambiguous.

### Why structural, not textual

Every sweep in this file is a question about **shape**, and shape is what text search cannot see:

- A discarded effect handle is a call whose result is bound to nothing — a *syntactic position*, not a string. No keyword identifies it.
- An exhaustive-looking match is a set of case arms measured against a type's real variants — a *structure*, not a name.
- A call moved inside a loop is a nesting relationship. Grep sees both lines and neither relationship.
- An aliased import or re-export renames the very token a text search keys on, so the call site that matters is the one grep cannot find.

Text search also fails in both directions at once: it misses real hits (renamed bindings, re-exports, multi-line calls, formatting variation) and floods you with false ones (comments, string literals, unrelated identifiers that share a substring). A sweep that must be *complete* to be worth anything — which is every sweep below, since their value is proving absence — cannot rest on it.

Write patterns against the language's grammar. `ast-grep --lang <lang> --pattern '<pattern>'` with metavariables (`$X`, `$$$ARGS`) expresses "a call in statement position whose value is unused" or "a spawn whose handle is never joined" directly; no text query approximates either. For multi-condition sweeps, use a YAML rule with `ast-grep scan --rule <file>` rather than chaining greps — `inside`, `has`, `follows`, and `not` are how the nesting and absence conditions get stated.

## The questions worth asking

**Outbound blast radius — who depends on the changed code.** For every changed function, type, or constant, find who depends on it. serena's reference lookup answers this from the language server, so it catches aliased imports and re-exports that a text search will not.

- Did every caller get updated for a changed signature?
- Did every implementer of a changed interface get updated? Use the implementations lookup, not a search for the interface name.
- Is a changed constant read anywhere that assumes the old value?

**Inbound blast radius — what the changed code now depends on.** The mirror question, and the one reviews skip. Dependents are where a change *breaks other code*; callees are where *other code breaks the change*. A diff can be flawless line by line and still wrong because it leans on a guarantee its callee does not make.

For every call the change adds, re-routes, or moves, open the callee and name the guarantee being assumed:

- Does the callee actually provide it — durability, ordering, atomicity, totality, completion before return?
- Does the callee's failure or cancellation path surface, or absorb, what the caller now needs to know?
- Was the callee written for a caller with weaker requirements than this one?

The callee is usually unchanged, so it will not appear in the diff and no dependents sweep will surface it. Findings here are **PR-level** in the sense `references/finding-schema.md` defines, and need the load-bearing clause.

**Read the definition, not the call site.** Phase 5 forbids claims built on inference. Jump to the symbol's definition before making one — the overload, default parameter, or decorator you did not know about lives there. This is a recall device as much as a precision one: opening the definition is how the inbound question gets answered at all.

**Include generated and vendored code in the trace.** Codegen output — IDL/schema stubs, ORM models, protobuf and Thrift types, client SDKs — is where forward-compatibility cases live that no hand-written file mentions. A generated union or enum commonly carries an unknown/default variant for versions the current schema does not know, and an exhaustive-looking match over the hand-written variants silently omits it. If the change matches on a generated type, read the generated definition and enumerate its real cases before calling the match total.

**Diagnostics on changed files.** The language server's own diagnostics catch type and resolution errors on the exact files under review. This is a check on the preflight gates, not a replacement: it finds problems in files the gates might not compile in isolation.

**Pattern sweeps for the preference pillars.** `ast-grep` is the right instrument for "does this change introduce the thing we do not do here" — mutation of a caller-owned argument, a loosened type, a swallowed error, a duplicated block. Write the pattern against the language's syntax rather than grepping for a keyword.

Run these against the changed files first, then against their dependents. A sweep of the whole repo produces pre-existing hits, which are not findings.

## Traps

- **`ast-grep` is not sound on shell.** It silently misses non-standard constructs in `bash`/`zsh` sources — tab-indented function bodies, subshell-body closing parens, heredocs. A clean sweep over shell proves nothing; read those files, or fall back to text search and say you did.
- **A silent zero result is not evidence.** Zero hits can mean "no such pattern" or "the pattern did not compile against this language." Sanity-check by running the pattern against a known instance before trusting an empty sweep.
- **serena needs the project indexed and the language server running.** If symbol lookups return nothing for a symbol you can see in the file, the server is not up for that language — say so and fall back, rather than reporting "no references found" as a fact.
- **The index may be of a different revision.** Structural and semantic tools read the working tree, not the commit under review. If the worktree is not at the reviewed revision, every sweep returns a confident, silently wrong answer — a live symbol reports zero references. **The sanity-check above does not catch this**, because the known instance is missing from the index too. Materialise the reviewed revision and point the tools at it:
  ```bash
  git archive <sha> | tar -x -C <scratch-dir>
  ```
- **Block bodies are brittle in some grammars.** A pattern capturing a brace block (`f { $$$BODY }`) can silently match nothing while the bare call `f` matches everywhere — observed in Scala, where single-line, multi-line, and partial-function-literal forms all differ. Match the call head structurally, then read the bodies. Always compare a body-capturing pattern's hit count against the bare-head count before trusting it.
- **Pre-existing matches are not findings.** Scope every sweep to the changed files and their dependents.

## When the semantic tier is unavailable

The tool ladder assumes its rungs exist. They frequently do not — a language server that will not start, an MCP server that times out, a project that is not indexed.

Say so in the report and state what it costs. With `ast-grep` alone you can still prove **presence** reliably; **absence** claims weaken — no aliased-import or re-export resolution, no implementations lookup, no diagnostics.

In that mode: sanity-check *every* absence claim against a known instance, not only the effect-lifetime sweep; prefer reading definitions and executing the unit over inferring from an empty sweep; and where absence carries a finding, mark it `Plausible` unless you drove the code.

## Allium specifications

When the repo carries `.allium` specifications, they are the authoritative statement of intended behaviour — above the PR description, which is prose and can be wrong.

- `allium check` — validate the specs parse and are structurally sound. A change that breaks its own spec is a finding.
- `allium model` — extract the domain model, to check that the change's vocabulary matches the domain's.
- `allium plan` — derive test obligations from the spec. Any obligation the change leaves untested is a testability finding with an authoritative source, not an opinion.

For spec-versus-implementation drift, use the `weed` skill — it exists for exactly this comparison. Divergence is a finding in whichever direction it runs: report whether the code or the spec is the thing that moved, and do not assume it is the code.
