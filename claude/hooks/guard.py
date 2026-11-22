#!/usr/bin/env python3
"""Claude Code PreToolUse hook: deterministic guard for rules that have zero exceptions.

Reads the tool call as JSON on stdin. Exit 0 = allow, exit 2 = block (stderr goes to Claude).
The rules are DATA: core/safety.json (schema socratex-safety/v1) names every rule and says how it is enforced:
  destructive-git, git-add-all, secret-files, ledger-dumps, refs-read-only, project-read-only-dirs,
  project-blocked-commands and safety-config-edits (the agent cannot edit the files that define or relax rules).
An owner layer relaxes a rule with `safety.allow: [id]` (config layers: defaults/profile yolo, local/overrides,
local/projects/<name>; a project file cannot); the guard resolves the effective config through core/core.py and skips
the listed ids. safety-config-edits cannot be relaxed. Project additions live in <project>/.ai/guard.json:
  {"big_files": ["TASKS.json"], "read_only_dirs": ["legacy-archive"],
   "blocked_commands": [{"pattern": "regex", "reason": "why"}], "big_file_reader": "how to read them"}
Malformed hook input or an unreadable core/safety.json fails CLOSED (blocked with a hint).
Owner-only switches (set outside the agent): SOCRATEX_GUARD=0 turns the guard off for one session;
SOCRATEX_GUARD_ALLOW_SAFETY_EDIT=1 lets the agent edit the protected safety and config files for one session.
SOCRATEX_HOME overrides the SocratexAI folder the rules and layers are read from (default: the folder of this hook).
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[2]
ROOT = Path(os.environ.get("SOCRATEX_HOME") or CODE_ROOT)
CMD_START = r"(?:^|[;&|(]\s*|&&\s*|\|\|\s*)"
REFS_WRITE = re.compile(r"(?:\b(?:rm|mv|cp|touch|mkdir|tee|rmdir|truncate|chmod|Remove-Item|Set-Content|Add-Content|"
                        r"Out-File|Move-Item|Copy-Item|New-Item)\b|\bsed\s+-\w*i|"
                        r"\bgit\s+(?:-[Cc]\s+\S+\s+)*(?:commit|push|reset|checkout|clean|apply|am|merge|rebase|restore)\b)",
                        re.IGNORECASE)
WRITE_VERBS = {"rm", "mv", "touch", "mkdir", "tee", "rmdir", "truncate", "chmod", "unlink", "remove-item", "set-content",
               "add-content", "out-file", "move-item", "new-item"}
GIT_WRITE = {"commit", "push", "reset", "checkout", "clean", "apply", "am", "merge", "rebase", "restore", "add", "rm", "mv"}
INTERPRETERS = {"python", "python3", "py", "node", "perl", "ruby", "pwsh", "powershell", "sh", "bash"}
INLINE_FLAGS = {"-c", "-e", "-command", "-encodedcommand"}
CODE_WRITES = re.compile(r"\b(?:write|open\s*\(|dump|Set-Content|Add-Content|Out-File|rename|replace|unlink|remove|copy|move|save)", re.IGNORECASE)


# ---------- the rules (core/safety.json) ----------

def load_safety() -> dict:
    """Read the named rules; raises when the file is unreadable or malformed, so the caller fails closed."""
    data = json.loads((ROOT / "core" / "safety.json").read_text(encoding="utf-8"))
    if data.get("schema") != "socratex-safety/v1" or not isinstance(data.get("rules"), list):
        raise ValueError("core/safety.json is not a socratex-safety/v1 file")
    return data


def expand(pattern: str, fragments: dict) -> str:
    for name, value in fragments.items():
        pattern = pattern.replace("{" + name + "}", value)
    return pattern


def project_dir() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())


def effective_allow() -> set[str]:
    """Ids the effective config relaxes (owner layers only). Any failure means no relaxation: the guard stays strict."""
    try:
        sys.path.insert(0, str(CODE_ROOT / "core"))
        import core
        return core.relaxed_rule_ids(project_dir(), ROOT)
    except Exception:  # noqa: BLE001 - an unreadable config must never loosen the guard
        return set()


def active_rules(safety: dict, allow: set[str]) -> list[dict]:
    """The rules that apply now: all of them, minus relaxable ones whose id is in `allow`."""
    return [rule for rule in safety["rules"] if not (rule["id"] in allow and rule["relaxable"])]


def enforcements(rules: list[dict], kind: str) -> list[dict]:
    return [entry for rule in rules for entry in rule["enforce"] if entry["kind"] == kind]


# ---------- paths ----------

def refs_root() -> str:
    """The reference packs folder as a lowercase forward-slash path."""
    root = os.environ.get("SOCRATEX_REFS") or str(Path.home() / "ai-refs")
    return root.replace("\\", "/").rstrip("/").lower()


def in_refs(path: str) -> bool:
    root = refs_root()
    norm = path.replace("\\", "/").lower()
    return norm == root or norm.startswith(root + "/")


def is_refs_path(token: str) -> bool:
    """True when one argument names a path inside the refs folder (free text with spaces never counts)."""
    text = token.strip("\"'").replace("\\", "/").lower()
    if not text or re.search(r"\s", text):
        return False
    if text == "~" or text.startswith("~/"):
        text = str(Path.home()).replace("\\", "/").lower() + text[1:]
    folder = refs_root().rsplit("/", 1)[-1]
    return in_refs(text) or ("/" + folder + "/") in ("/" + text.rstrip("/") + "/")


def refs_loose(segment: str) -> bool:
    folder = refs_root().rsplit("/", 1)[-1]
    return folder in segment.replace("\\", "/").lower() and bool(REFS_WRITE.search(segment))


def absolute_lower(token: str) -> str:
    """A path argument as an absolute, normalised, lowercase forward-slash string (relative ones resolve against the project)."""
    text = os.path.expandvars(os.path.expanduser(token.strip("\"'")))
    drive = re.match(r"^/([a-zA-Z])/", text)
    if os.name == "nt" and drive:  # git-bash style /c/Users/...
        text = drive.group(1) + ":/" + text[3:]
    if not os.path.isabs(text):
        text = os.path.join(project_dir(), text)
    return os.path.normpath(text).replace("\\", "/").lower()


def protected_hit(entry: dict, token: str) -> bool:
    """True when `token` names a file this protected-paths enforcement covers."""
    if not token or re.search(r"\s", token.strip("\"'")):
        return False
    path = absolute_lower(token)
    base = str(ROOT).replace("\\", "/").lower().rstrip("/")
    for pattern in entry.get("repo_paths", []):
        wanted = base + "/" + pattern.lower()
        if pattern.endswith("/**"):
            wanted = wanted[:-3]
            if path == wanted or path.startswith(wanted + "/"):
                return True
        elif path == wanted:
            return True
    return any(path == name.lower() or path.endswith("/" + name.lower()) for name in entry.get("anywhere_paths", []))


def protected_needles(entry: dict) -> list[str]:
    return [p.lower().removesuffix("/**") for p in entry.get("repo_paths", [])] + [p.lower() for p in entry.get("anywhere_paths", [])]


# ---------- Bash command analysis ----------

def segment_writes(segment: str, is_target, loose, git_write: set[str]) -> bool:
    """True when one shell segment writes to a path accepted by `is_target` (reads, searches and prose mentions pass)."""
    for match in re.finditer(r">>?\s*([^\s;&|<>]+)", segment):
        if is_target(match.group(1)):
            return True
    try:
        tokens = shlex.split(segment)
    except ValueError:  # unbalanced quotes: stay strict
        return loose(segment)
    while tokens and (re.fullmatch(r"\w+=\S*", tokens[0]) or tokens[0] in ("sudo", "command", "env")):
        tokens.pop(0)
    if not tokens:
        return False
    cmd, args = tokens[0].lower().rsplit("/", 1)[-1], tokens[1:]
    paths = [a for a in args if not a.startswith("-")]
    if cmd in WRITE_VERBS:
        return any(is_target(a) for a in args)
    if cmd in ("cp", "copy-item"):  # copying FROM the target is a read; only the destination counts
        return bool(paths) and is_target(paths[-1])
    if cmd == "sed":
        in_place = any(re.fullmatch(r"-\w*i\w*(\..*)?|--in-place(=.*)?", a) for a in args)
        return in_place and any(is_target(a) for a in args)
    if cmd == "git":
        index, sub = 0, ""
        while index < len(args):
            if args[index] in ("-C", "-c"):
                index += 2
            elif args[index].startswith("-"):
                index += 1
            else:
                sub = args[index]
                break
        return sub in git_write and any(is_target(a) for a in args)
    return False


def split_segments(command: str) -> list[str]:
    return re.split(r"\|\||&&|[;|&\n]", command)


def command_writes_refs(command: str) -> bool:
    folder = refs_root().rsplit("/", 1)[-1]
    if folder not in command.replace("\\", "/").lower():
        return False
    return any(segment_writes(part, is_refs_path, refs_loose, GIT_WRITE) for part in split_segments(command))


def command_writes_protected(command: str, entry: dict) -> bool:
    """A command that writes a protected file: write verbs, redirects and inline interpreter code that mentions one."""
    needles = protected_needles(entry)
    flat = command.replace("\\", "/").lower()
    if not any(needle in flat for needle in needles):
        return False

    def is_target(token: str) -> bool:
        return protected_hit(entry, token)

    def loose(segment: str) -> bool:
        text = segment.replace("\\", "/").lower()
        return any(needle in text for needle in needles) and bool(REFS_WRITE.search(segment))

    git_write = GIT_WRITE - {"add", "commit"}  # staging or committing what the owner changed does not alter it
    if any(segment_writes(part, is_target, loose, git_write) for part in split_segments(command)):
        return True
    for part in split_segments(command):  # inline code (python -c, heredocs) cannot be parsed: deny when it looks like a write
        words = part.split()
        if words and words[0].lower().rsplit("/", 1)[-1].removesuffix(".exe") in INTERPRETERS \
                and (INLINE_FLAGS & {w.lower() for w in words[1:]} or "<<" in part) and CODE_WRITES.search(command):
            return True
    return False


def bash_rules(config: dict, rules: list[dict], fragments: dict) -> list[tuple[re.Pattern, str]]:
    """Compiled (pattern, reason) pairs for the command checks of the active rules, in rule order."""
    compiled: list[tuple[re.Pattern, str]] = []
    for rule in rules:
        for entry in rule["enforce"]:
            kind = entry["kind"]
            if kind == "bash-regex":
                compiled.append((re.compile(expand(entry["regex"], fragments)), entry["reason"]))
            elif kind == "project-big-files" and config.get(entry["project_key"]):
                reader = config.get(entry["reader_key"], entry["default_reader"])
                names = "|".join(re.escape(name) for name in config[entry["project_key"]])
                read_verbs = fragments["READ_VERBS"]
                compiled.append((re.compile(read_verbs + r"\s+[^|;&]*(?:" + names + r")\b", re.IGNORECASE),
                                 f"Do not dump a whole ledger file; {reader}."))
            elif kind == "project-blocked-commands":
                for item in config.get(entry["project_key"], []):
                    pattern = CMD_START + item["pattern"] if item.get("command_start") else item["pattern"]
                    compiled.append((re.compile(pattern, re.IGNORECASE), item.get("reason", "Blocked by the project guard.")))
    return compiled


# ---------- checks ----------

def load_project_config() -> dict:
    path = project_dir() / ".ai" / "guard.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def block(reason: str) -> int:
    sys.stderr.write(f"Blocked by guard: {reason}\n")
    return 2


def protected_active(rules: list[dict], tool: str) -> list[dict]:
    """protected-paths enforcements that apply to `tool` and are not switched off by the owner's environment variable."""
    return [entry for entry in enforcements(rules, "protected-paths")
            if tool in entry["tools"] and os.environ.get(entry["override_env"]) != "1"]


def check_file(tool: str, path: str, tool_input: dict, config: dict, rules: list[dict]) -> int:
    norm = path.replace("\\", "/")
    name = norm.rsplit("/", 1)[-1]
    if tool in ("Edit", "Write"):
        for entry in protected_active(rules, tool):
            if protected_hit(entry, path):
                return block(entry["reason"].replace("{path}", norm))
    for entry in enforcements(rules, "file-name"):
        if tool in entry["tools"] and re.match(entry["name_regex"], name, re.IGNORECASE) \
                and not re.search(entry["except_regex"], name, re.IGNORECASE):
            return block(entry["reason"].replace("{name}", name))
    if tool in ("Edit", "Write"):
        if enforcements(rules, "refs-write") and in_refs(path):
            return block(enforcements(rules, "refs-write")[0]["reason"])
        for entry in enforcements(rules, "project-read-only-dirs"):
            if tool in entry["tools"]:
                for folder in config.get(entry["project_key"], []):
                    if re.search(r"(^|/)" + re.escape(folder.strip("/")) + r"/", norm, re.IGNORECASE):
                        return block(f"{folder} is read-only in this project; do not edit it.")
    if tool == "Read":
        for entry in enforcements(rules, "project-big-files"):
            if name in config.get(entry["project_key"], []):
                limit = tool_input.get("limit")
                if not isinstance(limit, int) or limit > entry["max_read_limit"]:
                    reader = config.get(entry["reader_key"], entry["default_reader"])
                    return block(f"{name} is huge; {reader}, or Read with limit <= {entry['max_read_limit']}.")
    return 0


def check_bash(command: str, config: dict, safety: dict, rules: list[dict]) -> int:
    for entry in protected_active(rules, "Bash"):
        if command_writes_protected(command, entry):
            return block(entry["reason"].replace("{path}", "a protected safety or config file"))
    refs = enforcements(rules, "refs-write")
    if refs and command_writes_refs(command):
        return block(refs[0]["bash_reason"])
    for pattern, reason in bash_rules(config, rules, safety["fragments"]):
        if pattern.search(command):
            return block(reason)
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
    try:
        safety = load_safety()
    except Exception as error:  # noqa: BLE001 - without the rules the guard cannot judge: fail closed
        return block(f"core/safety.json is unreadable ({error.__class__.__name__}: {error}), so every call blocks to stay safe. "
                     "Tell the owner to fix it (SOCRATEX_GUARD=0 disables the guard for one session).")
    rules = active_rules(safety, effective_allow())
    config = load_project_config()
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}
    if tool == "Bash":
        return check_bash(tool_input.get("command", ""), config, safety, rules)
    if tool in ("Read", "Edit", "Write"):
        path = tool_input.get("file_path", "")
        return check_file(tool, path, tool_input, config, rules) if path else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
