"""env_safe.py shows only provably non-secret env values and masks the rest."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "modules" / "tools" / "scripts"))

import env_safe  # noqa: E402

FIXTURE = """\
# Database settings
APP_ENV=local
APP_DEBUG=true
APP_KEY=base64:abcdEFGH1234abcdEFGH1234abcdEFGH1234abcd=
DB_HOST=mysql
DB_PORT=3306
DB_PASSWORD=hunter2
DB_DSN=mysql://root:pw@db/app
REDIS_HOST=redis.prod.example.com
MAIL_PASSWORD=
API_TOKEN=changeme
JWT=eyJhbGciOiJIUzI1NiJ9.abc.def
SERVICE_URL=http://localhost:8080/api
CALLBACK_URL=https://user:pass@example.com/cb
WEBHOOK_URL=https://hooks.example.com/services/T0000AAAA/B1111BBBB/Xx9Yy8Zz7Ww6Vv5Uu4
STORAGE_PATH=/var/www/storage
UNKNOWN_THING=some-value
export QUOTED="plain words" # trailing comment
MULTI="line one
secret line two"
AFTER_MULTI=1
# OLD_SECRET=abc123
# note: token AbCdEfGhIjKlMnOp1234567890
DB_URL=${DB_HOST}
"""


def run(tmp_path, text=FIXTURE):
    path = tmp_path / ".env.example"
    path.write_text(text, encoding="utf-8")
    return path


def as_dict(lines):
    return dict(line.split("=", 1) for line in lines if "=" in line and not line.startswith("#"))


def test_safe_values_shown(tmp_path):
    out = as_dict(env_safe.describe_single(run(tmp_path), False))
    assert out["APP_ENV"] == "local"
    assert out["APP_DEBUG"] == "true"
    assert out["DB_HOST"] == "mysql"
    assert out["DB_PORT"] == "3306"
    assert out["MAIL_PASSWORD"] == ""
    assert out["API_TOKEN"] == "changeme"
    assert out["SERVICE_URL"] == "http://localhost:8080/api"
    assert out["STORAGE_PATH"] == "/var/www/storage"
    assert out["DB_URL"] == "${DB_HOST}"
    assert out["AFTER_MULTI"] == "1"


def test_unsafe_values_masked(tmp_path):
    text = "\n".join(env_safe.describe_single(run(tmp_path), False))
    out = as_dict(text.splitlines())
    for key in ("APP_KEY", "DB_PASSWORD", "DB_DSN", "REDIS_HOST", "JWT", "CALLBACK_URL", "WEBHOOK_URL", "UNKNOWN_THING", "export QUOTED"):
        assert out[key] == env_safe.MASKED, key
    for leaked in ("hunter2", "abcdEFGH", "eyJ", "user:pass", "Xx9Yy8", "some-value", "secret line two", "trailing", "AbCdEfGh", "abc123"):
        assert leaked not in text, leaked


def test_comments_kept_and_commented_assignment_masked(tmp_path):
    lines = env_safe.describe_single(run(tmp_path), False)
    assert "# Database settings" in lines
    assert "# OLD_SECRET=<masked>" in lines


def test_keys_only(tmp_path):
    keys = env_safe.describe_single(run(tmp_path), True)
    assert keys[0] == "APP_ENV"
    assert "QUOTED" in keys and "MULTI" in keys and "secret line two" not in keys
    assert not any("=" in k or k.startswith("#") for k in keys)


def test_compare(tmp_path):
    first = tmp_path / "a.env"
    second = tmp_path / "b.env"
    first.write_text("APP_ENV=local\nDB_PASSWORD=one\nSAME_SECRET=x1\nONLY_A=1\nDB_PORT=3306\n", encoding="utf-8")
    second.write_text("APP_ENV=prod\nDB_PASSWORD=two\nSAME_SECRET=x1\nONLY_B=1\nDB_PORT=3306\n", encoding="utf-8")
    out = env_safe.describe_compare(first, second, False)
    assert "APP_ENV=local -> prod" in out
    assert "DB_PASSWORD=<different>" in out
    assert "SAME_SECRET=<masked>" in out
    assert "ONLY_A=1 <only in first>" in out
    assert "ONLY_B=1 <only in second>" in out
    assert "DB_PORT=3306" in out
    assert not any("one" in line or "two" in line for line in out if line.startswith("DB_PASSWORD"))


def test_missing_file_exit_code(tmp_path, capsys):
    assert env_safe.main([str(tmp_path / "nope")]) == 2
