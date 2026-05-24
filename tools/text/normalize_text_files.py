from __future__ import annotations

import argparse
from pathlib import Path


def convert_text_to_lf(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def expand_paths(paths: list[str]) -> list[str]:
    expanded: list[str] = []
    for path in paths:
        for entry in path.split(","):
            trimmed = entry.strip()
            if trimmed:
                expanded.append(trimmed)
    return expanded


def normalize_path(path: Path, check: bool) -> bool:
    content = path.read_text(encoding="utf-8")
    normalized = convert_text_to_lf(content)
    normalized_bytes = normalized.encode("utf-8")
    current_bytes = path.read_bytes()
    changed = current_bytes != normalized_bytes
    if changed and not check:
        path.write_bytes(normalized_bytes)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize selected text files to UTF-8 and LF line endings.")
    parser.add_argument("paths", nargs="*", default=["AGENTS.md", "DOCS.json"])
    parser.add_argument("--repo-root", "--root", default=".", dest="repo_root")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    changed_paths: list[str] = []

    for relative_path in expand_paths(args.paths):
        path = (root / relative_path).resolve()
        if normalize_path(path, args.check):
            changed_paths.append(relative_path)

    if not changed_paths:
        print("OK: text files already normalized")
        return 0

    if args.check:
        print("ERROR: text files need normalization:")
        for path in changed_paths:
            print(f" - {path}")
        return 1

    print("OK: normalized text files:")
    for path in changed_paths:
        print(f" - {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
