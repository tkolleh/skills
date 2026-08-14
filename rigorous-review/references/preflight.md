# Discovering a project's verification gates

`npm run preflight` is not a universal command, and neither is `npm`. Probe the task runners, then the language manifests, then fall back to CI. Run these in the review worktree.

## Task runners

```bash
[ -f package.json ] && node -e "console.log(Object.keys(require('./package.json').scripts||{}).join('\n'))"
[ -f Makefile ] && grep -E '^[a-zA-Z_-]+:' Makefile | sed 's/:.*//'
[ -f Justfile ] && just --list
[ -f Taskfile.yml ] && task --list-all
```

## Language manifests

Many well-tested repos have no task runner at all — a Rust or Go project often has only its manifest and CI. Probing solely for `package.json` / `Makefile` / `Justfile` reports "no gates found" for a project with a full suite.

```bash
ls Cargo.toml go.mod pyproject.toml build.sbt pom.xml build.gradle* Gemfile composer.json 2>/dev/null
```

## CI

The CI workflow is the authoritative list of gates — it is what actually blocks the merge. Prefer it over inferring from script names.

```bash
ls .github/workflows/ .gitlab-ci.yml .circleci/config.yml 2>/dev/null
grep -hoE '^[[:space:]]+run: .*' .github/workflows/<primary>.yml | sed 's/^ *run: //'
```

Two cautions the moment you read it:

- **Pick the primary workflow** — the one gating merges on this branch. Scraping every file surfaces docs, release, and website jobs instead of the build. A repo with seven workflows will hand you the wrong four.
- **CI steps are templates, not commands.** They carry matrix variables and environment expansions — `${{ matrix.job.target }}`, `$BUILD_CMD`, `${{ env.FEATURES }}`. Translate each into the plain local invocation (`cargo test --locked`), and never paste an unexpanded step into a shell.

## Fallback

With no task runner and no CI, use the ecosystem default for the manifest you found — `cargo test`, `go test ./...`, `pytest`, `sbt test`, `mvn verify` — and say in the report which default you chose and why.

With nothing discoverable at all, say so plainly and mark the review unverified-by-tooling. Never invent a command.

## Ordering

Run gates in the project's own order, cheapest first, so a fast failure surfaces early: install → codegen → typecheck → lint → unit → integration → build.

Do not stop at the first failure. A failing gate is a finding, and the author still needs the rest of the review.
