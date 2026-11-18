#!/usr/bin/env python3
"""Keep read-only reference packs (subrepos.json) in subrepos/ and search them on demand.

The packs are never installed, linked or executed: this tool only clones/updates them and reads their text.
subrepos/ is gitignored, so updating a pack never creates a change in SocratexAI that needs a push.

Usage:
    python tools/subrepos.py update            # clone missing packs, fast-forward the others
    python tools/subrepos.py list              # packs and their current commit
    python tools/subrepos.py search <words>    # skills/commands/agents whose name or description match
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "subrepos.json"
DEST = ROOT / "subrepos"
GIT_TIMEOUT = 180
SEARCH_DIRS = {"skills", "commands", "agents", "playbooks", "rules"}
SKIP_DIRS = {".git", "node_modules", "tests", "test", "docs", "examples"}


def load_manifest() -> list[dict]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["repos"]


def git(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=GIT_TIMEOUT)


def update_one(repo: dict) -> str:
    """Clone (shallow) or fast-forward one pack. Returns a one-line status; never raises on network trouble."""
    target = DEST / repo["name"]
    try:
        if not (target / ".git").exists():
            DEST.mkdir(exist_ok=True)
            done = git(["clone", "--depth", "1", "--branch", repo["branch"], repo["url"], str(target)])
            return f"{repo['name']}: cloned" if done.returncode == 0 else f"{repo['name']}: clone failed ({done.stderr.strip()[:120]})"
        before = git(["rev-parse", "HEAD"], target).stdout.strip()
        fetched = git(["fetch", "--depth", "1", "origin", repo["branch"]], target)
        if fetched.returncode != 0:
            return f"{repo['name']}: fetch failed, kept {before[:7]} ({fetched.stderr.strip()[:120]})"
        # The pack is a read-only mirror, so forcing it to upstream is safe.
        git(["reset", "--hard", "FETCH_HEAD"], target)
        after = git(["rev-parse", "HEAD"], target).stdout.strip()
        return f"{repo['name']}: " + ("up to date" if before == after else f"updated {before[:7]} -> {after[:7]}")
    except (OSError, subprocess.TimeoutExpired) as error:
        return f"{repo['name']}: skipped ({error.__class__.__name__})"


def cmd_update(quiet: bool = False) -> int:
    lines = [update_one(repo) for repo in load_manifest()]
    if not quiet or any("up to date" not in line for line in lines):
        print("\n".join(lines))
    return 0


def cmd_list() -> int:
    for repo in load_manifest():
        target = DEST / repo["name"]
        head = git(["rev-parse", "--short", "HEAD"], target).stdout.strip() if (target / ".git").exists() else "not cloned"
        print(f"{repo['name']:<12} {head:<10} {repo['what']}")
    return 0


def frontmatter(text: str) -> dict:
    match = re.match(r"---\r?\n(.*?)\r?\n---", text, re.DOTALL)
    fields: dict = {}
    for line in (match.group(1).splitlines() if match else []):
        key, _, value = line.partition(":")
        if value.strip() and key.strip() in ("name", "description"):
            fields[key.strip()] = value.strip().strip("\"'")
    return fields


def candidates(pack: Path):
    """Markdown files that describe a skill, command, agent or playbook."""
    for path in pack.rglob("*.md"):
        parts = set(path.relative_to(pack).parts[:-1])
        if parts & SKIP_DIRS or not (path.name == "SKILL.md" or parts & SEARCH_DIRS):
            continue
        yield path


def normalize(text: str) -> str:
    return re.sub(r"[-_]+", " ", text.lower())


def search(words: list[str], limit: int = 9, per_pack: int = 3) -> list[tuple[int, str, str, str]]:
    """Best matches over all packs; each pack contributes at most per_pack hits so none drowns the others."""
    terms = [normalize(word) for word in words if word.strip()]
    best: list[tuple[int, str, str, str]] = []
    for repo in load_manifest():
        pack = DEST / repo["name"]
        if not pack.exists():
            continue
        seen, hits = set(), []
        for path in candidates(pack):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")[:6000]
            except OSError:
                continue
            meta = frontmatter(text)
            name = meta.get("name") or (path.parent.name if path.name == "SKILL.md" else path.stem)
            description = meta.get("description", "")
            body, head = normalize(text), normalize(f"{name} {description}")
            score = sum(3 * head.count(term) + body.count(term) // 5 for term in terms)
            if score and all(term in body for term in terms) and name not in seen:
                seen.add(name)
                hits.append((score, f"{repo['name']}/{path.relative_to(pack).as_posix()}", name, description[:140]))
        best += sorted(hits, key=lambda hit: (-hit[0], len(hit[1])))[:per_pack]
    return sorted(best, key=lambda hit: -hit[0])[:limit]


def cmd_search(words: list[str]) -> int:
    if not DEST.exists():
        print("No packs yet: run `python tools/subrepos.py update` first.")
        return 1
    hits = search(words)
    if not hits:
        print("No match in the reference packs.")
        return 0
    for score, rel, name, description in hits:
        print(f"{name}  [{rel}]\n  {description}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage and search the read-only reference packs.")
    sub = parser.add_subparsers(dest="command", required=True)
    update = sub.add_parser("update", help="Clone missing packs and fast-forward the others.")
    update.add_argument("--quiet", action="store_true", help="Print only when something changed or failed.")
    sub.add_parser("list", help="Show the packs.")
    find = sub.add_parser("search", help="Find skills/commands/agents matching all the words.")
    find.add_argument("words", nargs="+")
    args = parser.parse_args(argv)
    if args.command == "update":
        return cmd_update(args.quiet)
    if args.command == "list":
        return cmd_list()
    return cmd_search(args.words)


if __name__ == "__main__":
    sys.exit(main())
