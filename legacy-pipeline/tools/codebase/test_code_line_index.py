from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import update_code_line_index as indexer


class CodeLineIndexTests(unittest.TestCase):
    def test_refresh_never_rewrites_identical_generated_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            indexer.write_utf8_file(root / "Example.cs", "public class Example {}")
            args = ["index", "--root", str(root)]
            with patch.object(sys, "argv", args), patch.object(indexer, "repo_root", return_value=root), \
                    patch.object(indexer, "tracked_code_paths", return_value=["Example.cs"]):
                self.assertEqual(indexer.main(), 0)
                with patch.object(indexer, "write_utf8_file", side_effect=AssertionError("redundant write")):
                    self.assertEqual(indexer.main(), 0)
                indexer.write_utf8_file(root / "Example.cs", "public class Example {}\n// changed")
                with patch.object(indexer, "write_utf8_file", wraps=indexer.write_utf8_file) as write:
                    self.assertEqual(indexer.main(), 0)
                self.assertEqual(write.call_count, 1, "Unchanged LARGE_FILES must not be rewritten either.")


if __name__ == "__main__":
    unittest.main()
