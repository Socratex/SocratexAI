#!/usr/bin/env python3
"""Smoke-test portable JSON tooling operations on temporary fixtures."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run(command: list[str], cwd: Path) -> None:
    completed = subprocess.run(command, cwd=cwd, check=False, text=True, capture_output=True)
    if completed.returncode != 0:
        output = "\n".join(part for part in [completed.stdout, completed.stderr] if part)
        raise RuntimeError(f"Command failed ({completed.returncode}): {' '.join(command)}\n{output}")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    root = script_dir.parents[1]
    tool = script_dir / "json_list_doc.py"
    with tempfile.TemporaryDirectory(prefix="socratex-json-smoke-") as temp_name:
        temp = Path(temp_name)
        fixture = temp / "list-doc.json"
        fixture.write_text(
            json.dumps(
                {
                    "index": ["alpha", "beta"],
                    "content": {
                        "alpha": {"title": "Alpha", "steps": ["first", "second"]},
                        "beta": {"title": "Beta", "steps": []},
                    },
                    "metadata": {"schema": "smoke/v1"},
                },
                indent=4,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )

        run([sys.executable, str(tool), "read-node", str(fixture), "content.alpha.title"], root)
        run(
            [
                sys.executable,
                str(tool),
                "set-node",
                str(fixture),
                "content.alpha.title",
                "--value-json",
                '"Alpha Updated"',
            ],
            root,
        )
        run(
            [
                sys.executable,
                str(tool),
                "insert-node-line",
                str(fixture),
                "content.alpha.steps",
                "--position",
                "after",
                "--reference-text",
                "first",
                "--text",
                "middle",
            ],
            root,
        )
        run(
            [
                sys.executable,
                str(tool),
                "move-node-line",
                str(fixture),
                "content.alpha.steps",
                "--line",
                "2",
                "--position",
                "end",
            ],
            root,
        )
        run([sys.executable, str(tool), "refresh-index", str(fixture)], root)

        updated = load(fixture)
        assert updated["content"]["alpha"]["title"] == "Alpha Updated"
        assert updated["content"]["alpha"]["steps"] == ["first", "second", "middle"]
        assert updated["index"] == ["alpha", "beta"]

        migrate_fixture = temp / "migrate-doc.json"
        migrate_fixture.write_text(
            json.dumps({"items": {"one": {"value": 1}, "two": {"value": 2}}, "metadata": {}}, indent=4) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        run([sys.executable, str(tool), "migrate-content", str(migrate_fixture), "items"], root)
        migrated = load(migrate_fixture)
        assert migrated["index"] == ["one", "two"]
        assert set(migrated["content"]) == {"one", "two"}

    print("OK: portable JSON tooling smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
