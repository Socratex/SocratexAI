#!/usr/bin/env python3
"""Validate SocratexPipeline feature contracts with Python-only tooling."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
from pipeline_package import DEFAULT_MANAGED_PATHS  # noqa: E402
from shared.repo_helpers import changed_paths as repo_changed_paths  # noqa: E402
from shared.repo_helpers import normalize_repo_path, repo_root as shared_repo_root  # noqa: E402


PIPELINE_ROOT_FILES = {
    "AGENTS.md",
    "PUBLIC-BOOTSTRAP.md",
    "QUALITY-GATE.json",
    "CHANGELOG.json",
    "COMMANDS.json",
    "DOCS.json",
    "FLOWS.json",
    "JSON-FORMAT-CONTRACT.json",
    "LICENSE",
    "NOTICE",
    "SCRIPTS.json",
    "WORKFLOW.json",
    "pipeline_featurelist.json",
    "README.md",
}
PIPELINE_ROOT_DIRS = ("tools/", "core/", "project/", "profiles/", "templates/", "adapters/", "evals/")
ALLOWED_DIRECTIONS = {"source_to_child", "child_to_source", "bidirectional", "source_only"}


def repo_root(start: Path) -> Path:
    root = shared_repo_root(start, marker_files=("SCRIPTS.json", "pipeline_featurelist.json"), use_git=False)
    if (root / "SCRIPTS.json").is_file() and (root / "pipeline_featurelist.json").is_file():
        return root
    raise SystemExit("Could not resolve repository root from current path.")


def script_package_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_contract_root(requested_root: str) -> Path:
    root = repo_root(Path(requested_root))
    package_root = repo_root(script_package_root())
    try:
        package_inside_requested = package_root.is_relative_to(root)
    except ValueError:
        package_inside_requested = False

    if root != package_root and package_inside_requested and is_installed_package_root(package_root):
        print(f"INFO: using installed SocratexAI package root for feature contracts: {package_root}")
        print(f"INFO: child project root is not a source pipeline contract root: {root}")
        return package_root
    return root


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return data


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        raw = value
    else:
        raw = [value]
    result: list[str] = []
    for item in raw:
        text = str(item).strip()
        if text and text not in result:
            result.append(text)
    return result


def raw_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    raw = value if isinstance(value, list) else [value]
    return [text for item in raw if (text := str(item).strip())]


def duplicate_items(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return duplicates


def add_duplicate_list_errors(errors: list[str], owner: str, field: str, value: Any) -> None:
    duplicates = duplicate_items(raw_string_list(value))
    for duplicate in duplicates:
        errors.append(f"{owner} contains duplicate {field} entry: {duplicate}")


def normalize_path(value: str) -> str:
    return normalize_repo_path(value)


def content_of(document: dict[str, Any]) -> dict[str, Any]:
    content = document.get("content")
    return content if isinstance(content, dict) else document


def features_of(feature_list: dict[str, Any]) -> list[str]:
    content = content_of(feature_list)
    return as_list(content.get("features"))


def raw_features_of(feature_list: dict[str, Any]) -> list[str]:
    content = content_of(feature_list)
    return raw_string_list(content.get("features"))


def contracts_of(feature_list: dict[str, Any]) -> dict[str, Any]:
    content = content_of(feature_list)
    contracts = content.get("feature_contracts")
    return contracts if isinstance(contracts, dict) else {}


def is_canonical_list_document(document: dict[str, Any]) -> bool:
    return list(document.keys()) == ["index", "content", "metadata"]


def is_installed_package_root(root: Path) -> bool:
    return root.name == "SocratexAI" and not (root / ".git").exists() and (root.parent / "SOCRATEX.md").is_file()


def path_under_any(path: str, roots: list[str]) -> bool:
    normalized = normalize_path(path)
    for root in roots:
        prefix = normalize_path(root).rstrip("/")
        if normalized == prefix or normalized.startswith(prefix + "/"):
            return True
    return False


def pipeline_owned_path(path: str) -> bool:
    normalized = normalize_path(path)
    if normalized.startswith("AI-compiled/"):
        return False
    return normalized in PIPELINE_ROOT_FILES or normalized.startswith(PIPELINE_ROOT_DIRS)


def path_exists(root: Path, relative: str) -> bool:
    normalized = normalize_path(relative)
    if "*" in normalized:
        return bool(list(root.glob(normalized)))
    return (root / normalized).exists()


def changed_paths(root: Path, explicit: list[str]) -> list[str]:
    return repo_changed_paths(root, explicit, diff_filter="ACMRD")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SocratexPipeline feature contracts.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--paths", nargs="*", default=[], help="Changed paths, comma-separated or repeated.")
    args = parser.parse_args()

    root = resolve_contract_root(args.repo_root)
    if is_installed_package_root(root):
        print(f"SKIP: source-pipeline feature contract check is not valid for an installed child-project package: {root}")
        return 0

    errors: list[str] = []
    feature_list = read_json(root / "pipeline_featurelist.json")
    scripts = read_json(root / "SCRIPTS.json")
    script_content = content_of(scripts)

    if not is_canonical_list_document(feature_list):
        errors.append("pipeline_featurelist.json must use canonical root keys in this order: index, content, metadata.")
    else:
        index = as_list(feature_list.get("index"))
        content = feature_list.get("content") if isinstance(feature_list.get("content"), dict) else {}
        for key in ("features", "feature_contracts"):
            if key not in index:
                errors.append(f"pipeline_featurelist.json index must include '{key}'.")
            if key not in content:
                errors.append(f"pipeline_featurelist.json content is missing '{key}'.")

    raw_features = raw_features_of(feature_list)
    features = features_of(feature_list)
    contracts = contracts_of(feature_list)
    for feature in duplicate_items(raw_features):
        errors.append(f"Duplicate feature id in features index: {feature}")
    feature_set = set(features)
    if not features:
        errors.append("pipeline_featurelist.json must contain a non-empty content.features index.")
    if not contracts:
        errors.append("pipeline_featurelist.json must contain content.feature_contracts.")
    for feature in features:
        if feature not in contracts:
            errors.append(f"Missing feature contract for feature id: {feature}")
    for contract_name in contracts:
        if contract_name not in feature_set:
            errors.append(f"feature_contracts contains key not present in features index: {contract_name}")

    all_required_paths: list[str] = []
    installed_package = is_installed_package_root(root)
    for feature in features:
        contract = contracts.get(feature)
        if not isinstance(contract, dict):
            continue
        if not str(contract.get("summary", "")).strip():
            errors.append(f"Feature '{feature}' contract is missing summary.")
        required_paths = as_list(contract.get("required_paths"))
        required_scripts = as_list(contract.get("required_scripts"))
        required_docs = as_list(contract.get("required_docs"))
        promotion_checklist = as_list(contract.get("promotion_checklist"))
        verification_commands = as_list(contract.get("verification_commands"))
        sync_direction = str(contract.get("sync_direction", "")).strip()
        for field_name in (
            "required_paths",
            "required_scripts",
            "required_docs",
            "promotion_checklist",
            "verification_commands",
        ):
            add_duplicate_list_errors(errors, f"Feature '{feature}'", field_name, contract.get(field_name))
        if not required_paths:
            errors.append(f"Feature '{feature}' must list at least one required_paths entry.")
        if not promotion_checklist:
            errors.append(f"Feature '{feature}' must list promotion_checklist.")
        if not verification_commands:
            errors.append(f"Feature '{feature}' must list verification_commands.")
        if not str(contract.get("known_failure_if_missing", "")).strip():
            errors.append(f"Feature '{feature}' must describe known_failure_if_missing.")
        if sync_direction not in ALLOWED_DIRECTIONS:
            errors.append(f"Feature '{feature}' has invalid sync_direction '{sync_direction}'.")

        skip_source_only = installed_package and sync_direction == "source_only"
        for required_path in required_paths:
            if skip_source_only:
                continue
            all_required_paths.append(required_path)
            if not path_exists(root, required_path):
                errors.append(f"Feature '{feature}' required path is missing: {normalize_path(required_path)}")
            if sync_direction in {"source_to_child", "bidirectional"} and not path_under_any(required_path, DEFAULT_MANAGED_PATHS):
                errors.append(f"Feature '{feature}' required path is not mirrored by managed package sync: {normalize_path(required_path)}")
        for script_name in required_scripts:
            if script_name not in script_content:
                errors.append(f"Feature '{feature}' requires script missing from SCRIPTS.json: {script_name}")
                continue
            entry = script_content.get(script_name)
            script_path = entry.get("path") if isinstance(entry, dict) else ""
            if not str(script_path).strip():
                errors.append(f"Feature '{feature}' requires script with empty path: {script_name}")
            elif not (root / normalize_path(str(script_path))).is_file():
                errors.append(f"Feature '{feature}' requires script file missing from repo: {script_name} -> {script_path}")
        for doc_path in required_docs:
            if not skip_source_only and not path_exists(root, doc_path):
                errors.append(f"Feature '{feature}' required doc is missing: {normalize_path(doc_path)}")
        catalog_entries = contract.get("required_catalog_entries")
        if isinstance(catalog_entries, dict):
            for catalog_name, entries in catalog_entries.items():
                add_duplicate_list_errors(
                    errors,
                    f"Feature '{feature}'",
                    f"required_catalog_entries.{catalog_name}",
                    entries,
                )
                catalog_file = catalog_name if str(catalog_name).endswith(".json") else f"{catalog_name}.json"
                catalog_path = root / catalog_file
                if not catalog_path.is_file():
                    errors.append(f"Feature '{feature}' references missing catalog: {catalog_file}")
                    continue
                catalog_content = content_of(read_json(catalog_path))
                for entry_name in as_list(entries):
                    if entry_name not in catalog_content:
                        errors.append(f"Feature '{feature}' requires missing catalog entry: {catalog_file} -> {entry_name}")

    pipeline_changed = [path for path in changed_paths(root, args.paths) if pipeline_owned_path(path)]
    for path in pipeline_changed:
        if path == "pipeline_featurelist.json":
            continue
        if not path_under_any(path, all_required_paths):
            errors.append(f"Changed pipeline-owned path is not assigned to any feature contract required_paths: {path}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK: feature contracts cover {len(features)} feature(s).")
    if pipeline_changed:
        print("OK: changed pipeline-owned paths are assigned to feature contracts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
