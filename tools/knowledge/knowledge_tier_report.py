import argparse
import json
import sqlite3
import subprocess
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

DEFAULT_DB_PATH = "AI-compiled/project/knowledge.sqlite"
DEFAULT_FILE_DIR = "AI-compiled/project/knowledge-files"
BACKENDS = ("auto", "documents", "knowledge_files", "sqlite")


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


def scan_document_entries(repo_root: Path, include_templates: bool) -> tuple[list[dict[str, Any]], list[dict[str, str]], int]:
    entries: list[dict[str, Any]] = []
    parse_errors: list[dict[str, str]] = []
    files_scanned = 0

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
    return entries, parse_errors, files_scanned


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def scan_file_entries(repo_root: Path, file_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]], int]:
    entries_path = file_dir / "entries.json"
    tags_path = file_dir / "entry_tags.json"
    documents_path = file_dir / "documents.json"
    missing = [path for path in (entries_path, tags_path, documents_path) if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing knowledge file table(s): " + ", ".join(str(path.relative_to(repo_root)) for path in missing))

    tag_rows_by_entry: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in read_json(tags_path):
        tag_rows_by_entry[(str(row.get("document_path", "")), str(row.get("entry_name", "")))].append(str(row.get("tag", "")))

    entries: list[dict[str, Any]] = []
    for row in read_json(entries_path):
        document_path = str(row.get("document_path", ""))
        name = str(row.get("name", ""))
        tier, issue = classify_tier(row.get("context_tier"))
        entries.append(
            {
                "document_path": document_path,
                "selector": str(row.get("source_selector", "")),
                "id": name,
                "title": row.get("title") or name,
                "type": row.get("type", ""),
                "subtype": row.get("subtype", ""),
                "context_tier": tier,
                "tier_issue": issue,
                "load_at_start": bool(row.get("load_at_start")),
                "tags": normalize_tags(tag_rows_by_entry.get((document_path, name), [])),
            }
        )
    return entries, [], len(read_json(documents_path))


def scan_sqlite_entries(repo_root: Path, db_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]], int]:
    if not db_path.is_file():
        raise FileNotFoundError(f"missing knowledge SQLite database: {db_path.relative_to(repo_root)}")

    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    try:
        tag_rows_by_entry: dict[tuple[str, str], list[str]] = defaultdict(list)
        for row in connection.execute("select document_path, entry_name, tag from entry_tags order by tag"):
            tag_rows_by_entry[(str(row["document_path"]), str(row["entry_name"]))].append(str(row["tag"]))

        entries: list[dict[str, Any]] = []
        for row in connection.execute("select * from entries order by document_path, name"):
            document_path = str(row["document_path"])
            name = str(row["name"])
            tier, issue = classify_tier(row["context_tier"])
            entries.append(
                {
                    "document_path": document_path,
                    "selector": str(row["source_selector"] or ""),
                    "id": name,
                    "title": row["title"] or name,
                    "type": row["type"] or "",
                    "subtype": row["subtype"] or "",
                    "context_tier": tier,
                    "tier_issue": issue,
                    "load_at_start": bool(row["load_at_start"]),
                    "tags": normalize_tags(tag_rows_by_entry.get((document_path, name), [])),
                }
            )
        files_scanned = int(connection.execute("select count(*) from documents").fetchone()[0])
        return entries, [], files_scanned
    finally:
        connection.close()


def backend_current(repo_root: Path, backend: str, db_path: Path, file_dir: Path) -> bool:
    script = Path(__file__).resolve().with_name("knowledge_index.py")
    if backend == "sqlite":
        command = [sys.executable, "-B", str(script), "check", "--repo-root", str(repo_root), "--db", str(db_path)]
    elif backend == "knowledge_files":
        command = [sys.executable, "-B", str(script), "file-check", "--repo-root", str(repo_root), "--file-dir", str(file_dir)]
    else:
        return True
    return subprocess.run(command, cwd=repo_root, check=False, capture_output=True, text=True).returncode == 0


def choose_backend(repo_root: Path, db_path: Path, file_dir: Path) -> str:
    if backend_current(repo_root, "sqlite", db_path, file_dir):
        return "sqlite"
    if backend_current(repo_root, "knowledge_files", db_path, file_dir):
        return "knowledge_files"
    return "documents"


def build_report(
    repo_root: Path,
    include_templates: bool,
    backend: str,
    backend_source: str,
    files_scanned: int,
    entries: list[dict[str, Any]],
    parse_errors: list[dict[str, str]],
) -> dict[str, Any]:
    files_with_entries = {entry["document_path"] for entry in entries}

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
        "backend": backend,
        "backend_source": backend_source,
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


def scan_repo(
    repo_root: Path,
    include_templates: bool,
    backend: str = "documents",
    db_path: Path | None = None,
    file_dir: Path | None = None,
) -> dict[str, Any]:
    requested_backend = backend
    resolved_db_path = (repo_root / (db_path or Path(DEFAULT_DB_PATH))).resolve()
    resolved_file_dir = (repo_root / (file_dir or Path(DEFAULT_FILE_DIR))).resolve()
    selected_backend = choose_backend(repo_root, resolved_db_path, resolved_file_dir) if requested_backend == "auto" else requested_backend

    if selected_backend == "documents":
        entries, parse_errors, files_scanned = scan_document_entries(repo_root, include_templates)
    elif selected_backend == "knowledge_files":
        entries, parse_errors, files_scanned = scan_file_entries(repo_root, resolved_file_dir)
    elif selected_backend == "sqlite":
        entries, parse_errors, files_scanned = scan_sqlite_entries(repo_root, resolved_db_path)
    else:
        raise ValueError(f"Unsupported backend: {selected_backend}")

    return build_report(
        repo_root,
        include_templates,
        selected_backend,
        requested_backend,
        files_scanned,
        entries,
        parse_errors,
    )


def format_markdown(report: dict[str, Any], show_entries: bool) -> str:
    lines: list[str] = []
    summary = report["summary"]
    lines.append(f"# Knowledge Tier Report")
    lines.append("")
    lines.append(f"- repo: `{report['repo_root']}`")
    lines.append(f"- backend: `{report['backend']}`")
    lines.append(f"- backend_source: `{report['backend_source']}`")
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
    parser.add_argument("--backend", "-Backend", choices=BACKENDS, default="documents", help="Tier metadata backend. auto prefers current SQLite, then file fallback, then source documents.")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="SQLite knowledge database path relative to repo root.")
    parser.add_argument("--file-dir", default=DEFAULT_FILE_DIR, help="Knowledge file fallback directory relative to repo root.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    report = scan_repo(repo_root, args.include_templates, args.backend, Path(args.db), Path(args.file_dir))
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
