import argparse
import copy
import json
from pathlib import Path
from typing import Any

EXCLUDED_PARTS = {
    ".git",
    "AI-compiled",
    "docs-tech/cache",
    "ignored",
    "Tools/Python312",
    "Tools/python-installer",
    "Tools/tmp",
}
EXCLUDED_PATHS = {
    "docs-tech/CODE_LINE_INDEX.json",
    "docs-tech/LARGE_FILES.json",
    "docs-tech/PIPELINE-BOOTSTRAP.json",
    "docs-tech/TOOL-ERRORS.json",
}


class LiteralString(str):
    pass


def load_document(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def render_document(path: Path, value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=4) + "\n"


def write_document(path: Path, value: Any) -> None:
    path.write_text(render_document(path, value), encoding="utf-8", newline="\n")


def repo_relative(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def is_excluded(path: Path, repo_root: Path) -> bool:
    relative = repo_relative(path, repo_root)
    if relative in EXCLUDED_PATHS:
        return True
    return any(relative == part or relative.startswith(f"{part}/") for part in EXCLUDED_PARTS)


def iter_document_paths(repo_root: Path, patterns: list[str]) -> list[Path]:
    paths: set[Path] = set()
    for pattern in patterns:
        for path in repo_root.glob(pattern):
            if path.is_file() and path.suffix in {".json", ".json", ".json"} and not is_excluded(path, repo_root):
                paths.add(path.resolve())
    return sorted(paths)


def item_title(item_key: str, item: Any) -> str:
    if isinstance(item, dict) and isinstance(item.get("title"), str) and item["title"].strip():
        return item["title"].strip()
    return item_key.replace("_", " ").title()


SUPPORT_ITEM_KEYS = {
    "purpose",
    "pass_index",
    "pass_execution_contract",
    "current_strategic_direction",
    "non_negotiable_domain_modeling_principles",
    "active_passes",
    "current_recommended_next_step",
}


def normalize_index_keys(index: Any, items: dict[str, Any]) -> list[str]:
    keys: list[str] = []
    if isinstance(index, list):
        for entry in index:
            if isinstance(entry, str):
                key = entry.strip()
            elif isinstance(entry, dict):
                key = str(entry.get("key", "")).strip()
            else:
                key = ""
            if key and key not in keys:
                keys.append(key)
    elif isinstance(index, dict):
        for key in index.keys():
            key_text = str(key).strip()
            if key_text and key_text not in keys:
                keys.append(key_text)
    for key in items.keys():
        if key not in keys:
            keys.append(key)
    return [key for key in keys if key != "quick_index"]


def slim_item(item_key: str, item: Any) -> Any:
    if not isinstance(item, dict):
        return item
    title = item_title(item_key, item)
    payload = copy.deepcopy(item.get("data", item))
    if isinstance(payload, dict):
        payload.pop("key", None)
        payload.pop("level", None)
        payload.pop("title", None)
    slimmed: dict[str, Any] = {"title": title}
    if isinstance(payload, dict):
        slimmed.update(payload)
    else:
        slimmed["value"] = payload
    return slimmed


def order_item_keys(index_keys: list[str]) -> list[str]:
    return index_keys


def is_support_item_key(key: str) -> bool:
    if key.startswith("pass_") and pass_number_from_key(key):
        return False
    return (
        key in SUPPORT_ITEM_KEYS
        or key.endswith("_contract")
        or key.startswith("current_")
        or key.startswith("non_negotiable_")
    )


def pass_index_labels(items: dict[str, Any]) -> dict[str, str]:
    labels: dict[str, str] = {}
    pass_index = items.get("pass_index")
    if isinstance(pass_index, dict):
        content = pass_index.get("content")
        if isinstance(content, str) and content.strip():
            for line in content.splitlines():
                trimmed = line.strip()
                if not trimmed.startswith("- "):
                    continue
                for item_key in items.keys():
                    pass_number = pass_number_from_key(item_key)
                    if pass_number and f"Pass {pass_number}" in trimmed:
                        labels[item_key] = trimmed[2:].strip()
                        break
    return labels


def pass_number_from_key(key: str) -> str:
    if not key.startswith("pass_"):
        return ""
    parts = key.split("_")
    if len(parts) < 2 or not parts[1].isdigit():
        return ""
    return parts[1]


def build_quick_index_item(index_keys: list[str], items: dict[str, Any]) -> dict[str, str]:
    pass_labels = pass_index_labels(items)
    lines: list[str] = []
    for key in index_keys:
        lines.append(f"- {pass_labels.get(key, item_title(key, items.get(key, {})))}")
    if not lines:
        lines.append("- (empty)")
    return {
        "title": "Quick Index",
        "content": "\n".join(lines) + "\n",
    }


def metadata_from_legacy_root(data: dict[str, Any]) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    for source_key in ("metadata", "meta"):
        source = data.get(source_key)
        if isinstance(source, dict):
            metadata.update(copy.deepcopy(source))

    for key, value in data.items():
        if key in {"index", "quick_index", "items", "content", "metadata", "meta"}:
            continue
        metadata[key] = copy.deepcopy(value)
    return metadata


def canonical_document(index_keys: list[str], content: dict[str, Any], metadata: dict[str, Any], include_quick_index: bool) -> dict[str, Any]:
    ordered_keys = ["quick_index"] + index_keys if include_quick_index else list(index_keys)
    ordered_content: dict[str, Any] = {}
    if include_quick_index:
        ordered_content["quick_index"] = build_quick_index_item(index_keys, content)
    ordered_content.update({key: content[key] for key in index_keys if key in content})
    for key, value in content.items():
        if key not in ordered_content:
            ordered_content[key] = value

    return {
        "index": ordered_keys,
        "content": ordered_content,
        "metadata": metadata,
    }


def slim_document(data: Any) -> Any:
    if not isinstance(data, dict):
        return data

    raw_content = data.get("content")
    if isinstance(raw_content, dict):
        content = copy.deepcopy(raw_content)
        index_keys = order_item_keys(normalize_index_keys(data.get("index", []), content))
        include_quick_index = "quick_index" in raw_content
        return canonical_document(index_keys, content, metadata_from_legacy_root(data), include_quick_index)

    raw_items = data.get("items")
    if not isinstance(raw_items, dict):
        return data

    content = {key: slim_item(key, item) for key, item in raw_items.items()}
    index_keys = order_item_keys(normalize_index_keys(data.get("index", []), content))
    return canonical_document(index_keys, content, metadata_from_legacy_root(data), include_quick_index=True)


def command_slim(args: argparse.Namespace) -> None:
    repo_root = Path(args.repo_root).resolve()
    paths = iter_document_paths(repo_root, args.paths)
    changed: list[str] = []
    for path in paths:
        original = load_document(path)
        slimmed = slim_document(original)
        rendered = render_document(path, slimmed)
        current = path.read_text(encoding="utf-8")
        if slimmed == original and rendered == current:
            continue
        changed.append(repo_relative(path, repo_root))
        if not args.check:
            write_document(path, slimmed)
    for path in changed:
        print(path)
    if args.check and changed:
        raise SystemExit(1)
    print(f"OK: {'would normalize' if args.check else 'normalized'} {len(changed)} structured document(s).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize structured JSON documents to canonical index/content/metadata layout.")
    parser.add_argument("paths", nargs="*", default=["**/*.json"])
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    command_slim(args)


if __name__ == "__main__":
    main()
