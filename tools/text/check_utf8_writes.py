from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_TOOLS_ROOT))

from shared.repo_helpers import git_lines  # noqa: E402


UNSAFE_COMMAND_PATTERN = re.compile(r"\b(Set-Content|Out-File|Add-Content)\b")
HUNK_PATTERN = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def expand_paths(values: list[str]) -> list[str]:
    expanded: list[str] = []
    for value in values:
        for item in value.split(","):
            trimmed = item.strip()
            if trimmed:
                expanded.append(trimmed)
    return expanded


def relative_git_path(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def tracked_by_git(repo_root: Path, git_path: str) -> bool:
    return bool(git_lines(repo_root, ["ls-files", "--error-unmatch", "--", git_path], allow_failure=True))


def added_line_numbers(path: Path, repo_root: Path) -> set[int] | None:
    git_path = relative_git_path(path, repo_root)
    if not tracked_by_git(repo_root, git_path):
        return None

    line_numbers: set[int] = set()
    current_new_line = 0

    for diff_line in git_lines(repo_root, ["diff", "--unified=0", "--", git_path], allow_failure=True):
        hunk_match = HUNK_PATTERN.match(diff_line)
        if hunk_match:
            current_new_line = int(hunk_match.group(1))
            continue
        if diff_line.startswith(("+++", "---")):
            continue
        if diff_line.startswith("+"):
            line_numbers.add(current_new_line)
            current_new_line += 1
            continue
        if diff_line.startswith("-"):
            continue
        if current_new_line > 0:
            current_new_line += 1

    return line_numbers


def check_path(path: Path, repo_root: Path) -> list[str]:
    if not path.is_file():
        return []

    checked_lines = added_line_numbers(path, repo_root)
    violations: list[str] = []
    display_path = relative_git_path(path, repo_root)

    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if checked_lines is not None and index not in checked_lines:
            continue
        if line.strip().startswith("#"):
            continue

        match = UNSAFE_COMMAND_PATTERN.search(line)
        if match:
            violations.append(
                f"{display_path}:{index}: use Write-Utf8File / tools/text/write_utf8_file.py instead of {match.group(1)}"
            )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Check changed text files for legacy unsafe text write commands.")
    parser.add_argument("paths", nargs="*", help="Files to check. Missing paths are ignored.")
    parser.add_argument(
        "--paths",
        dest="paths_option",
        action="append",
        default=[],
        help="Comma-separated or repeated files to check.",
    )
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[2]))
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    paths = expand_paths([*args.paths, *args.paths_option])
    violations: list[str] = []

    for path_text in paths:
        path = Path(path_text)
        if not path.is_absolute():
            path = repo_root / path
        violations.extend(check_path(path.resolve(), repo_root))

    if violations:
        print("ERROR: unsafe legacy text writes found:")
        for violation in violations:
            print(f" - {violation}")
        return 1

    print("OK: no unsafe legacy text writes in checked paths")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
