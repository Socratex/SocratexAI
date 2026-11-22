#!/usr/bin/env python3
# REDIRECT to modules/tools/scripts/check_leaks.py; kept for external callers (see `sox shims`).
import json, runpy, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
try:  # usage counter; any failure is ignored so the command never breaks
    (ROOT / "state").mkdir(exist_ok=True)
    with open(ROOT / "state" / "shim-usage.jsonl", "a", encoding="utf-8") as log:
        log.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "shim": "check_leaks", "argv0": sys.argv[0]}) + "\n")
except Exception:
    pass
NEW = ROOT / "modules/tools/scripts/check_leaks.py"
sys.path.insert(0, str(NEW.parent))
sys.argv[0] = str(NEW)
runpy.run_path(str(NEW), run_name="__main__")
