"""Select scripts and the comment fix script: what they flag and what they leave alone."""

from __future__ import annotations

import json

import pytest

import common
from conftest import REGISTRY_PATH

REGISTRY = {c["id"]: c for c in common.load_registry(REGISTRY_PATH, None)["checkers"]}
FIX_CHECKERS = [c for c in REGISTRY.values() if c.get("fix_script")]
FIX_SAMPLES = {"comments": ("s.py", "# x = foo(1)\n# return the result\ndef f(result):\n    # open the file\n"
                                    "    # return result\n    return result\n")}


def select(repo, checker_id, rel, text):
    repo.write(rel, text)
    count = len(text.splitlines())
    chunks = [{"file": rel, "line_start": 1, "line_end": count, "split": False}]
    return common.run_select(REGISTRY[checker_id], chunks, repo.path)


def test_comments_flags_dead_code_and_repeats_but_not_prose(repo):
    text = ("# old = sum(items)\n# return the result\n# Note: this is about rounding\n"
            "# return value\nresult = 1\nprint(result)\n")
    items = select(repo, "comments", "a.py", text)
    flagged = {(i["line_start"], i["category"]) for i in items if i.get("mechanical")}
    assert (1, "dead-code") in flagged
    assert 3 not in {line for line, _ in flagged} and 4 not in {line for line, _ in flagged}


def test_comments_repeat_needs_the_next_code_line(repo):
    items = select(repo, "comments", "a.py", "def f(result):\n    # return the result\n    return result\n")
    assert [(i["line_start"], i["category"]) for i in items if i.get("mechanical")] == [(2, "comment-repeats-code")]


def test_comments_offers_remaining_comment_to_the_model(repo):
    items = select(repo, "comments", "a.py", "x = 1\n# keeps totals in sync with the ledger\ny = 2\n")
    assert [i for i in items if not i.get("mechanical")]


def test_test_necessity_finds_assertionless_and_duplicate_tests(repo):
    text = ("def test_a():\n    x = 1\n\n\n"
            "def test_b():\n    assert 1 == 1\n\n\n"
            "def test_c():\n    assert 1 == 1\n")
    items = select(repo, "test-necessity", "tests/test_x.py", text)
    assert {(i["line_start"], i["category"]) for i in items} == {(1, "test-without-assertion"), (9, "duplicate-test")}


def test_test_necessity_ignores_non_test_files(repo):
    assert select(repo, "test-necessity", "lib.py", "def test_a():\n    pass\n") == []


def test_contracts_flags_swallowed_errors(repo):
    text = "try:\n    run()\nexcept:\n    pass\ntry:\n    run()\nexcept ValueError as err:\n    raise\n"
    items = select(repo, "contracts", "c.py", text)
    assert [i["category"] for i in items] == ["bare-except"]


def test_readability_flags_long_function(repo):
    body = "".join(f"    x{i} = {i}\n" for i in range(50))
    items = select(repo, "readability", "r.py", "def big():\n" + body)
    assert [i["category"] for i in items] == ["long-function"]


def test_architecture_offers_new_imports(repo):
    items = select(repo, "architecture", "m.py", "import os\nfrom a import b\n\nx = 1\n")
    assert [(i["line_start"], i["line_end"]) for i in items] == [(1, 2)]


def test_leaks_reports_without_echoing_the_value(repo):
    secret = "sk-ant-" + "A" * 24
    items = select(repo, "leaks", "k.txt", f"token = {secret}\nok = 1\n")
    assert len(items) == 1 and items[0]["line_start"] == 1
    assert secret not in json.dumps(items)


def test_select_with_unparsable_python_gives_no_candidates(repo):
    assert select(repo, "contracts", "bad.py", "def (:\n") == []


def test_registry_has_fix_scripts_to_test():
    assert FIX_CHECKERS


@pytest.mark.parametrize("checker", FIX_CHECKERS, ids=lambda c: c["id"])
def test_every_fix_script_is_idempotent(repo, checker):
    assert checker["id"] in FIX_SAMPLES, "add a sample for the new fix_script"
    rel, text = FIX_SAMPLES[checker["id"]]
    path = repo.write(rel, text)
    common.run_fix_script(checker["fix_script"], path, repo.path, checker["here"])
    first = path.read_bytes()
    assert first != text.encode("utf-8")
    common.run_fix_script(checker["fix_script"], path, repo.path, checker["here"])
    assert path.read_bytes() == first
