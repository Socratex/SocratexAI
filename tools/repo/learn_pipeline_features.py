#!/usr/bin/env python3
"""Promote reviewed project feature contracts into the source feature list."""

from __future__ import annotations

import argparse
import re
from collections import OrderedDict
from datetime import date
from pathlib import Path
from typing import Any

from repo_tool_helpers import as_list, content_of, package_root, read_json, split_values, write_json


def features_of(document: dict[str, Any]) -> list[str]:
    return as_list(content_of(document).get("features"))


def contracts_of(document: dict[str, Any]) -> OrderedDict[str, Any]:
    contracts = content_of(document).get("feature_contracts")
    return OrderedDict(contracts or {}) if isinstance(contracts, dict) else OrderedDict()


def metadata_value(document: dict[str, Any], name: str, fallback: str) -> str:
    for container in (document, document.get("metadata") if isinstance(document.get("metadata"), dict) else {}):
        value = str(container.get(name, "")).strip()
        if value:
            return value
    return fallback


def excluded(feature: str, patterns: list[str]) -> bool:
    return any(pattern and re.search(pattern, feature) for pattern in patterns)


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote reusable feature IDs and contracts into source pipeline_featurelist.json.")
    parser.add_argument("--project-path", "-ProjectPath", required=True)
    parser.add_argument("--source-feature-list-path", "-SourceFeatureListPath", default="")
    parser.add_argument("--include-features", "-IncludeFeatures", nargs="*", default=[])
    parser.add_argument("--exclude-patterns", "-ExcludePatterns", nargs="*", default=["project_specific", "runtime_diagnostic"])
    parser.add_argument("--apply", "-Apply", action="store_true")
    parser.add_argument("--accept-all", "-AcceptAll", action="store_true")
    args = parser.parse_args()

    source_path = Path(args.source_feature_list_path).resolve() if args.source_feature_list_path else package_root() / "pipeline_featurelist.json"
    project_root = Path(args.project_path).resolve()
    project_path = project_root / "pipeline_featurelist.json"
    include = set(split_values(args.include_features))
    patterns = split_values(args.exclude_patterns)

    source = read_json(source_path)
    project = read_json(project_path)
    source_features = features_of(source)
    project_features = features_of(project)
    candidate_features = [feature for feature in project_features if feature not in source_features]
    selected = [
        feature
        for feature in candidate_features
        if args.accept_all or feature in include or not excluded(feature, patterns)
    ]

    print("==> pipeline feature learning")
    print(f"source: {source_path}")
    print(f"project: {project_path}")
    print(f"candidates: {len(candidate_features)}")
    for feature in candidate_features:
        print(f" - {feature} [{'selected' if feature in selected else 'excluded'}]")

    if not args.apply:
        print("No changes made. Rerun with --apply and optionally --include-features or --accept-all.")
        return 0
    if not selected:
        print("OK: no selected features to add.")
        return 0

    source_contracts = contracts_of(source)
    project_contracts = contracts_of(project)
    for feature in selected:
        if feature not in project_contracts:
            raise SystemExit(
                f"Selected feature '{feature}' has no feature_contracts entry in project feature list. Promote full artifacts and contract first."
            )

    updated = list(source_features)
    for feature in selected:
        if feature not in updated:
            updated.append(feature)
        source_contracts[feature] = project_contracts[feature]

    payload = OrderedDict(
        index=["features", "feature_contracts"],
        content=OrderedDict(features=updated, feature_contracts=source_contracts),
        metadata=OrderedDict(
            schema="socratex-pipeline-featurelist/v4",
            pipeline_id=metadata_value(source, "pipeline_id", "socratex_pipeline"),
            role=metadata_value(source, "role", "source"),
            updated_at=date.today().isoformat(),
            comparison_contract="Use features for cheap source/instance comparison; use feature_contracts for artifact-level synchronization and promotion checks.",
            required_contract_fields=[
                "summary",
                "required_paths",
                "required_scripts",
                "required_catalog_entries",
                "required_docs",
                "sync_direction",
                "promotion_checklist",
                "verification_commands",
                "known_failure_if_missing",
            ],
            sync_directions=["source_to_child", "child_to_source", "bidirectional", "source_only"],
        ),
    )
    write_json(source_path, payload)
    print(f"OK: added {len(selected)} feature(s) and feature contract(s) to source pipeline feature list.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
