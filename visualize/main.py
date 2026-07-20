import argparse
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

LARGE_FILE_THRESHOLD_MB = 10
SCATTER_SAMPLE_ROWS = 5000


def _file_size_mb(data_path):
    return Path(data_path).stat().st_size / (1024 * 1024)


def _duckdb_read_expr(data_path):
    fn = "read_json_auto" if Path(data_path).suffix.lower() == ".json" else "read_csv_auto"
    return f"{fn}('{data_path}')"


class DuckDBError(Exception):
    pass


def _run_duckdb_json(query):
    try:
        result = subprocess.run(
            ["duckdb", "-json", "-c", query],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        raise DuckDBError("duckdb not found on PATH; install via your package manager (e.g. `brew install duckdb`)")

    if result.returncode != 0:
        raise DuckDBError(result.stderr.strip() or "duckdb query failed with no error output")

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return []


_DUCKDB_TYPE_MAP = {
    "numeric": ("BIGINT", "HUGEINT", "DOUBLE", "FLOAT", "DECIMAL", "INTEGER", "SMALLINT", "TINYINT"),
    "temporal": ("DATE", "TIMESTAMP", "TIME"),
}


def _duckdb_column_type(duckdb_type):
    duckdb_type = (duckdb_type or "").upper()
    for our_type, prefixes in _DUCKDB_TYPE_MAP.items():
        if any(duckdb_type.startswith(p) for p in prefixes):
            return our_type
    return "categorical"


def _load_rows(data_path):
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"data file not found: {data_path}")

    if path.suffix.lower() == ".json":
        with path.open() as f:
            rows = json.load(f)
        if not isinstance(rows, list):
            raise ValueError("JSON data file must contain a list of records")
        return rows

    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def _infer_column_type(values):
    non_null = [v for v in values if v not in (None, "")]
    if not non_null:
        return "unknown"

    numeric_count = 0
    for v in non_null:
        try:
            float(v)
            numeric_count += 1
        except (TypeError, ValueError):
            pass
    if numeric_count == len(non_null):
        return "numeric"

    temporal_markers = ("-", "/")
    temporal_count = sum(
        1 for v in non_null if isinstance(v, str) and any(m in v for m in temporal_markers) and any(c.isdigit() for c in v)
    )
    if temporal_count == len(non_null):
        return "temporal"

    return "categorical"


def _recommend_chart(columns, row_count):
    numeric = [c for c, meta in columns.items() if meta["type"] == "numeric"]
    temporal = [c for c, meta in columns.items() if meta["type"] == "temporal"]
    categorical = [c for c, meta in columns.items() if meta["type"] == "categorical"]

    if temporal and numeric:
        return "line", temporal[0], numeric[0]
    if categorical and numeric:
        low_cardinality = [c for c in categorical if columns[c]["cardinality"] <= 12]
        x = low_cardinality[0] if low_cardinality else categorical[0]
        if columns[x]["cardinality"] <= 6 and row_count <= 12:
            return "pie", x, numeric[0]
        return "bar", x, numeric[0]
    if len(numeric) >= 2:
        return "scatter", numeric[0], numeric[1]
    if categorical:
        return "bar", categorical[0], None
    return "bar", None, None


def _analyze_large_file(data_path):
    read_expr = _duckdb_read_expr(data_path)

    summary = _run_duckdb_json(f"SUMMARIZE SELECT * FROM {read_expr}")
    row_count = _run_duckdb_json(f"SELECT COUNT(*) AS n FROM {read_expr}")[0]["n"]

    columns = {}
    for col in summary:
        col_type = _duckdb_column_type(col.get("column_type"))
        null_pct = col.get("null_percentage") or 0
        meta = {
            "type": col_type,
            "null_count": round(row_count * (float(null_pct) / 100)),
            "cardinality": col.get("approx_unique"),
        }
        if col_type == "numeric":
            meta["min"] = float(col["min"]) if col.get("min") is not None else None
            meta["max"] = float(col["max"]) if col.get("max") is not None else None
        columns[col["column_name"]] = meta

    return {"row_count": row_count, "columns": columns}


def cmd_analyze(args):
    if _file_size_mb(args.data_path) >= LARGE_FILE_THRESHOLD_MB:
        try:
            result = _analyze_large_file(args.data_path)
        except DuckDBError as e:
            print(json.dumps({"status": "error", "reason": str(e), "stage": "analyze"}))
            sys.exit(1)

        row_count, columns = result["row_count"], result["columns"]
        chart_type, x_axis, y_axis = _recommend_chart(columns, row_count)
        print(json.dumps({
            "status": "success",
            "engine": "duckdb",
            "size_mb": round(_file_size_mb(args.data_path), 2),
            "row_count": row_count,
            "columns": columns,
            "recommended_chart_type": chart_type,
            "recommended_x": x_axis,
            "recommended_y": y_axis,
        }))
        return

    try:
        rows = _load_rows(args.data_path)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        print(json.dumps({"status": "error", "reason": str(e), "stage": "analyze"}))
        sys.exit(1)

    if not rows:
        print(json.dumps({"status": "error", "reason": "data file has no rows", "stage": "analyze"}))
        sys.exit(1)

    field_names = list(rows[0].keys())
    columns = {}
    for field in field_names:
        values = [row.get(field) for row in rows]
        col_type = _infer_column_type(values)
        non_null = [v for v in values if v not in (None, "")]
        meta = {
            "type": col_type,
            "null_count": len(values) - len(non_null),
            "cardinality": len(set(non_null)),
        }
        if col_type == "numeric":
            nums = [float(v) for v in non_null]
            meta["min"] = min(nums) if nums else None
            meta["max"] = max(nums) if nums else None
        columns[field] = meta

    chart_type, x_axis, y_axis = _recommend_chart(columns, len(rows))

    print(json.dumps({
        "status": "success",
        "row_count": len(rows),
        "columns": columns,
        "recommended_chart_type": chart_type,
        "recommended_x": x_axis,
        "recommended_y": y_axis,
    }))


_VEGA_TYPE = {"numeric": "quantitative", "temporal": "temporal", "categorical": "nominal", "unknown": "nominal"}


def _build_spec(rows, chart_type, x_axis, y_axis):
    mark = {"bar": "bar", "line": "line", "scatter": "point", "pie": "arc", "auto": "bar"}.get(chart_type, "bar")

    def vega_type(field):
        return _VEGA_TYPE[_infer_column_type([row.get(field) for row in rows])]

    encoding = {}
    if x_axis:
        encoding["x"] = {"field": x_axis, "type": vega_type(x_axis)}
    if y_axis:
        encoding["y"] = {"field": y_axis, "type": "quantitative"}

    if chart_type == "pie":
        encoding = {
            "theta": {"field": y_axis, "type": "quantitative"},
            "color": {"field": x_axis, "type": vega_type(x_axis)},
        }

    return {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "data": {"values": rows},
        "mark": mark,
        "encoding": encoding,
    }


def _duckdb_field_names(data_path):
    read_expr = _duckdb_read_expr(data_path)
    described = _run_duckdb_json(f"DESCRIBE SELECT * FROM {read_expr}")
    return [col["column_name"] for col in described]


def _quote_ident(name):
    return '"' + name.replace('"', '""') + '"'


def _large_file_rows(data_path, chart_type, x_axis, y_axis):
    read_expr = _duckdb_read_expr(data_path)
    x_ident, y_ident = _quote_ident(x_axis), _quote_ident(y_axis)

    if chart_type == "scatter":
        query = f"SELECT {x_ident}, {y_ident} FROM {read_expr} USING SAMPLE {SCATTER_SAMPLE_ROWS} ROWS"
        aggregation = f"random sample of {SCATTER_SAMPLE_ROWS} rows"
    else:
        query = (
            f"SELECT {x_ident}, SUM({y_ident}) AS {y_ident} FROM {read_expr} "
            f"GROUP BY {x_ident} ORDER BY {x_ident}"
        )
        aggregation = f"sum({y_axis}) grouped by {x_axis}"

    rows = _run_duckdb_json(query)
    return rows, aggregation


def cmd_render(args):
    is_large = _file_size_mb(args.data_path) >= LARGE_FILE_THRESHOLD_MB
    aggregation = None
    rows = None
    available_fields = set()

    try:
        if is_large:
            available_fields = set(_duckdb_field_names(args.data_path))
        else:
            rows = _load_rows(args.data_path)
    except DuckDBError as e:
        print(json.dumps({"status": "error", "reason": str(e), "stage": "render"}))
        sys.exit(1)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        print(json.dumps({"status": "error", "reason": str(e), "stage": "render"}))
        sys.exit(1)

    if not is_large:
        if not rows:
            print(json.dumps({"status": "error", "reason": "data file has no rows", "stage": "render"}))
            sys.exit(1)
        available_fields = set(rows[0].keys())

    for field in (args.x_axis, args.y_axis):
        if field and field not in available_fields:
            print(json.dumps({
                "status": "error",
                "reason": f"field '{field}' not found in data columns: {sorted(available_fields)}",
                "stage": "render",
            }))
            sys.exit(1)

    if is_large:
        try:
            rows, aggregation = _large_file_rows(args.data_path, args.chart_type, args.x_axis, args.y_axis)
        except DuckDBError as e:
            print(json.dumps({"status": "error", "reason": str(e), "stage": "render"}))
            sys.exit(1)

    spec = _build_spec(rows, args.chart_type, args.x_axis, args.y_axis)
    output_path = args.output_path or "./generated_visualization.svg"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as spec_file:
        json.dump(spec, spec_file)
        spec_path = spec_file.name

    try:
        result = subprocess.run(
            ["vl2svg", spec_path, output_path],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print(json.dumps({
            "status": "error",
            "reason": "vl2svg not found on PATH; install with `npm install -g vega-cli vega-lite`",
            "stage": "render",
        }))
        sys.exit(1)
    finally:
        Path(spec_path).unlink(missing_ok=True)

    if result.returncode != 0:
        print(json.dumps({
            "status": "error",
            "reason": result.stderr.strip() or "vl2svg failed with no error output",
            "stage": "render",
        }))
        sys.exit(1)

    output = {
        "status": "success",
        "output_path": output_path,
        "chart_type": args.chart_type,
        "spec": spec,
    }
    if is_large:
        output["engine"] = "duckdb"
        output["aggregated"] = True
        output["aggregation"] = aggregation
    print(json.dumps(output))


def main():
    parser = argparse.ArgumentParser(description="Data Visualization Skill")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="Inspect data and recommend a chart type")
    analyze_parser.add_argument("--data_path", type=str, required=True, help="Path to data file (CSV or JSON)")
    analyze_parser.set_defaults(func=cmd_analyze)

    render_parser = subparsers.add_parser("render", help="Render a chart from data")
    render_parser.add_argument("--data_path", type=str, required=True, help="Path to data file (CSV or JSON)")
    render_parser.add_argument("--chart_type", type=str, required=True, choices=["bar", "scatter", "line", "pie"])
    render_parser.add_argument("--x_axis", type=str, default=None)
    render_parser.add_argument("--y_axis", type=str, default=None)
    render_parser.add_argument("--output_path", type=str, default=None, help="Output SVG path")
    render_parser.set_defaults(func=cmd_render)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
