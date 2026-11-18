#!/usr/bin/env python3
"""Compare project pipeline features with the source manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from repo_tool_helpers import as_list, content_of, package_root, read_json, split_values, utc_stamp, write_json


def features_of(document: dict[str, Any]) -> list[str]:
    return as_list(content_of(document).get("features"))


def contracts_of(document: dict[str, Any]) -> dict[str, Any]:
    contracts = content_of(document).get("feature_contracts")
    return contracts if isinstance(contracts, dict) else {}


def featurelist_id(document: dict[str, Any], fallback_path: Path) -> str:
    for container in (document, document.get("metadata") if isinstance(document.get("metadata"), dict) else {}):
        value = str(container.get("pipeline_id", "")).strip()
        if value:
            return value
    value = re.sub(r"[^a-z0-9]+", "_", fallback_path.name.lower()).strip("_")
    return value or "project_pipeline"


def excluded(feature: str, patterns: list[str]) -> bool:
    return any(pattern and re.search(pattern, feature) for pattern in patterns)


def report_hash(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Report project pipeline features not present in source.")
    parser.add_argument("--project-path", "-ProjectPath", required=True)
    parser.add_argument("--source-feature-list-path", "-SourceFeatureListPath", default="")
    parser.add_argument("--exclude-patterns", "-ExcludePatterns", nargs="*", default=["project_specific", "runtime_diagnostic"])
    parser.add_argument("--output-path", "-OutputPath", default="")
    args = parser.parse_args()

    source_path = Path(args.source_feature_list_path).resolve() if args.source_feature_list_path else package_root() / "pipeline_featurelist.json"
    project_root = Path(args.project_path).resolve()
    project_path = project_root / "pipeline_featurelist.json"
    patterns = split_values(args.exclude_patterns)

    source = read_json(source_path)
    project = read_json(project_path)
    source_features = features_of(source)
    project_features = features_of(project)
    project_contracts = contracts_of(project)
    candidate_features = [feature for feature in project_features if feature not in source_features]
    missing_from_project = [feature for feature in source_features if feature not in project_features]

    candidates = []
    for feature in candidate_features:
        is_excluded = excluded(feature, patterns)
        candidates.append(
            {
                "id": feature,
                "status": "excluded_by_pattern" if is_excluded else "review_candidate",
                "contract_status": "contract_present" if feature in project_contracts else "missing_contract",
                "recommendation": "Keep project-specific unless a maintainer explicitly promotes it."
                if is_excluded
                else "Review for promotion into the source pipeline.",
            }
        )

    hash_payload = {
        "source_pipeline_id": featurelist_id(source, source_path),
        "project_pipeline_id": featurelist_id(project, project_root),
        "project_features_not_in_source": candidate_features,
        "source_features_not_in_project": missing_from_project,
    }
    payload = {
        "schema": "socratex-pipeline-learning-report/v1",
        "report_hash": report_hash(hash_payload),
        "generated_at": utc_stamp(),
        "source_featurelist_path": str(source_path),
        "project_path": str(project_root),
        "project_featurelist_path": str(project_path),
        "source_pipeline_id": hash_payload["source_pipeline_id"],
        "project_pipeline_id": hash_payload["project_pipeline_id"],
        "candidate_count": len(candidate_features),
        "review_candidate_count": len([item for item in candidates if item["status"] == "review_candidate"]),
        "excluded_candidate_count": len([item for item in candidates if item["status"] == "excluded_by_pattern"]),
        "candidates": candidates,
        "source_features_missing_from_project": missing_from_project,
        "recommendation": "Use this report as intake only. Promote only reusable, project-agnostic features into the source pipeline, and promote content.feature_contracts with every accepted feature ID.",
    }

    if args.output_path:
        output = Path(args.output_path)
        if not output.is_absolute():
            output = package_root() / output
        write_json(output, payload)
        print(f"OK: wrote pipeline learning report: {output}")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=4))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
