#!/usr/bin/env python3
"""Verify commit isolation with concurrent edits in a temporary Git repository."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import finalize_changed_files_commit_push as finisher
import finalize_task_check_commit_push as wrapper
import run_final_task_checks as final_checks


def check_index_finalization_order() -> None:
    for quality, no_index, failure in ((True, False, 0), (False, False, 0), (True, True, 0), (True, False, 9)):
        calls: list[tuple[str, list[str]]] = []

        def record(label: str, command: list[str], root: Path) -> int:
            calls.append((label, command))
            return failure if label == "quality gate" else 0

        with tempfile.TemporaryDirectory(prefix="final-index-") as directory:
            argv = [
                "final-checks", "--repo-root", directory, "--no-normalize", "--no-doc-cache",
                "--no-audit", "--no-compiled-context-check", "--no-cache-check", "--no-output",
            ]
            if quality:
                argv.append("--quality")
            if no_index:
                argv.append("--no-line-index")
            with patch.object(sys, "argv", argv), patch.object(final_checks, "run", side_effect=record), patch.object(
                final_checks, "git_changed_paths", return_value=[]
            ):
                assert final_checks.main() == failure

        labels = [label for label, _ in calls]
        if no_index:
            assert not any("code line index" in label for label in labels), labels
        elif failure:
            assert "code line index check" not in labels, labels
        elif quality:
            gate = labels.index("quality gate")
            refresh = labels.index("post-quality code line index refresh")
            check = labels.index("code line index check")
            assert gate < refresh < check, labels
            assert "--changed-only" not in calls[refresh][1]
            assert "--changed-only" not in calls[check][1]
        else:
            assert "code line index check" in labels, labels
    print("OK: final index refresh/check follows quality; failure and disabled-index controls pass.")


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True, encoding="utf-8").strip()


def main() -> int:
    check_index_finalization_order()
    with tempfile.TemporaryDirectory(prefix="scoped-finalizer-") as directory:
        root = Path(directory)
        git(root, "init", "--quiet")
        for name in ("selected.txt", "concurrent.txt", "removed.txt"):
            (root / name).write_text("baseline\n", encoding="utf-8")
        git(root, "add", ".")
        git(root, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--quiet", "-m", "baseline")
        (root / "selected.txt").write_text("task edit\n", encoding="utf-8")
        (root / "concurrent.txt").write_text("other task\n", encoding="utf-8")
        (root / "unrelated.txt").write_text("new concurrent file\n", encoding="utf-8")
        (root / "removed.txt").unlink()
        generated = root / "docs-tech/cache/doc_index.json"
        generated.parent.mkdir(parents=True)
        generated.write_text("{}\n", encoding="utf-8")
        logs = root / "logs/local.json"
        logs.parent.mkdir()
        logs.write_text("{}\n", encoding="utf-8")
        selected = finisher.final_commit_candidate_paths(root, ["selected.txt,removed.txt"])
        assert selected == ["docs-tech/cache/doc_index.json", "removed.txt", "selected.txt"], selected
        assert finisher.stage_paths(root, selected) == 0
        assert git(root, "diff", "--cached", "--name-only").splitlines() == selected
        all_paths = finisher.final_commit_candidate_paths(root, [])
        assert "concurrent.txt" in all_paths and "unrelated.txt" in all_paths
        assert "logs/local.json" not in all_paths
        missing = finisher.final_commit_candidate_paths(root, ["missing.txt"])
        assert missing == ["docs-tech/cache/doc_index.json"]
        with patch.object(sys, "argv", ["finalizer", "--message", "test", "--repo-root", str(root), "--paths", "selected.txt", "--no-push"]):
            with patch.object(wrapper, "repo_root", return_value=root), patch.object(wrapper.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as execute:
                assert wrapper.main() == 0
                command = execute.call_args.args[0]
                assert command[command.index("--paths") + 1] == "selected.txt"
    print("OK: scoped commit stages selected/deleted files and generated cache, excludes concurrent edits/logs, and wrapper forwards --paths.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
