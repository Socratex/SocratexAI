#!/usr/bin/env python3
"""Score the risk of a change from its diff and pick a verification level.

The score is deterministic: it comes from changed paths and sizes, never from a model's opinion.
Levels: LIGHT (fast gate of the changed area), STANDARD (+ full quality gate),
FULL (+ independent high-tier reviewer on diff and spec, + manual check request).

Rules, layered (later wins): defaults/RISK-RULES.json, then modules/profiles/<name>/RISK-RULES.json for each
config key `profiles`, then each file of config key `risk_rules` (project-relative or absolute paths).
Lists append without duplicates (path rules with the same name join their globs); scalar values are replaced.
Legacy: when neither key is set, the project's .ai/RISK-RULES.json replaces the defaults entirely.
Run from inside the project (it scores the git repository of the current directory).

Usage:
    risk_score.py                      # working tree against HEAD
    risk_score.py --commit HEAD        # one commit
    risk_score.py --paths a.cs b.py    # only these paths from the working tree
    risk_score.py --tier cheap --attempt 2
Prints one JSON object: {"score", "level", "reasons", "files", "lines"}.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SOCRATEX_HOME = Path(__file__).resolve().parents[3]
DEFAULT_RULES = SOCRATEX_HOME / "defaults" / "RISK-RULES.json"
PROJECT_RULES = Path(".ai") / "RISK-RULES.json"
PROFILES_DIR = SOCRATEX_HOME / "modules" / "profiles"


def project_root(start: Path | None = None) -> Path:
    """Git top level of the current project; the tools run from any project, not from SocratexAI."""
    start = start or Path.cwd()
    result = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=start, capture_output=True, text=True)
    return Path(result.stdout.strip()) if result.returncode == 0 and result.stdout.strip() else start


ROOT = project_root()
LEVELS = ("LIGHT", "STANDARD", "FULL")


@dataclass(frozen=True)
class FileChange:
    path: str
    lines: int


def layered_config(root: Path, socratex_home: Path | None = None) -> tuple[list[str], list[str]]:
    """Config keys `profiles` and `risk_rules` of the project (merged config layers; see docs/OVERRIDES.md)."""
    home = socratex_home or SOCRATEX_HOME
    sys.path.insert(0, str(home / "core"))
    try:
        import core
        values = core.resolve(root, home)["values"]
    except Exception as exc:  # a broken config must not stop scoring; the legacy path still works
        print(f"warning: config not read, using default risk rules: {exc}", file=sys.stderr)
        return [], []
    finally:
        sys.path.remove(str(home / "core"))
    return list(values.get("profiles", [])), list(values.get("risk_rules", []))


def merge_rules(base: dict, over: dict) -> dict:
    """Merge one rules layer over another: dicts deep-merge, lists append without duplicates, scalars are replaced.
    Path rules with the same name join their globs and take the later points."""
    merged = dict(base)
    for key, value in over.items():
        current = merged.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            merged[key] = merge_rules(current, value)
        elif key == "path_rules" and isinstance(current, list) and isinstance(value, list):
            merged[key] = merge_path_rules(current, value)
        elif isinstance(current, list) and isinstance(value, list):
            merged[key] = current + [item for item in value if item not in current]
        else:
            merged[key] = value
    return merged


def merge_path_rules(base: list[dict], over: list[dict]) -> list[dict]:
    rules = [dict(rule) for rule in base]
    for rule in over:
        same = next((r for r in rules if r["name"] == rule["name"]), None)
        if same is None:
            rules.append(dict(rule))
        else:
            same["points"] = rule["points"]
            same["globs"] = same["globs"] + [g for g in rule["globs"] if g not in same["globs"]]
    return rules


def _read_rules(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"risk rules file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def build_rules(root: Path, profiles: list[str], files: list[str], default: Path = DEFAULT_RULES,
                profiles_dir: Path = PROFILES_DIR) -> dict:
    """Layer defaults, profile files, then extra files (relative ones against the project root)."""
    rules = _read_rules(default)
    for name in profiles:
        rules = merge_rules(rules, _read_rules(profiles_dir / name / "RISK-RULES.json"))
    for entry in files:
        path = Path(entry)
        rules = merge_rules(rules, _read_rules(path if path.is_absolute() else root / path))
    return rules


def load_rules(path: Path | None = None, root: Path | None = None) -> dict:
    """Rules for scoring: an explicit file as is; else layered config; else legacy .ai file; else defaults."""
    if path is not None:
        return _read_rules(path)
    root = root or ROOT
    profiles, files = layered_config(root)
    if profiles or files:
        return build_rules(root, profiles, files)
    legacy = root / PROJECT_RULES
    return _read_rules(legacy if legacy.exists() else DEFAULT_RULES)


def matches(path: str, globs: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in globs)


def is_test_path(path: str, markers: list[str]) -> bool:
    return any(marker in path for marker in markers)


def relevant(changes: list[FileChange], rules: dict) -> list[FileChange]:
    """Drop generated files (caches, compiled indexes, binaries) that say nothing about risk."""
    return [change for change in changes if not matches(change.path, rules.get("ignore_globs", []))]


def score_changes(changes: list[FileChange], rules: dict, *, tier: str = "standard", attempt: int = 1) -> dict:
    """Pure scoring: same changes and rules always give the same result."""
    changes = relevant(changes, rules)
    if not changes:
        return {"score": 0, "level": "LIGHT", "reasons": ["no changes"], "files": 0, "lines": 0}

    paths = [change.path for change in changes]
    total_lines = sum(change.lines for change in changes)
    score = 0
    reasons: list[str] = []

    for rule in rules["path_rules"] + rules.get("learned", []):
        hits = [path for path in paths if matches(path, rule["globs"])]
        if hits:
            score += rule["points"]
            reasons.append(f"{rule['name']} {rule['points']:+d} ({hits[0]})")

    size = rules["size"]
    if total_lines > size["lines"] or len(changes) > size["files"]:
        score += size["points"]
        reasons.append(f"size {len(changes)} files / {total_lines} lines {size['points']:+d}")

    tests = rules["missing_tests"]
    code = [path for path in paths if path.endswith(tuple(tests["code_suffixes"])) and not is_test_path(path, tests["test_markers"])]
    if code and not any(is_test_path(path, tests["test_markers"]) for path in paths):
        score += tests["points"]
        reasons.append(f"code without test changes {tests['points']:+d}")

    writer = rules["writer"]
    if tier == "cheap":
        score += writer["cheap_tier_points"]
        reasons.append(f"cheap tier wrote it {writer['cheap_tier_points']:+d}")
    if attempt > 1:
        score += writer["retry_points"]
        reasons.append(f"attempt {attempt} {writer['retry_points']:+d}")

    docs = rules["docs_only"]
    if all(path.endswith(tuple(docs["suffixes"])) for path in paths):
        score += docs["points"]
        reasons.append(f"docs only {docs['points']:+d}")

    levels = rules["levels"]
    score = max(0, min(score, levels["score_cap"]))
    level = "LIGHT" if score <= levels["light_max"] else "STANDARD" if score <= levels["standard_max"] else "FULL"
    return {"score": score, "level": level, "reasons": reasons, "files": len(changes), "lines": total_lines}


def renamed_target(path: str) -> str:
    """Git numstat renames look like 'a/{old => new}/c' or 'old => new'; keep the new path."""
    if " => " not in path:
        return path
    if "{" in path and "}" in path:
        prefix, rest = path.split("{", 1)
        inner, suffix = rest.split("}", 1)
        return (prefix + inner.split(" => ", 1)[1] + suffix).replace("//", "/")
    return path.split(" => ", 1)[1]


def parse_numstat(text: str) -> list[FileChange]:
    changes = []
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added, removed, path = parts
        path = renamed_target(path)
        lines = (int(added) if added.isdigit() else 0) + (int(removed) if removed.isdigit() else 0)
        changes.append(FileChange(path.replace("\\", "/"), lines))
    return changes


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True,
                          encoding="utf-8", errors="replace").stdout


def untracked_changes(paths: list[str]) -> list[FileChange]:
    names = git("ls-files", "--others", "--exclude-standard", "--", *paths).splitlines()
    changes = []
    for name in names:
        try:
            lines = len((ROOT / name).read_text(encoding="utf-8", errors="replace").splitlines())
        except OSError:
            lines = 0
        changes.append(FileChange(name, lines))
    return changes


def collect_changes(commit: str | None, paths: list[str]) -> list[FileChange]:
    if commit:
        return parse_numstat(git("show", "--numstat", "--format=", commit, "--", *paths))
    return parse_numstat(git("diff", "--numstat", "HEAD", "--", *paths)) + untracked_changes(paths)


def main() -> int:
    parser = argparse.ArgumentParser(description="Score change risk and pick a verification level.")
    parser.add_argument("--commit", help="Score one commit instead of the working tree.")
    parser.add_argument("--paths", nargs="*", default=[], help="Limit to these paths.")
    parser.add_argument("--tier", choices=("cheap", "standard", "high", "top"), default="standard", help="Tier that wrote the change.")
    parser.add_argument("--attempt", type=int, default=1, help="Attempt number on this task (2+ = retry).")
    args = parser.parse_args()
    result = score_changes(collect_changes(args.commit, args.paths), load_rules(), tier=args.tier, attempt=args.attempt)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
