#!/usr/bin/env python3
"""SocratexPipeline toolchain doctor with Python-only tooling."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from repo_tool_helpers import repo_root, run


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    if ok:
        print(f"OK: {name} - {detail}")
    else:
        print(f"FAIL: {name} - {detail}")
        failures.append(name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check core SocratexPipeline tooling.")
    parser.add_argument("--audit-docs", "-AuditDocs", action="store_true")
    parser.add_argument("--repo-root", default="")
    args = parser.parse_args()

    root = repo_root(Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve())
    failures: list[str] = []
    print("==> SocratexPipeline toolchain doctor")
    check("git", bool(shutil.which("git")), shutil.which("git") or "missing", failures)
    check("python", bool(shutil.which("python3") or shutil.which("python")), shutil.which("python3") or shutil.which("python") or "missing", failures)
    finalizer = root / "tools" / "repo" / "finalize_task_check_commit_push.py"
    check("done finalizer", finalizer.is_file(), str(finalizer), failures)
    check("code workflow", (root / "project" / "code" / "WORKFLOW.json").is_file(), str(root / "project" / "code" / "WORKFLOW.json"), failures)
    check("agent contract", (root / "core" / "AGENT-CONTRACT.json").is_file(), str(root / "core" / "AGENT-CONTRACT.json"), failures)
    check("doc tool", (root / "tools" / "documents" / "document_read_cache_engine.py").is_file(), str(root / "tools" / "documents" / "document_read_cache_engine.py"), failures)
    check("UTF-8 write guard", (root / "tools" / "text" / "check_utf8_writes.py").is_file(), str(root / "tools" / "text" / "check_utf8_writes.py"), failures)

    status = subprocess.run(["git", "status", "--short"], cwd=root, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    check("git status", status.returncode == 0, "repository is readable", failures)

    if args.audit_docs:
        audit = root / "tools" / "documents" / "audit_docs.py"
        if audit.is_file():
            code = run("document audit", [sys.executable, "-B", str(audit), "--repo-root", str(root)], root)
            check("document audit", code == 0, "audit completed" if code == 0 else f"exit code {code}", failures)
        else:
            check("document audit", False, f"missing {audit}", failures)

    print()
    if failures:
        print(f"FAIL: doctor found {len(failures)} missing or broken tool(s).")
        return 1
    print("OK: doctor found no missing critical tools.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

