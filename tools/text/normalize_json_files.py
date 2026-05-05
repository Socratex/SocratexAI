import argparse
import json
from pathlib import Path
from typing import Any


EXCLUDED_PARTS = {".git", "AI-compiled/project/knowledge.sqlite", "ignored", "tools/Python312", "tools/tmp"}


def is_excluded(path: Path) -> bool:
    normalized = path.as_posix()
    return any(part in normalized.split("/") or normalized.endswith(part) for part in EXCLUDED_PARTS)


def ordered_document(value: Any) -> Any:
    if not isinstance(value, dict):
        return value
    ordered: dict[str, Any] = {}
    for key in ("index", "content", "items", "metadata", "meta"):
        if key in value:
            ordered[key] = value[key]
    for key, child in value.items():
        if key not in ordered:
            ordered[key] = child
    return ordered


def normalize_path(path: Path, check: bool) -> bool:
    data = json.loads(path.read_text(encoding="utf-8"))
    normalized = json.dumps(ordered_document(data), ensure_ascii=False, indent=4) + "\n"
    current = path.read_text(encoding="utf-8")
    changed = current != normalized
    if changed and not check:
        path.write_text(normalized, encoding="utf-8", newline="\n")
    return changed


def iter_paths(root: Path, patterns: list[str]) -> list[Path]:
    paths: set[Path] = set()
    for pattern in patterns:
        for path in root.glob(pattern):
            if path.is_file() and path.suffix.lower() == ".json" and not is_excluded(path.relative_to(root)):
                paths.add(path.resolve())
    return sorted(paths)


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize JSON files as UTF-8, LF, four-space indentation, final newline.")
    parser.add_argument("paths", nargs="*", default=["**/*.json"])
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    changed = []
    for path in iter_paths(root, args.paths):
        if normalize_path(path, args.check):
            changed.append(path.relative_to(root).as_posix())

    for path in changed:
        print(path)
    print(f"OK: {'would normalize' if args.check else 'normalized'} {len(changed)} JSON file(s).")
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
