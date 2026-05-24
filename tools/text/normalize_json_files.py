import argparse
import json
import sys
from pathlib import Path
from typing import Any


EXCLUDED_PARTS = {
    ".git",
    "AI-compiled/project/knowledge.sqlite",
    "ignored",
    "tools/Python312",
    "tools/tmp",
}
DEFAULT_EXCLUDED_PREFIXES = [
    "AI-compiled/",
    "SocratexAI/AI-compiled/",
    "SocratexAI/docs-tech/cache/",
    "SocratexAI/ignored/",
    "docs-tech/cache/",
]
DEFAULT_EXCLUDED_PATHS = [
    "docs-tech/CODE_LINE_INDEX.json",
    "docs-tech/LARGE_FILES.json",
    "docs-tech/PIPELINE-BOOTSTRAP.json",
    "docs-tech/TOOL-ERRORS.json",
]


def split_values(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        for part in value.split(","):
            item = part.strip()
            if item:
                output.append(item)
    return output


def normalize_repo_path(path: str) -> str:
    return path.replace("\\", "/").strip()


def is_excluded(path: Path, excluded_prefixes: list[str], excluded_paths: list[str]) -> bool:
    normalized = normalize_repo_path(path.as_posix())
    parts = normalized.split("/")
    return (
        any(part in parts or normalized.endswith(part) for part in EXCLUDED_PARTS)
        or any(normalized.startswith(prefix) for prefix in excluded_prefixes)
        or normalized in excluded_paths
    )


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
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    normalized = json.dumps(ordered_document(data), ensure_ascii=False, indent=4) + "\n"
    current = path.read_text(encoding="utf-8-sig")
    changed = current != normalized
    if changed and not check:
        path.write_text(normalized, encoding="utf-8", newline="\n")
    return changed


def iter_paths(root: Path, patterns: list[str], excluded_prefixes: list[str], excluded_paths: list[str]) -> list[Path]:
    paths: set[Path] = set()
    for pattern in patterns:
        for path in root.glob(pattern):
            if (
                path.is_file()
                and path.suffix.lower() == ".json"
                and not is_excluded(path.relative_to(root), excluded_prefixes, excluded_paths)
            ):
                paths.add(path.resolve())
    return sorted(paths)


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize JSON files as UTF-8, LF, four-space indentation, final newline.")
    parser.add_argument("paths", nargs="*", default=["**/*.json"])
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--exclude-prefix", action="append", default=[])
    parser.add_argument("--exclude-path", action="append", default=[])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    excluded_prefixes = DEFAULT_EXCLUDED_PREFIXES + split_values(args.exclude_prefix)
    excluded_paths = DEFAULT_EXCLUDED_PATHS + split_values(args.exclude_path)
    patterns = split_values(args.path) if args.path else args.paths
    changed: list[str] = []
    errors: list[str] = []
    for path in iter_paths(root, patterns, excluded_prefixes, excluded_paths):
        relative = path.relative_to(root).as_posix()
        try:
            if normalize_path(path, args.check):
                changed.append(relative)
        except Exception as exc:
            errors.append(f"{relative}: JSON normalization failed: {exc}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    for path in changed:
        print(path)
    print(f"OK: {'would normalize' if args.check else 'normalized'} {len(changed)} JSON file(s).")
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
