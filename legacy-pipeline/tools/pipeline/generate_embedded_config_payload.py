import argparse
import base64
import json
from pathlib import Path


DEFAULT_EXCLUDED_DIRECTORY_NAMES = {
    ".git",
    ".engine-config",
    ".import",
    ".venv",
    "__pycache__",
    "build",
    "logs",
    "logs-diagnostics",
    "logs-performance",
    "saves",
    "Save",
    "tmp",
    "Python312",
    "python-installer",
}


def should_skip_path(path: Path, excluded_directory_names: set[str]) -> bool:
    return any(part in excluded_directory_names for part in path.parts)


def to_resource_path(repo_root: Path, game_root: Path, json_path: Path) -> str:
    if json_path.is_relative_to(game_root):
        return "res://" + json_path.relative_to(game_root).as_posix()
    if json_path.is_relative_to(repo_root / "configs"):
        return "res://configs/" + json_path.name
    return "res://embedded_external/" + json_path.relative_to(repo_root).as_posix()


def iter_json_files(repo_root: Path, excluded_directory_names: set[str]) -> list[Path]:
    json_paths: list[Path] = []
    for path in repo_root.rglob("*.json"):
        relative_path = path.relative_to(repo_root)
        if should_skip_path(relative_path, excluded_directory_names):
            continue
        json_paths.append(path)
    return sorted(json_paths)


def iter_game_json_files(repo_root: Path, game_root: Path, excluded_directory_names: set[str]) -> list[Path]:
    return [path for path in iter_json_files(repo_root, excluded_directory_names) if path.is_relative_to(game_root)]


def iter_root_config_json_files(repo_root: Path, excluded_directory_names: set[str]) -> list[Path]:
    configs_root = repo_root / "configs"
    return [
        path
        for path in iter_json_files(repo_root, excluded_directory_names)
        if path.is_relative_to(configs_root)
    ]


def build_payload(repo_root: Path, game_root: Path, excluded_directory_names: set[str]) -> dict[str, str]:
    payload: dict[str, str] = {}
    for json_path in iter_game_json_files(repo_root, game_root, excluded_directory_names):
        resource_path = to_resource_path(repo_root, game_root, json_path)
        json_text = json_path.read_text(encoding="utf-8")
        payload[resource_path] = base64.b64encode(json_text.encode("utf-8")).decode("ascii")
    for json_path in iter_root_config_json_files(repo_root, excluded_directory_names):
        resource_path = to_resource_path(repo_root, game_root, json_path)
        json_text = json_path.read_text(encoding="utf-8")
        payload[resource_path] = base64.b64encode(json_text.encode("utf-8")).decode("ascii")
    return payload


def validate_required_payload(payload: dict[str, str], required_resource_paths: list[str]) -> None:
    missing_paths = sorted(set(required_resource_paths) - set(payload.keys()))
    if missing_paths:
        raise RuntimeError(
            "Embedded config payload is missing required file(s): "
            + ", ".join(missing_paths)
        )


def write_payload_script(output_path: Path, payload: dict[str, str]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload_text = json.dumps(payload, indent="\t", sort_keys=True)
    output_path.write_text(
        "\n".join(
            [
                "extends RefCounted",
                "",
                "# Export-generated JSON payload for self-contained playtest executables.",
                "const JSON_BASE64_BY_RESOURCE_PATH := " + payload_text,
                "",
                "",
                "func has_json_payload(resource_path: String) -> bool:",
                "\treturn JSON_BASE64_BY_RESOURCE_PATH.has(resource_path)",
                "",
                "",
                "func get_json_text(resource_path: String) -> String:",
                "\tvar encoded_text: String = String(JSON_BASE64_BY_RESOURCE_PATH.get(resource_path, \"\"))",
                "\tif encoded_text.is_empty():",
                "\t\treturn \"\"",
                "\treturn Marshalls.base64_to_raw(encoded_text).get_string_from_utf8()",
                "",
                "",
                "func get_json_payload(resource_path: String) -> Variant:",
                "\tvar json_text: String = get_json_text(resource_path)",
                "\tif json_text.is_empty():",
                "\t\treturn null",
                "\treturn JSON.parse_string(json_text)",
                "",
            ]
        ),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a Godot GDScript resource with embedded JSON payloads.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--game-root", default="Game")
    parser.add_argument("--output-path", default="Game/local_ignored_scripts/embedded_config_payload.gd")
    parser.add_argument("--exclude-dir", action="append", default=[])
    parser.add_argument("--required-resource", action="append", default=[])
    return parser.parse_args()


def resolve_path(repo_root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[2]
    game_root = resolve_path(repo_root, args.game_root)
    output_path = resolve_path(repo_root, args.output_path)
    excluded_directory_names = set(DEFAULT_EXCLUDED_DIRECTORY_NAMES)
    excluded_directory_names.update(args.exclude_dir)
    payload = build_payload(repo_root, game_root, excluded_directory_names)
    validate_required_payload(payload, args.required_resource)
    write_payload_script(output_path, payload)
    print(f"Embedded JSON payload files: {len(payload)}")
    for resource_path in sorted(payload.keys()):
        print(f"  {resource_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
