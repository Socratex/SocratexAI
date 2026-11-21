"""Merger of the review pipeline: combines per-checker result files into one schema-validated findings.json."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE / "findings.schema.json"
DOC_SCHEMA = "socratex-review-findings/v1"
RESERVED = {"findings.json", "summary.json"}
SEVERITIES = ("blocker", "major", "minor", "nit")
CONFIDENCES = ("high", "medium", "low")
JSON_TYPES = {"string": str, "integer": int, "boolean": bool, "array": list, "object": dict}


class SchemaError(ValueError):
    """The findings document does not match findings.schema.json."""


def check(value, schema: dict, where: str = "$") -> list[str]:
    """Validate the JSON Schema subset the findings schema uses: type, enum, required, properties, items, bounds."""
    errors: list[str] = []
    expected = schema.get("type")
    if expected:
        python_type = JSON_TYPES[expected]
        wrong_bool = expected == "integer" and isinstance(value, bool)
        if not isinstance(value, python_type) or wrong_bool:
            return [f"{where}: expected {expected}"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{where}: {value!r} not in {schema['enum']}")
    if isinstance(value, str) and len(value) < schema.get("minLength", 0):
        errors.append(f"{where}: too short")
    if isinstance(value, int) and not isinstance(value, bool) and value < schema.get("minimum", value):
        errors.append(f"{where}: below minimum")
    if isinstance(value, dict):
        errors += [f"{where}: missing {name}" for name in schema.get("required", []) if name not in value]
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            errors += [f"{where}: unexpected {name}" for name in value if name not in props]
        for name, sub in props.items():
            if name in value:
                errors += check(value[name], sub, f"{where}.{name}")
    if isinstance(value, list) and "items" in schema:
        for number, item in enumerate(value):
            errors += check(item, schema["items"], f"{where}[{number}]")
    return errors


def validate(doc: dict) -> list[str]:
    return check(doc, json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))


def rank(finding: dict) -> tuple:
    """Sort key where smaller wins: higher severity, higher confidence, earlier line."""
    return (SEVERITIES.index(finding["severity"]), CONFIDENCES.index(finding["confidence"]), finding["line_start"])


def joins(cluster: list[dict], reach: int, finding: dict) -> bool:
    if finding["line_start"] <= reach:
        return True
    return (finding["line_start"] == reach + 1 and finding.get("chunk_split", False)
            and any(member.get("chunk_split") for member in cluster))


def dedupe(findings: list[dict]) -> list[dict]:
    """Same file, overlapping lines (or touching across a split boundary), same category: keep the strongest, supersede the rest."""
    result = [copy.deepcopy(f) for f in findings]
    groups: dict[tuple, list[dict]] = {}
    for finding in result:
        if finding["status"] == "open":
            groups.setdefault((finding["file"], finding["category"]), []).append(finding)
    for members in groups.values():
        members.sort(key=lambda f: (f["line_start"], f["line_end"]))
        cluster: list[dict] = [members[0]]
        reach = members[0]["line_end"]
        clusters = []
        for finding in members[1:]:
            if joins(cluster, reach, finding):
                cluster.append(finding)
                reach = max(reach, finding["line_end"])
            else:
                clusters.append(cluster)
                cluster, reach = [finding], finding["line_end"]
        clusters.append(cluster)
        for group in clusters:
            winner = min(group, key=rank)
            winner["line_start"] = min(f["line_start"] for f in group)
            winner["line_end"] = max(f["line_end"] for f in group)
            for loser in group:
                if loser is not winner:
                    loser["status"] = "superseded"
                    loser["superseded_by"] = winner["id"]
    return result


def load_results(run_dir: Path) -> list[dict]:
    results = []
    for path in sorted(Path(run_dir).glob("*.json")):
        if path.name in RESERVED:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "checker" in data:
            results.append(data)
    return results


def checker_row(result: dict) -> dict:
    cost = result.get("cost", {})
    row = {"id": result["checker"], "status": result.get("status", "done"), "tier": result.get("tier", "script"),
           "model_calls": cost.get("model_calls", 0), "input_chunks": cost.get("input_chunks", 0),
           "input_lines": cost.get("input_lines", 0)}
    if result.get("reason"):
        row["reason"] = result["reason"]
    if cost.get("skipped_chunks"):
        row["skipped_chunks"] = cost["skipped_chunks"]
    return row


def build_document(run_id: str, results: list[dict], rounds: int = 0) -> dict:
    findings = [f for result in results for f in result.get("findings", [])]
    return {"schema": DOC_SCHEMA, "run_id": run_id, "rounds": rounds,
            "checkers": [checker_row(r) for r in results], "findings": dedupe(findings)}


def write_document(run_dir: Path, doc: dict) -> Path:
    errors = validate(doc)
    if errors:
        raise SchemaError("; ".join(errors[:5]))
    path = Path(run_dir) / "findings.json"
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return path


def merge_run(run_dir: Path, run_id: str, rounds: int = 0) -> dict:
    doc = build_document(run_id, load_results(run_dir), rounds)
    write_document(run_dir, doc)
    return doc


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: merge.py RUN_DIR", file=sys.stderr)
        return 2
    run_dir = Path(argv[0])
    doc = merge_run(run_dir, run_dir.name)
    print(f"Merged {len(doc['checkers'])} checkers into {run_dir / 'findings.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
