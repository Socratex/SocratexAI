"""Select for the comments checker: mechanical dead-code and repeating comments, plus comments left for the model."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "engine"))

import comment_rules  # noqa: E402
import selectlib  # noqa: E402


def main() -> None:
    request = selectlib.load_request()
    rows: list[dict] = []
    for rel in selectlib.files_of(request):
        suffix = Path(rel).suffix.lower()
        lines = selectlib.read_lines(request, rel)
        issues = comment_rules.find_issues(suffix, lines)
        flagged = {issue.line for issue in issues}
        rows += [selectlib.candidate(rel, i.line, i.line, i.category, i.message, mechanical=True, severity="nit")
                 for i in issues if selectlib.is_changed(request["chunks"], rel, i.line)]
        remaining = [n for n, body in comment_rules.full_line_comments(suffix, lines)
                     if n not in flagged and not (n == 1 and body.startswith("!"))
                     and selectlib.overlaps(request["chunks"], rel, n, n)]
        if remaining:
            rows.append(selectlib.candidate(rel, remaining[0], min(len(lines), remaining[-1] + 2), "comment-review",
                                            "Comments to judge: justified, accurate, not repeating the code."))
    selectlib.emit(rows)


if __name__ == "__main__":
    main()
