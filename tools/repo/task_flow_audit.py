#!/usr/bin/env python3
"""Print the task-flow closure checklist without a legacy shell runtime."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared.cli_helpers import configure_stdio  # noqa: E402
from shared.repo_helpers import changed_paths, repo_root  # noqa: E402


def first_existing_changelog(root: Path, explicit: str) -> Path | None:
    if explicit.strip():
        path = Path(explicit)
        return path if path.is_absolute() else root / path
    for candidate in ("CHANGELOG.json", "CHANGELOG.md"):
        path = root / candidate
        if path.is_file():
            return path
    return None


def latest_json_changelog_entry(path: Path) -> str:
    document = json.loads(path.read_text(encoding="utf-8"))
    changelog = document.get("content", document) if isinstance(document, dict) else document
    if not isinstance(changelog, dict):
        return ""
    entries = changelog.get("entries")
    if not isinstance(entries, list) or not entries:
        return ""
    entry = entries[-1]
    if not isinstance(entry, dict):
        return ""
    parts: list[str] = []
    for name in ("date", "feature", "change"):
        value = str(entry.get(name, "")).strip()
        if value:
            parts.append(f"{name}: {value}")
    return " | ".join(parts)


def latest_markdown_changelog_entry(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    headings = [index for index, line in enumerate(lines) if line.startswith("## ")]
    if not headings:
        return ""
    start = headings[-1]
    entry_lines: list[str] = []
    for index in range(start, len(lines)):
        line = lines[index]
        if index > start and line.startswith("## "):
            break
        stripped = line.strip()
        if stripped:
            entry_lines.append(stripped)
    return " ".join(entry_lines[:8])


def latest_changelog_entry(path: Path | None) -> str:
    if path is None or not path.is_file():
        return ""
    if path.suffix.lower() == ".json":
        return latest_json_changelog_entry(path)
    return latest_markdown_changelog_entry(path)


def complex_task_shape(paths: list[str], forced: bool) -> bool:
    if forced or len(paths) >= 6:
        return True
    for path in paths:
        normalized = path.replace("\\", "/")
        if any(f"/{part}/" in f"/{normalized}" for part in ("core", "project", "profiles", "tools", "context-docs", "docs-tech", "templates")):
            return True
        name = Path(normalized).name
        if name in {"FLOWS.json", "WORKFLOW.json", "COMMANDS.json", "SCRIPTS.json", "pipeline_featurelist.json", "_PLAN.json"}:
            return True
    return False


def non_empty_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return bool(value)
    if isinstance(value, Iterable):
        return bool(list(value))
    return True


def validate_closure_evidence(path: Path, is_complex: bool) -> None:
    if not path.is_file():
        raise RuntimeError(f"Closure evidence file not found: {path}")
    evidence = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(evidence, dict):
        raise RuntimeError("Closure evidence must be a JSON object.")
    required = [
        "context_route",
        "flow_execution",
        "closure_evidence",
        "changelog_truth",
        "tool_failure_response",
        "tool_discipline",
    ]
    for name in required:
        if not non_empty_value(evidence.get(name)):
            raise RuntimeError(f"Closure evidence is missing or empty: {name}")
    closure = evidence.get("closure_evidence")
    if not isinstance(closure, dict):
        raise RuntimeError("Closure evidence must include closure_evidence object.")
    if not non_empty_value(closure.get("changed_files")):
        raise RuntimeError("Closure evidence must include closure_evidence.changed_files.")
    if not non_empty_value(closure.get("verification_commands")):
        raise RuntimeError("Closure evidence must include closure_evidence.verification_commands.")
    if is_complex and not non_empty_value(evidence.get("adversarial_review")):
        raise RuntimeError("Complex task closure evidence must include adversarial_review.")
    print()
    print(f"OK: closure evidence file satisfies task-flow audit contract: {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print task-flow closure audit prompts.")
    parser.add_argument("--paths", nargs="*", default=[], help="Explicit changed paths, comma-separated or repeated.")
    parser.add_argument("--project-root", default="", help="Project root. Defaults to nearest git root.")
    parser.add_argument("--changelog-path", default="", help="Explicit changelog path.")
    parser.add_argument("--complex", action="store_true", help="Force complex-task audit prompts.")
    parser.add_argument("--no-changelog", action="store_true", help="Skip changelog lookup.")
    parser.add_argument("--require-closure-evidence", action="store_true", help="Validate closure evidence JSON.")
    parser.add_argument("--closure-evidence-path", default="", help="Closure evidence JSON path.")
    return parser.parse_args()


def main() -> int:
    configure_stdio()
    args = parse_args()
    root = Path(args.project_root).resolve() if args.project_root else repo_root(Path(__file__).resolve())
    try:
        paths = changed_paths(root, args.paths)
        changelog = first_existing_changelog(root, args.changelog_path)
        latest = "" if args.no_changelog else latest_changelog_entry(changelog)
        is_complex = complex_task_shape(paths, args.complex)

        print("==> task flow audit")
        print(f"Changed path count: {len(paths)}")
        for path in paths[:40]:
            print(f"- {path}")
        if len(paths) > 40:
            print(f"... truncated {len(paths) - 40} path(s)")

        print()
        print("Required closure artifacts:")
        print("- context_route: cite loaded FLOWS/WORKFLOW/DOCS/STATE/plan/context records that were relevant.")
        print("- flow_execution: cite the selected flow and the concrete steps/subroutines followed.")
        print("- closure_evidence: cite changed files, verification commands, generated artifacts, and remaining risk; do not close with prose only.")
        print("- changelog_truth: state whether changelog was updated from actual shipped changes; if not needed, state why.")
        print("- tool_failure_response: if a tool failed mechanically, state whether the tool or its input contract was fixed; if no tool failed, state that.")
        print("- tool_discipline: state which repo tools/scripts were used and which edits were manual.")

        if not args.no_changelog:
            print()
            if changelog is None:
                print("Changelog: no changelog file found; closure must justify why no changelog artifact exists.")
            elif not latest:
                print(f"Changelog: {changelog.relative_to(root).as_posix()} exists but no latest entry was detected; closure must justify/update it when required.")
            else:
                print(f"Latest changelog artifact from {changelog.relative_to(root).as_posix()}:")
                print(latest)

        if is_complex:
            print()
            print("Complex-task adversarial review required from changelog artifact:")
            print("- Re-read the changelog claim as if it were a bug report about this diff.")
            print("- Check whether the diff actually implements the claim, not just the intended direction.")
            print("- Check for missing verification, hidden scope expansion, tool bypass, stale plan/state, and future retrofit debt.")
            print("- Report one concise pass/fail/risk result in closure.")

        if args.require_closure_evidence:
            if not args.closure_evidence_path.strip():
                raise RuntimeError("Closure evidence is required. Pass --closure-evidence-path <json>.")
            evidence_path = Path(args.closure_evidence_path)
            if not evidence_path.is_absolute():
                evidence_path = root / evidence_path
            validate_closure_evidence(evidence_path, is_complex)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
