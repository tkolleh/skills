# Chart selection reference

Load only when recommendation is ambiguous or the user asks why a type was chosen.
Source of truth for defaults is `main.py` `_recommend_chart` — keep this table aligned.

## Type inference (small files, Python path)

| Observed values | Type |
|-----------------|------|
| All non-null parse as float | `numeric` |
| All non-null are strings with `-` or `/` and a digit | `temporal` |
| Otherwise | `categorical` |
| All null/empty | `unknown` |

Large files (≥10MB): DuckDB column types mapped via `_duckdb_column_type`
(BIGINT/DOUBLE/… → numeric; DATE/TIMESTAMP/TIME → temporal; else categorical).
Cardinality/`null_count` are approximate.

## Recommendation decision order

1. **line** — any `temporal` + any `numeric` → x=first temporal, y=first numeric
2. **pie** — any `categorical` + `numeric`, chosen categorical cardinality ≤6 **and** row_count ≤12
3. **bar** — any `categorical` + `numeric` (prefer cardinality ≤12 for x)
4. **scatter** — ≥2 `numeric` columns, no better categorical/temporal path
5. **bar** fallback — categorical only (y may be null) or last-resort defaults

## Chart → encoding intent

| chart_type | Typical x | Typical y | Notes |
|------------|-----------|-----------|-------|
| bar | categorical | numeric | Default for category vs measure |
| line | temporal | numeric | Time series |
| scatter | numeric | numeric | Correlation / two measures |
| pie | categorical (≤6) | numeric | Small part-to-whole only |

## Large-file render behavior

When file size ≥10MB and render uses DuckDB:

| chart_type | Aggregation |
|------------|-------------|
| bar, line, pie | `sum(y) GROUP BY x` |
| scatter | random sample of 5,000 rows |

Always surface `"aggregation"` from render JSON to the user.

## Agent anti-patterns

- Guessing columns from filename without analyze
- Blind-retry render after field-not-found (re-analyze instead)
- Omitting aggregation disclaimer on large-file charts
- Forcing pie on high-cardinality categories
- Plotting every column in one chart
