import argparse
import glob
import json
import sys
from pathlib import Path
from typing import Any

import yaml


LONG_TEXT_LIMIT = 120
EXCLUDED_CACHE_PARTS = {
    ".git",
    "Tools/Python312",
    "Tools/python-installer",
    "Tools/tmp",
}

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


class DocToolDumper(yaml.SafeDumper):
    pass


def represent_multiline_string(dumper: yaml.Dumper, value: str) -> yaml.ScalarNode:
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


DocToolDumper.add_representer(str, represent_multiline_string)


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def write_value(value: Any, output_json: bool) -> None:
    if output_json:
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return
    print(yaml.dump(value, Dumper=DocToolDumper, allow_unicode=True, sort_keys=False, width=1000))


def summarize_value(value: Any) -> Any:
    if isinstance(value, dict):
        summary: dict[str, Any] = {}
        for key, child in value.items():
            if key in {"content", "body", "goal", "summary"} and isinstance(child, str):
                summary[key] = summarize_text(child)
            elif key == "toc" and isinstance(child, list):
                summary[key] = [summarize_toc_item(item) for item in child]
            elif key == "index":
                summary[key] = summarize_index(child)
            elif key == "items" and isinstance(child, dict):
                summary[key] = {
                    item_key: summarize_item(item_value)
                    for item_key, item_value in child.items()
                }
            elif isinstance(child, (dict, list)):
                summary[key] = summarize_value(child)
            else:
                summary[key] = child
        return summary
    if isinstance(value, list):
        return [summarize_value(item) for item in value]
    if isinstance(value, str):
        return summarize_text(value)
    return value


def summarize_text(text: str) -> str:
    compact = " ".join(text.split())
    if len(compact) <= LONG_TEXT_LIMIT:
        return compact
    return f"<text {len(text)} chars: {compact[:LONG_TEXT_LIMIT]}...>"


def summarize_toc_item(item: Any) -> Any:
    if not isinstance(item, dict):
        return summarize_value(item)
    allowed = ["id", "key", "title", "ref", "status", "priority", "tags"]
    return {key: item[key] for key in allowed if key in item}


def summarize_index_item(item: Any) -> Any:
    if isinstance(item, str):
        return item
    if not isinstance(item, dict):
        return summarize_value(item)
    allowed = ["key", "title", "status", "priority", "tags"]
    return {key: item[key] for key in allowed if key in item}


def summarize_index(index: Any) -> Any:
    if isinstance(index, dict):
        return {str(key): summarize_text(str(value)) for key, value in index.items()}
    if isinstance(index, list):
        return [summarize_index_item(item) for item in index]
    return summarize_value(index)


def summarize_item(item: Any) -> Any:
    if not isinstance(item, dict):
        return summarize_value(item)
    summary = {"title": item.get("title", "")}
    data = item.get("data")
    if data is None:
        data = {key: value for key, value in item.items() if key != "title"}
    if isinstance(data, dict):
        summary["data_keys"] = list(data.keys())
        if "content" in data and isinstance(data["content"], str):
            summary["content"] = summarize_text(data["content"])
    elif isinstance(data, str):
        summary["data"] = summarize_text(data)
    return summary


def resolve_selector(document: Any, selector: str) -> Any:
    if selector == "" or selector == ".":
        return document

    ref = resolve_key_to_ref(document, selector)
    if ref:
        selector = ref

    current = document
    for part in selector.split("."):
        if isinstance(current, dict):
            if part in current:
                current = current[part]
                continue
            if part.isdigit() and str(part) in current:
                current = current[str(part)]
                continue
            raise KeyError(f"Missing path part '{part}' in selector '{selector}'")
        if isinstance(current, list):
            try:
                index = int(part)
            except ValueError as exc:
                raise KeyError(
                    f"Selector part '{part}' is not a list index in '{selector}'"
                ) from exc
            current = current[index]
            continue
        raise KeyError(f"Cannot descend into scalar at '{part}' in selector '{selector}'")
    return current


def resolve_key_to_ref(document: Any, key: str) -> str:
    if isinstance(document, dict):
        items = document.get("items")
        if isinstance(items, dict) and key in items:
            if isinstance(items[key], dict) and "data" in items[key]:
                return f"items.{key}.data"
            return f"items.{key}"
        index = document.get("index")
        if isinstance(index, dict) and key in index and isinstance(items, dict) and key in items:
            if isinstance(items[key], dict) and "data" in items[key]:
                return f"items.{key}.data"
            return f"items.{key}"
        if isinstance(index, list):
            for item in index:
                if isinstance(item, dict) and str(item.get("key", "")) == key:
                    item_key = str(item.get("key", ""))
                    if isinstance(items, dict) and item_key in items:
                        if isinstance(items[item_key], dict) and "data" in items[item_key]:
                            return f"items.{item_key}.data"
                        return f"items.{item_key}"
    for node in walk_nodes(document):
        if not isinstance(node, dict):
            continue
        if str(node.get("key", "")) == key:
            return str(node.get("ref", ""))
        if str(node.get("id", "")) == key and "ref" in node:
            return str(node.get("ref", ""))
    return ""


def walk_nodes(value: Any):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_nodes(child)


def build_document_cache(path: Path, repo_root: Path) -> dict[str, Any]:
    document = load_yaml(path)
    keys: dict[str, dict[str, Any]] = {}
    collect_keys(document, "", keys)
    relative_path = path.resolve().relative_to(repo_root.resolve()).as_posix()
    return {
        "path": relative_path,
        "document": get_document_metadata(document),
        "routing": summarize_value(get_document_routing(document)),
        "toc": summarize_value(get_document_index(document)),
        "top_level_keys": list(document.keys()) if isinstance(document, dict) else [],
        "keys": keys,
    }


def get_document_metadata(document: Any) -> dict[str, Any]:
    if not isinstance(document, dict):
        return {}
    if isinstance(document.get("document"), dict):
        return document.get("document", {})
    meta = document.get("meta")
    if isinstance(meta, dict) and isinstance(meta.get("document"), dict):
        return meta.get("document", {})
    return {}


def get_document_index(document: Any) -> Any:
    if not isinstance(document, dict):
        return []
    if isinstance(document.get("index"), (dict, list)):
        return document.get("index", [])
    if isinstance(document.get("toc"), list):
        return document.get("toc", [])
    return []


def get_document_routing(document: Any) -> dict[str, Any]:
    if not isinstance(document, dict):
        return {}
    if isinstance(document.get("routing"), dict):
        return document.get("routing", {})
    meta = document.get("meta")
    if isinstance(meta, dict) and isinstance(meta.get("routing"), dict):
        return meta.get("routing", {})
    return {}


def collect_keys(value: Any, path: str, keys: dict[str, dict[str, Any]]) -> None:
    if isinstance(value, dict):
        items = value.get("items")
        if isinstance(items, dict):
            for item_key, item in items.items():
                title = item.get("title", "") if isinstance(item, dict) else ""
                target_path = f"items.{item_key}.data" if isinstance(item, dict) and "data" in item else f"items.{item_key}"
                keys[str(item_key)] = {
                    "path": target_path,
                    "title": title,
                    "ref": target_path,
                    "status": "",
                }
        stable_key = value.get("key")
        stable_id = value.get("id")
        for candidate in [stable_key, stable_id]:
            if candidate is None:
                continue
            candidate_text = str(candidate)
            if not candidate_text:
                continue
            if candidate_text in keys and keys[candidate_text].get("title", ""):
                continue
            keys[candidate_text] = {
                "path": path,
                "title": value.get("title", ""),
                "ref": value.get("ref", path),
                "status": value.get("status", ""),
            }
        for child_key, child_value in value.items():
            child_path = child_key if path == "" else f"{path}.{child_key}"
            collect_keys(child_value, child_path, keys)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            collect_keys(child, f"{path}.{index}" if path else str(index), keys)


def expand_paths(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            paths.extend(Path(match) for match in matches)
        else:
            paths.append(Path(pattern))
    return sorted(
        {
            path.resolve()
            for path in paths
            if path.exists() and path.is_file() and not is_excluded_cache_path(path)
        }
    )


def is_excluded_cache_path(path: Path) -> bool:
    normalized = path.as_posix()
    return any(f"/{part}/" in normalized or normalized.endswith(f"/{part}") for part in EXCLUDED_CACHE_PARTS)


def command_keys(args: argparse.Namespace) -> None:
    document = load_yaml(Path(args.path))
    output = {
        "path": str(Path(args.path)),
        "document": get_document_metadata(document),
        "top_level_keys": list(document.keys()) if isinstance(document, dict) else [],
        "toc": summarize_value(get_document_index(document)),
        "keys": {},
    }
    collect_keys(document, "", output["keys"])
    write_value(output, args.json)


def command_read(args: argparse.Namespace) -> None:
    document = load_yaml(Path(args.path))
    value = resolve_selector(document, args.selector)
    write_value(value, args.json)


def command_build_cache(args: argparse.Namespace) -> None:
    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    document_caches = [build_document_cache(path, repo_root) for path in expand_paths(args.paths)]
    cache = {
        "schema_version": 1,
        "documents": document_caches,
    }
    output_path = output_dir / "doc_index.json"
    output_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(output_path))


def main() -> None:
    parser = argparse.ArgumentParser(description="YAML documentation reader/cache helper.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    keys_parser = subparsers.add_parser("keys")
    keys_parser.add_argument("path")
    keys_parser.add_argument("--json", action="store_true")
    keys_parser.set_defaults(func=command_keys)

    read_parser = subparsers.add_parser("read")
    read_parser.add_argument("path")
    read_parser.add_argument("selector")
    read_parser.add_argument("--json", action="store_true")
    read_parser.set_defaults(func=command_read)

    cache_parser = subparsers.add_parser("build-cache")
    cache_parser.add_argument("paths", nargs="+")
    cache_parser.add_argument("--output-dir", required=True)
    cache_parser.add_argument("--repo-root", required=True)
    cache_parser.set_defaults(func=command_build_cache)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
