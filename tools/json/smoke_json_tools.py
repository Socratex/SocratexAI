#!/usr/bin/env python3
"""Smoke-test portable JSON tooling operations on temporary fixtures."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared.repo_helpers import run_step  # noqa: E402


def run(command: list[str], cwd: Path) -> None:
    exit_code = run_step(" ".join(command), command, cwd)
    if exit_code != 0:
        raise RuntimeError(f"Command failed ({exit_code}): {' '.join(command)}")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    root = script_dir.parents[1]
    tool = script_dir / "json_list_doc.py"
    node_tool = script_dir / "json_node_edit.py"
    read_tool = script_dir / "json_read.py"
    line_insert_tool = script_dir / "json_line_insert.py"
    line_move_tool = script_dir / "json_line_move.py"
    refresh_tool = script_dir / "json_refresh_index.py"
    migrate_tool = script_dir / "json_migrate_content.py"
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

        run([sys.executable, "-B", str(read_tool), str(fixture), "alpha", "--collection", "content"], root)
        run([sys.executable, "-B", str(node_tool), "read", "--path", str(fixture), "--node", "content.alpha.title"], root)
        run(
            [
                sys.executable,
                "-B",
                str(node_tool),
                "set",
                "--path",
                str(fixture),
                "--node",
                "content.alpha.title",
                "--value-json",
                '"Alpha Updated"',
            ],
            root,
        )
        run(
            [
                sys.executable,
                "-B",
                str(line_insert_tool),
                "--path",
                str(fixture),
                "--key",
                "alpha",
                "--collection",
                "content",
                "--field-path",
                "steps",
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
                "-B",
                str(line_move_tool),
                "--path",
                str(fixture),
                "--key",
                "alpha",
                "--collection",
                "content",
                "--field-path",
                "steps",
                "--line",
                "2",
                "--position",
                "end",
            ],
            root,
        )
        run([sys.executable, "-B", str(refresh_tool), str(fixture)], root)

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
        run([sys.executable, "-B", str(migrate_tool), str(migrate_fixture), "items"], root)
        migrated = load(migrate_fixture)
        assert migrated["index"] == ["one", "two"]
        assert set(migrated["content"]) == {"one", "two"}

    print("OK: portable JSON tooling smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
