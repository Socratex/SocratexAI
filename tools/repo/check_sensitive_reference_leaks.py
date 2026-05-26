#!/usr/bin/env python3
"""Smoke-test reusable pipeline sources for private reference leaks."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared.repo_helpers import git_lines  # noqa: E402


@dataclass(frozen=True)
class Rule:
    rule_id: str
    regex: re.Pattern[str]
    allowed_basenames: tuple[str, ...] = ()


def repo_relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def is_installed_package_root(root: Path) -> bool:
    return root.name == "SocratexAI" and (root.parent / "SOCRATEX.md").is_file()


def skipped(relative: str) -> bool:
    parts = relative.split("/")
    return (
        relative == ".git"
        or relative.startswith(".git/")
        or "__pycache__" in parts
        or relative.endswith(".pyc")
    )


def candidate_files(root: Path) -> list[Path]:
    if (root / ".git").exists():
        relatives = git_lines(root, ["ls-files", "--cached", "--others", "--exclude-standard"], allow_failure=True)
        if relatives:
            return [root / relative for relative in relatives]
    return sorted(item for item in root.rglob("*") if item.is_file())


def line_number(text: str, index: int) -> int:
    return text.count("\n", 0, max(index, 0)) + 1


def rules() -> list[Rule]:
    return [
        Rule("private-project-a", re.compile(r"Rift" + r"bound[\s_-]*" + r"Van" + r"guard", re.IGNORECASE)),
        Rule("private-project-b", re.compile("Om" + "ega", re.IGNORECASE)),
        Rule("private-project-b-legacy-path", re.compile(r"v3[\s_-]*" + "om" + "ega", re.IGNORECASE)),
        Rule("external-private-domain", re.compile(r"plan[.]com(?![A-Za-z0-9_])", re.IGNORECASE)),
        Rule("private-identity", re.compile("micha[lł]|jasi[nń]ski", re.IGNORECASE), ("LICENSE", "LICENCE")),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check for private source-pipeline reference leaks.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--max-findings", type=int, default=200, help="Maximum findings to print.")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    violations: list[tuple[str, int, str, str]] = []
    print("==> sensitive reference leak smoke test")
    print(f"Root: {root}")
    if is_installed_package_root(root):
        print("SKIP: source-pipeline sensitive leak smoke is not valid for an installed child-project package.")
        return 0

    for path in candidate_files(root):
        if not path.is_file():
            continue
        relative = repo_relative(root, path)
        if skipped(relative):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        basename = path.name
        for rule in rules():
            if rule.allowed_basenames and basename in rule.allowed_basenames:
                continue
            for match in rule.regex.finditer(text):
                violations.append((relative, line_number(text, match.start()), rule.rule_id, match.group(0)))
                if len(violations) >= args.max_findings:
                    break
            if len(violations) >= args.max_findings:
                break
        if len(violations) >= args.max_findings:
            break

    if violations:
        print(f"\nFAIL: found {len(violations)} sensitive reference leak(s).")
        for path, line, rule_id, match in violations:
            print(f"{path}:{line}: {rule_id}: {match}")
        if len(violations) >= args.max_findings:
            print(f"Output stopped at MaxFindings={args.max_findings}.")
        return 1

    print("OK: no sensitive reference leaks found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
