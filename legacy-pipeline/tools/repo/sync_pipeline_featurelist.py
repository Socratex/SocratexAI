#!/usr/bin/env python3
"""Synchronize a child-project pipeline_featurelist.json from a SocratexAI source manifest."""

from __future__ import annotations

import argparse
import json
import re
from collections import OrderedDict
from datetime import date
from pathlib import Path
from typing import Any


def read_json(path: Path) -> OrderedDict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=OrderedDict)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=4) + "\n", encoding="utf-8", newline="\n")


def as_list(value: Any) -> list[str]:
    raw = value if isinstance(value, list) else ([] if value is None else [value])
    result: list[str] = []
    for item in raw:
        text = str(item).strip()
        if text and text not in result:
            result.append(text)
    return result


def content_of(document: dict[str, Any]) -> dict[str, Any]:
    content = document.get("content")
    return content if isinstance(content, dict) else document


def features_of(document: dict[str, Any]) -> list[str]:
    return as_list(content_of(document).get("features"))


def contracts_of(document: dict[str, Any]) -> OrderedDict[str, Any]:
    contracts = content_of(document).get("feature_contracts")
    return contracts if isinstance(contracts, OrderedDict) else OrderedDict(contracts or {})


def pipeline_id(document: dict[str, Any], fallback: str) -> str:
    for container in (document, document.get("metadata") if isinstance(document.get("metadata"), dict) else {}):
        value = str(container.get("pipeline_id", "")).strip()
        if value:
            return value
    return fallback


def default_pipeline_id(root: Path) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", root.name.lower()).strip("_")
    return value or "project_pipeline"


def is_list_manifest(document: dict[str, Any]) -> bool:
    return isinstance(document.get("content"), dict) and isinstance(document["content"].get("features"), list)


def target_requires_list_manifest(root: Path) -> bool:
    docs_path = root / "DOCS.json"
    if not docs_path.is_file():
        return False
    try:
        docs = read_json(docs_path)
    except Exception:
        return False
    description = str(content_of(docs).get("pipeline_featurelist.json", "")).lower()
    return ("root" in description and "index" in description and "content" in description and "metadata" in description) or "canonical json document shape" in description


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync instance pipeline_featurelist.json from source.")
    parser.add_argument("--target-path", default=".", help="Child project root.")
    parser.add_argument("--source-feature-list-path", default="", help="Source pipeline_featurelist.json.")
    parser.add_argument("--output-path", default="", help="Output pipeline_featurelist.json.")
    parser.add_argument("--pipeline-id", default="", help="Instance pipeline id.")
    parser.add_argument("--extra-features", nargs="*", default=[], help="Extra local feature ids.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    target = Path(args.target_path).resolve()
    output = Path(args.output_path).resolve() if args.output_path else target / "pipeline_featurelist.json"
    if args.source_feature_list_path:
        source_path = Path(args.source_feature_list_path).resolve()
    elif (target / "SocratexAI" / "pipeline_featurelist.json").is_file():
        source_path = target / "SocratexAI" / "pipeline_featurelist.json"
    else:
        source_path = Path(__file__).resolve().parents[2] / "pipeline_featurelist.json"

    source = read_json(source_path)
    source_features = features_of(source)
    if not source_features:
        raise SystemExit(f"Source feature list has no features: {source_path}")
    source_contracts = contracts_of(source)

    existing = read_json(output) if output.is_file() else OrderedDict()
    existing_features = features_of(existing)
    existing_contracts = contracts_of(existing)
    preserve_list_shape = is_list_manifest(existing) or is_list_manifest(source) or target_requires_list_manifest(target)

    features = []
    for feature in [*source_features, *existing_features, *args.extra_features]:
        if feature not in features:
            features.append(feature)

    same = [feature for feature in source_features if feature in features]
    missing = [feature for feature in source_features if feature not in features]
    extra = [feature for feature in features if feature not in source_features]
    comparison = OrderedDict(
        same_as_source=not missing and not extra,
        same=same,
        missing_from_instance=missing,
        extra_in_instance=extra,
    )

    feature_contracts: OrderedDict[str, Any] = OrderedDict()
    for feature in features:
        if feature in source_contracts:
            feature_contracts[feature] = source_contracts[feature]
        elif feature in existing_contracts:
            feature_contracts[feature] = existing_contracts[feature]

    instance_id = args.pipeline_id or default_pipeline_id(target)
    source_id = pipeline_id(source, "socratex_pipeline")
    if preserve_list_shape:
        index = as_list(existing.get("index"))
        for required in ("features", "comparison_to_source"):
            if required not in index:
                index.append(required)
        if feature_contracts and "feature_contracts" not in index:
            index.append("feature_contracts")
        existing_content = content_of(existing) if isinstance(existing, dict) else {}
        for key in existing_content:
            if key not in index:
                index.append(key)
        content: OrderedDict[str, Any] = OrderedDict()
        for key in index:
            if key == "features":
                content[key] = features
            elif key == "comparison_to_source":
                content[key] = comparison
            elif key == "feature_contracts" and feature_contracts:
                content[key] = feature_contracts
            else:
                content[key] = existing_content.get(key, [])
        metadata = OrderedDict(existing.get("metadata", {}) if isinstance(existing.get("metadata"), dict) else {})
        metadata.setdefault("schema", "socratex-pipeline-featurelist/v2")
        metadata["pipeline_id"] = instance_id
        metadata["role"] = "instance"
        metadata["source_pipeline_id"] = source_id
        metadata["updated_at"] = date.today().isoformat()
        metadata["comparison_contract"] = "features is the cheap comparison layer; project-owned content keeps its local list-document shape."
        payload = OrderedDict(index=index, content=content, metadata=metadata)
    else:
        payload = OrderedDict(
            schema="socratex-pipeline-featurelist/v2",
            pipeline_id=instance_id,
            role="instance",
            source_pipeline_id=source_id,
            updated_at=date.today().isoformat(),
            features=features,
            comparison_to_source=comparison,
        )
        if feature_contracts:
            payload["feature_contracts"] = feature_contracts
            payload["metadata"] = OrderedDict(
                comparison_contract="Use features and comparison_to_source for cheap comparison; preserve source feature contracts plus instance-owned extra feature contracts."
            )

    if args.dry_run:
        print(f"Would write instance pipeline feature list: {output}")
        print(json.dumps(payload, ensure_ascii=False, indent=4))
        return 0
    write_json(output, payload)
    print(f"OK: synced pipeline feature list: {output}")
    print(f"same={len(same)} missing={len(missing)} extra={len(extra)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
