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

## Check the forge before running anything

If CI already ran on the reviewed SHA, read those results first. They are stronger evidence than a local re-run — same commit, same environment, no local toolchain drift — and they cover gates you may not be able to run at all (hosted scanners, cloud-backed integration suites).

```bash
gh api repos/<owner>/<repo>/commits/<sha>/status
```

**Read it even when you are told the gates pass — especially then.** "CI is green" is a claim about some commit, often an earlier one, and it is the cheapest claim in the review to check: one call, no worktree, no toolchain. In the test that produced this rule the reviewer was told the gates all passed and reviewed on that basis; the commit's actual status was `failure` with four red checks. A premise that costs one API call to verify is never worth accepting on trust, and a reviewer who repeats it inherits it.

**A green check is a claim, and some checks report success without having run.** Read the state of every check, not just the aggregate, and ask of each one whether it actually executed on *this* SHA:

- **Pending is not passing.** A check that never reported looks like absence, not failure, and disappears into an aggregate. At the commit that produced this rule the unit and integration suites — the only gates that exercise the changed code — sat `pending` and never reported, while the reviewer had been told the gates passed.
- **A bot's status can outlive the bot.** An automated reviewer that stopped running may still post `success` with a description like "Review completed". Verified on that same commit: a review bot's check read `"Review completed" — success` on a head it had not reviewed, because it auto-paused rounds earlier. Corroborate a review bot's check against its actual comments on recent commits before reading its silence as approval.
- **Separate code gates from process gates.** Approval counts, ownership, and policy checks are red for reasons unrelated to the code; reporting them as failing gates misleads the author, and letting them crowd out a genuinely red build misleads them worse.

Run gates locally only for what CI did not cover, or when no CI result exists for this exact SHA. Record in the preflight table which source each row came from.

Steps about install and codegen churn apply only to gates you ran locally.

## Fallback

With no task runner and no CI, use the ecosystem default for the manifest you found — `cargo test`, `go test ./...`, `pytest`, `sbt test`, `mvn verify` — and say in the report which default you chose and why.

With nothing discoverable at all, say so plainly and mark the review unverified-by-tooling. Never invent a command.

## Ordering

Run gates in the project's own order, cheapest first, so a fast failure surfaces early: install → codegen → typecheck → lint → unit → integration → build.

Do not stop at the first failure. A failing gate is a finding, and the author still needs the rest of the review.
