#!/usr/bin/env python3
"""Mirror source-managed SocratexAI package files into a child project."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline_package import DEFAULT_CHILD_GENERATED_PATHS, DEFAULT_MANAGED_PATHS, DEFAULT_PROTECTED_PATHS


GENERATED_CACHE_DIRS = {"__pycache__"}
GENERATED_CACHE_SUFFIXES = {".pyc", ".pyo"}


def normalize_path(value: str) -> str:
    return value.replace("\\", "/").strip("/")


def relative_path(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def under_any(relative: str, roots: list[str]) -> bool:
    normalized = normalize_path(relative)
    for root in roots:
        prefix = normalize_path(root)
        if normalized == prefix or normalized.startswith(prefix + "/"):
            return True
    return False


def sha256_file(path: Path) -> str:
    if not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_manifest(path: Path) -> OrderedDict[str, Any]:
    if not path.is_file():
        return OrderedDict(
            metadata=OrderedDict(),
            managed_files=OrderedDict(),
            project_profile_files=OrderedDict(),
            local_overrides=[],
            preserved_unmanaged=[],
            removed_unmanaged=[],
        )
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=OrderedDict)


def write_manifest(path: Path, manifest: OrderedDict[str, Any], dry_run: bool) -> None:
    if dry_run:
        print(f"Would write package manifest: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=4) + "\n", encoding="utf-8", newline="\n")


def source_files_for_path(source_root: Path, relative: str, child_generated_paths: list[str]) -> list[Path]:
    source_path = source_root / relative
    if not source_path.exists():
        return []
    if source_path.is_file():
        return [source_path]
    files: list[Path] = []
    for path in sorted(source_path.rglob("*")):
        if not path.is_file():
            continue
        if any(part in GENERATED_CACHE_DIRS for part in path.parts) or path.suffix.lower() in GENERATED_CACHE_SUFFIXES:
            continue
        rel = relative_path(source_root, path)
        if rel.startswith((".git/", ".agents/", ".codex/")):
            continue
        if under_any(rel, child_generated_paths):
            continue
        files.append(path)
    return files


def copy_managed_file(
    source_root: Path,
    install_root: Path,
    relative: str,
    previous_managed: dict[str, Any],
    new_managed: OrderedDict[str, Any],
    local_overrides: list[str],
    force_managed: bool,
    dry_run: bool,
) -> None:
    source_path = source_root / relative
    destination = install_root / relative
    source_hash = sha256_file(source_path)
    destination_hash = sha256_file(destination)
    previous_entry = previous_managed.get(relative, {})
    previous_hash = previous_entry.get("hash", "") if isinstance(previous_entry, dict) else ""
    has_local_change = destination_hash and destination_hash != source_hash and (not previous_hash or destination_hash != previous_hash)
    if has_local_change and not force_managed:
        local_overrides.append(relative)
        return
    if dry_run:
        verb = "Unchanged" if destination_hash == source_hash else "Would update"
        print(f"{verb} managed file: {relative}")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)
    new_managed[relative] = OrderedDict(hash=source_hash, source=relative)


def apply_project_profile(
    source_root: Path,
    project_root: Path,
    profile: str,
    previous_profile: dict[str, Any],
    new_profile: OrderedDict[str, Any],
    local_overrides: list[str],
    force_managed: bool,
    dry_run: bool,
) -> None:
    if not profile:
        return
    profile_root = source_root / "profiles" / profile
    profile_config = profile_root / "PROFILE.json"
    if not profile_config.is_file():
        raise SystemExit(f"Unknown pipeline profile '{profile}': {profile_config}")
    profile_data = json.loads(profile_config.read_text(encoding="utf-8"))
    paths = profile_data.get("content", {}).get("managed_project_files", {}).get("paths", [])
    for raw in paths:
        relative = normalize_path(str(raw))
        source_path = profile_root / relative
        destination = project_root / relative
        if not source_path.is_file():
            raise SystemExit(f"Profile '{profile}' is missing managed project file: {relative}")
        source_hash = sha256_file(source_path)
        destination_hash = sha256_file(destination)
        previous_entry = previous_profile.get(relative, {})
        previous_hash = previous_entry.get("hash", "") if isinstance(previous_entry, dict) else ""
        has_local_change = destination_hash and destination_hash != source_hash and (not previous_hash or destination_hash != previous_hash)
        if has_local_change and not force_managed:
            local_overrides.append(relative)
            continue
        if dry_run:
            verb = "Unchanged" if destination_hash == source_hash else "Would update"
            print(f"{verb} profile file: {relative}")
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, destination)
        new_profile[relative] = OrderedDict(hash=source_hash, source=f"profiles/{profile}/{relative}")


def prune_unmanaged(
    install_root: Path,
    managed_files: OrderedDict[str, Any],
    generated_paths: list[str],
    protected_paths: list[str],
    local_overrides: list[str],
    dry_run: bool,
) -> tuple[list[str], list[str]]:
    if not install_root.exists():
        return [], []
    managed = set(managed_files.keys())
    protected = [*protected_paths, "PIPELINE-PACKAGE.json"]
    preserved: list[str] = []
    removed: list[str] = []
    for path in sorted(install_root.rglob("*"), reverse=True):
        if not path.is_file():
            continue
        rel = relative_path(install_root, path)
        if rel in managed or under_any(rel, generated_paths) or under_any(rel, protected) or under_any(rel, local_overrides):
            continue
        if dry_run:
            print(f"Would remove unmanaged package file: {rel}")
        else:
            path.unlink()
        removed.append(rel)
    if not dry_run:
        for directory in sorted([p for p in install_root.rglob("*") if p.is_dir()], key=lambda p: len(p.parts), reverse=True):
            if not any(directory.iterdir()):
                directory.rmdir()
    for path in sorted(install_root.rglob("*")):
        if not path.is_file():
            continue
        rel = relative_path(install_root, path)
        if rel in managed or under_any(rel, generated_paths) or under_any(rel, protected) or under_any(rel, local_overrides):
            continue
        preserved.append(rel)
    return sorted(set(preserved)), sorted(set(removed))


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync a managed SocratexAI package into a child project.")
    parser.add_argument("--source-root", "-SourceRoot", required=True)
    parser.add_argument("--install-root", "-InstallRoot", required=True)
    parser.add_argument("--project-root", "-ProjectRoot", default="")
    parser.add_argument("--profile", "-Profile", default="")
    parser.add_argument("--managed-paths", "-ManagedPaths", nargs="*", default=DEFAULT_MANAGED_PATHS)
    parser.add_argument("--child-generated-paths", "-ChildGeneratedPaths", nargs="*", default=DEFAULT_CHILD_GENERATED_PATHS)
    parser.add_argument("--protected-paths", "-ProtectedPaths", nargs="*", default=DEFAULT_PROTECTED_PATHS)
    parser.add_argument("--apply-project-profile", "-ApplyProjectProfile", action="store_true")
    parser.add_argument("--prune-unmanaged", "-PruneUnmanaged", action="store_true")
    parser.add_argument("--force-managed", "-ForceManaged", action="store_true")
    parser.add_argument("--dry-run", "-DryRun", action="store_true")
    args = parser.parse_args()

    source_root = Path(args.source_root).resolve()
    install_root = Path(args.install_root).resolve()
    project_root = Path(args.project_root).resolve() if args.project_root else install_root.parent
    manifest_path = install_root / "PIPELINE-PACKAGE.json"
    if args.dry_run:
        print(f"Would ensure install root: {install_root}")
    else:
        install_root.mkdir(parents=True, exist_ok=True)

    previous = read_manifest(manifest_path)
    previous_managed = previous.get("managed_files", {}) if isinstance(previous.get("managed_files"), dict) else {}
    previous_profile = previous.get("project_profile_files", {}) if isinstance(previous.get("project_profile_files"), dict) else {}
    new_managed: OrderedDict[str, Any] = OrderedDict()
    new_profile: OrderedDict[str, Any] = OrderedDict()
    local_overrides: list[str] = []

    for managed_path in args.managed_paths:
        if not str(managed_path).strip():
            continue
        for source_file in source_files_for_path(source_root, normalize_path(managed_path), args.child_generated_paths):
            rel = relative_path(source_root, source_file)
            copy_managed_file(
                source_root,
                install_root,
                rel,
                previous_managed,
                new_managed,
                local_overrides,
                args.force_managed,
                args.dry_run,
            )

    if args.apply_project_profile and args.profile:
        apply_project_profile(
            source_root,
            project_root,
            args.profile,
            previous_profile,
            new_profile,
            local_overrides,
            args.force_managed,
            args.dry_run,
        )

    preserved, removed = ([], [])
    if args.prune_unmanaged:
        preserved, removed = prune_unmanaged(
            install_root,
            new_managed,
            args.child_generated_paths,
            args.protected_paths,
            local_overrides,
            args.dry_run,
        )

    manifest = OrderedDict()
    manifest["metadata"] = OrderedDict(
        package="SocratexAI",
        schema="socratex-pipeline-package/v1",
        source_root=str(source_root),
        synced_at_utc=datetime.now(timezone.utc).isoformat(),
        profile=args.profile,
        model="source-managed package plus child additions and explicit overrides",
        child_generated_paths=args.child_generated_paths,
        protected_paths=args.protected_paths,
    )
    manifest["managed_files"] = new_managed
    manifest["project_profile_files"] = new_profile
    manifest["local_overrides"] = sorted(set(local_overrides))
    manifest["preserved_unmanaged"] = preserved
    manifest["removed_unmanaged"] = removed
    write_manifest(manifest_path, manifest, args.dry_run)

    print("OK: managed SocratexAI package sync complete.")
    if local_overrides:
        print("Preserved local overrides:")
        for path in sorted(set(local_overrides)):
            print(f" - {path}")
    if removed:
        print("Removed unmanaged package files:")
        for path in removed:
            print(f" - {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
