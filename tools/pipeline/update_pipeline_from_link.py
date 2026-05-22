#!/usr/bin/env python3
"""Python-first SocratexPipeline updater for installed child projects."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Any


def run(command: list[str], cwd: Path) -> None:
    completed = subprocess.run(command, cwd=cwd, check=False)
    if completed.returncode != 0:
        raise SystemExit(f"{' '.join(command)} failed with exit code {completed.returncode}")


def content_of(config: dict[str, Any]) -> dict[str, Any]:
    content = config.get("content")
    return content if isinstance(content, dict) else config


def configured_profile(config_path: Path, explicit: str) -> str:
    if explicit:
        return explicit
    if not config_path.is_file():
        return ""
    try:
        content = content_of(json.loads(config_path.read_text(encoding="utf-8")))
    except Exception:
        return ""
    pipeline = content.get("pipeline") if isinstance(content.get("pipeline"), dict) else {}
    if str(pipeline.get("profile", "")).strip():
        return str(pipeline["profile"]).strip()
    if str(content.get("project_subcontext", "")).lower() == "gamedev":
        return "SocratexGamedev"
    return ""


def is_git_source(source: str) -> bool:
    return source.startswith("git+") or source.endswith(".git") or "github.com/" in source


def resolve_source(source: str, source_mode: str, git_ref: str, temp_root: Path) -> Path:
    if source_mode == "LocalPath" or (source_mode == "Auto" and Path(source).exists()):
        return Path(source).resolve()
    temp_root.mkdir(parents=True, exist_ok=True)
    if source_mode == "Git" or (source_mode == "Auto" and is_git_source(source)):
        repo_url = source.removeprefix("git+")
        ref = git_ref
        if "#" in repo_url:
            repo_url, ref = repo_url.split("#", 1)
        clone_root = temp_root / "source"
        run(["git", "clone", "--depth", "1", "--branch", ref, repo_url, str(clone_root)], temp_root)
        return clone_root
    zip_path = temp_root / "pipeline.zip"
    urllib.request.urlretrieve(source, zip_path)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(temp_root)
    dirs = [path for path in temp_root.iterdir() if path.is_dir()]
    return dirs[0] if len(dirs) == 1 else temp_root


def update_directives(target_root: Path, mode: str, directive_files: list[str], dry_run: bool) -> None:
    socratex_file = target_root / "SOCRATEX.md"
    if not socratex_file.is_file():
        raise SystemExit("Missing root SOCRATEX.md. Install or import SocratexPipeline before updating directives.")
    merge_directive = "Primary directive: read and respect `SOCRATEX.md` before following this file. SocratexPipeline is installed under `SocratexAI/`."
    replace_directive = "# Agent Directive\n\nRead `SOCRATEX.md` first and treat it as the controlling AI pipeline directive for this project.\n\nSocratexPipeline is installed under `SocratexAI/`.\n"
    for directive in directive_files:
        target = target_root / directive
        if mode == "snapshot":
            if target.exists() and not dry_run:
                destination = target.with_name(target.name + ".old")
                shutil.copy2(target, destination)
            continue
        if mode == "replace":
            if dry_run:
                print(f"Would replace directive file: {directive}")
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    shutil.copy2(target, target.with_name(target.name + ".old"))
                target.write_text(replace_directive, encoding="utf-8", newline="\n")
            continue
        if target.exists():
            current = target.read_text(encoding="utf-8")
            if "SOCRATEX.md" in current:
                print(f"Skip merge; SOCRATEX.md directive already appears in {directive}")
                continue
            merged = current.rstrip() + "\n\n" + merge_directive + "\n"
        else:
            merged = replace_directive
        if dry_run:
            print(f"Would merge directive file: {directive}")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(merged, encoding="utf-8", newline="\n")


def refresh_document_cache(install_root: Path) -> None:
    cache_engine = install_root / "tools" / "documents" / "document_read_cache_engine.py"
    if not cache_engine.is_file():
        return
    run(
        [
            sys.executable,
            str(cache_engine),
            "build-cache",
            "__ALL_JSON__",
            "--output-dir",
            str(install_root / "docs-tech" / "cache"),
            "--repo-root",
            str(install_root),
        ],
        install_root,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Update an installed SocratexPipeline package.")
    parser.add_argument("--source", required=True)
    parser.add_argument("--target-path", default=".")
    parser.add_argument("--source-mode", choices=("Auto", "LocalPath", "Zip", "Git"), default="Auto")
    parser.add_argument("--git-ref", default="main")
    parser.add_argument("--packs", nargs="*", default=["code"])
    parser.add_argument("--profile", default="")
    parser.add_argument("--directive-mode", choices=("snapshot", "merge", "replace"), default="merge")
    parser.add_argument("--directive-files", nargs="*", default=["AGENTS.md"])
    parser.add_argument("--reinitialize-new", action="store_true")
    parser.add_argument("--full-verify", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    target_root = Path(args.target_path).resolve()
    install_root = target_root / "SocratexAI"
    with tempfile.TemporaryDirectory(prefix="socratex-pipeline-update-") as raw_temp:
        source_root = resolve_source(args.source, args.source_mode, args.git_ref, Path(raw_temp))
        profile = configured_profile(install_root / "PIPELINE-CONFIG.json", args.profile)
        print("==> updating SocratexPipeline")
        print(f"Source: {source_root}")
        print(f"Target: {target_root}")
        print(f"Install root: {install_root}")
        if profile:
            print(f"Project profile: {profile}")

        sync_script = source_root / "tools" / "pipeline" / "sync_managed_pipeline_package.py"
        if not sync_script.is_file():
            raise SystemExit(f"Update source is missing required managed package sync script: {sync_script}")
        sync_cmd = [
            sys.executable,
            str(sync_script),
            "--source-root",
            str(source_root),
            "--install-root",
            str(install_root),
            "--project-root",
            str(target_root),
            "--prune-unmanaged",
        ]
        if profile:
            sync_cmd += ["--profile", profile, "--apply-project-profile"]
        if args.dry_run:
            sync_cmd.append("--dry-run")
        run(sync_cmd, target_root)

        template_controller = source_root / "templates" / "SOCRATEX.md"
        if template_controller.is_file():
            if args.dry_run:
                print(f"Would copy root controller: {template_controller} -> {target_root / 'SOCRATEX.md'}")
            else:
                shutil.copy2(template_controller, target_root / "SOCRATEX.md")

        if args.reinitialize_new:
            print("WARNING: --reinitialize-new still requires the legacy reinitializer until its Python port lands.")
        if not args.dry_run:
            refresh_document_cache(install_root)
            feature_sync = install_root / "tools" / "repo" / "sync_pipeline_featurelist.py"
            if feature_sync.is_file():
                run([sys.executable, str(feature_sync), "--target-path", str(target_root)], target_root)
            update_directives(target_root, args.directive_mode, args.directive_files, args.dry_run)
            contract_check = install_root / "tools" / "repo" / "check_pipeline_feature_contracts.py"
            if contract_check.is_file():
                run([sys.executable, str(contract_check), "--repo-root", str(install_root)], install_root)
            if args.full_verify:
                audit = install_root / "tools" / "documents" / "audit_docs.py"
                if audit.is_file():
                    run([sys.executable, str(audit), "--repo-root", str(install_root)], install_root)
            else:
                print("Skipped full verification. Use --full-verify to run the Python document audit.")
    print("Pipeline update complete. SocratexAI is active for this project; future sessions should start from SOCRATEX.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
