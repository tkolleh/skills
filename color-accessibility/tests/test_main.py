#!/usr/bin/env python3
"""Unit tests for color-accessibility/main.py (requires pastel on PATH)."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import main as ca  # noqa: E402


class TestContrastMath(unittest.TestCase):
    def test_black_white_is_21(self):
        r = ca.contrast_ratio("#000000", "#ffffff")
        self.assertAlmostEqual(r, 21.0, places=1)

    def test_identical_is_1(self):
        r = ca.contrast_ratio("#336699", "#336699")
        self.assertAlmostEqual(r, 1.0, places=2)

    def test_gray_on_white_fails_aa(self):
        rep = ca.pair_report("#777777", "#ffffff")
        self.assertFalse(rep["passes_aa"])
        self.assertLess(rep["ratio"], 4.5)
        self.assertEqual(rep["level"], "fail")

    def test_neon_green_textcolor_black(self):
        self.assertEqual(ca.textcolor("#50fa7b"), "#000000")
        rep = ca.pair_report("#000000", "#50fa7b")
        self.assertTrue(rep["passes_aaa"])
        self.assertGreater(rep["ratio"], 7.0)


class TestMixAndFix(unittest.TestCase):
    def test_mix_dim_dracula(self):
        out = ca.mix_dim("#f8f8f2", "#282a36", fraction=0.6)
        self.assertEqual(out["mixed"], "#9e9fa1")
        self.assertGreaterEqual(out["contrast_vs_bg"]["ratio"], 3.0)

    def test_fix_auto_low_contrast(self):
        out = ca.fix_pair("#888888", "#777777", adjust="auto", target=4.5)
        self.assertEqual(out["status"], "ok")
        self.assertGreaterEqual(out["pair"]["ratio"], 4.5)
        self.assertTrue(out["pair"]["passes_aa"])


class TestCLI(unittest.TestCase):
    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ROOT / "main.py"), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_contrast_cli_pass(self):
        p = self._run("contrast", "--fg", "#000000", "--bg", "#ffffff")
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["status"], "success")
        self.assertAlmostEqual(data["ratio"], 21.0, places=1)

    def test_contrast_cli_fail_exit(self):
        p = self._run("contrast", "--fg", "#777777", "--bg", "#ffffff")
        self.assertEqual(p.returncode, 1)
        data = json.loads(p.stdout)
        self.assertEqual(data["status"], "fail")

    def test_help(self):
        p = self._run("--help")
        self.assertEqual(p.returncode, 0)
        self.assertIn("contrast", p.stdout)


if __name__ == "__main__":
    unittest.main()
