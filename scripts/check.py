#!/usr/bin/env python3
"""Run the controller and deterministic-core regression tests (no network).

    python3 scripts/check.py          # all tests
    python3 scripts/check.py -k Loop  # tests whose name matches
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

if __name__ == "__main__":
    pattern = sys.argv[sys.argv.index("-k") + 1] if "-k" in sys.argv else None
    loader = unittest.TestLoader()
    if pattern:
        loader.testNamePatterns = [f"*{pattern}*"]
    suite = loader.discover(str(ROOT / "tests"), top_level_dir=str(ROOT))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
