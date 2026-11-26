#!/usr/bin/env python3
"""Optional desktop side panel: Work map (lot-map) and Flow (flow-panel) stacked in one pane (side-stack).

Without it flow-panel opens its own pane (dots only). With it:
  - side-stack (upstream, pinned) and lot-map (upstream, pinned, plus claude/mods/patches/lot-map-side-stack.patch)
    are built into a local marketplace `sox-local` outside this repo and installed with `claude plugin`;
  - ~/.config/side-stack/config.json gets order [lot-map, flow-panel] and open_on_start true.
Called by install.py when the owner answered yes; also usable alone: `panel_stack.py [--check|--remove]`.
Upstream lot-map is uninstalled (it would draw twice). Both upstream projects are MIT; the code is read-only copies.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
ROOT = Path(__file__).resolve().parents[3]
PATCH = ROOT / "claude" / "mods" / "patches" / "lot-map-side-stack.patch"
MARKET = HOME / "claude-mods" / "sox-local"
MARKET_NAME = "sox-local"
CONFIG = HOME / ".config" / "side-stack" / "config.json"
ORDER = ["lot-map", "flow-panel"]
# name -> (repo, pinned commit, patch or None)
PARTS = {
    "side-stack": ("https://github.com/lucas-saldanha-werneck/side-stack.git", "b64ada8", None),
    "lot-map": ("https://github.com/alexeyw/lot-map.git", "ea9de48f", PATCH),
}


def run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    exe = shutil.which(args[0])  # Windows: `claude` is claude.cmd, which CreateProcess does not find by name
    return subprocess.run([exe or args[0], *args[1:]], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def installed() -> str:
    return run(["claude", "plugin", "list"]).stdout


def is_installed() -> bool:
    text = installed()
    return all(f"{name}@{MARKET_NAME}" in text for name in PARTS)


def config_ok() -> bool:
    try:
        data = json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return data.get("order") == ORDER and data.get("open_on_start") is True


def check() -> list[str]:
    """Report lines for what is missing (empty when the combo is fully set up)."""
    out = []
    if shutil.which("claude") is None:
        return ["panel stack: the claude CLI is not on PATH"]
    if not is_installed():
        out.append("panel stack: side-stack and lot-map are not installed from sox-local")
    if not config_ok():
        out.append(f"panel stack: {CONFIG} lacks order {ORDER} or open_on_start")
    return out


def build_market() -> None:
    """Clone the pinned upstream sources into the local marketplace and patch lot-map."""
    if shutil.which("git") is None:
        raise SystemExit("git is required")
    if MARKET.exists():
        shutil.rmtree(MARKET)
    (MARKET / ".claude-plugin").mkdir(parents=True)
    for name, (repo, commit, patch) in PARTS.items():
        target = MARKET / name
        for step in (["git", "-c", "core.autocrlf=false", "clone", "-q", repo, str(target)],
                     ["git", "checkout", "-q", commit]):
            done = run(step, cwd=target if step[1] == "checkout" else None)
            if done.returncode:
                raise SystemExit(f"{name}: {' '.join(step[:3])} failed: {done.stderr.strip()}")
        shutil.rmtree(target / ".git", ignore_errors=True)
        if patch is not None:
            # --ignore-whitespace: the patch is stored with LF, a checkout may have CRLF
            done = run(["git", "apply", "-p1", "--ignore-whitespace", str(patch)], cwd=target)
            if done.returncode:
                raise SystemExit(f"{name}: patch does not apply (upstream changed?): {done.stderr.strip()}")
    manifest = {
        "name": MARKET_NAME,
        "description": "Local copies: side-stack and lot-map patched as its guest (SocratexAI claude/mods/patches)",
        "owner": {"name": "local"},
        "plugins": [{"name": name, "source": f"./{name}"} for name in PARTS],
    }
    (MARKET / ".claude-plugin" / "marketplace.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def write_config() -> None:
    """Set order and open_on_start; every other key of an existing file is kept."""
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    try:
        data = json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    data["order"] = ORDER
    data["open_on_start"] = True
    CONFIG.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")


def install() -> int:
    if shutil.which("claude") is None:
        print("panel stack: the claude CLI is not on PATH, nothing done")
        return 1
    build_market()
    for line in (["plugin", "uninstall", "lot-map@lot-map"], ["plugin", "marketplace", "remove", "lot-map"],
                 ["plugin", "marketplace", "remove", MARKET_NAME], ["plugin", "marketplace", "add", str(MARKET)],
                 *(["plugin", "install", f"{name}@{MARKET_NAME}"] for name in PARTS)):
        done = run(["claude", *line])
        # removing what is not there fails harmlessly; adding and installing must work
        must_work = line[1] == "install" or line[1:3] == ["marketplace", "add"]
        if done.returncode and must_work:
            print(f"panel stack: `claude {' '.join(line)}` failed: {(done.stderr or done.stdout).strip()}")
            return 1
    write_config()
    print("panel stack installed: restart Claude Desktop, then /stack (Work map on top, Flow below)")
    return 0


def remove() -> int:
    for name in PARTS:
        run(["claude", "plugin", "uninstall", f"{name}@{MARKET_NAME}"])
    run(["claude", "plugin", "marketplace", "remove", MARKET_NAME])
    shutil.rmtree(MARKET, ignore_errors=True)
    print("panel stack removed (flow-panel opens its own pane again; ~/.config/side-stack/config.json is kept)")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if "--check" in args:
        lines = check()
        print("\n".join(lines) if lines else "panel stack is set up")
        return 1 if lines else 0
    if "--remove" in args:
        return remove()
    return install()


if __name__ == "__main__":
    sys.exit(main())
