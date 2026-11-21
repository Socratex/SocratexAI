"""Select for test-necessity: Python tests without any assertion and tests whose body duplicates an earlier test."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))

import selectlib  # noqa: E402

ASSERT_CALLS = {"raises", "warns", "fail", "approx", "skip", "xfail"}


def is_test_file(rel: str) -> bool:
    path = Path(rel)
    return path.suffix == ".py" and (path.name.startswith("test_") or path.stem.endswith("_test")
                                     or "tests" in path.parts or "test" in path.parts)


def has_assertion(func: ast.AST) -> bool:
    for node in ast.walk(func):
        if isinstance(node, ast.Assert):
            return True
        if isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
            if name.startswith("assert") or name in ASSERT_CALLS:
                return True
    return False


def body_signature(func: ast.FunctionDef) -> str:
    body = func.body[1:] if (func.body and isinstance(func.body[0], ast.Expr)
                             and isinstance(func.body[0].value, ast.Constant)) else func.body
    return "|".join(ast.dump(stmt) for stmt in body) + "#" + ast.dump(func.args)


def analyse(rel: str, lines: list[str]) -> list[dict]:
    try:
        tree = ast.parse("\n".join(lines) + "\n")
    except SyntaxError:
        return []
    tests = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
             and n.name.startswith("test")]
    tests.sort(key=lambda n: n.lineno)
    rows, seen = [], {}
    for func in tests:
        if not has_assertion(func):
            rows.append(selectlib.candidate(rel, func.lineno, func.end_lineno, "test-without-assertion",
                                            f"Test {func.name} has no assertion."))
        signature = body_signature(func)
        if signature in seen:
            rows.append(selectlib.candidate(rel, func.lineno, func.end_lineno, "duplicate-test",
                                            f"Test {func.name} repeats the body of {seen[signature]}."))
        else:
            seen[signature] = func.name
    return rows


def main() -> None:
    request = selectlib.load_request()
    rows: list[dict] = []
    for rel in selectlib.files_of(request):
        if not is_test_file(rel):
            continue
        found = analyse(rel, selectlib.read_lines(request, rel))
        rows += [r for r in found if selectlib.overlaps(request["chunks"], rel, r["line_start"], r["line_end"])]
    selectlib.emit(rows)


if __name__ == "__main__":
    main()
