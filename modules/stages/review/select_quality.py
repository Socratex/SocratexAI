"""Select for readability, architecture and contracts: cheap diff-grep and AST heuristics that pick candidates for a model."""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "engine"))

import selectlib  # noqa: E402

MAX_FUNCTION_LINES = 40
MAX_NESTING = 4
NESTING_NODES = (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.AsyncFor, ast.AsyncWith)
IMPORT_LINE = re.compile(r"^\s*(import\s|from\s+\S+\s+import\s|#include\s|using\s+\S+;|(const|let|var)\s+.*=\s*require\()")
EMPTY_CATCH = re.compile(r"\bcatch\s*(\([^)]*\))?\s*\{\s*\}")


def parse(lines: list[str]) -> ast.AST | None:
    try:
        return ast.parse("\n".join(lines) + "\n")
    except SyntaxError:
        return None


def nesting_depth(node: ast.AST, depth: int = 0) -> int:
    deepest = depth
    for child in ast.iter_child_nodes(node):
        deeper = depth + 1 if isinstance(child, NESTING_NODES) else depth
        deepest = max(deepest, nesting_depth(child, deeper))
    return deepest


def readability(rel: str, lines: list[str]) -> list[dict]:
    tree = parse(lines) if rel.endswith(".py") else None
    rows = []
    for node in ast.walk(tree) if tree else []:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        length = node.end_lineno - node.lineno + 1
        if length > MAX_FUNCTION_LINES:
            rows.append(selectlib.candidate(rel, node.lineno, node.end_lineno, "long-function",
                                            f"Function {node.name} is {length} lines long."))
        if nesting_depth(node) > MAX_NESTING:
            rows.append(selectlib.candidate(rel, node.lineno, node.end_lineno, "deep-nesting",
                                            f"Function {node.name} nests control flow deeper than {MAX_NESTING} levels."))
    return rows


def swallows(handler: ast.ExceptHandler) -> bool:
    return all(isinstance(s, (ast.Pass, ast.Continue)) or (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))
               for s in handler.body)


def contracts(rel: str, lines: list[str]) -> list[dict]:
    rows = []
    tree = parse(lines) if rel.endswith(".py") else None
    for node in ast.walk(tree) if tree else []:
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                rows.append(selectlib.candidate(rel, node.lineno, node.end_lineno, "bare-except",
                                                "Bare except hides every error type."))
            elif swallows(node):
                rows.append(selectlib.candidate(rel, node.lineno, node.end_lineno, "swallowed-error",
                                                "Exception is caught and silently dropped."))
    if not rel.endswith(".py"):
        rows += [selectlib.candidate(rel, n, n, "swallowed-error", "Empty catch block drops the error.")
                 for n, line in enumerate(lines, 1) if EMPTY_CATCH.search(line)]
    return rows


def architecture(rel: str, lines: list[str]) -> list[dict]:
    rows: list[dict] = []
    for number, line in enumerate(lines, 1):
        if not IMPORT_LINE.match(line):
            continue
        if rows and rows[-1]["line_end"] == number - 1:
            rows[-1]["line_end"] = number
        else:
            rows.append(selectlib.candidate(rel, number, number, "module-boundary",
                                            "New dependency: does it respect module boundaries?"))
    return rows


MODES = {"readability": readability, "contracts": contracts, "architecture": architecture}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=sorted(MODES), required=True)
    mode = MODES[parser.parse_args().mode]
    request = selectlib.load_request()
    rows: list[dict] = []
    for rel in selectlib.files_of(request):
        found = mode(rel, selectlib.read_lines(request, rel))
        rows += [r for r in found if selectlib.overlaps(request["chunks"], rel, r["line_start"], r["line_end"])]
    selectlib.emit(rows)


if __name__ == "__main__":
    main()
