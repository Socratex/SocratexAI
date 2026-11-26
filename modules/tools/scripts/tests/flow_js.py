"""Shared helper of the flow-panel tests: runs the real pure modules of the mod (model, rules, format, palette, draw) with Node 22+."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[4]
HOOKS = ROOT / "claude/mods/flow-panel/hooks"
PURE = ["model", "rules", "format", "palette", "draw"]  # no engine imports: Node can load them as they are
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


def _stage(tmp: Path) -> None:
    """Copy the pure modules next to the test script. The mod imports siblings without an extension (what the engine
    resolves); Node needs the extension, so it is added in the copy only."""
    for name in PURE:
        text = (HOOKS / f"{name}.ts").read_text(encoding="utf-8")
        (tmp / f"{name}.ts").write_text(re.sub(r"from '(\./[a-z]+)'", r"from '\1.ts'", text), encoding="utf-8")


def _execute(code: str) -> object:
    node = node_path()
    if node is None:
        raise unittest.SkipTest("Node 22+ not available")
    with tempfile.TemporaryDirectory() as tmp:
        _stage(Path(tmp))
        script = Path(tmp) / "t.mts"
        imports = "\n".join(f"import * as m{i} from './{name}.ts'" for i, name in enumerate(PURE))
        scope = "Object.assign(globalThis, " + ", ".join(f"m{i}" for i in range(len(PURE))) + ")"
        script.write_text(f"{imports}\n{scope}\n{code}\n", encoding="utf-8")
        res = subprocess.run(
            [node, "--experimental-strip-types", "--no-warnings", str(script)], capture_output=True, text=True, encoding="utf-8"
        )
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout)


def run_blocks(expr: str, *_names: str) -> object:
    """Evaluate a JS expression with every exported name of the pure modules in scope (the names are kept for old callers)."""
    return _execute(f"console.log(JSON.stringify(({expr}) ?? null))")


def run_module(tail: str) -> object:
    """Evaluate JS statements with every exported name of the pure modules in scope (the drawing included)."""
    return _execute(tail)
