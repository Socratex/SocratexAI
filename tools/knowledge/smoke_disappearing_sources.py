#!/usr/bin/env python3
"""Check knowledge discovery races without hiding explicit missing inputs."""

from __future__ import annotations

import contextlib
import io
import tempfile
from pathlib import Path
from unittest.mock import patch

import knowledge_index as index


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="knowledge-discovery-") as directory:
        root = Path(directory)
        existing = root / "existing.json"
        existing.write_text("{}\n", encoding="utf-8")
        missing = root / "removed.json"
        warnings = io.StringIO()
        with patch.object(index, "discover_structured_sources", return_value=[missing, existing]):
            with contextlib.redirect_stderr(warnings):
                entries, hashes = index.collect_all_entries(root)
        assert entries == [] and list(hashes) == ["existing.json"]
        assert "removed.json" in warnings.getvalue()
        try:
            index.collect_document_entries(root, "removed.json")
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("Explicit missing sources must fail")
        with patch.object(index, "discover_structured_sources", return_value=[existing]):
            with patch.object(index, "collect_document_entries", side_effect=FileNotFoundError("dependency")):
                try:
                    index.collect_all_entries(root)
                except FileNotFoundError:
                    pass
                else:
                    raise AssertionError("Missing dependencies of an existing document must fail")
        existing.write_text("invalid JSON\n", encoding="utf-8")
        with patch.object(index, "discover_structured_sources", return_value=[existing]):
            try:
                index.collect_all_entries(root)
            except ValueError:
                pass
            else:
                raise AssertionError("Malformed documents must fail")
    print("OK: vanished discovered files are skipped with a warning; explicit missing inputs, dependencies and malformed JSON still fail.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
