"""Shared helper of the flow-panel tests: runs parts of the real register.tsx with Node 22+."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[2]
SOURCE = ROOT / "claude/mods/flow-panel/hooks/register.tsx"
NODES = [str(Path.home() / ".local/opt/node22/bin/node"), "node"]


def node_path() -> str | None:
    for candidate in NODES:
        path = candidate if Path(candidate).is_absolute() else shutil.which(candidate)
        if not path or not Path(path).exists():
            continue
        out = subprocess.run([path, "--version"], capture_output=True, text=True).stdout.strip()
        major = int(re.match(r"v(\d+)", out).group(1)) if re.match(r"v(\d+)", out) else 0
        if major >= 22:
            return path
    return None


def _execute(code: str) -> object:
    node = node_path()
    if node is None:
        raise unittest.SkipTest("Node 22+ not available")
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "t.ts"
        script.write_text(code, encoding="utf-8")
        res = subprocess.run(
            [node, "--experimental-strip-types", "--no-warnings", str(script)], capture_output=True, text=True, encoding="utf-8"
        )
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout)


def block(name: str) -> str:
    found = re.search(rf"// <{name}>\n(.*?)// </{name}>", SOURCE.read_text(encoding="utf-8"), re.S)
    assert found, f"{name} block markers missing in register.tsx"
    return found.group(1)


def run_blocks(expr: str, *names: str) -> object:
    """Evaluate a JS expression with the named marked blocks of register.tsx in scope."""
    code = "\n".join(block(n) for n in names) + f"\nconsole.log(JSON.stringify(({expr}) ?? null))\n"
    return _execute(code)


def run_module(tail: str) -> object:
    """Evaluate JS after everything in register.tsx before `export const register` (the pure part, drawing included).

    The one value import from the engine is replaced by a stub; the rest is type-only.
    """
    text = SOURCE.read_text(encoding="utf-8")
    head = text[: text.index("export const register")]
    head = re.sub(r"^import \{[^}]*\} from 'claude-code'\n", "const atom = (..._a: unknown[]): unknown => ({})\nconst read = 0\nconst update = 0\n", head, count=1, flags=re.M)
    return _execute(head + "\n" + tail + "\n")
