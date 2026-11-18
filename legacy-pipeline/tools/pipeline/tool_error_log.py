#!/usr/bin/env python3
"""Append repeatable tool failures to TOOL-ERRORS.json with Python-only tooling."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pipeline_script_helpers import (
    append_indexed_content_entry,
    configure_stdio,
    now_local_timestamp,
    package_root,
    read_json,
    unique_key,
    write_json,
)


def default_document() -> dict[str, Any]:
    return {
        "index": [],
        "content": {},
        "metadata": {
            "document": {"title": "Tool Errors", "type": "tool_error_registry", "language": "en"},
            "purpose": "Records repeatable repository tool invocation, input, result, quoting, path, encoding, and contract failures so the owning script or script catalog can be hardened instead of relying on manual memory.",
        },
    }


def default_path() -> Path:
    root = package_root()
    workspace_root = root
    if root.name == "SocratexAI" and (root.parent / "docs-tech").is_dir():
        workspace_root = root.parent
    return workspace_root / "docs-tech" / "TOOL-ERRORS.json"


def read_details(inline: str, file_path: str) -> Any:
    if inline and file_path:
        raise SystemExit("Use only one of --details-json or --details-json-file.")
    raw = Path(file_path).resolve().read_text(encoding="utf-8") if file_path else inline
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", "-Path", default="")
    parser.add_argument("--key", "-Key", default="")
    parser.add_argument("--title", "-Title", default="")
    parser.add_argument("--status", "-Status", default="open")
    parser.add_argument("--tool", "-Tool", default="")
    parser.add_argument("--failure", "-Failure", default="")
    parser.add_argument("--failing-command-shape", "-FailingCommandShape", default="")
    parser.add_argument("--observed-error", "-ObservedError", default="")
    parser.add_argument("--suspected-contract-gap", "-SuspectedContractGap", default="")
    parser.add_argument("--fix-target", "-FixTarget", default="")
    parser.add_argument("--details-json", "-DetailsJson", default="")
    parser.add_argument("--details-json-file", "-DetailsJsonFile", default="")
    parser.add_argument("--observed-at", "-ObservedAt", default="")
    parser.add_argument("--json", "-Json", action="store_true")
    args = parser.parse_args()

    path = Path(args.path).resolve() if args.path else default_path()
    if path.is_file():
        document = read_json(path)
    else:
        document = default_document()
    if not isinstance(document, dict):
        raise SystemExit(f"Tool error document must be an object: {path}")
    title = args.title or "Tool Error"
    key = unique_key(document, args.key, title, "tool_error")
    entry: dict[str, Any] = {"title": title, "status": args.status, "observed_at": args.observed_at or now_local_timestamp()}
    for field, value in (
        ("tool", args.tool),
        ("failure", args.failure),
        ("failing_command_shape", args.failing_command_shape),
        ("observed_error", args.observed_error),
        ("suspected_contract_gap", args.suspected_contract_gap),
        ("fix_target", args.fix_target),
    ):
        if value:
            entry[field] = value
    details = read_details(args.details_json, args.details_json_file)
    if details is not None:
        entry["details"] = details
    append_indexed_content_entry(document, key, entry)
    write_json(path, document)
    result = {"ok": True, "key": key, "path": str(path)}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=4))
    else:
        print(f"OK: logged {key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
