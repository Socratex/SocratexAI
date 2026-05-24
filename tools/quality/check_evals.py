#!/usr/bin/env python3
"""Validate the manual eval framework files and scenario links."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCENARIO_IDS = [
    "priority_conflict",
    "low_friction_adoption",
    "on_demand_team",
    "finish_boundary",
    "document_ownership",
    "compiled_instruction_layer",
    "three_tier_fit",
    "code_engineering_context_preload",
    "knowledge_freshness_and_fallback",
    "knowledge_entry_lifecycle",
    "pipeline_update_artifact_sync",
    "context_tagged_knowledge_prelude",
    "task_type_router",
    "unknown_task_routing",
]

PERSONA_IDS = ["power_user_socratex", "builder_user_kuba", "basic_user_emcia"]
README_NEEDLES = [
    "manual first",
    "baseline",
    "with-pipeline",
    "low-friction maturity path",
    "missed_context",
    "do not add new synthetic scenarios",
]


def read_required(root: Path, relative: str, errors: list[str]) -> str:
    path = root / relative
    if not path.is_file():
        errors.append(f"Missing eval file: {relative}")
        return ""
    return path.read_text(encoding="utf-8")


def read_json_text(text: str, label: str, errors: list[str]) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except Exception as exc:
        errors.append(f"{label} is not valid JSON: {exc}")
        return {}
    return data if isinstance(data, dict) else {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check manual eval framework structure.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--eval-dir", default="evals", help="Eval directory relative to repo root.")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    eval_dir = args.eval_dir.strip().strip("/\\") or "evals"
    eval_root = root / eval_dir
    errors: list[str] = []

    if not eval_root.is_dir():
        print(f"ERROR: Missing eval directory: {eval_dir}", file=sys.stderr)
        return 1

    required_files = [
        f"{eval_dir}/README.md",
        f"{eval_dir}/personas.json",
        f"{eval_dir}/expected-behaviors.json",
        f"{eval_dir}/scoring.md",
        f"{eval_dir}/results/baseline.json",
        f"{eval_dir}/results/with-pipeline.json",
    ]
    required_files.extend(f"{eval_dir}/prompts/{scenario_id}.md" for scenario_id in SCENARIO_IDS)
    file_text = {relative: read_required(root, relative, errors) for relative in required_files}

    expected = read_json_text(file_text[f"{eval_dir}/expected-behaviors.json"], "expected-behaviors.json", errors)
    scenarios = expected.get("scenarios")
    scenario_by_id: dict[str, dict[str, Any]] = {}
    if isinstance(scenarios, list):
        for item in scenarios:
            if isinstance(item, dict) and item.get("id") is not None:
                scenario_by_id[str(item["id"])] = item

    result_sets: dict[str, set[str]] = {}
    for result_file in (f"{eval_dir}/results/baseline.json", f"{eval_dir}/results/with-pipeline.json"):
        payload = read_json_text(file_text[result_file], result_file, errors)
        results = payload.get("results")
        result_sets[result_file] = set()
        if isinstance(results, list):
            for item in results:
                if isinstance(item, dict) and item.get("scenario") is not None:
                    result_sets[result_file].add(str(item["scenario"]))

    for scenario_id in SCENARIO_IDS:
        scenario = scenario_by_id.get(scenario_id)
        if scenario is None:
            errors.append(f"expected-behaviors.json missing scenario id: {scenario_id}")
        elif scenario.get("prompt_file") != f"{eval_dir}/prompts/{scenario_id}.md":
            errors.append(f"expected-behaviors.json missing prompt_file for: {scenario_id}")
        for result_file, result_ids in result_sets.items():
            if scenario_id not in result_ids:
                errors.append(f"{result_file} missing result entry for: {scenario_id}")

    personas = read_json_text(file_text[f"{eval_dir}/personas.json"], "personas.json", errors)
    persona_items = personas.get("personas")
    persona_ids: set[str] = set()
    if isinstance(persona_items, list):
        for item in persona_items:
            if isinstance(item, dict) and item.get("id") is not None:
                persona_ids.add(str(item["id"]))
    for persona_id in PERSONA_IDS:
        if persona_id not in persona_ids:
            errors.append(f"personas.json missing persona id: {persona_id}")

    readme = file_text[f"{eval_dir}/README.md"].lower()
    for needle in README_NEEDLES:
        if needle.lower() not in readme:
            errors.append(f"README.md missing required phrase: {needle}")

    if errors:
        print("ERROR: eval framework check failed.")
        for error in errors:
            print(f" - {error}")
        return 1

    print("OK: eval framework files are present and internally linked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
