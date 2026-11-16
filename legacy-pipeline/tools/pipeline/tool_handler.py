#!/usr/bin/env python3
"""Invoke approved tools through a JSON envelope with Python-only tooling."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

from pipeline_script_helpers import configure_stdio


ParameterBuilder = Callable[[Path, str, dict[str, Any]], list[str]]


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lstrip("-")).strip("_").lower()


def get_param(parameters: dict[str, Any], *names: str, default: Any = None) -> Any:
    wanted = {normalize_name(name) for name in names}
    for key, value in parameters.items():
        if normalize_name(key) in wanted:
            return value
    return default


def set_param(parameters: dict[str, Any], name: str, value: Any) -> None:
    normalized = normalize_name(name)
    for key in list(parameters.keys()):
        if normalize_name(key) == normalized:
            parameters[key] = value
            return
    parameters[name] = value


def provided(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def split_values(values: list[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        for part in str(value).split(","):
            cleaned = part.strip()
            if cleaned:
                result.append(cleaned)
    return result


def flag_args(parameters: dict[str, Any], mapping: dict[str, str]) -> list[str]:
    args: list[str] = []
    for source, target in mapping.items():
        value = get_param(parameters, source)
        if isinstance(value, bool) and value:
            args.append(target)
    return args


def option_args(parameters: dict[str, Any], mapping: dict[str, str]) -> list[str]:
    args: list[str] = []
    for source, target in mapping.items():
        value = get_param(parameters, source)
        if not provided(value):
            continue
        if isinstance(value, list):
            args.append(target)
            args.extend(str(item) for item in value)
        else:
            args.extend([target, str(value)])
    return args


def tool_path(root: Path, tools_dir: str, relative: str) -> Path:
    return root / tools_dir / relative


def python_tool(root: Path, tools_dir: str, relative: str, *args: str) -> list[str]:
    return [sys.executable, "-B", str(tool_path(root, tools_dir, relative)), *args]


def load_parameters(inline_json: str, json_file: str) -> dict[str, Any]:
    if inline_json and json_file:
        raise ValueError("Use only one of --parameters-json or --parameters-json-file.")
    raw = Path(json_file).resolve().read_text(encoding="utf-8") if json_file else (inline_json or "{}")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("Parameters JSON must be an object.")
    return value


def document_alias(value: str) -> str:
    aliases = {
        "scripts": "SCRIPTS.json",
        "script": "SCRIPTS.json",
        "script_index": "script_index",
        "commands": "COMMANDS.json",
        "command": "COMMANDS.json",
        "command_index": "command_index",
        "flows": "FLOWS.json",
        "flow": "FLOWS.json",
        "flow_index": "flow_index",
        "docs": "DOCS.json",
        "workflow": "WORKFLOW.json",
        "state": "STATE",
        "rules": "rules",
        "entrypoint": "entrypoint",
        "bootstrap": "bootstrap",
        "engineering": "engineering",
    }
    return aliases.get(value.strip().lower(), value)


def read_compiled_context_args(root: Path, tools_dir: str, parameters: dict[str, Any]) -> list[str]:
    document = get_param(parameters, "document", default="")
    if not provided(document):
        raise ValueError("Missing required parameter 'Document'.")
    args = python_tool(root, tools_dir, "pipeline/read_compiled_context.py", document_alias(str(document)))
    args.extend(option_args(parameters, {"CompiledRoot": "--compiled-root"}))
    args.extend(flag_args(parameters, {"AllowStale": "--allow-stale", "SkipCurrentCheck": "--skip-current-check", "Json": "--json"}))
    return args


def doc_keys_args(root: Path, tools_dir: str, parameters: dict[str, Any]) -> list[str]:
    path = get_param(parameters, "path", default="")
    if not provided(path):
        raise ValueError("Missing required parameter 'Path'.")
    if tool_path(root, tools_dir, "documents/doc_tool.py").is_file():
        args = python_tool(root, tools_dir, "documents/doc_tool.py", "keys", str(path))
    else:
        args = python_tool(root, tools_dir, "documents/list_document_keys.py", str(path))
    args.extend(flag_args(parameters, {"Json": "--json"}))
    return args


def doc_read_args(root: Path, tools_dir: str, parameters: dict[str, Any]) -> list[str]:
    path = get_param(parameters, "path", default="")
    selector = get_param(parameters, "selector", "key", default="")
    if not provided(path) or not provided(selector):
        raise ValueError("Missing required parameters 'Path' and 'Selector'.")
    if tool_path(root, tools_dir, "documents/doc_tool.py").is_file():
        args = python_tool(root, tools_dir, "documents/doc_tool.py", "read", str(path), str(selector))
    else:
        args = python_tool(root, tools_dir, "documents/read_document_item.py", str(path), str(selector))
    args.extend(flag_args(parameters, {"Json": "--json"}))
    return args


def doc_search_args(root: Path, tools_dir: str, parameters: dict[str, Any]) -> list[str]:
    query = get_param(parameters, "query", "terms", default=[])
    terms = split_values(query if isinstance(query, list) else [query])
    if not terms:
        raise ValueError("Missing required parameter 'Query'.")
    doc_tool = tool_path(root, tools_dir, "documents/doc_tool.py")
    if not doc_tool.is_file():
        raise ValueError("doc_search requires documents/doc_tool.py in the selected tools directory.")
    args = python_tool(root, tools_dir, "documents/doc_tool.py", "search", *terms, "--repo-root", str(root))
    args.extend(option_args(parameters, {"Cache": "--cache", "Limit": "--limit"}))
    args.extend(flag_args(parameters, {"Json": "--json"}))
    return args


def doc_item_insert_args(root: Path, tools_dir: str, parameters: dict[str, Any]) -> list[str]:
    path = get_param(parameters, "path", default="")
    key = get_param(parameters, "key", default="")
    if not provided(path) or not provided(key):
        raise ValueError("Missing required parameters 'Path' and 'Key'.")
    if tool_path(root, tools_dir, "documents/doc_item.py").is_file():
        args = python_tool(root, tools_dir, "documents/doc_item.py", "insert", str(path), str(key))
    else:
        args = python_tool(root, tools_dir, "documents/insert_document_item.py", str(path), str(key))
    args.extend(option_args(parameters, {"Title": "--title", "Content": "--content", "ContentFile": "--content-file", "ItemFile": "--item-file", "Position": "--position", "Before": "--before", "After": "--after"}))
    args.extend(flag_args(parameters, {"AllowEmpty": "--allow-empty", "Replace": "--replace"}))
    return args


def json_item_args(script: str) -> ParameterBuilder:
    def build(root: Path, tools_dir: str, parameters: dict[str, Any]) -> list[str]:
        path = get_param(parameters, "path", default="")
        key = get_param(parameters, "key", default="")
        if not provided(path) or not provided(key):
            raise ValueError("Missing required parameters 'Path' and 'Key'.")
        args = python_tool(root, tools_dir, f"json/{script}.py", str(path), str(key))
        args.extend(option_args(parameters, {"Text": "--text", "ValueJson": "--value-json", "ValueJsonFile": "--value-json-file", "NewKey": "--new-key", "Collection": "--collection", "Position": "--position", "Reference": "--reference"}))
        args.extend(flag_args(parameters, {"ValueJsonStdin": "--value-json-stdin"}))
        return args
    return build


def passthrough_python(relative_script: str) -> ParameterBuilder:
    def build(root: Path, tools_dir: str, parameters: dict[str, Any]) -> list[str]:
        script_relative = relative_script.replace("Tools/", f"{tools_dir}/").replace("tools/", f"{tools_dir}/")
        args = [sys.executable, "-B", str(root / script_relative)]
        for key, value in parameters.items():
            if not provided(value):
                continue
            flag = "--" + normalize_name(key).replace("_", "-")
            if isinstance(value, bool):
                if value:
                    args.append(flag)
            elif isinstance(value, list):
                args.append(flag)
                args.extend(str(item) for item in value)
            else:
                args.extend([flag, str(value)])
        return args
    return build


def gpt_conversation_archive_args(root: Path, tools_dir: str, parameters: dict[str, Any]) -> list[str]:
    command = get_param(parameters, "command", "subcommand", default="")
    if not provided(command):
        raise ValueError("Missing required parameter 'Command' (list, search, read, or index).")
    args = python_tool(root, tools_dir, "adapters/gpt_conversation_archive.py", str(command))
    args.extend(option_args(parameters, {
        "Source": "--source",
        "Output": "--output",
        "Query": "--query",
        "Project": "--project",
        "Limit": "--limit",
        "MaxSnippetChars": "--max-snippet-chars",
        "ConversationId": "--conversation-id",
        "Position": "--position",
        "TitleContains": "--title-contains",
        "Format": "--format",
        "AssistantMode": "--assistant-mode",
    }))
    args.extend(flag_args(parameters, {"AnyTerm": "--any-term", "NoMetadata": "--no-metadata"}))
    return args


OPERATIONS: dict[str, tuple[str, ParameterBuilder]] = {
    "read_compiled_context": ("read_compiled_context.py", read_compiled_context_args),
    "compiled_context": ("read_compiled_context.py", read_compiled_context_args),
    "context_read": ("read_compiled_context.py", read_compiled_context_args),
    "doc_keys": ("document keys", doc_keys_args),
    "document_keys": ("document keys", doc_keys_args),
    "doc_read": ("document read", doc_read_args),
    "document_read": ("document read", doc_read_args),
    "doc_search": ("doc_tool.py search", doc_search_args),
    "doc_item_insert": ("document item insert", doc_item_insert_args),
    "document_item_insert": ("document item insert", doc_item_insert_args),
    "json_item_insert": ("json_item_insert.py", json_item_args("json_item_insert")),
    "json_item_set": ("json_item_set.py", json_item_args("json_item_set")),
    "gdscript_outline": ("gdscript_outline.py", passthrough_python("tools/gamedev/gdscript_outline.py")),
    "godot_script": ("run_godot_script.py", passthrough_python("tools/gamedev/run_godot_script.py")),
    "godot_headless": ("run_godot_script.py", passthrough_python("tools/gamedev/run_godot_script.py")),
    "run_godot_script": ("run_godot_script.py", passthrough_python("tools/gamedev/run_godot_script.py")),
    "route_retest_report": ("route_retest_report.py", passthrough_python("tools/gamedev/route_retest_report.py")),
    "tool_error_log": ("tool_error_log.py", passthrough_python("tools/pipeline/tool_error_log.py")),
    "gpt_shared_conversation_extract": ("gpt_shared_conversation_extract.py", passthrough_python("tools/adapters/gpt_shared_conversation_extract.py")),
    "gpt_share_extract": ("gpt_shared_conversation_extract.py", passthrough_python("tools/adapters/gpt_shared_conversation_extract.py")),
    "gpt_conversation_archive": ("gpt_conversation_archive.py", gpt_conversation_archive_args),
    "gpt_archive": ("gpt_conversation_archive.py", gpt_conversation_archive_args),
}


def log_error(root: Path, tools_dir: str, args: argparse.Namespace, title: str, message: str, operation: str, target: str, parameters: dict[str, Any]) -> str:
    if args.no_error_log:
        return ""
    details = {"operation": operation, "target_script": target, "parameters": parameters}
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        json.dump(details, handle, ensure_ascii=False, indent=4)
        details_path = handle.name
    try:
        command = python_tool(
            root,
            tools_dir,
            "pipeline/tool_error_log.py",
            "--title",
            title,
            "--status",
            "open",
            "--tool",
            f"{tools_dir}/pipeline/tool_handler.py",
            "--failure",
            message,
            "--observed-error",
            message,
            "--suspected-contract-gap",
            "tool_handler input validation or target execution failed.",
            "--fix-target",
            target,
            "--details-json-file",
            details_path,
            "--json",
        )
        if args.error_log_path:
            command.extend(["--path", args.error_log_path])
        completed = subprocess.run(command, cwd=root, check=False, capture_output=True, text=True)
        if completed.returncode == 0:
            return str(json.loads(completed.stdout).get("key", ""))
    finally:
        Path(details_path).unlink(missing_ok=True)
    return ""


def write_envelope(envelope: dict[str, Any], output_mode: str) -> None:
    if output_mode == "json":
        print(json.dumps(envelope, ensure_ascii=False, indent=4))
        return
    if envelope["ok"]:
        print(f"OK: {envelope['operation']} -> {envelope['target_script']}")
        for line in envelope.get("output", []):
            print(line)
        return
    print(f"ERROR: {envelope['operation']}")
    if envelope.get("error", {}).get("message"):
        print(envelope["error"]["message"])
    if envelope.get("logged_error_key"):
        print(f"logged_error_key: {envelope['logged_error_key']}")


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", nargs="?")
    parser.add_argument("--operation", "-Operation", dest="operation_flag")
    parser.add_argument("--parameters-json", "-ParametersJson", default="")
    parser.add_argument("--parameters-json-file", "-ParametersJsonFile", default="")
    parser.add_argument("--output-mode", "-OutputMode", choices=["json", "text"], default="json")
    parser.add_argument("--error-log-path", "-ErrorLogPath", default="")
    parser.add_argument("--no-error-log", "-NoErrorLog", action="store_true")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--tools-dir", default="tools")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[2]
    tools_dir = args.tools_dir.strip().strip("/\\") or "tools"
    operation = args.operation_flag or args.operation
    if not operation:
        parser.error("operation is required")
    operation_key = normalize_name(operation)
    envelope: dict[str, Any] = {
        "ok": False,
        "operation": operation,
        "normalized_operation": operation_key,
        "target_script": "",
        "target_path": "",
        "normalized_parameters": {},
        "command": [],
        "exit_code": None,
        "output": [],
        "error": {"type": "", "message": ""},
        "logged_error_key": "",
    }

    try:
        parameters = load_parameters(args.parameters_json, args.parameters_json_file)
        if operation_key == "read_compiled_context":
            document = get_param(parameters, "Document")
            if provided(document):
                set_param(parameters, "Document", document_alias(str(document)))
        envelope["normalized_parameters"] = parameters
        if operation_key not in OPERATIONS:
            message = f"Unknown tool operation '{operation}'."
            envelope["error"] = {"type": "unknown_operation", "message": message}
            envelope["logged_error_key"] = log_error(root, tools_dir, args, "Tool Handler Unknown Operation", message, operation, "", parameters)
            write_envelope(envelope, args.output_mode)
            return 2
        target_name, builder = OPERATIONS[operation_key]
        command = builder(root, tools_dir, parameters)
        envelope["target_script"] = target_name
        envelope["target_path"] = command[2] if len(command) > 2 else ""
        envelope["command"] = command
        completed = subprocess.run(command, cwd=root, check=False, capture_output=True, text=True)
        output: list[str] = []
        if completed.stdout:
            output.extend(completed.stdout.splitlines())
        if completed.stderr:
            output.extend(completed.stderr.splitlines())
        envelope["exit_code"] = completed.returncode
        envelope["output"] = output
        if completed.returncode != 0:
            envelope["error"] = {"type": "target_execution", "message": f"Target script exited with code {completed.returncode}."}
            write_envelope(envelope, args.output_mode)
            return completed.returncode
        envelope["ok"] = True
        write_envelope(envelope, args.output_mode)
        return 0
    except Exception as exc:
        message = str(exc)
        envelope["error"] = {"type": "handler_exception", "message": message}
        envelope["logged_error_key"] = log_error(root, tools_dir, args, "Tool Handler Invocation Error", message, operation, envelope["target_script"], envelope["normalized_parameters"])
        write_envelope(envelope, args.output_mode)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
