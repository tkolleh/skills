---
name: visualize
description: Generate charts (bar, line, scatter, pie) from CSV or JSON data using Vega-Lite, with automatic column-type detection and chart-type recommendation.
---

# Data Visualization Creator

Generate plots, charts, and graphs from data using `vega-cli`/`vega-lite`, with automatic visualization type selection based on the data's actual column types.

Requires `vl2svg` on PATH (install via `npm install -g vega-cli vega-lite`). Files 10MB or larger additionally require the `duckdb` CLI on PATH (install via `brew install duckdb` or see https://duckdb.org/docs/installation).

## Instructions for the LLM Agent

0. **If the data isn't already a file** (the user pasted a table, or handed you inline JSON/CSV), write it to a file in the session scratch directory first — do not invent a path, and do not write it into the project's working directory. Then pass that path as `--data_path`.

1. **Analyze first.** Run:
   ```
   python3 main.py analyze --data_path <path>
   ```
   This inspects the data file and returns a small JSON summary: row count, per-column type (`numeric` / `categorical` / `temporal`), null counts, cardinality, and a `recommended_chart_type` / `recommended_x` / `recommended_y`. Read this summary instead of the raw data file — do not guess column names or types from the file's contents or filename.

   For files ≥10MB, this step uses DuckDB to query the file directly instead of loading it into memory — the output includes `"engine": "duckdb"` and `"size_mb"` so you know this path was taken. The column stats (cardinality, null counts) are DuckDB's own summary statistics rather than exact Python counts, but are accurate enough for chart-type recommendation.

2. **Render using the analysis output** (or explicit user-specified overrides for chart type / axes):
   ```
   python3 main.py render --data_path <path> --chart_type <bar|scatter|line|pie> --x_axis <field> --y_axis <field>
   ```
   This builds a Vega-Lite spec and renders it to an SVG file via `vl2svg`.

   For files ≥10MB, the data is aggregated via DuckDB before rendering rather than plotted row-by-row: `bar`/`line`/`pie` charts show `sum(y_axis)` grouped by `x_axis`; `scatter` charts show a random 5,000-row sample. The output JSON includes `"aggregated": true` and an `"aggregation"` field describing exactly what was computed — **always mention this to the user** when reporting the result (e.g. "this chart shows totals per category, not every individual row" or "this scatter plot shows a 5,000-row sample of the N-row dataset"). Do not present an aggregated/sampled chart as if it plotted every row.

3. **Respond.** On success, report the SVG `output_path` to the user. On failure, the script returns structured JSON (`{"status": "error", "reason": ..., "stage": ...}`) — report the reason directly rather than retrying blindly; if the `reason` names an invalid field, re-check the `analyze` output for the correct column name.

4. **PNG output** is not produced by default. If the user explicitly asks for a raster image, rasterize the resulting SVG separately (e.g. with `rsvg-convert` or `vl2png` using the same spec) rather than assuming PNG is needed.
