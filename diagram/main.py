import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

_ENTITY_RE = re.compile(r"^([A-Za-z_][\w.]*)\s*:\s*(\|md|\{)", re.MULTILINE)
_ACTOR_RE = re.compile(r"shape\s*:\s*person", re.MULTILINE)
_EDGE_RE = re.compile(r"^([A-Za-z_][\w.]*)\s*(->|<-|--)\s*([A-Za-z_][\w.]*)", re.MULTILINE)
_CLASS_BLOCK_RE = re.compile(r"([A-Za-z_][\w]*)\s*:\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", re.DOTALL)
_FILL_RE = re.compile(r"fill\s*:\s*\"?([^\"\n]+?)\"?\s*(?:\n|$)")
_FONT_COLOR_RE = re.compile(r"font-color\s*:\s*\"?([^\"\n]+?)\"?\s*(?:\n|$)")


class PastelError(Exception):
    pass


def _strip_comments(text):
    return "\n".join(line for line in text.splitlines() if not line.strip().startswith("#"))


def _parse_shape(d2_text):
    text = _strip_comments(d2_text)

    entities = set(_ENTITY_RE.findall(text))
    entities = {name for name, _ in entities} if entities and isinstance(next(iter(entities)), tuple) else entities
    edges = _EDGE_RE.findall(text)
    has_actors = bool(_ACTOR_RE.search(text))

    edge_pairs = [(src, dst) for src, _, dst in edges]
    has_cycles = _has_cycle(edge_pairs)
    has_time_ordering = _looks_sequential(edge_pairs)

    return {
        "entity_count": len(entities),
        "relationship_count": len(edge_pairs),
        "has_cycles": has_cycles,
        "has_time_ordering": has_time_ordering,
        "has_actors": has_actors,
    }


def _has_cycle(edge_pairs):
    graph = {}
    for src, dst in edge_pairs:
        graph.setdefault(src, []).append(dst)

    visiting, visited = set(), set()

    def dfs(node):
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for neighbor in graph.get(node, []):
            if dfs(neighbor):
                return True
        visiting.discard(node)
        visited.add(node)
        return False

    return any(dfs(node) for node in graph)


def _looks_sequential(edge_pairs):
    if len(edge_pairs) < 2:
        return False
    involved = set()
    for src, dst in edge_pairs:
        involved.add(src)
        involved.add(dst)
    # A request/response chain touches few distinct nodes relative to edge count
    # (the same small set of actors passing messages back and forth repeatedly).
    return len(involved) <= max(3, len(edge_pairs) // 2 + 1)


def _recommend_diagram_type(shape):
    if shape["has_actors"] and shape["has_time_ordering"]:
        return "sequence"
    if shape["has_cycles"] and not shape["has_actors"]:
        return "state"
    return "c4"


def cmd_recommend_diagram_type(args):
    path = Path(args.model_path)
    if not path.exists():
        print(json.dumps({"status": "error", "reason": f"file not found: {args.model_path}", "stage": "recommend"}))
        sys.exit(1)

    shape = _parse_shape(path.read_text())
    diagram_type = _recommend_diagram_type(shape)

    print(json.dumps({
        "status": "success",
        "shape": shape,
        "recommended_diagram_type": diagram_type,
    }))


def _run_pastel_textcolor(hex_or_name):
    try:
        result = subprocess.run(
            ["pastel", "textcolor", hex_or_name],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        raise PastelError("pastel not found on PATH; install via `brew install pastel` or `cargo install pastel`")

    if result.returncode != 0:
        raise PastelError(result.stderr.strip() or f"pastel failed on input '{hex_or_name}'")

    return result.stdout.strip()


def _normalize_color(value):
    try:
        result = subprocess.run(
            ["pastel", "format", "hex", value],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        raise PastelError("pastel not found on PATH; install via `brew install pastel` or `cargo install pastel`")

    if result.returncode != 0:
        return None
    return result.stdout.strip().lower()


def _extract_classes(d2_text):
    text = _strip_comments(d2_text)
    classes_match = re.search(r"classes\s*:\s*\{(.*)", text, re.DOTALL)
    if not classes_match:
        return {}

    body = classes_match.group(1)
    depth = 1
    end = 0
    for i, ch in enumerate(body):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    body = body[:end]

    classes = {}
    for name, block in _CLASS_BLOCK_RE.findall(body):
        fill_match = _FILL_RE.search(block)
        font_match = _FONT_COLOR_RE.search(block)
        if fill_match:
            classes[name] = {
                "fill": fill_match.group(1).strip(),
                "font_color": font_match.group(1).strip() if font_match else None,
            }
    return classes


def cmd_check_contrast(args):
    path = Path(args.model_path)
    if not path.exists():
        print(json.dumps({"status": "error", "reason": f"file not found: {args.model_path}", "stage": "check-contrast"}))
        sys.exit(1)

    classes = _extract_classes(path.read_text())
    if not classes:
        print(json.dumps({"status": "error", "reason": "no classes with a fill found", "stage": "check-contrast"}))
        sys.exit(1)

    results = []
    try:
        for name, decl in classes.items():
            fill = decl["fill"]
            recommended = _run_pastel_textcolor(fill)
            declared = decl["font_color"]
            declared_norm = _normalize_color(declared) if declared else None
            recommended_norm = _normalize_color(recommended)
            ok = declared_norm is not None and declared_norm == recommended_norm
            results.append({
                "class": name,
                "fill": fill,
                "declared_font_color": declared,
                "recommended_font_color": recommended,
                "ok": ok,
            })
    except PastelError as e:
        print(json.dumps({"status": "error", "reason": str(e), "stage": "check-contrast"}))
        sys.exit(1)

    all_ok = all(r["ok"] for r in results)
    print(json.dumps({
        "status": "success" if all_ok else "fail",
        "all_ok": all_ok,
        "classes": results,
    }))
    if not all_ok:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Diagram Skill")
    subparsers = parser.add_subparsers(dest="command", required=True)

    recommend_parser = subparsers.add_parser(
        "recommend-diagram-type", help="Analyze a D2 model file and recommend a diagram type"
    )
    recommend_parser.add_argument("--model_path", type=str, required=True, help="Path to a .d2 file")
    recommend_parser.set_defaults(func=cmd_recommend_diagram_type)

    contrast_parser = subparsers.add_parser(
        "check-contrast", help="Validate fill/font-color pairs in a D2 file's classes using pastel"
    )
    contrast_parser.add_argument("--model_path", type=str, required=True, help="Path to a .d2 file")
    contrast_parser.set_defaults(func=cmd_check_contrast)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
