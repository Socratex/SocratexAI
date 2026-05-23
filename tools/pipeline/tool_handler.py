#!/usr/bin/env python3
"""Single JSON-friendly tool dispatcher for Python SocratexPipeline tools."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import re
from pathlib import Path
from typing import Any

from pipeline_script_helpers import configure_stdio


def normalize_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", value.strip().lstrip("-")).strip("_").lower()


def provided(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    if isinstance(value, (list, tuple, dict)) and len(value) == 0:
        return False
    return True


def read_parameters(inline: str, file_path: str) -> dict[str, Any]:
    if inline and file_path:
        raise ValueError("Use only one of --parameters-json or --parameters-json-file.")
    raw = Path(file_path).resolve().read_text(encoding="utf-8") if file_path else inline or "{}"
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Parameters JSON is invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("Parameters JSON must be an object.")
    return value


def get_param(parameters: dict[str, Any], name: str) -> Any:
    normalized = normalize_name(name)
    for key, value in parameters.items():
        if normalize_name(key) == normalized:
            return value
    return None


def set_param(parameters: dict[str, Any], name: str, value: Any) -> None:
    normalized = normalize_name(name)
    for key in list(parameters.keys()):
        if normalize_name(key) == normalized:
            parameters[key] = value
            return
    parameters[name] = value


def script_catalog_entry(repo_root: Path, script_name: str) -> dict[str, Any]:
    catalog_path = repo_root / "SCRIPTS.json"
    if not catalog_path.is_file():
        return {}
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    content = catalog.get("content", {}) if isinstance(catalog, dict) else {}
    return content.get(script_name, {}) if isinstance(content, dict) else {}


def argument_list(parameters: dict[str, Any], ordered_names: list[str]) -> list[str]:
    arguments: list[str] = []
    used: set[str] = set()
    names = ordered_names + [key for key in parameters if normalize_name(key) not in {normalize_name(item) for item in ordered_names}]
    for name in names:
        value = get_param(parameters, name)
        normalized = normalize_name(name)
        if normalized in used or not provided(value):
            continue
        used.add(normalized)
        flag = "--" + normalize_name(name).replace("_", "-")
        if isinstance(value, bool):
            if value:
                arguments.append(flag)
            continue
        arguments.append(flag)
        if isinstance(value, (list, tuple)):
            arguments.extend(str(item) for item in value)
        else:
            arguments.append(str(value))
    return arguments


def write_envelope(envelope: dict[str, Any], output_mode: str) -> None:
    if output_mode == "json":
        print(json.dumps(envelope, ensure_ascii=False, indent=4))
        return
    if envelope["ok"]:
        print(f"OK: {envelope['operation']} -> {envelope['target_script']}")
        for line in envelope["output"]:
            print(line)
        return
    print(f"ERROR: {envelope['operation']}")
    if envelope["error"]["message"]:
        print(envelope["error"]["message"])
    if envelope["logged_error_key"]:
        print(f"logged_error_key: {envelope['logged_error_key']}")


def log_input_error(repo_root: Path, title: str, message: str, operation: str, script_name: str, parameters: dict[str, Any], error_log_path: str, disabled: bool) -> str:
    if disabled:
        return ""
    logger = repo_root / "tools" / "pipeline" / "tool_error_log.py"
    if not logger.is_file():
        return ""
    details = {"operation": operation, "target_script": script_name, "parameters": parameters}
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        json.dump(details, handle, ensure_ascii=False, indent=4)
        details_file = handle.name
    try:
        cmd = [
            sys.executable,
            str(logger),
            "--title",
            title,
            "--status",
            "open",
            "--tool",
            "tools/pipeline/tool_handler.py",
            "--failure",
            message,
            "--observed-error",
            message,
            "--suspected-contract-gap",
            "tool_handler input validation or alias normalization rejected this invocation before target execution.",
            "--fix-target",
            script_name,
            "--details-json-file",
            details_file,
            "--json",
        ]
        if error_log_path:
            cmd.extend(["--path", error_log_path])
        completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if completed.returncode != 0:
            return ""
        payload = json.loads(completed.stdout)
        return str(payload.get("key", ""))
    except Exception:
        return ""
    finally:
        Path(details_file).unlink(missing_ok=True)


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", nargs="?")
    parser.add_argument("--operation", "-Operation", dest="operation_flag")
    parser.add_argument("--parameters-json", "-ParametersJson", default="")
    parser.add_argument("--parameters-json-file", "-ParametersJsonFile", default="")
    parser.add_argument("--output-mode", "-OutputMode", choices=("json", "text"), default="json")
    parser.add_argument("--error-log-path", "-ErrorLogPath", default="")
    parser.add_argument("--no-error-log", "-NoErrorLog", action="store_true")
    args = parser.parse_args()
    operation = args.operation_flag or args.operation
    if not operation:
        parser.error("operation is required")

    repo_root = Path(__file__).resolve().parents[2]
    operation_key = normalize_name(operation)
    operation_map = {
        "read_compiled_context": ("read_compiled_context.py", "read_compiled_context.py", "tools/pipeline/read_compiled_context.py"),
        "compiled_context": ("read_compiled_context.py", "read_compiled_context.py", "tools/pipeline/read_compiled_context.py"),
        "context_read": ("read_compiled_context.py", "read_compiled_context.py", "tools/pipeline/read_compiled_context.py"),
        "doc_keys": ("list_document_keys.py", "list_document_keys.py", "tools/documents/list_document_keys.py"),
        "document_keys": ("list_document_keys.py", "list_document_keys.py", "tools/documents/list_document_keys.py"),
        "doc_read": ("read_document_item.py", "read_document_item.py", "tools/documents/read_document_item.py"),
        "document_read": ("read_document_item.py", "read_document_item.py", "tools/documents/read_document_item.py"),
        "doc_item_insert": ("insert_document_item.py", "insert_document_item.py", "tools/documents/insert_document_item.py"),
        "document_item_insert": ("insert_document_item.py", "insert_document_item.py", "tools/documents/insert_document_item.py"),
        "json_item_insert": ("json_item_insert.py", "json_item_insert.py", "tools/json/json_item_insert.py"),
        "json_item_set": ("json_item_set.py", "json_item_set.py", "tools/json/json_item_set.py"),
        "tool_error_log": ("tool_error_log.py", "tool_error_log.py", "tools/pipeline/tool_error_log.py"),
    }
    envelope = {
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
    parameters: dict[str, Any] = {}
    try:
        parameters = read_parameters(args.parameters_json, args.parameters_json_file)
        if operation_key not in operation_map:
            message = f"Unknown tool operation '{operation}'."
            envelope["error"] = {"type": "unknown_operation", "message": message}
            envelope["logged_error_key"] = log_input_error(repo_root, "Tool Handler Unknown Operation", message, operation, "", parameters, args.error_log_path, args.no_error_log)
            write_envelope(envelope, args.output_mode)
            return 2
        catalog_script, target_script, target_relative = operation_map[operation_key]
        target_path = repo_root / target_relative
        envelope["target_script"] = target_script
        envelope["target_path"] = str(target_path)
        if catalog_script == "read_compiled_context.py":
            document = get_param(parameters, "Document")
            aliases = {"scripts": "SCRIPTS.json", "script": "SCRIPTS.json", "commands": "COMMANDS.json", "command": "COMMANDS.json", "flows": "FLOWS.json", "flow": "FLOWS.json", "docs": "DOCS.json", "workflow": "workflow", "rules": "rules", "entrypoint": "entrypoint", "bootstrap": "bootstrap", "engineering": "engineering"}
            if provided(document) and str(document).strip().lower() in aliases:
                set_param(parameters, "Document", aliases[str(document).strip().lower()])
        entry = script_catalog_entry(repo_root, catalog_script)
        input_spec = entry.get("input", {}) if isinstance(entry, dict) else {}
        required = list(input_spec.get("required", [])) if isinstance(input_spec, dict) else []
        optional = list(input_spec.get("optional", [])) if isinstance(input_spec, dict) else []
        if required or optional:
            allowed = {normalize_name(item) for item in required + optional}
            for name in required:
                if not provided(get_param(parameters, name)):
                    message = f"Missing required parameter '{name}' for {target_script}."
                    envelope["normalized_parameters"] = parameters
                    envelope["error"] = {"type": "input_validation", "message": message}
                    envelope["logged_error_key"] = log_input_error(repo_root, "Tool Handler Missing Required Parameter", message, operation, target_script, parameters, args.error_log_path, args.no_error_log)
                    write_envelope(envelope, args.output_mode)
                    return 2
            for key in parameters:
                if normalize_name(key) not in allowed:
                    message = f"Unknown parameter '{key}' for {target_script}."
                    envelope["normalized_parameters"] = parameters
                    envelope["error"] = {"type": "input_validation", "message": message}
                    envelope["logged_error_key"] = log_input_error(repo_root, "Tool Handler Unknown Parameter", message, operation, target_script, parameters, args.error_log_path, args.no_error_log)
                    write_envelope(envelope, args.output_mode)
                    return 2
        arguments = argument_list(parameters, required + optional)
        command = [sys.executable, str(target_path), *arguments]
        envelope["normalized_parameters"] = parameters
        envelope["command"] = command
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
        envelope["exit_code"] = completed.returncode
        output = []
        if completed.stdout:
            output.extend(completed.stdout.splitlines())
        if completed.stderr:
            output.extend(completed.stderr.splitlines())
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
        envelope["logged_error_key"] = log_input_error(repo_root, "Tool Handler Invocation Error", message, operation, str(envelope["target_script"]), parameters, args.error_log_path, args.no_error_log)
        write_envelope(envelope, args.output_mode)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
