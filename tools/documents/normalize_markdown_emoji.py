from __future__ import annotations

import argparse
import re
from pathlib import Path

from document_wrapper_helpers import repo_root, split_values
from shared.repo_helpers import git_lines


def project_markdown_paths(root: Path) -> list[str]:
    excluded = ("Tools/Python312/", "Tools/python-installer/", "Tools/tmp/")
    return [line for line in git_lines(root, ["ls-files", "*.md"]) if not any(part in line for part in excluded)]


def starts_with_symbol(text: str) -> bool:
    stripped = text.lstrip()
    return not stripped or ord(stripped[0]) > 127


def add_emoji_to_heading(line: str, emoji: str) -> str:
    match = re.match(r"^(#{1,6}\s+)(.*)$", line)
    if not match or starts_with_symbol(match.group(2)):
        return line
    return f"{match.group(1)}{emoji} {match.group(2)}"


def add_emoji_to_list_line(line: str, emoji: str) -> str:
    match = re.match(r"^(\s*(?:[-*+]|\d+[.)])\s+\[[ xX]\]\s+)(.*)$", line)
    if match:
        return line if starts_with_symbol(match.group(2)) else f"{match.group(1)}{emoji} {match.group(2)}"
    match = re.match(r"^(\s*(?:[-*+]|\d+[.)])\s+)(.*)$", line)
    if not match or starts_with_symbol(match.group(2)):
        return line
    return f"{match.group(1)}{emoji} {match.group(2)}"


def is_paragraph_start(lines: list[str], index: int) -> bool:
    line = lines[index]
    if not line.strip() or re.match(r"^\s*(#{1,6}\s+|[-*+]\s+|\d+[.)]\s+|>\s*|\|)", line):
        return False
    if re.match(r"^\s*(```|~~~|---+\s*$|\*\*\*+\s*$|___+\s*$|<!--)", line):
        return False
    if starts_with_symbol(line):
        return False
    for previous in range(index - 1, -1, -1):
        prior = lines[previous]
        if not prior.strip():
            return True
        if re.match(r"^\s*(#{1,6}\s+|[-*+]\s+|\d+[.)]\s+|>\s*|\|)", prior):
            return True
        if re.match(r"^\s*(```|~~~|---+\s*$|\*\*\*+\s*$|___+\s*$|<!--)", prior):
            return True
        return False
    return True


def convert_markdown_emoji(content: str, emoji: str) -> str:
    lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    toc_index = -1
    for index, line in enumerate(lines[:80]):
        if re.match(r"^##\s+(TOC|Table of Contents|Contents|Index)\s*$", line):
            toc_index = index
            break
        if re.match(r"^##\s+", line):
            break

    in_fence = False
    for index, line in enumerate(lines):
        if re.match(r"^\s*(```|~~~)", line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if re.match(r"^#{1,6}\s+", line):
            lines[index] = add_emoji_to_heading(line, emoji)
        elif is_paragraph_start(lines, index):
            match = re.match(r"^(\s*)(.*)$", line)
            lines[index] = f"{match.group(1)}{emoji} {match.group(2)}" if match else line

    if toc_index >= 0:
        in_fence = False
        for index in range(toc_index + 1, len(lines)):
            line = lines[index]
            if re.match(r"^\s*(```|~~~)", line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            if re.match(r"^##\s+", line):
                break
            if re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", line):
                lines[index] = add_emoji_to_list_line(line, emoji)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize Markdown headings, paragraph starts, and TOC lines with emoji.")
    parser.add_argument("positional_paths", nargs="*")
    parser.add_argument("--paths", "-Paths", nargs="*", default=[])
    parser.add_argument("--default-emoji", "-DefaultEmoji", default="🧭")
    parser.add_argument("--check", "-Check", action="store_true")
    parser.add_argument("--repo-root", default="")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve() if args.repo_root else repo_root()
    targets = split_values(args.paths + args.positional_paths)
    if not targets:
        targets = project_markdown_paths(root)

    changed: list[str] = []
    for target in targets:
        path = (root / target).resolve()
        content = path.read_text(encoding="utf-8-sig")
        updated = convert_markdown_emoji(content, args.default_emoji)
        if updated != content:
            changed.append(target)
            if not args.check:
                path.write_text(updated, encoding="utf-8", newline="")

    if not changed:
        print("OK: markdown TOC and paragraph emoji already normalized")
        return 0
    if args.check:
        print("ERROR: markdown files need TOC or paragraph emoji normalization:")
        for path in changed:
            print(f" - {path}")
        return 1
    print("OK: normalized markdown TOC and paragraph emoji:")
    for path in changed:
        print(f" - {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
