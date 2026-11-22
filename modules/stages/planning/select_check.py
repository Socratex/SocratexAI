"""Select for the check stage: hands the model only the slice (owner answers, plan, research notes), nothing else.

Deterministic, no model. One candidate per chunk of slice.md; every other file of the run is ignored, so the checker
never sees the conversation or the original files.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Import with the shared engine folder and this folder first, then take them off again so importing this
# module in-process never shadows same-named modules of the review pipeline.
_added = [str(q) for q in (HERE, HERE.parents[1] / "engine") if str(q) not in sys.path]
sys.path[:0] = _added
try:
    import selectlib  # noqa: E402
    import stage_files  # noqa: E402
finally:
    for _path in _added:
        sys.path.remove(_path)

HINT = ("Compare the plan with the owner answers: report mismatches with the intent, missing coverage of an answer and "
        "any research note that contradicts an answer.")


def main() -> None:
    request = selectlib.load_request()
    rows = [selectlib.candidate(c["file"], c["line_start"], c["line_end"], "intent-check", HINT)
            for c in request["chunks"] if c["file"] == stage_files.SLICE]
    selectlib.emit(rows)


if __name__ == "__main__":
    main()
