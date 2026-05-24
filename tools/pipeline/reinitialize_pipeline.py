#!/usr/bin/env python3
"""Recreate missing initialized SocratexAI artifacts without overwriting memory."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from pipeline_script_helpers import configure_stdio, split_values, write_json


def content_of(value: Any) -> Any:
    if isinstance(value, dict) and isinstance(value.get("content"), dict):
        return value["content"]
    return value


def ensure_template(template_root: Path, install_root: Path, template: str, destination: str, dry_run: bool) -> None:
    source = template_root / template
    target = install_root / destination
    if not source.is_file():
        print(f"Skipped missing template: {template}")
        return
    if target.exists():
        return
    if dry_run:
        print(f"Would create missing initialized file: {target}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    print(f"Created missing initialized file: {destination}")


def read_config(path: Path) -> tuple[str, Any]:
    if not path.is_file():
        return "", {}
    text = path.read_text(encoding="utf-8")
    try:
        return text, json.loads(text)
    except Exception as exc:
        raise SystemExit("PIPELINE-CONFIG.json is not valid JSON.") from exc


def config_packs(config: Any) -> list[str]:
    content = content_of(config)
    if isinstance(content, dict) and isinstance(content.get("active_project_packs"), list):
        return [str(item) for item in content["active_project_packs"]]
    return []


def changelog_enabled(config: Any, use_changelog: str) -> bool:
    if use_changelog != "auto":
        return use_changelog == "yes"
    content = content_of(config)
    if isinstance(content, dict) and isinstance(content.get("changelog"), dict):
        value = str(content["changelog"].get("enabled", "yes")).lower()
        return value not in {"no", "false", "disabled", "off"}
    return True


def ensure_config_defaults(path: Path, config: Any, enabled: bool, dry_run: bool) -> None:
    if not path.is_file():
        return
    content = content_of(config)
    if not isinstance(content, dict):
        return
    changed = False
    if content.get("changelog") is None:
        content["changelog"] = {"enabled": "yes" if enabled else "no"}
        changed = True
    if content.get("communication") is None:
        content["communication"] = {"profile": "standard"}
        changed = True
    pipeline = content.setdefault("pipeline", {})
    if isinstance(pipeline, dict) and "reinitialize_command" not in pipeline:
        pipeline["reinitialize_command"] = "python SocratexAI/tools/pipeline/reinitialize_pipeline.py --target-path ."
        changed = True
    if changed:
        if dry_run:
            print("Would update PIPELINE-CONFIG.json with missing reinitialization defaults.")
            return
        write_json(path, config)
        print("Updated PIPELINE-CONFIG.json with missing reinitialization defaults.")


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-path", "-TargetPath", default=".")
    parser.add_argument("--packs", "-Packs", nargs="*", default=[])
    parser.add_argument("--use-changelog", "-UseChangelog", choices=("yes", "no", "auto"), default="auto")
    parser.add_argument("--dry-run", "-DryRun", action="store_true")
    args = parser.parse_args()

    target_root = Path(args.target_path).resolve()
    install_root = target_root / "SocratexAI"
    template_root = install_root / "templates"
    config_path = install_root / "PIPELINE-CONFIG.json"
    if not install_root.exists():
        raise SystemExit(f"Missing SocratexAI install root: {install_root}")
    if not template_root.exists():
        raise SystemExit(f"Missing SocratexAI templates root: {template_root}")

    _, config = read_config(config_path)
    packs = split_values(args.packs) or config_packs(config) or ["code"]
    enabled = changelog_enabled(config, args.use_changelog)
    print("==> reinitializing missing SocratexAI artifacts only")
    print(f"Target: {target_root}")
    print(f"Packs: {', '.join(packs)}")
    print(f"Changelog enabled: {enabled}")
    ensure_config_defaults(config_path, config, enabled, args.dry_run)

    for template in ["WORKFLOW.json", "team/product.json", "team/technical.json", "team/performance.json", "team/experience.json", "team/pipeline.json", "docs-tech/KNOWLEDGE-VIEWS.json"]:
        ensure_template(template_root, install_root, template, template, args.dry_run)
    for pack in packs:
        if pack == "code":
            for template, destination in [
                ("code/DOCS.json", "DOCS.json"),
                ("code/STATE.json", "STATE.json"),
                ("code/_PLAN.json", "_PLAN.json"),
                ("code/DECISIONS.json", "DECISIONS.json"),
                ("code/PIPELINE-CONFIG.json", "PIPELINE-CONFIG.json"),
                ("code/TODO.json", "TODO.json"),
                ("code/BUGS.json", "BUGS.json"),
                ("code/BUGS-SOLVED.json", "BUGS-SOLVED.json"),
                ("code/_PROMPT-QUEUE.json", "_PROMPT-QUEUE.json"),
                ("code/_INSTRUCTION-QUEUE.json", "_INSTRUCTION-QUEUE.json"),
                ("code/current_task.json", "docs-tech/cache/current_task.json"),
                ("code/context-docs/ENGINEERING.json", "context-docs/ENGINEERING.json"),
                ("code/context-docs/TECHNICAL.json", "context-docs/TECHNICAL.json"),
                ("code/context-docs/FROZEN_LAYERS.json", "context-docs/FROZEN_LAYERS.json"),
            ]:
                ensure_template(template_root, install_root, template, destination, args.dry_run)
            if enabled:
                ensure_template(template_root, install_root, "code/CHANGELOG.json", "CHANGELOG.json", args.dry_run)
        else:
            for template in ["DOCS.json", "STATE.md", "_PLAN.md", "DECISIONS.md", "BACKLOG.md", "ISSUES.md", "JOURNAL.md", "REVIEW.md", "PIPELINE-CONFIG.json"]:
                ensure_template(template_root, install_root, template, template, args.dry_run)
    if not args.dry_run:
        for script, script_args in [
            (install_root / "tools" / "repo" / "sync_pipeline_featurelist.py", ["--target-path", str(target_root)]),
            (install_root / "tools" / "knowledge" / "knowledge_compile.py", []),
        ]:
            if script.is_file():
                import subprocess, sys

                completed = subprocess.run([sys.executable, str(script), *script_args], check=False)
                if completed.returncode != 0:
                    raise SystemExit(f"{script.name} failed with exit code {completed.returncode}")
    print("Reinitialization complete. Existing project memory was preserved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
