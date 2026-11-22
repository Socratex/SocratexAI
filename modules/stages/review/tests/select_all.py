"""Test select script: offers every given chunk as a judge candidate."""

import json
import sys

request = json.load(sys.stdin)
print(json.dumps([{"file": c["file"], "line_start": c["line_start"], "line_end": c["line_end"],
                   "category": "all", "message": "candidate"} for c in request["chunks"]]))
