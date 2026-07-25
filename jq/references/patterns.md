# jq advanced patterns (load on demand)

Use when the base `SKILL.md` essentials are not enough.

## Streaming and large inputs

```bash
# NDJSON: one JSON value per line (default stream-friendly)
jq -c 'select(.level == "error")' app.ndjson

# Stream parser for huge single values (path tuples)
jq -c --stream 'select(.[0][-1] == "id") | .[1]' huge.json

# First N objects from an array without loading extras in the filter logic
jq -c '.[0:5][]' big-array.json
```

Avoid `jq -s` (slurp) on multi-GB inputs unless you must build one array.

## Merge and deep update

```bash
# Shallow merge two objects
jq -s '.[0] * .[1]' a.json b.json

# Set nested path creating parents as needed
jq 'setpath(["a","b","c"]; 1)' obj.json

# Delete key
jq 'del(.secrets)' config.json

# Recursive walk: redact fields named "password"
jq 'walk(if type == "object" and has("password") then del(.password) else . end)' data.json
```

## Error handling

```bash
# try/catch per element
jq '.[] | try .payload.message catch "invalid"' items.json

# Alternate if null
jq '.name // "unknown"' user.json

# Optional iterator (skip missing)
jq '.items[]? | .id' maybe.json
```

## Sorting, unique, indexing

```bash
jq 'sort_by(.created_at) | reverse' events.json
jq 'unique_by(.email)' users.json
jq 'map({key: .id, value: .}) | from_entries' rows.json
jq 'group_by(.status) | map({status: .[0].status, ids: map(.id)})' tasks.json
```

## Variables and multipass

```bash
jq --arg env "prod" --argjson limit 10 \
  '[.[] | select(.env == $env)] | .[0:$limit]' deploys.json

# Bind intermediate
jq '.users as $u | .roles[] | . + {user_count: ($u | length)}' data.json
```

## CSV / TSV from JSON (output only)

```bash
jq -r '.[] | [.id, .name, .email] | @csv' users.json
jq -r @tsv <<< $'["a","b"]'
```

Still require JSON *input*; this skill is not a CSV parser.

## In-place edit checklist

1. `cp file.json file.json.bak` if destructive risk is high
2. `jq '...' file.json > file.json.tmp`
3. `jq empty file.json.tmp` must succeed
4. `mv file.json.tmp file.json`

## Common footguns

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `parse error` | NDJSON fed as one value | use line-wise `jq` without `-s`, or `--seq` |
| empty output | wrong path / wrong case | `jq 'keys'` / sample one object |
| shell breaks on `"` | filter in double quotes | single-quote filter; `--arg` for data |
| OOM | slurp huge file | stream / NDJSON / `--stream` |
| `Cannot index string` | type mismatch | `select(type=="object")` before indexing |
