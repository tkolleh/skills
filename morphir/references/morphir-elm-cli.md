# morphir-elm CLI reference

Verified facts about the `morphir-elm` CLI and project shape. Everything here was confirmed by direct use, not assumed — where a behavior is unverified, it's marked as such rather than guessed at.

## No separate `elm` binary required

`morphir-elm` bundles its own Elm frontend. `morphir-elm make` completes successfully with no `elm` executable on PATH at all. Don't add an `elm` install as a prerequisite check for this toolchain — it's not needed.

## Subcommands

- `make` — compiles an Elm source tree into Morphir IR (`ir.json` or a name of your choosing via `-o`).
- `gen` — generates target-language code from an IR file. Verified targets include Scala, SpringBoot, Cypher, RDF triples, and TypeScript.
- `develop` — serves a web UI for browsing a project's IR on a local port. See the skill's `scripts/morphir-develop` wrapper for a guaranteed-cleanup way to run this.
- `test`, `treeview` — exist in the CLI's help output; not exercised or verified as part of this skill's development. Don't assume their exact behavior without checking `--help` first.

## Project shape

A minimal Morphir project is two files:

`morphir.json`:
```json
{
  "name": "MyProject",
  "sourceDirectory": "src",
  "exposedModules": ["Feature"]
}
```

`src/MyProject/Feature.elm`:
```elm
module MyProject.Feature exposing (..)
```

Two things about this shape are easy to get backwards:

- The project's `name` field prefixes the module path under `sourceDirectory` — the actual file lives at `src/<Name-as-path>/<Module>.elm`, mirroring the `name` you chose.
- `exposedModules` entries name the leaf module only (`"Feature"`, not `"MyProject.Feature"`) — they're relative to `name`, which already supplies the prefix.

For a project covering more than one function/domain, add each domain as its own directory under the same `sourceDirectory`, and add its leaf module name to `exposedModules` — one project, multiple exposed modules, rather than one project per function or per domain.

## `gen` target-version defaults

`gen -e/--target-version` (Scala target) defaults to `2.11`. If the codebase being generated for is on a newer major/minor (e.g. `2.12`), pass `-e` explicitly — the flag is accepted and does what you'd expect, but the default will silently produce code targeting an older language version than the actual project uses if you don't set it.

`gen -c/--copy-deps` copies the Morphir SDK runtime alongside the generated output, making the output tree self-contained (expect on the order of dozens of extra files). This makes the output easy to accidentally treat as drop-in — don't wire generated output into a real build without deliberate review; it was never meant as a substitute for hand-written code, only as a human-reviewable artifact for the decision-table verification workflow (see `../decision-table-methodology.md`).

## `gen`'s output is not a correctness-check diff target

The single most important operational fact about this CLI: generated code from `gen` **always diverges textually from hand-written source**, even when both are behaviorally identical. Every operation in generated Scala routes through `morphir.sdk.*` wrapper functions, everything is curried and explicitly type-ascribed, and package/object naming derives mechanically from the Elm module path. A short, simple Elm function can produce generated Scala that bears no surface resemblance to idiomatic hand-written code targeting the same behavior.

This rules out "diff the generated code against the hand-written original" as a verification strategy — a real behavioral bug and a purely mechanical/stylistic difference look identical under that lens. Use the decision-table method instead (`../decision-table-methodology.md`): compare **behavior on shared concrete inputs**, not source text.

## `develop`'s IR filename is fixed

`morphir-elm develop` reads a file literally named `morphir-ir.json` from its project directory — this is not configurable via a flag. If your `make` step wrote its output under a different name (e.g. plain `ir.json`), either point `make -o` at `morphir-ir.json` directly, or copy/rename the file before running `develop`. The failure mode when the file is missing/misnamed is a clear file-not-found error, not a silent misbehavior — but it's an easy trap to hit once, since nothing about the `make` step nudges you toward the exact filename `develop` expects.
