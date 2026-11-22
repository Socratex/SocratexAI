#!/usr/bin/env python3
"""Redirect shims at the old tools/<name>.py paths, kept for projects that still call $SOCRATEX_HOME/tools/....

Each shim forwards argv and the exit code to modules/tools/scripts/<name>.py and appends one JSON line
{ts, shim, argv0} to state/shim-usage.jsonl (silent on any failure). `sox shims` lists them with call counts,
so the owner can see whether anything still calls the old paths and delete a shim when it is unused.
Stdlib only; used by core/sox and tests/test_shims.py.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET_DIR = "modules/tools/scripts"
USAGE_FILE = Path("state") / "shim-usage.jsonl"
# CLI scripts only; importable helpers (generated.py) have no outside caller and get no shim.
SHIM_NAMES = ("backup", "build_index", "check_leaks", "improvements_check", "install", "json_read", "risk_score",
              "routing_log", "routing_stats", "skill_learn", "state", "subrepos", "update")

TEMPLATE = '''#!/usr/bin/env python3
# REDIRECT to {target}; kept for external callers (see `sox shims`).
import json, runpy, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
try:  # usage counter; any failure is ignored so the command never breaks
    (ROOT / "state").mkdir(exist_ok=True)
    with open(ROOT / "state" / "shim-usage.jsonl", "a", encoding="utf-8") as log:
        log.write(json.dumps({{"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "shim": "{name}", "argv0": sys.argv[0]}}) + "\\n")
except Exception:
    pass
NEW = ROOT / "{target}"
sys.path.insert(0, str(NEW.parent))
sys.argv[0] = str(NEW)
runpy.run_path(str(NEW), run_name="__main__")
'''


def render(name: str) -> str:
    """The exact text of the shim for one script."""
    return TEMPLATE.format(name=name, target=f"{TARGET_DIR}/{name}.py")


def shim_path(name: str, root: Path | None = None) -> Path:
    return (root or ROOT) / "tools" / f"{name}.py"


def regenerate(root: Path | None = None) -> list[Path]:
    """Write every shim (replacing stale text). Returns the paths that changed."""
    changed = []
    for name in SHIM_NAMES:
        path = shim_path(name, root)
        text = render(name)
        if not path.is_file() or path.read_text(encoding="utf-8") != text:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
            changed.append(path)
    return changed


def problems(root: Path | None = None) -> list[str]:
    """Missing or edited shims, shims without a target script, and stray files in tools/."""
    base = root or ROOT
    found = []
    for name in SHIM_NAMES:
        path = shim_path(name, base)
        if not path.is_file():
            found.append(f"missing shim: tools/{name}.py")
        elif path.read_text(encoding="utf-8") != render(name):
            found.append(f"shim differs from its template: tools/{name}.py")
        if not (base / TARGET_DIR / f"{name}.py").is_file():
            found.append(f"shim target missing: {TARGET_DIR}/{name}.py")
    tools = base / "tools"
    if tools.is_dir():
        known = {f"{name}.py" for name in SHIM_NAMES}
        found += [f"unexpected file in tools/: {p.name}" for p in sorted(tools.iterdir())
                  if p.is_file() and p.name not in known]
    return found


def usage(root: Path | None = None) -> dict[str, dict]:
    """{shim: {"calls": n, "last": ts, "callers": [argv0, ...]}} read from state/shim-usage.jsonl (bad lines skipped)."""
    result = {name: {"calls": 0, "last": "", "callers": []} for name in SHIM_NAMES}
    path = (root or ROOT) / USAGE_FILE
    if not path.is_file():
        return result
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(line)
            entry = result[row["shim"]]
        except (ValueError, KeyError, TypeError):
            continue
        entry["calls"] += 1
        entry["last"] = max(entry["last"], str(row.get("ts", "")))
        caller = str(row.get("argv0", ""))
        if caller and caller not in entry["callers"]:
            entry["callers"].append(caller)
    return result


def lines(root: Path | None = None, show_list: bool = True, show_usage: bool = True) -> list[str]:
    """Report lines for `sox shims`: one row per shim."""
    counts = usage(root)
    out = []
    for name in SHIM_NAMES:
        row = f"tools/{name}.py"
        if show_list:
            row += f"  ->  {TARGET_DIR}/{name}.py"
        if show_usage:
            entry = counts[name]
            row += f"  calls: {entry['calls']}" + (f"  last: {entry['last']}" if entry["calls"] else "")
        out.append(row)
    unused = [n for n in SHIM_NAMES if not counts[n]["calls"]]
    if show_usage:
        out.append(f"{len(unused)} of {len(SHIM_NAMES)} shims were never called (state/shim-usage.jsonl); "
                   "delete an unused shim once no external project needs it.")
    return out
