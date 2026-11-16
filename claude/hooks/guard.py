#!/usr/bin/env python3
"""Claude Code PreToolUse hook: deterministic guard for rules that have zero exceptions.

Reads the tool call as JSON on stdin. Exit 0 = allow, exit 2 = block (stderr goes to Claude).
Global rules (keep this list short; preferences belong in the rules, not here):
  1. Destructive git that would wipe other sessions' uncommitted work or rewrite shared history.
  2. Secret files (.env, keys) are never read or edited by the agent.
  3. Whole-file dumps of the project's big ledger files (listed in .ai/guard.json "big_files").
Project additions live in <project>/.ai/guard.json:
  {"big_files": ["TASKS.json"], "read_only_dirs": ["legacy-archive"],
   "blocked_commands": [{"pattern": "regex", "reason": "why"}], "big_file_reader": "how to read them"}
Malformed hook input fails CLOSED (blocked with a retry hint). Opt out for one session with SOCRATEX_GUARD=0.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

SECRET_NAME = re.compile(r"^(\.env(\..+)?|.+\.(pem|pfx|key|p12)|id_rsa|id_ed25519|\.credentials\.json|auth\.json)$", re.IGNORECASE)
SECRET_OK = re.compile(r"\.(example|sample|template)$", re.IGNORECASE)
READ_VERBS = r"(?:cat|type|Get-Content|gc|head|tail|more|less|bat)"
CMD_START = r"(?:^|[;&|(]\s*|&&\s*|\|\|\s*)"
# "git" followed by optional global options such as -C <dir> or -c k=v, which must not hide a subcommand.
GIT = r"\bgit\s+(?:-[Cc]\s+\S+\s+|--[\w-]+(?:=\S+)?\s+)*"
DEFAULT_READER = "read single fields with $SOCRATEX_HOME/tools/json_read.py"

GIT_RULES = (
    (GIT + r"reset\s+--hard\b", "git reset --hard would destroy uncommitted work (other sessions share this tree)."),
    (GIT + r"clean\s+-\w*[fdx]", "git clean would delete untracked work."),
    (GIT + r"(?:checkout|restore)\s+(?:--\s+)?\.(?:\s|$)", "Bulk checkout/restore of '.' would wipe uncommitted work."),
    (GIT + r"stash\s+(?:drop|clear)\b", "Dropping stashes loses work."),
    (GIT + r"push\b[^|;&]*\s(?:--force\b|-f\b)", "Force push rewrites shared history; ask the owner."),
    (GIT + r"branch\s+-D\b", "Force-deleting a branch loses commits; ask the owner."),
    (GIT + r"add\s+(?:-\w*A\w*|--all|\.)(?:\s|$)", "Stage your own paths only; add -A or . would sweep in other sessions' uncommitted work."),
    (READ_VERBS + r"\s+[^|;&]*\.env(?:\.(?!example|sample|template)\w+)?(?:\s|$|[\"'])", "Secret files are off limits."),
)


def load_project_config() -> dict:
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())
    path = root / ".ai" / "guard.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def bash_rules(config: dict) -> list[tuple[re.Pattern, str]]:
    rules = [(re.compile(pattern), reason) for pattern, reason in GIT_RULES]
    big = config.get("big_files", [])
    if big:
        reader = config.get("big_file_reader", DEFAULT_READER)
        names = "|".join(re.escape(name) for name in big)
        rules.append((re.compile(READ_VERBS + r"\s+[^|;&]*(?:" + names + r")\b", re.IGNORECASE),
                      f"Do not dump a whole ledger file; {reader}."))
    for item in config.get("blocked_commands", []):
        rules.append((re.compile(CMD_START + item["pattern"] if item.get("command_start") else item["pattern"], re.IGNORECASE),
                      item.get("reason", "Blocked by the project guard.")))
    return rules


def block(reason: str) -> int:
    sys.stderr.write(f"Blocked by guard: {reason}\n")
    return 2


def check_file(tool: str, path: str, tool_input: dict, config: dict) -> int:
    norm = path.replace("\\", "/")
    name = norm.rsplit("/", 1)[-1]
    if SECRET_NAME.match(name) and not SECRET_OK.search(name):
        return block(f"{name} looks like a secret file; the agent must not read or edit it.")
    if tool in ("Edit", "Write"):
        for folder in config.get("read_only_dirs", []):
            if re.search(r"(^|/)" + re.escape(folder.strip("/")) + r"/", norm, re.IGNORECASE):
                return block(f"{folder} is read-only in this project; do not edit it.")
    if tool == "Read" and name in config.get("big_files", []):
        limit = tool_input.get("limit")
        if not isinstance(limit, int) or limit > 300:
            reader = config.get("big_file_reader", DEFAULT_READER)
            return block(f"{name} is huge; {reader}, or Read with limit <= 300.")
    return 0


def main() -> int:
    if os.environ.get("SOCRATEX_GUARD") == "0":
        return 0
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            raise ValueError("tool call is not a JSON object")
    except Exception as error:  # noqa: BLE001 - any parse failure must fail closed
        return block(f"could not read the tool call ({error.__class__.__name__}), so it blocks to stay safe. "
                     "Retry the same call once; if it keeps failing, tell the owner (SOCRATEX_GUARD=0 disables it).")
    config = load_project_config()
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}
    if tool == "Bash":
        command = tool_input.get("command", "")
        for pattern, reason in bash_rules(config):
            if pattern.search(command):
                return block(reason)
        return 0
    if tool in ("Read", "Edit", "Write"):
        path = tool_input.get("file_path", "")
        return check_file(tool, path, tool_input, config) if path else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
