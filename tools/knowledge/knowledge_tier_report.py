import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


SKIP_DIR_PREFIXES = (
    "AI-compiled/",
    "docs-tech/cache/",
    "ignored/",
    "logs/",
    "logs-diagnostics/",
    "logs-performance/",
    "OUTPUT/",
    "temp/",
    "tmp/",
    "Tools/tmp/",
    "tools/tmp/",
    "Game/.godot/",
    "SocratexAI/AI-compiled/",
    "SocratexAI/docs-tech/cache/",
    "SocratexAI/ignored/",
    "SocratexAI/OUTPUT/",
    "SocratexAI/temp/",
    "SocratexAI/tmp/",
    "SocratexAI/tools/tmp/",
)

SKIP_SUFFIXES = (
    "/manifest.json",
    "/stale-report.json",
)

SKIP_EXACT = {
    "docs-tech/CODE_LINE_INDEX.json",
    "docs-tech/LARGE_FILES.json",
    "SocratexAI/docs-tech/CODE_LINE_INDEX.json",
    "SocratexAI/docs-tech/LARGE_FILES.json",
}

TIER_LABELS = {
    1: "core decision gates",
    2: "routed operating rules",
    3: "patterns, archetypes, and deep references",
    4: "history, vision, and simplified backlog",
    5: "FOMO and inactive inspiration",
}


def normalize_path(path: str) -> str:
    return path.replace("\\", "/")


def should_skip(relative_path: str, include_templates: bool) -> bool:
    path = normalize_path(relative_path)
    if path in SKIP_EXACT:
        return True
    if path.endswith(SKIP_SUFFIXES):
        return True
    if not include_templates and (path.startswith("templates/") or path.startswith("SocratexAI/templates/")):
        return True
    return any(path.startswith(prefix) for prefix in SKIP_DIR_PREFIXES)


def is_knowledge_entry(value: dict[str, Any]) -> bool:
    return (
        isinstance(value.get("id"), str)
        and isinstance(value.get("type"), str)
        and "tags" in value
        and ("rule" in value or "body" in value or "summary" in value)
    )


def iter_entries(value: Any, selector: str = ""):
    if isinstance(value, dict):
        if is_knowledge_entry(value):
            yield selector, value
            return
        for key, child in value.items():
            child_selector = f"{selector}.{key}" if selector else str(key)
            yield from iter_entries(child, child_selector)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_selector = f"{selector}.{index}" if selector else str(index)
            yield from iter_entries(child, child_selector)


def normalize_tags(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        values = raw.split(",")
    else:
        values = list(raw)
    return sorted({str(tag).strip() for tag in values if str(tag).strip()})


def classify_tier(raw: Any) -> tuple[int | None, str | None]:
    if raw is None or raw == "":
        return None, "missing"
    try:
        tier = int(raw)
    except (TypeError, ValueError):
        return None, "invalid"
    if tier < 1 or tier > 5:
        return None, "invalid"
    return tier, None


def scan_repo(repo_root: Path, include_templates: bool) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    parse_errors: list[dict[str, str]] = []
    files_scanned = 0
    files_with_entries: set[str] = set()

    for path in sorted(repo_root.rglob("*.json"), key=lambda item: normalize_path(str(item.relative_to(repo_root)))):
        relative = normalize_path(str(path.relative_to(repo_root)))
        if should_skip(relative, include_templates):
            continue
        files_scanned += 1
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as error:  # noqa: BLE001 - report exact parse failure, do not hide file.
            parse_errors.append({"path": relative, "error": str(error)})
            continue
        for selector, entry in iter_entries(data):
            tier, issue = classify_tier(entry.get("context_tier"))
            tags = normalize_tags(entry.get("tags"))
            files_with_entries.add(relative)
            entries.append(
                {
                    "document_path": relative,
                    "selector": selector,
                    "id": entry.get("id", ""),
                    "title": entry.get("title") or entry.get("id", ""),
                    "type": entry.get("type", ""),
                    "subtype": entry.get("subtype", ""),
                    "context_tier": tier,
                    "tier_issue": issue,
                    "load_at_start": entry.get("load_at_start"),
                    "tags": tags,
                }
            )

    by_tier: dict[str, Any] = {}
    for tier in range(1, 6):
        tier_entries = [entry for entry in entries if entry["context_tier"] == tier]
        tag_counts: Counter[str] = Counter()
        type_counts: Counter[str] = Counter()
        document_counts: Counter[str] = Counter()
        for entry in tier_entries:
            tag_counts.update(entry["tags"])
            type_counts.update([str(entry["type"])])
            document_counts.update([entry["document_path"]])
        by_tier[str(tier)] = {
            "label": TIER_LABELS[tier],
            "count": len(tier_entries),
            "categories": dict(sorted(tag_counts.items())),
            "types": dict(sorted(type_counts.items())),
            "documents": dict(sorted(document_counts.items())),
        }

    missing = [entry for entry in entries if entry["tier_issue"] == "missing"]
    invalid = [entry for entry in entries if entry["tier_issue"] == "invalid"]
    tier_coverage_ok = len(missing) == 0 and len(invalid) == 0
    strict_ok = tier_coverage_ok and len(parse_errors) == 0
    return {
        "repo_root": str(repo_root),
        "include_templates": include_templates,
        "scope": "knowledge entries with id/type/tags and rule/body/summary",
        "status": {
            "tier_coverage_ok": tier_coverage_ok,
            "strict_ok": strict_ok,
            "message": (
                "OK: wszystko zatierowane; all discovered knowledge entries have valid context_tier."
                if tier_coverage_ok
                else "ERROR: missing or invalid context_tier entries found."
            ),
        },
        "summary": {
            "json_files_scanned": files_scanned,
            "json_files_with_entries": len(files_with_entries),
            "entries": len(entries),
            "with_context_tier": len([entry for entry in entries if entry["context_tier"] is not None]),
            "missing_context_tier": len(missing),
            "invalid_context_tier": len(invalid),
            "parse_errors": len(parse_errors),
        },
        "by_tier": by_tier,
        "missing_entries": missing,
        "invalid_entries": invalid,
        "parse_errors": parse_errors,
    }


def format_markdown(report: dict[str, Any], show_entries: bool) -> str:
    lines: list[str] = []
    summary = report["summary"]
    lines.append(f"# Knowledge Tier Report")
    lines.append("")
    lines.append(f"- repo: `{report['repo_root']}`")
    lines.append(f"- scope: {report['scope']}")
    lines.append(f"- include_templates: `{str(report['include_templates']).lower()}`")
    lines.append(f"- json_files_scanned: `{summary['json_files_scanned']}`")
    lines.append(f"- json_files_with_entries: `{summary['json_files_with_entries']}`")
    lines.append(f"- entries: `{summary['entries']}`")
    lines.append(f"- with_context_tier: `{summary['with_context_tier']}`")
    lines.append(f"- missing_context_tier: `{summary['missing_context_tier']}`")
    lines.append(f"- invalid_context_tier: `{summary['invalid_context_tier']}`")
    lines.append(f"- parse_errors: `{summary['parse_errors']}`")
    lines.append(f"- status: `{report['status']['message']}`")
    lines.append("")
    lines.append("## Tiers")
    lines.append("")
    lines.append("| Tier | Label | Count | Categories |")
    lines.append("| --- | --- | ---: | --- |")
    for tier in range(1, 6):
        data = report["by_tier"][str(tier)]
        categories = ", ".join(f"{key}={value}" for key, value in data["categories"].items()) or "-"
        lines.append(f"| {tier} | {data['label']} | {data['count']} | {categories} |")
    if show_entries:
        lines.append("")
        lines.append("## Missing")
        if not report["missing_entries"]:
            lines.append("")
            lines.append("- none")
        for entry in report["missing_entries"]:
            lines.append(f"- `{entry['document_path']}#{entry['selector']}` `{entry['id']}`")
        lines.append("")
        lines.append("## Invalid")
        if not report["invalid_entries"]:
            lines.append("")
            lines.append("- none")
        for entry in report["invalid_entries"]:
            lines.append(f"- `{entry['document_path']}#{entry['selector']}` `{entry['id']}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Report and validate context_tier metadata on knowledge documentation entries.")
    parser.add_argument("--repo-root", "-RepoRoot", default=".", help="Repository root to scan.")
    parser.add_argument("--include-templates", "-IncludeTemplates", action="store_true", help="Include templates/ knowledge documents.")
    parser.add_argument("--strict", "-Strict", action="store_true", help="Exit nonzero when entries miss context_tier, have invalid tiers, or JSON parse errors are found.")
    parser.add_argument("--show-entries", "-ShowEntries", action="store_true", help="Include missing/invalid entry locations in markdown output.")
    parser.add_argument("--format", "-Format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    report = scan_repo(Path(args.repo_root).resolve(), args.include_templates)
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_markdown(report, args.show_entries))

    if args.strict:
        summary = report["summary"]
        if summary["missing_context_tier"] or summary["invalid_context_tier"] or summary["parse_errors"]:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
