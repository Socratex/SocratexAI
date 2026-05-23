from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path


VALID_LINE_ENDINGS = {"Preserve", "LF", "CRLF"}


def convert_to_configured_line_ending(text: str, line_ending: str = "LF") -> str:
    if line_ending not in VALID_LINE_ENDINGS:
        raise ValueError(f"Invalid line ending: {line_ending}")
    if line_ending == "Preserve":
        return text

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if line_ending == "CRLF":
        return normalized.replace("\n", "\r\n")
    return normalized


def convert_to_utf8_file_text(value: object, no_newline: bool = False, line_ending: str = "LF") -> str:
    if isinstance(value, str):
        text = value
    elif isinstance(value, Iterable):
        text = "\n".join(str(entry) for entry in value)
    else:
        text = str(value)

    text = convert_to_configured_line_ending(text, line_ending)
    if not no_newline and not text.endswith("\n"):
        text += "\r\n" if line_ending == "CRLF" else "\n"
    return text


def read_utf8_file(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_utf8_file(
    path: str | Path,
    value: object,
    no_newline: bool = False,
    line_ending: str = "LF",
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = convert_to_utf8_file_text(value, no_newline=no_newline, line_ending=line_ending)
    target.write_text(text, encoding="utf-8", newline="")
