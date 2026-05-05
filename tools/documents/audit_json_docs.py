import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_LEGACY_DOCUMENT_KEYS = {"id", "key", "title", "type", "version", "owner", "language", "canonical", "generated"}
EXCLUDED_PARTS = {".git", "Tools/Python312", "Tools/python-installer", "Tools/tmp", "ignored"}


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def repo_path(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def is_excluded(path: Path, repo_root: Path) -> bool:
    relative = repo_path(path, repo_root)
    return any(relative == part or relative.startswith(f"{part}/") for part in EXCLUDED_PARTS)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_selector(document: Any, selector: str) -> Any:
    current = document
    if selector in {"", "."}:
        return current
    for part in selector.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
            continue
        if isinstance(current, list):
            current = current[int(part)]
            continue
        raise KeyError(part)
    return current


def validate_document(path: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    relative = repo_path(path, repo_root)
    try:
        data = load_json(path)
    except Exception as exc:
        return [f"{relative}: JSON parse failed: {exc}"]

    if not isinstance(data, dict):
        return [f"{relative}: top-level JSON value must be an object."]

    if "index" in data or "items" in data or "content" in data:
        errors.extend(validate_compact_document(data, relative))
    elif "document" in data or "toc" in data:
        errors.extend(validate_legacy_document(data, relative, repo_root))
    else:
        return errors

    text = path.read_text(encoding="utf-8")
    forbidden_tokens = ["legacy_markdown", "source_migrated_from", "compatibility shim"]
    for token in forbidden_tokens:
        if token in text:
            errors.append(f"{relative}: contains retired migration token: {token}.")

    return errors


def validate_compact_document(data: dict[str, Any], relative: str) -> list[str]:
    errors: list[str] = []
    index = data.get("index")
    items = data.get("items")
    content = data.get("content")
    collection = items if isinstance(items, dict) else content
    collection_name = "items" if isinstance(items, dict) else "content"
    if not isinstance(collection, dict):
        errors.append(f"{relative}: compact document must have an items or content object.")
        collection = {}
    if not isinstance(index, (dict, list)):
        errors.append(f"{relative}: compact document must have an index list or object.")
        index_entries: list[tuple[str, Any, str]] = []
    elif isinstance(index, dict):
        index_entries = [(str(key), value, f"index.{key}") for key, value in index.items()]
    else:
        index_entries = []
        for row_index, item in enumerate(index):
            if isinstance(item, str):
                index_entries.append((item.strip(), item, f"index[{row_index}]"))
            elif isinstance(item, dict):
                index_entries.append((str(item.get("key", "")).strip(), item.get("title", ""), f"index[{row_index}]"))
            else:
                errors.append(f"{relative}: index[{row_index}] must be a key string or object.")
    for item_key, label, location in index_entries:
        if item_key == "":
            errors.append(f"{relative}: {location} missing non-empty key.")
            continue
        if str(label).strip() == "":
            errors.append(f"{relative}: {location} missing non-empty label.")
        if item_key not in collection:
            errors.append(f"{relative}: {location} points at missing item: {item_key}.")
    for item_key, item in collection.items():
        if not isinstance(item, dict):
            errors.append(f"{relative}: {collection_name}.{item_key} must be an object.")
            continue
        if "title" in item and str(item.get("title", "")).strip() == "":
            errors.append(f"{relative}: {collection_name}.{item_key}.title must not be empty.")
        if not item:
            errors.append(f"{relative}: {collection_name}.{item_key} must contain data.")
    if collection_name == "items":
        if "quick_index" not in collection:
            errors.append(f"{relative}: items.quick_index is missing.")
        elif isinstance(index, list) and (not index or index[0] != "quick_index"):
            errors.append(f"{relative}: index must start with quick_index.")
        if collection:
            first_item_key = next(iter(collection.keys()))
            if first_item_key != "quick_index":
                errors.append(f"{relative}: items must start with quick_index.")
    return errors


def validate_legacy_document(data: dict[str, Any], relative: str, repo_root: Path) -> list[str]:
    errors: list[str] = []
    metadata = data.get("document")
    if not isinstance(metadata, dict):
        errors.append(f"{relative}: missing document metadata object.")
    else:
        missing = sorted(REQUIRED_LEGACY_DOCUMENT_KEYS - set(metadata.keys()))
        if missing:
            errors.append(f"{relative}: document metadata missing key(s): {', '.join(missing)}.")
        if str(metadata.get("id", "")).strip() == "":
            errors.append(f"{relative}: document.id must not be empty.")
        if str(metadata.get("key", "")).strip() == "":
            errors.append(f"{relative}: document.key must not be empty.")
        if str(metadata.get("title", "")).strip() == "":
            errors.append(f"{relative}: document.title must not be empty.")

    toc = data.get("toc")
    if toc is None:
        errors.append(f"{relative}: missing toc list.")
    elif not isinstance(toc, list):
        errors.append(f"{relative}: toc must be a list.")
    else:
        for index, item in enumerate(toc):
            if not isinstance(item, dict):
                errors.append(f"{relative}: toc[{index}] must be an object.")
                continue
            for key in ["key", "title", "ref"]:
                if str(item.get(key, "")).strip() == "":
                    errors.append(f"{relative}: toc[{index}] missing non-empty {key}.")
            ref = str(item.get("ref", ""))
            if ref == "":
                continue
            if ":" in ref:
                target_path_text = ref.split(":", 1)[0]
                target_path = repo_root / target_path_text
                if target_path_text.endswith(".json") and not target_path.exists():
                    errors.append(f"{relative}: toc[{index}] cross-file ref target does not exist: {target_path_text}.")
                continue
            try:
                resolve_selector(data, ref)
            except Exception:
                errors.append(f"{relative}: toc[{index}] ref does not resolve locally: {ref}.")
    return errors


def validate_cache(repo_root: Path, json_paths: list[Path]) -> list[str]:
    cache_path = repo_root / "docs-tech/cache/doc_index.json"
    if not cache_path.exists():
        return ["docs-tech/cache/doc_index.json: missing generated document cache."]
    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"docs-tech/cache/doc_index.json: JSON parse failed: {exc}"]

    cached_paths = {
        str(item.get("path", "")).replace("\\", "/")
        for item in cache.get("documents", [])
        if isinstance(item, dict)
    }
    expected_paths = {repo_path(path, repo_root) for path in json_paths}
    missing = sorted(expected_paths - cached_paths)
    stale = sorted(path for path in cached_paths - expected_paths if path.endswith(".json"))
    errors: list[str] = []
    if missing:
        errors.append(f"docs-tech/cache/doc_index.json: missing JSON document(s): {', '.join(missing)}.")
    if stale:
        errors.append(f"docs-tech/cache/doc_index.json: stale JSON document(s): {', '.join(stale)}.")
    return errors


def validate_pipeline_config_schema(repo_root: Path) -> list[str]:
    path = repo_root / "templates" / "code" / "PIPELINE-CONFIG.json"
    relative = repo_path(path, repo_root)
    if not path.exists():
        return [f"{relative}: missing pipeline config template."]
    try:
        data = load_json(path)
    except Exception as exc:
        return [f"{relative}: JSON parse failed: {exc}"]
    errors: list[str] = []
    pipeline = data.get("pipeline")
    if not isinstance(pipeline, dict):
        errors.append(f"{relative}: missing pipeline object.")
    elif "update_source" not in pipeline:
        errors.append(f"{relative}: missing pipeline.update_source.")
    elif "remove_command" not in pipeline:
        errors.append(f"{relative}: missing pipeline.remove_command.")
    elif "reinitialize_command" not in pipeline:
        errors.append(f"{relative}: missing pipeline.reinitialize_command.")
    if not isinstance(data.get("changelog"), dict):
        errors.append(f"{relative}: missing changelog object.")
    if not isinstance(data.get("communication"), dict):
        errors.append(f"{relative}: missing communication object.")
    if not isinstance(data.get("project_profile"), dict):
        errors.append(f"{relative}: missing project_profile object.")
    if not isinstance(data.get("runtime_status"), dict):
        errors.append(f"{relative}: missing runtime_status object.")
    workflow = data.get("workflow")
    if not isinstance(workflow, dict):
        errors.append(f"{relative}: missing workflow object.")
    elif "branch_mode" not in workflow:
        errors.append(f"{relative}: missing workflow.branch_mode.")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate JSON documentation files and generated document cache.")
    parser.add_argument("--repo-root", required=True)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    json_paths = sorted(
        path
        for path in repo_root.rglob("*.json")
        if path.is_file() and not is_excluded(path, repo_root)
    )

    errors: list[str] = []
    for path in json_paths:
        errors.extend(validate_document(path, repo_root))
    errors.extend(validate_cache(repo_root, json_paths))
    errors.extend(validate_pipeline_config_schema(repo_root))

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)

    print(f"OK: validated {len(json_paths)} JSON document(s) and document cache.")


if __name__ == "__main__":
    main()
