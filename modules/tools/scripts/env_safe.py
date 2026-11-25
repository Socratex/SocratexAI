#!/usr/bin/env python3
"""Read env files safely for AI agents: show keys and provably non-secret values, mask everything else.

Usage:
    env_safe.py FILE                 # KEY=value when provably safe, KEY=<masked> otherwise; comments kept
    env_safe.py FILE --keys-only     # only the variable names
    env_safe.py FILE --compare OTHER # differing unsafe values print as <different>, safe ones as `a -> b`

Default for any unknown value is masked. Inline comments after a value are dropped.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

MASKED = "<masked>"
DIFFERENT = "<different>"

SECRET_SUBSTRINGS = ("PASSWORD", "PASSWD", "SECRET", "TOKEN", "CREDENTIAL", "PRIVATE", "DSN", "APIKEY", "AUTH", "SALT")
SECRET_WORDS = {"KEY", "KEYS", "PWD", "PASS", "SIG", "SIGNATURE", "COOKIE", "CERT"}

KNOWN_SAFE_KEYS = {
    "APP_ENV", "APP_DEBUG", "APP_NAME", "APP_LOCALE", "APP_FALLBACK_LOCALE", "LOG_LEVEL", "LOG_CHANNEL", "NODE_ENV",
    "TZ", "TIMEZONE", "COMPOSE_PROJECT_NAME", "DB_CONNECTION", "CACHE_DRIVER", "CACHE_STORE", "QUEUE_CONNECTION",
    "SESSION_DRIVER", "MAIL_MAILER", "MAIL_ENCRYPTION", "FILESYSTEM_DISK", "BROADCAST_DRIVER", "ENVIRONMENT", "STAGE",
}
SAFE_WORD = re.compile(r"[A-Za-z][A-Za-z0-9_.\- ]{0,63}")

BOOLEANS = {"true", "false", "yes", "no", "on", "off", "null", "none", "0", "1"}
PLACEHOLDER = re.compile(
    r"(?i)^(changeme|change[_-]me|replace[_-]?me|your[_\-a-z0-9]*here|your[_-][a-z0-9_-]+|x{3,}|\*{3,}|todo|tbd|"
    r"placeholder|example|dummy|fake|<[^<>]*>|\[[^\[\]]*\]|insert[_-].*|set[_-]me)$"
)
VARIABLE_REFERENCE = re.compile(r"^\$\{?[A-Za-z_][A-Za-z0-9_]*\}?$")
LOCAL_HOST = re.compile(r"^(localhost|127\.0\.0\.1|::1|0\.0\.0\.0|host\.docker\.internal|[a-z][a-z0-9_-]*)$")
PATH_LIKE = re.compile(r"^(~|\.{1,2})?/[A-Za-z0-9_./\-]*$|^\.{1,2}/[A-Za-z0-9_./\-]*$")
URL = re.compile(r"^([a-z][a-z0-9+.\-]*)://([^/?#@\s]+)((?:/[^?#\s]*)?)$", re.IGNORECASE)
TOKEN_RUN = re.compile(r"[A-Za-z0-9+/=_\-]{16,}")
ASSIGNMENT = re.compile(r"^(?P<lead>\s*(?:#\s*)?(?:export\s+)?)(?P<key>[A-Za-z_][A-Za-z0-9_.]*)\s*=(?P<rest>.*)$")


@dataclass
class Entry:
    key: str
    value: str  # unquoted real value
    lead: str  # whitespace, comment marker, export keyword


def is_secret_key(key: str) -> bool:
    upper = key.upper()
    if any(part in upper for part in SECRET_SUBSTRINGS):
        return True
    return any(word in SECRET_WORDS for word in re.split(r"[_.\-]", upper))


def looks_random(text: str) -> bool:
    if text.startswith("eyJ"):
        return True
    for run in TOKEN_RUN.findall(text):
        has_digit = any(c.isdigit() for c in run)
        has_alpha = any(c.isalpha() for c in run)
        if len(run) >= 32 or (len(run) >= 20 and has_digit and has_alpha):
            return True
        if len(run) >= 16 and has_digit and has_alpha and any(c.isupper() for c in run) and any(c.islower() for c in run):
            return True
    return False


def is_small_integer(value: str) -> bool:
    return value.isdigit() and len(value) <= 5 and int(value) <= 65535


def is_safe_url(value: str) -> bool:
    match = URL.match(value)
    if not match:
        return False
    authority, path = match.group(2), match.group(3)
    if "@" in authority or looks_random(authority):
        return False
    return not any(looks_random(segment) for segment in path.split("/"))


def is_local_host(value: str) -> bool:
    return bool(LOCAL_HOST.match(value)) and not looks_random(value)


def is_host_key(key: str) -> bool:
    return bool(re.search(r"(?:^|_)(HOST|HOSTNAME)$", key.upper()))


def is_safe(key: str, value: str) -> bool:
    if value == "" or value.lower() in BOOLEANS or PLACEHOLDER.match(value) or VARIABLE_REFERENCE.match(value):
        return True
    if is_secret_key(key):
        return False
    if is_small_integer(value):
        return True
    if is_host_key(key):
        return is_local_host(value)
    if key.upper() in KNOWN_SAFE_KEYS:
        return bool(SAFE_WORD.fullmatch(value)) and not looks_random(value)
    if PATH_LIKE.match(value):
        return not looks_random(value)
    return is_safe_url(value)


def split_value(rest: str) -> tuple[str, bool]:
    """Return the unquoted value and whether a quoted value continues on the next line."""
    rest = rest.strip()
    if rest[:1] in ("'", '"'):
        quote = rest[0]
        end = rest.find(quote, 1)
        while end != -1 and rest[end - 1] == "\\" and quote == '"':
            end = rest.find(quote, end + 1)
        if end == -1:
            return rest[1:], True
        return rest[1:end], False
    return re.split(r"\s+#", rest, maxsplit=1)[0].strip(), False


def mask_comment(line: str) -> str:
    return TOKEN_RUN.sub(lambda m: MASKED if looks_random(m.group(0)) else m.group(0), line)


def parse(text: str):
    """Yield ('raw', line) for blank/comment lines, ('entry', Entry) for assignments; commented-out assignments count as entries."""
    pending_quote = False
    for line in text.splitlines():
        if pending_quote:
            pending_quote = not any(c in line for c in "'\"")
            continue
        match = ASSIGNMENT.match(line)
        if not match:
            yield ("raw", mask_comment(line) if line.lstrip().startswith("#") else line)
            continue
        value, pending_quote = split_value(match.group("rest"))
        yield ("entry", Entry(match.group("key"), value, match.group("lead")))
    return


def render_entry(entry: Entry) -> str:
    shown = entry.value if is_safe(entry.key, entry.value) else MASKED
    return f"{entry.lead}{entry.key}={shown}"


def read_entries(path: Path) -> dict[str, Entry]:
    entries: dict[str, Entry] = {}
    for kind, item in parse(path.read_text(encoding="utf-8", errors="replace")):
        if kind == "entry" and not item.lead.lstrip().startswith("#"):
            entries[item.key] = item
    return entries


def describe_single(path: Path, keys_only: bool) -> list[str]:
    lines = []
    for kind, item in parse(path.read_text(encoding="utf-8", errors="replace")):
        if kind == "raw":
            if not keys_only:
                lines.append(item)
        elif keys_only:
            if not item.lead.lstrip().startswith("#"):
                lines.append(item.key)
        else:
            lines.append(render_entry(item))
    return lines


def shown_value(entry: Entry) -> str:
    return entry.value if is_safe(entry.key, entry.value) else MASKED


def describe_compare(left: Path, right: Path, keys_only: bool) -> list[str]:
    a, b = read_entries(left), read_entries(right)
    lines = []
    for key in list(a) + [k for k in b if k not in a]:
        if key not in b:
            status = "<only in first>"
        elif key not in a:
            status = "<only in second>"
        elif a[key].value == b[key].value:
            status = None
        else:
            both_safe = is_safe(key, a[key].value) and is_safe(key, b[key].value)
            status = f"{a[key].value} -> {b[key].value}" if both_safe else DIFFERENT
        if keys_only:
            lines.append(key if status is None else f"{key} {status}")
        elif status is None:
            lines.append(f"{key}={shown_value(a[key])}")
        elif status.startswith("<only"):
            source = a if key in a else b
            lines.append(f"{key}={shown_value(source[key])} {status}")
        else:
            lines.append(f"{key}={status}")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read env files safely: safe values shown, the rest masked.")
    parser.add_argument("file")
    parser.add_argument("--keys-only", action="store_true", help="print only variable names")
    parser.add_argument("--compare", metavar="OTHER", help="compare with a second env file")
    args = parser.parse_args(argv)

    paths = [Path(args.file)] + ([Path(args.compare)] if args.compare else [])
    for path in paths:
        if not path.is_file():
            sys.stderr.write(f"env_safe: not a file: {path}\n")
            return 2
    lines = describe_compare(paths[0], paths[1], args.keys_only) if args.compare else describe_single(paths[0], args.keys_only)
    sys.stdout.write("\n".join(lines) + ("\n" if lines else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
