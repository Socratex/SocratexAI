"""Detect full-line comments that are commented-out code or merely repeat the next code line (shared by select and fix)."""

from __future__ import annotations

import ast
import io
import re
import tokenize
from dataclasses import dataclass

HASH_SUFFIXES = {".py"}
SLASH_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".java", ".c", ".cc", ".cpp", ".h", ".hpp", ".cs", ".go", ".rs", ".kt",
                  ".swift", ".php"}
QUIRK = re.compile(r"\b(TODO|FIXME|NOTE|HACK|XXX|WARNING|BUG)\b|noqa|type:|pragma|nosec|pylint|fmt:|isort|-\*-|eslint|"
                   r"prettier|ts-ignore|@ts-", re.IGNORECASE)
STOPWORDS = {"the", "a", "an", "to", "of", "and", "or", "is", "are", "this", "that", "it", "for", "in", "on", "with",
             "by", "we", "be", "if", "then"}
BLOCK_OPENER = re.compile(r"^(if|elif|else|for|while|def|class|try|except|finally|with)\b.*:$")
CODE_SHAPE = re.compile(r"[()=<>\[\].]")
SLASH_CODE = re.compile(r"^(?:.*[;{}]|(?:if|for|while)\s*\(.*\)\s*\{?)$")
SIMPLE_NODES = (ast.Assign, ast.AugAssign, ast.Import, ast.ImportFrom, ast.Delete, ast.Raise, ast.Assert)


@dataclass(frozen=True)
class Issue:
    line: int
    category: str
    message: str


def comment_marker(suffix: str) -> str | None:
    if suffix in HASH_SUFFIXES:
        return "#"
    if suffix in SLASH_SUFFIXES:
        return "//"
    return None


def full_line_comments(suffix: str, lines: list[str]) -> list[tuple[int, str]]:
    """(1-based line, comment text without marker) for every comment that stands alone on its line."""
    marker = comment_marker(suffix)
    if marker is None:
        return []
    if suffix == ".py":
        try:
            tokens = list(tokenize.generate_tokens(io.StringIO("\n".join(lines) + "\n").readline))
        except (tokenize.TokenError, IndentationError, SyntaxError):
            return []
        return [(t.start[0], t.string[1:].strip()) for t in tokens
                if t.type == tokenize.COMMENT and t.line.strip().startswith("#")]
    return [(number, line.strip()[2:].strip()) for number, line in enumerate(lines, 1) if line.strip().startswith("//")]


def is_dead_code(suffix: str, body: str) -> bool:
    body = body.strip()
    if not body or QUIRK.search(body) or body.startswith("!"):
        return False
    if suffix != ".py":
        return bool(SLASH_CODE.match(body)) and bool(CODE_SHAPE.search(body))
    if BLOCK_OPENER.match(body):
        if body in {"else:", "try:", "finally:"}:
            return True
        try:
            ast.parse(body + "\n    pass")
        except SyntaxError:
            return False
        return bool(CODE_SHAPE.search(body))
    try:
        tree = ast.parse(body)
    except SyntaxError:
        return False
    if len(tree.body) != 1:
        return False
    node = tree.body[0]
    if isinstance(node, SIMPLE_NODES):
        return True
    if isinstance(node, ast.Expr):
        return isinstance(node.value, ast.Call)
    if isinstance(node, ast.Return):
        return node.value is not None and not isinstance(node.value, (ast.Name, ast.Constant))
    return False


def stem(word: str) -> str:
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def words(text: str) -> set[str]:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    return {stem(w) for w in re.split(r"[^A-Za-z0-9]+", spaced.lower()) if w and w not in STOPWORDS}


def repeats_code(comment: str, code_line: str) -> bool:
    if QUIRK.search(comment):
        return False
    wanted = words(comment)
    return len(wanted) >= 2 and wanted <= words(code_line)


def find_issues(suffix: str, lines: list[str]) -> list[Issue]:
    """Mechanical comment problems of one file: dead code in comments and comments repeating the next line."""
    issues: list[Issue] = []
    for number, body in full_line_comments(suffix, lines):
        marker = comment_marker(suffix)
        if number == 1 and body.startswith("!"):
            continue
        if is_dead_code(suffix, body):
            issues.append(Issue(number, "dead-code", "Commented-out code."))
            continue
        following = lines[number] if number < len(lines) else ""
        if following.strip() and not following.strip().startswith(marker or "#") and repeats_code(body, following):
            issues.append(Issue(number, "comment-repeats-code", "Comment only repeats the next line of code."))
    return issues
