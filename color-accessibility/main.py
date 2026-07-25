#!/usr/bin/env python3
"""Color accessibility helpers on top of the pastel CLI (no fake pastel contrast)."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from typing import Any


class PastelError(Exception):
    pass


def _run_pastel(*args: str) -> str:
    try:
        result = subprocess.run(
            ["pastel", *args],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise PastelError(
            "pastel not found on PATH; install via `brew install pastel` or `cargo install pastel`"
        ) from exc
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip()
        raise PastelError(err or f"pastel failed: {' '.join(args)}")
    return result.stdout.strip()


def format_hex(color: str) -> str:
    return _run_pastel("format", "hex", color).lower()


def luminance(color: str) -> float:
    return float(_run_pastel("format", "luminance", color))


def textcolor(color: str) -> str:
    return format_hex(_run_pastel("textcolor", color))


def contrast_ratio(fg: str, bg: str) -> float:
    """WCAG relative-luminance contrast: (L1 + 0.05) / (L2 + 0.05)."""
    l1, l2 = luminance(fg), luminance(bg)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def wcag_level(ratio: float, *, large_text: bool = False) -> str:
    aa = 3.0 if large_text else 4.5
    aaa = 4.5 if large_text else 7.0
    if ratio >= aaa:
        return "AAA"
    if ratio >= aa:
        return "AA"
    return "fail"


def pair_report(fg: str, bg: str, *, large_text: bool = False) -> dict[str, Any]:
    fg_hex, bg_hex = format_hex(fg), format_hex(bg)
    ratio = contrast_ratio(fg_hex, bg_hex)
    recommended = textcolor(bg_hex)
    return {
        "fg": fg_hex,
        "bg": bg_hex,
        "ratio": round(ratio, 3),
        "level": wcag_level(ratio, large_text=large_text),
        "passes_aa": ratio >= (3.0 if large_text else 4.5),
        "passes_aaa": ratio >= (4.5 if large_text else 7.0),
        "recommended_fg_for_bg": recommended,
        "fg_matches_recommended": fg_hex == recommended,
        "large_text": large_text,
    }


def mix_dim(fg: str, bg: str, fraction: float = 0.6, colorspace: str = "Lab") -> dict[str, Any]:
    """Mix fg toward bg; fraction is how much of the *base* (fg) pastel keeps (0–1)."""
    if not 0.0 <= fraction <= 1.0:
        raise ValueError("fraction must be between 0.0 and 1.0")
    mixed = _run_pastel(
        "mix", f"--colorspace={colorspace}", f"--fraction={fraction}", fg, bg
    )
    mixed_hex = format_hex(mixed)
    return {
        "fg": format_hex(fg),
        "bg": format_hex(bg),
        "fraction": fraction,
        "colorspace": colorspace,
        "mixed": mixed_hex,
        "contrast_vs_bg": pair_report(mixed_hex, bg),
    }


def _nudge(color: str, direction: str, amount: float) -> str:
    cmd = "darken" if direction == "darken" else "lighten"
    return format_hex(_run_pastel(cmd, str(amount), color))


def _direction_away_from(other_luma: float, current_luma: float) -> str:
    """Pick lighten/darken to increase distance from the other color's luma."""
    if current_luma >= other_luma:
        return "lighten" if current_luma < 1.0 - 1e-6 else "darken"
    return "darken" if current_luma > 1e-6 else "lighten"


def fix_pair(
    fg: str,
    bg: str,
    *,
    target: float = 4.5,
    large_text: bool = False,
    adjust: str = "fg",
    max_steps: int = 24,
    step: float = 0.05,
) -> dict[str, Any]:
    """Nudge fg or bg lightness until contrast >= target (or steps exhausted)."""
    if adjust not in {"fg", "bg", "auto"}:
        raise ValueError("adjust must be fg, bg, or auto")
    if large_text and math.isclose(target, 4.5):
        target = 3.0
    fg_h, bg_h = format_hex(fg), format_hex(bg)
    history: list[dict[str, Any]] = []
    current = pair_report(fg_h, bg_h, large_text=large_text)
    history.append(current)
    if current["ratio"] >= target:
        return {"status": "ok", "adjusted": adjust, "steps": 0, "pair": current, "history": history}

    which = adjust
    if adjust == "auto":
        rec = textcolor(bg_h)
        trial = pair_report(rec, bg_h, large_text=large_text)
        if trial["ratio"] >= target:
            return {
                "status": "ok",
                "adjusted": "fg",
                "steps": 1,
                "pair": trial,
                "history": history + [trial],
                "note": "switched fg to pastel textcolor",
            }
        which = "fg"

    for i in range(1, max_steps + 1):
        if which == "fg":
            direction = _direction_away_from(luminance(bg_h), luminance(fg_h))
            fg_h = _nudge(fg_h, direction, step)
        else:
            direction = _direction_away_from(luminance(fg_h), luminance(bg_h))
            bg_h = _nudge(bg_h, direction, step)

        current = pair_report(fg_h, bg_h, large_text=large_text)
        history.append(current)
        if current["ratio"] >= target:
            return {
                "status": "ok",
                "adjusted": which,
                "steps": i,
                "pair": current,
                "history": history,
            }

    return {
        "status": "fail",
        "adjusted": which,
        "steps": max_steps,
        "pair": current,
        "history": history,
        "reason": f"could not reach contrast {target}:1 in {max_steps} steps",
    }


def cmd_contrast(args: argparse.Namespace) -> None:
    report = pair_report(args.fg, args.bg, large_text=args.large_text)
    target = args.min_ratio if args.min_ratio is not None else (3.0 if args.large_text else 4.5)
    report["meets_min"] = report["ratio"] >= target
    report["min_ratio"] = target
    print(json.dumps({"status": "success" if report["meets_min"] else "fail", **report}))
    if not report["meets_min"]:
        sys.exit(1)


def cmd_textcolor(args: argparse.Namespace) -> None:
    bg = format_hex(args.bg)
    fg = textcolor(bg)
    report = pair_report(fg, bg, large_text=args.large_text)
    print(json.dumps({"status": "success", "bg": bg, "fg": fg, "pair": report}))


def cmd_mix_dim(args: argparse.Namespace) -> None:
    out = mix_dim(args.fg, args.bg, fraction=args.fraction, colorspace=args.colorspace)
    print(json.dumps({"status": "success", **out}))


def cmd_fix(args: argparse.Namespace) -> None:
    out = fix_pair(
        args.fg,
        args.bg,
        target=args.min_ratio,
        large_text=args.large_text,
        adjust=args.adjust,
        max_steps=args.max_steps,
        step=args.step,
    )
    print(json.dumps(out))
    if out["status"] != "ok":
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="WCAG color accessibility helpers (pastel-backed). pastel has no contrast subcommand."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("contrast", help="Compute WCAG contrast ratio for a fg/bg pair")
    p.add_argument("--fg", required=True)
    p.add_argument("--bg", required=True)
    p.add_argument("--large-text", action="store_true")
    p.add_argument("--min-ratio", type=float, default=None)
    p.set_defaults(func=cmd_contrast)

    p = sub.add_parser("textcolor", help="Optimal black/white fg for a background via pastel textcolor")
    p.add_argument("--bg", required=True)
    p.add_argument("--large-text", action="store_true")
    p.set_defaults(func=cmd_textcolor)

    p = sub.add_parser("mix-dim", help="Mix fg toward bg in Lab/OkLab for dimmed UI text")
    p.add_argument("--fg", required=True)
    p.add_argument("--bg", required=True)
    p.add_argument("--fraction", type=float, default=0.6, help="pastel --fraction (amount of base fg kept)")
    p.add_argument("--colorspace", default="Lab", choices=["Lab", "LCh", "RGB", "HSL", "OkLab"])
    p.set_defaults(func=cmd_mix_dim)

    p = sub.add_parser("fix", help="Nudge fg or bg until contrast meets min ratio")
    p.add_argument("--fg", required=True)
    p.add_argument("--bg", required=True)
    p.add_argument("--min-ratio", type=float, default=4.5)
    p.add_argument("--large-text", action="store_true")
    p.add_argument("--adjust", choices=["fg", "bg", "auto"], default="auto")
    p.add_argument("--max-steps", type=int, default=24)
    p.add_argument("--step", type=float, default=0.05)
    p.set_defaults(func=cmd_fix)

    args = parser.parse_args()
    try:
        args.func(args)
    except (PastelError, ValueError) as exc:
        print(json.dumps({"status": "error", "reason": str(exc)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
