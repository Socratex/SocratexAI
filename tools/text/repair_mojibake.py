from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


MARKERS = {
    "\u00c2",
    "\u00c4",
    "\u00c5",
    "\u00e2",
    "\u0103",
    "\u010f",
    "\u0110",
    "\u0111",
    "\u0139",
    "\u015f",
    "\u0161",
    "\ufffd",
}
NON_ASCII_PATTERN = re.compile(r"[^\x00-\x7F]+")


def suspicion_score(text: str) -> int:
    score = sum(text.count(marker) for marker in MARKERS)
    score += sum(1 for char in text if 0x0080 <= ord(char) <= 0x009F)
    return score


def convert_mojibake_token(token: str) -> str:
    original_score = suspicion_score(token)
    if original_score == 0:
        return token

    best_text = token
    best_score = original_score
    for encoding in ("cp1250", "cp1252"):
        try:
            candidate = token.encode(encoding).decode("utf-8")
        except UnicodeError:
            continue
        candidate_score = suspicion_score(candidate)
        if candidate_score < best_score and "\ufffd" not in candidate:
            best_text = candidate
            best_score = candidate_score
    return best_text


def repair_text(text: str) -> str:
    return NON_ASCII_PATTERN.sub(lambda match: convert_mojibake_token(match.group(0)), text)


def relative_to_root(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def default_targets(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "*.md", "*.json", "*.json", "*.ps1"],
        check=True,
        text=True,
        capture_output=True,
    )
    return [(root / line).resolve() for line in result.stdout.splitlines() if line.strip()]


def expand_paths(paths: list[str]) -> list[str]:
    expanded: list[str] = []
    for path in paths:
        for entry in path.split(","):
            trimmed = entry.strip()
            if trimmed:
                expanded.append(trimmed)
    return expanded


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair common mojibake corruption in selected text files.")
    parser.add_argument("paths", nargs="*", default=[])
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    target_paths = default_targets(root) if not args.paths else [(root / path).resolve() for path in expand_paths(args.paths)]
    changed_files: list[str] = []

    for path in target_paths:
        if not path.is_file():
            if args.paths:
                raise FileNotFoundError(f"Missing target file: {path}")
            continue

        content = path.read_text(encoding="utf-8")
        repaired = repair_text(content)
        if repaired == content:
            continue

        changed_files.append(relative_to_root(path, root))
        if not args.check:
            path.write_text(repaired, encoding="utf-8", newline="")

    for path in changed_files:
        print(f"MOJIBAKE: {path}")

    if changed_files and args.check:
        print(f"ERROR: mojibake repair check failed with {len(changed_files)} file(s) needing repair.")
        return 1
    if changed_files:
        print(f"OK: repaired mojibake in {len(changed_files)} file(s).")
    else:
        print("OK: no mojibake repairs needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
