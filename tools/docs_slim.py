import argparse
import copy
from pathlib import Path
from typing import Any

import yaml


EXCLUDED_PARTS = {".git", "Tools/Python312", "Tools/python-installer", "Tools/tmp"}


class LiteralString(str):
    pass


class SlimYamlDumper(yaml.SafeDumper):
    pass


def represent_multiline_string(dumper: yaml.Dumper, value: str) -> yaml.ScalarNode:
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


SlimYamlDumper.add_representer(str, represent_multiline_string)
SlimYamlDumper.add_representer(LiteralString, represent_multiline_string)


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def write_yaml(path: Path, value: Any) -> None:
    path.write_text(
        yaml.dump(value, Dumper=SlimYamlDumper, allow_unicode=True, sort_keys=False, width=1000),
        encoding="utf-8",
    )


def repo_relative(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def is_excluded(path: Path, repo_root: Path) -> bool:
    relative = repo_relative(path, repo_root)
    return any(relative == part or relative.startswith(f"{part}/") for part in EXCLUDED_PARTS)


def iter_yaml_paths(repo_root: Path, patterns: list[str]) -> list[Path]:
    paths: set[Path] = set()
    for pattern in patterns:
        for path in repo_root.glob(pattern):
            if path.is_file() and path.suffix in {".yaml", ".yml"} and not is_excluded(path, repo_root):
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
    "non_negotiable_worldgen_principles",
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


def slim_document(data: Any) -> Any:
    if not isinstance(data, dict):
        return data
    raw_items = data.get("items")
    if not isinstance(raw_items, dict):
        return data

    slimmed_items = {key: slim_item(key, item) for key, item in raw_items.items()}
    index_keys = order_item_keys(normalize_index_keys(data.get("index", []), slimmed_items))
    ordered_keys = ["quick_index"] + index_keys
    ordered_items = {"quick_index": build_quick_index_item(index_keys, slimmed_items)}
    ordered_items.update({key: slimmed_items[key] for key in index_keys if key in slimmed_items})
    result: dict[str, Any] = {
        "index": ordered_keys,
        "items": ordered_items,
    }
    for key, value in data.items():
        if key in {"index", "quick_index", "items", "meta"}:
            continue
        result[key] = copy.deepcopy(value)
    if isinstance(data.get("meta"), dict):
        result["meta"] = copy.deepcopy(data["meta"])
    return result


def command_slim(args: argparse.Namespace) -> None:
    repo_root = Path(args.repo_root).resolve()
    paths = iter_yaml_paths(repo_root, args.paths)
    changed: list[str] = []
    for path in paths:
        original = load_yaml(path)
        slimmed = slim_document(original)
        rendered = yaml.dump(slimmed, Dumper=SlimYamlDumper, allow_unicode=True, sort_keys=False, width=1000)
        current = path.read_text(encoding="utf-8")
        if slimmed == original and rendered == current:
            continue
        changed.append(repo_relative(path, repo_root))
        if not args.check:
            path.write_text(rendered, encoding="utf-8")
    for path in changed:
        print(path)
    if args.check and changed:
        raise SystemExit(1)
    print(f"OK: {'would slim' if args.check else 'slimmed'} {len(changed)} YAML document(s).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Slim YAML documents to index/items/meta layout.")
    parser.add_argument("paths", nargs="*", default=["**/*.yaml", "**/*.yml"])
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    command_slim(args)


if __name__ == "__main__":
    main()
