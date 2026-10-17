"""Unit tests for the pure parts of the bench: python -m pytest bench"""

from bench import is_ai, is_russian, ws_name
from report import build


def test_ws_name_is_opaque_and_stable():
    a, b = ws_name(1, "churn", "lab", 1), ws_name(1, "churn", "bare", 1)
    assert a == ws_name(1, "churn", "lab", 1)
    assert a != b and "lab" not in a and "bare" not in b


def test_ai_files_are_excluded_from_code_metrics():
    assert is_ai("CLAUDE.md") and is_ai("src/CLAUDE.md") and is_ai(".claude/skills/x/SKILL.md")
    assert not is_ai("churn/train.py") and not is_ai("README.md")


def test_russian_survives_dense_code_refs():
    assert is_russian("Сплит делается в `src/churn/train.py:51-69`, параметры в `configs/params.toml:8`.")
    assert not is_russian("The split lives in `src/churn/train.py:51-69`.")


def row(arm, step, kind, **kw):
    base = {
        "ws": f"c-{arm}",
        "case": "c",
        "arm": arm,
        "rep": 1,
        "step": step,
        "kind": kind,
        "tokens": 50_000,
        "tools": 1,
        "ms": 60_000,
        "cost_usd": None,
        "files": ["a.py"],
        "loc_py": 100,
        "loc_all": 100,
        "ai_loc": 0,
        "tests_added": 2,
        "max_new_file": 50,
        "out_of_scope": 0,
        "committed": True,
        "on_main": True,
        "questions": 0,
        "reply_words": 10,
    }
    return base | kw


def test_report_flags_reproduced_conclusions():
    rows = [
        row("lab", "P0", "deploy", files=[], loc_py=0, loc_all=0),
        row("lab", "P1", "code", solved=False, pytest=True, ruff_errors=0, loc_py=60),
        row("bare", "P1", "code", solved=True, pytest=True, ruff_errors=0),
        row("lab", "P3", "question", russian=True, files=[]),
        row("bare", "P3", "question", russian=False, files=[]),
    ]
    text, tsv = build(rows, {}, ["lab", "bare"])
    assert "| Less code with lab-forge (≤ −15%) | −30% | -40% | yes |" in text
    assert "| Solved, hidden checks | 0/1 | 1/1 |" in text
    assert "| Tune phrase applied in next session | 1/1 | 0/1 |" in text
    assert len(tsv.splitlines()) == len(rows) + 1
