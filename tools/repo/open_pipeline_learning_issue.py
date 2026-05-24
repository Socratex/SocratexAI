#!/usr/bin/env python3
"""Generate a prefilled GitHub issue URL for pipeline learning intake."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
from pathlib import Path
from typing import Any

from repo_tool_helpers import git_lines, package_root, split_values


def remote_repository(root: Path) -> tuple[str, str]:
    env_repo = os.environ.get("GITHUB_REPOSITORY", "")
    if "/" in env_repo:
        owner, repo = env_repo.split("/", 1)
        if owner and repo:
            return owner, repo
    lines = git_lines(root, ["remote", "get-url", "origin"], allow_failure=True)
    if not lines:
        return "", ""
    url = lines[0]
    marker = "github.com"
    if marker not in url:
        return "", ""
    tail = url.split(marker, 1)[1].lstrip(":/")
    parts = tail.removesuffix(".git").split("/")
    return (parts[0], parts[1]) if len(parts) >= 2 else ("", "")


def markdown_list(values: list[str]) -> str:
    return "\n".join(f"- `{value}`" for value in values) if values else "- none"


def issue_body(report: dict[str, Any], summary: str, changed_scripts: list[str], reporter_instruction: str) -> str:
    review = [item["id"] for item in report.get("candidates", []) if item.get("status") == "review_candidate"]
    excluded = [item["id"] for item in report.get("candidates", []) if item.get("status") == "excluded_by_pattern"]
    missing = [str(item) for item in report.get("source_features_missing_from_project", [])]
    summary = summary.strip() or "The reporting project exposes pipeline feature IDs that should be reviewed against the source SocratexPipeline feature list."
    reporter_instruction = reporter_instruction.strip() or "- none"
    return "\n".join(
        [
            f"<!-- socratex-pipeline-learning-report:{report.get('report_hash', '')} -->",
            "# SocratexPipeline Learning Report",
            "",
            "## Source",
            "",
            f"- Source pipeline: `{report.get('source_pipeline_id', '')}`",
            f"- Project pipeline: `{report.get('project_pipeline_id', '')}`",
            f"- Reported: {report.get('generated_at', '')}",
            f"- Report hash: `{report.get('report_hash', '')}`",
            "",
            "## What AI Learned",
            "",
            summary,
            "",
            "## What This Intake Tool Does",
            "",
            "- `tools/repo/report_pipeline_learning.py` compares a project `pipeline_featurelist.json` with the source manifest and classifies unknown feature IDs.",
            "- `tools/repo/open_pipeline_learning_issue.py` turns that report into this prefilled GitHub Issue URL without using a write token or API write.",
            "- `tools/repo/learn_pipeline_features.py` is the maintainer-side promotion tool for reviewed reusable feature IDs.",
            "- `tools/repo/sync_pipeline_featurelist.py` propagates source feature IDs back into installed project instance manifests after the source learns something reusable.",
            "",
            "## Changed Scripts Or Files To Review",
            "",
            markdown_list(changed_scripts),
            "",
            "## Review Candidates",
            "",
            markdown_list(review),
            "",
            "## Excluded Candidates",
            "",
            markdown_list(excluded),
            "",
            "## Source Features Missing From Project",
            "",
            markdown_list(missing),
            "",
            "## Recommendation",
            "",
            "Use this report as intake only. Promote only reusable, project-agnostic feature IDs into the source pipeline after review.",
            "",
            "## Maintainer Instructions",
            "",
            "1. Check whether each review candidate is reusable outside the reporting project.",
            "2. Keep project-specific, framework-specific, or domain-specific IDs out of the source manifest unless they describe a generic pipeline capability.",
            "3. Promote selected reusable IDs with:",
            "",
            "```bash",
            'python -B tools/repo/learn_pipeline_features.py --project-path "<project>" --apply --include-features <ids>',
            "```",
            "",
            "4. After promotion, update or reinitialize consuming projects so `tools/repo/sync_pipeline_featurelist.py` can refresh their instance manifests.",
            "",
            "## Reporter Notes",
            "",
            reporter_instruction,
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a prefilled GitHub Issue URL.")
    parser.add_argument("--project-path", "-ProjectPath", required=True)
    parser.add_argument("--source-feature-list-path", "-SourceFeatureListPath", default="")
    parser.add_argument("--owner", "-Owner", default="")
    parser.add_argument("--repo", "-Repo", default="")
    parser.add_argument("--issue-title", "-IssueTitle", default="SocratexPipeline Learning Report")
    parser.add_argument("--learned-summary", "-LearnedSummary", default="")
    parser.add_argument("--changed-scripts", "-ChangedScripts", nargs="*", default=[])
    parser.add_argument("--reporter-instruction", "-ReporterInstruction", default="")
    parser.add_argument("--exclude-patterns", "-ExcludePatterns", nargs="*", default=["project_specific", "runtime_diagnostic"])
    parser.add_argument("--open", "-Open", action="store_true", help="Print-only parity flag; Python path does not launch a browser.")
    args = parser.parse_args()

    root = package_root()
    owner, repo = args.owner, args.repo
    if not owner or not repo:
        detected_owner, detected_repo = remote_repository(root)
        owner = owner or detected_owner
        repo = repo or detected_repo
    if not owner or not repo:
        print("ERROR: missing GitHub repository. Pass --owner and --repo or configure origin/GITHUB_REPOSITORY.", file=sys.stderr)
        return 2

    report_command = [
        sys.executable,
        "-B",
        str(root / "tools" / "repo" / "report_pipeline_learning.py"),
        "--project-path",
        args.project_path,
        "--exclude-patterns",
        ",".join(split_values(args.exclude_patterns)),
    ]
    if args.source_feature_list_path:
        report_command.extend(["--source-feature-list-path", args.source_feature_list_path])
    completed = subprocess.run(report_command, cwd=root, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        print(completed.stderr or completed.stdout, file=sys.stderr)
        return completed.returncode
    report = json.loads(completed.stdout)
    title = f"{args.issue_title}: {report.get('project_pipeline_id', '')}"
    body = issue_body(report, args.learned_summary, split_values(args.changed_scripts), args.reporter_instruction)
    query = urllib.parse.urlencode({"title": title, "body": body, "labels": "socratex-pipeline,learning-inbox"})
    url = f"https://github.com/{owner}/{repo}/issues/new?{query}"

    if len(url) > 7500:
        print(f"WARNING: generated issue URL is long ({len(url)} characters).")
    print("OK: generated prefilled GitHub Issue URL.")
    print(url)
    if args.open:
        print("NOTE: --open is intentionally print-only in the Python path.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
