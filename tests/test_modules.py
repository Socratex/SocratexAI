"""Tests for module manifests (modules/**/module.json), their schema and the index generated from them."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_index  # noqa: E402


def manifest(name: str = "demo", **over: object) -> dict:
    data = {"schema": "socratex-module/v1", "name": name, "kind": "tools", "what": "w", "when": "w",
            "entry": [], "paths": [f"{name}.py"], "tests": []}
    data.update(over)
    return data


@pytest.fixture()
def fake(tmp_path):
    """A fake repo root with the real schema; `add` writes a manifest and the files it names."""
    (tmp_path / "core").mkdir()
    shutil.copy(ROOT / "core" / "module.schema.json", tmp_path / "core" / "module.schema.json")

    def add(data: dict, folder: str | None = None) -> Path:
        for item in data.get("paths", []) + data.get("tests", []):
            (tmp_path / item).parent.mkdir(parents=True, exist_ok=True)
            (tmp_path / item).touch()
        file = tmp_path / "modules" / (folder or data["name"]) / "module.json"
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps(data), encoding="utf-8")
        return file

    add.root = tmp_path
    return add


def test_real_manifests_are_valid():
    manifests, errors = build_index.validate_manifests(ROOT)
    assert errors == []
    assert {m["name"] for m in manifests} >= {"review", "planning", "engine", "routing", "memory", "scripts", "gpt"}


def test_every_real_path_and_test_exists():
    for m in build_index.load_modules(ROOT):
        for item in m["paths"] + m["tests"]:
            assert (ROOT / item).exists(), f"{m['name']}: {item}"


def test_no_real_path_is_claimed_twice():
    claims = [(item, m["name"]) for m in build_index.load_modules(ROOT) for item in m["paths"]]
    for i, (a, owner_a) in enumerate(claims):
        for b, owner_b in claims[i + 1:]:
            assert not build_index._overlaps(a, b), f"{a} ({owner_a}) overlaps {b} ({owner_b})"


def test_real_requires_point_to_existing_modules():
    modules = build_index.load_modules(ROOT)
    names = {m["name"] for m in modules}
    for m in modules:
        assert set(m.get("requires", [])) <= names


def test_index_has_modules_and_keeps_entries():
    index = json.loads((ROOT / "INDEX.json").read_text(encoding="utf-8"))
    assert [m["name"] for m in index["modules"]]
    assert {"name", "kind", "what", "when", "entry", "paths"} == set(index["modules"][0])
    paths = {e["path"] for section in ("docs", "data", "tools") for e in index[section]}
    assert {"tools/review/run.py", "core/ROUTING.json", "tools/build_index.py"} <= paths


def test_index_is_current_and_generation_is_idempotent():
    first = json.dumps(build_index.build(), indent=2, ensure_ascii=False) + "\n"
    second = json.dumps(build_index.build(), indent=2, ensure_ascii=False) + "\n"
    assert first == second
    assert (ROOT / "INDEX.json").read_text(encoding="utf-8") == first, "run: sox index"
    assert build_index.run_index(check=True) == 0


def test_unknown_field_fails_with_file_and_key(fake):
    file = fake(manifest(extra="x"))
    _, errors = build_index.validate_manifests(fake.root)
    assert any(file.relative_to(fake.root).as_posix() in e and "extra" in e for e in errors)


def test_missing_required_key_fails(fake):
    data = manifest()
    del data["when"]
    fake(data)
    _, errors = build_index.validate_manifests(fake.root)
    assert any("module.json" in e and "'when'" in e for e in errors)


def test_missing_path_fails_with_file_and_key(fake):
    file = fake(manifest())
    (fake.root / "demo.py").unlink()
    _, errors = build_index.validate_manifests(fake.root)
    assert any(file.relative_to(fake.root).as_posix() in e and "paths" in e and "demo.py" in e for e in errors)


def test_missing_test_path_fails(fake):
    file = fake(manifest(tests=["t/test_x.py"]))
    (fake.root / "t" / "test_x.py").unlink()
    _, errors = build_index.validate_manifests(fake.root)
    assert any("tests" in e and "t/test_x.py" in e for e in errors)


def test_path_claimed_by_two_modules_fails(fake):
    fake(manifest("two", paths=["shared/file.py"]))
    fake(manifest("one", paths=["shared"]))
    _, errors = build_index.validate_manifests(fake.root)
    assert any("overlaps" in e for e in errors)


def test_unknown_requires_fails(fake):
    fake(manifest(requires=["ghost"]))
    _, errors = build_index.validate_manifests(fake.root)
    assert any("requires" in e and "ghost" in e for e in errors)


def test_name_must_match_folder(fake):
    fake(manifest("demo"), folder="other")
    _, errors = build_index.validate_manifests(fake.root)
    assert any("folder name" in e for e in errors)


def test_load_modules_raises_on_broken_manifest(fake):
    fake(manifest(kind="nonsense"))
    with pytest.raises(build_index.ManifestError):
        build_index.load_modules(fake.root)
