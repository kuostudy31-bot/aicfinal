"""Permitted-source enforcement happens in code, before any network call."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aicfinal.http import SourceNotPermitted, fetch  # noqa: E402


class AllowlistTests(unittest.TestCase):
    def test_unlisted_host_is_refused(self):
        with self.assertRaises(SourceNotPermitted):
            fetch("https://example.com/data.csv", use_cache=False)

    def test_lookalike_host_is_refused(self):
        with self.assertRaises(SourceNotPermitted):
            fetch("https://data.sec.gov.evil.example/x", use_cache=False)


if __name__ == "__main__":
    unittest.main()
