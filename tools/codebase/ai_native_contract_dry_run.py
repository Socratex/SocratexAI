#!/usr/bin/env python3
"""Print AI-native contract rollout candidates without modifying files."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_TOOLS_ROOT))

from shared.cli_helpers import configure_stdio  # noqa: E402
from shared.repo_helpers import git_lines, normalize_repo_path  # noqa: E402


CODE_EXTENSIONS = {".gd", ".cs", ".ts", ".tsx", ".js", ".jsx", ".py", ".java", ".kt", ".go", ".rs", ".php"}
IMPORTANT_WORDS = (
    "movement",
    "player",
    "world",
    "worldgen",
    "diagnostic",
    "runtime",
    "stream",
    "save",
    "persistence",
    "combat",
    "enemy",
    "camera",
    "ui",
    "audio",
    "registry",
    "repository",
    "service",
    "system",
    "controller",
    "orchestrator",
    "coordinator",
    "pipeline",
    "quality",
    "tool",
)
BOUNDARY_PARTS = {"domain", "application", "infrastructure", "system", "systems", "service", "services", "runtime", "diagnostic", "diagnostics"}
SKIP_PARTS = {".git", "AI-compiled", "SocratexAI", "ignored", "logs", "logs-diagnostics", "logs-performance", "node_modules", "vendor"}
SKIP_SUFFIXES = (".uid", ".import", ".tres", ".tscn")

def normalize(path: str) -> str:
    return normalize_repo_path(path)


def git_files(project_root: Path) -> list[str]:
    tracked = git_lines(project_root, ["ls-files"], allow_failure=True)
    if tracked:
        return [normalize(line) for line in tracked]
    files: list[str] = []
    for root, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [name for name in dirnames if name not in SKIP_PARTS]
        for filename in filenames:
            relative = normalize(str((Path(root) / filename).relative_to(project_root)))
            files.append(relative)
    return files


def should_skip(path: str) -> bool:
    normalized = normalize(path)
    parts = set(normalized.split("/"))
    if parts & SKIP_PARTS:
        return True
    if normalized.startswith("Tools/Python312/") or normalized.startswith("Tools/python-installer/") or normalized.startswith("Tools/tmp/"):
        return True
    if normalized.startswith("Game/test-scripts/"):
        return True
    return normalized.endswith(SKIP_SUFFIXES)


def line_count(path: Path) -> int:
    try:
        return sum(1 for _line in path.read_text(encoding="utf-8", errors="replace").splitlines())
    except OSError:
        return 0


def score_candidate(path: str, lines: int) -> tuple[int, str]:
    normalized = normalize(path).lower()
    parts = set(normalized.split("/"))
    score = 0
    reason = "large or boundary-like code file"
    if any(word in normalized for word in IMPORTANT_WORDS):
        score += 5
        reason = "named system/runtime/diagnostic path"
    if lines >= 250:
        score += 4
    elif lines >= 120:
        score += 2
    if parts & BOUNDARY_PARTS:
        score += 3
    if "_test" in normalized or "test_" in normalized or "spec" in normalized:
        score -= 2
    return score, reason


def candidates(project_root: Path, max_candidates: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for relative_path in git_files(project_root):
        if should_skip(relative_path):
            continue
        if Path(relative_path).suffix not in CODE_EXTENSIONS:
            continue
        full_path = project_root / relative_path
        if not full_path.is_file():
            continue
        lines = line_count(full_path)
        score, reason = score_candidate(relative_path, lines)
        if score <= 0:
            continue
        rows.append({"path": relative_path, "lines": lines, "score": score, "reason": reason})
    return sorted(rows, key=lambda row: (-int(row["score"]), -int(row["lines"]), str(row["path"])))[:max_candidates]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", "-ProjectRoot", default=".")
    parser.add_argument("--max-candidates", "-MaxCandidates", type=int, default=40)
    return parser.parse_args()


def main() -> int:
    configure_stdio()
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    rows = candidates(project_root, args.max_candidates)

    print("# AI-native code contract dry run")
    print("")
    print(f"Project root: {project_root}")
    print("Mode: dry-run only; no files were modified.")
    print("")
    print("## Header standard")
    print("")
    print("Place this as a comment-prefixed JSON-like block at the top of major system, boundary, diagnostic, runtime, or repeatedly agent-touched source files:")
    print("")
    print("AI_CONTRACT:")
    print('  purpose: "What this file exists to own."')
    print("  owns:")
    print('    - "state, behavior, or invariant owned here"')
    print("  must_not:")
    print('    - "side effect, layer, or responsibility that belongs elsewhere"')
    print("  design_goals:")
    print('    - "reader-visible intent, feel, safety, budget, or extension goal"')
    print("  non_goals:")
    print('    - "tempting behavior this file must not grow into"')
    print("  diagnostics:")
    print('    taxonomy: "[DOMAIN][SYSTEM][EVENT]"')
    print('    fields: ["stable_field_name"]')
    print("  layer:")
    print('    name: "DOMAIN_OR_LAYER"')
    print('    cannot_depend_on: ["forbidden dependency"]')
    print("  ai_notes:")
    print('    - "short future-agent warning only when useful"')
    print("")
    print("## Candidate rollout files")
    print("")
    if not rows:
        print("No strong candidates found by the lightweight heuristic.")
        return 0
    for row in rows:
        print(f"- {row['path']} ({row['lines']} lines, score {row['score']}) - {row['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
