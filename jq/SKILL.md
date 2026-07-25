---
name: jq
description: >-
  Trigger on: jq, jq filter, jq query, process JSON, filter JSON, transform JSON,
  extract from JSON, parse API response JSON, NDJSON, pretty-print JSON, jq select,
  group_by JSON, update JSON file with jq. Specialized procedure for complex JSON
  processing with the jq CLI. Prefer over ad-hoc Python/Node one-offs for extract,
  filter, format, aggregate, or in-place JSON transforms. Do not use for binary
  files, CSV/XML conversion, or general scripting unrelated to JSON.
license: MIT
compatibility: "Requires jq CLI on PATH (jq 1.6+)"
metadata:
  audience: developers
  workflow: data-engineering
  tags: "jq, json, cli, data"
  tools: "bash, jq"
---

# jq — JSON processing with the jq CLI

## When to use

- User wants to extract, filter, transform, aggregate, or pretty-print JSON with `jq`
- Input is JSON / JSON array / NDJSON (newline-delimited JSON), API payloads, logs, configs
- Prefer this over writing a throwaway Python/Node script for the same JSON job

Do **not** use when:

- File is binary, CSV, XML, YAML-only (unless already converted to JSON)
- Task is general bash/Python scripting with no JSON core
- User only needs to open/edit JSON in an editor (no filter)

## Prerequisites

```bash
command -v jq >/dev/null || { echo "jq not installed"; exit 1; }
jq --version   # expect 1.6+
```

If missing: tell the user to install (`brew install jq` / `apt install jq`) and STOP.

## Procedure

Work phases in order. Do not skip. Prefer pure `jq` over `python`/`node` for JSON work.

### Phase 1 — Structure analysis

1. Identify inputs: path(s), stdin, or API response the user provided.
2. Peek schema before complex filters:
   - Small file: `jq 'type, (if type=="array" then length else keys end)' <file>`
   - Huge / unknown: `jq -c 'limit(1; .)' <file>` or first NDJSON line via `head -n 1`
   - Validate: `jq empty <file>` — non-zero exit → report parse error and STOP
3. Note shape: object vs array vs NDJSON stream; nested keys needed; size class (<10MB / large).
4. **Completion:** input path(s) known, type known, filter target keys identified (or error reported).

### Phase 2 — Filter construction

Design filter with explicit pipeline stages (compose with `|`):

1. **Select** path into focus: `.items[]`, `.[]`, `.data.results?`
2. **Filter** rows: `select(.status == "active")`
3. **Transform** shape: `{id, name: .user.name}` or `map(...)`
4. **Aggregate** if needed: `group_by(.k) | map({k: .[0].k, n: length})` or `map(.items | map(.price*.qty) | add)`
5. **Output flags:** pretty default; `-r` bare strings; `-c` compact; `-s` only if slurp is required

**Safety (mandatory):**

- Pass untrusted strings via `--arg` / `--argjson`, never interpolate into the filter string
- Optional paths: use `?` (`.a.b?`) to avoid hard errors on missing keys
- NEVER redirect jq onto the same path it reads: `jq ... file > file` truncates the file. Always:

```bash
jq '<filter>' file.json > file.json.tmp && mv file.json.tmp file.json
```

Deep cookbook (load only if needed): `references/patterns.md`

6. **Completion:** one copy-pastable `jq ...` command ready; `--arg` used where user/env text is involved.

### Phase 3 — Execution

1. Run via shell: `jq [flags] '<filter>' <file>` or pipe into `jq`.
2. File rewrites: temp + `mv` only (see Safety).
3. Large files / NDJSON: stream; do **not** `jq -s` for simple filters/counts.
4. On non-zero exit: capture stderr; fix or report; do not invent output.
5. Always include the exact command in the user-facing answer.
6. **Completion:** command ran; stdout/stderr captured; exit code known.

### Phase 4 — Validation

1. Empty result → re-check with `keys`, sample object, `?` / casing.
2. Confirm output type matches request (JSON vs raw list vs count).
3. For file writes: `jq empty file.json` and spot-check changed + preserved fields.
4. Return command + short summary + truncated sample if large.
5. **Completion:** answer matches intent, or clear failure + diagnostic.

## Essential patterns (keep loaded)

```bash
jq '.users[] | select(.age > 21)' data.json
jq 'map({name: .user.name, role: .auth.role})' data.json
jq 'group_by(.category) | map({cat: .[0].category, count: length})' data.json
jq --arg id "$ID" '.[] | select(.id == $id)' data.json
jq -r '.[].title' pulls.json
jq -c 'select(.level=="error" and .service=="auth")' app.ndjson | wc -l
jq '.version="2.0.0"' package.json > package.json.tmp && mv package.json.tmp package.json
# nested totals example
jq '[.orders[] | select(.status=="paid") | {buyer: .buyer.name, total: ([.items[] | .price*.qty] | add)}] | sort_by(-.total)' orders.json
```

## Guardrails

- Validate JSON first (`jq empty`).
- `--arg` / `--argjson` for external values; single-quote filters in the shell.
- Avoid `-s` on large/NDJSON inputs for simple work.
- No shell-injecting user text into the filter body.
- Prefer `jq` over Python/Node for the same JSON transform.
- File rewrite: temp + `mv` only; never `jq ... f > f`.

## Examples

### Extract names (raw)

```bash
jq -r '.users[] | select(.status=="active" and .age>21) | .name' users.json | sort
```

### Update config safely

```bash
jq '.version="2.0.0" | .scripts.build="tsc -b"' package.json > package.json.tmp && mv package.json.tmp package.json
```

### Env-safe lookup

```bash
jq --arg name "$TARGET_NAME" '.users[] | select(.name == $name)' users.json
```

### Non-trigger

"Convert this CSV" / "write a Python ETL" → do not load this skill.

## References (load only if needed)

- `references/patterns.md` — streaming, merge, walk, try/catch, group_by detail
