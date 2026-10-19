"""Unit tests for the pure parts of the bench: python -m pytest bench"""

import json
import sys
import types
from pathlib import Path

from report import build, read_tsv

import bench
from bench import is_ai, is_russian, ws_name


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
    return base | kw | {"n_files": len(kw.get("files", base["files"]))}


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


def test_session_sees_only_allowed_secrets(monkeypatch, tmp_path):
    seen = {}

    def fake_sh(cmd, cwd=None, env=None, check=True, timeout=None):
        seen.update(env)
        return types.SimpleNamespace(stdout=json.dumps({"result": "ok", "usage": {}}), stderr="")

    monkeypatch.setattr(bench, "sh", fake_sh)
    for k in ("CLAUDE_CODE_OAUTH_TOKEN", "LIQUID_AI_API_KEY", "GITHUB_TOKEN", "S3_SECRET_ACCESS_KEY"):
        monkeypatch.setenv(k, "x")
    bench.claude("p", tmp_path, tmp_path, None)
    assert "CLAUDE_CODE_OAUTH_TOKEN" in seen and seen["HOME"] == str(tmp_path)
    assert not {"LIQUID_AI_API_KEY", "GITHUB_TOKEN", "S3_SECRET_ACCESS_KEY"} & set(seen)
    bench.claude("p", tmp_path, tmp_path, None, keys=["LIQUID_AI_API_KEY"])
    assert "LIQUID_AI_API_KEY" in seen and "GITHUB_TOKEN" not in seen


def test_claude_returns_the_four_usage_fields(monkeypatch, tmp_path):
    usage = {
        "input_tokens": 10,
        "output_tokens": 20,
        "cache_read_input_tokens": 1000,
        "cache_creation_input_tokens": 40,
    }
    out = json.dumps({"result": "ok", "usage": usage, "total_cost_usd": 0.5})
    monkeypatch.setattr(bench, "sh", lambda *a, **k: types.SimpleNamespace(stdout=out, stderr=""))
    _, tokens, _, _, cost, got = bench.claude("p", tmp_path, tmp_path, None)
    assert tokens == 1070 and cost == 0.5 and got == usage


def test_transcript_wins_when_the_cli_under_reports(monkeypatch, tmp_path):
    """A background task resumed the session: the CLI saw one call, the transcript has two (one streamed twice)."""
    call = {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 1000, "cache_creation_input_tokens": 0}
    lines = [
        {"type": "assistant", "message": {"id": "a", "usage": call}},
        {"type": "assistant", "message": {"id": "a", "usage": call}},
        {"type": "user", "message": {"content": "x"}},
        {"type": "assistant", "message": {"id": "b", "usage": call}},
    ]
    session = tmp_path / ".claude" / "projects" / "p" / "s1.jsonl"
    session.parent.mkdir(parents=True)
    session.write_text("".join(json.dumps(line) + "\n" for line in lines))
    out = json.dumps({"result": "ok", "usage": call, "total_cost_usd": 0.1, "num_turns": 1, "session_id": "s1"})
    monkeypatch.setattr(bench, "sh", lambda *a, **k: types.SimpleNamespace(stdout=out, stderr=""))
    _, tokens, turns, _, cost, got = bench.claude("p", tmp_path, tmp_path, None)
    assert tokens == 2000 and turns == 2 and cost == 0.1 and got["reported_tokens"] == 1000


def verdict(x, y, winner):
    code = dict.fromkeys(("success", "correctness", "practices", "optimality", "bloat", "scope"), 4)
    return {
        "X": {"P1": code | {"methodology": x, "tests": x}},
        "Y": {"P1": code | {"methodology": y, "tests": y}},
        "winner": {"P1": winner, "overall": winner},
    }


def test_weighted_score_and_order_flip_is_a_tie():
    reviews = {
        "c-r1": {"map": {"X": "lab", "Y": "bare"}, "scores": verdict(5, 1, "X")},
        "c-r1.swap": {"map": {"X": "bare", "Y": "lab"}, "scores": verdict(1, 5, "X")},
    }
    text, _ = build([], reviews, ["lab", "bare"])
    assert "| **code sum of 30** | 24 | 24 |" in text  # the old sum ignores the new criteria
    assert "| **weighted code score, 1-5** | 4.4 | 2.7 |" in text  # (2*5 + 2*5 + 5.5*4) / 9.5 vs (2 + 2 + 22) / 9.5
    assert "| c-r1 | tie, tie |" in text
    assert "X/Y order changed the winner in 2 of 2 calls" in text


def test_modes_never_share_a_table():
    rows = [row("lab", "P1", "code", solved=True, pytest=True, ruff_errors=0, mode="headless")]
    rows += [row("bare", "P1", "code", solved=True, pytest=True, ruff_errors=0, mode="agent")]
    text, _ = build(rows, {}, ["lab", "bare"])
    assert "## Objective metrics (agent)" in text and "## Objective metrics (headless)" in text
    assert "| Solved, hidden checks | 0/0 | 1/1 |" in text and "| Solved, hidden checks | 1/1 | 0/0 |" in text


def test_report_rebuilds_from_runs_tsv():
    rows = [
        row("lab", "P1", "code", solved=True, pytest=True, ruff_errors=0, bad_imports=0, cost_usd=0.25),
        row("bare", "P1", "code", solved=False, pytest=False, ruff_errors=2, bad_imports=1, bare_pytest=False),
        row("lab", "P3", "question", russian=True, files=[]),
    ]
    rows[0] |= {"mutants_killed": 1, "mutants_applied": 3, "bare_pytest": True}
    rows[1] |= {"mutants_killed": 0, "mutants_applied": 2}
    text, tsv = build(rows, {}, ["lab", "bare"])
    back = read_tsv(tsv)
    for r, kind in zip(back, ("code", "code", "question")):
        r["kind"] = kind
    again, tsv_again = build(back, {}, ["lab", "bare"])
    assert tsv_again == tsv
    assert again.replace("| Style stability across repeats (0-1) | — | — |", "") == text.replace(
        "| Style stability across repeats (0-1) | — | — |", ""
    )
    assert "| Mutants killed by the agent's tests | 1/3 | 0/2 |" in text
    assert "| Bare `pytest` green after step | 1/1 | 0/1 |" in text


def test_committed_v03_report_rebuilds_line_for_line(tmp_path):
    res = Path(bench.BENCH) / "results" / "2026-10-18-v0.3"
    args = types.SimpleNamespace(
        out=tmp_path, runs=res / "runs.tsv", verdicts=[res / "verdicts" / "v03-bare"], pair=["v03", "bare"]
    )
    new = iter(bench.rebuild(args).splitlines())
    old = (res / "v03-bare.md").read_text().splitlines()
    assert all(line in new for line in old)  # every committed line, in order; new rows may sit between them


def test_mutant_killed_survived_or_not_reached(tmp_path):
    (tmp_path / "area.py").write_text("import math\n\n\ndef side(a):\n    return math.sqrt(a)\n")
    mu = {
        "id": "m",
        "breaks": "sqrt is off by one",
        "run": "-c 'import area; area.side(4)'",
        "patch": "import math\n_s = math.sqrt\n\n\ndef sqrt(x):\n    hit()\n    return _s(x) + 1\n\n\nmath.sqrt = sqrt\n",
    }
    py, b = sys.executable, object.__new__(bench.Bench)
    biting = "from area import side\n\n\ndef test_side():\n    assert side(9) == 3\n"
    (tmp_path / "test_a.py").write_text(biting)
    assert b.mutant(py, tmp_path, mu, ["test_a.py"]) == "killed"
    (tmp_path / "test_a.py").write_text("from area import side\n\n\ndef test_side():\n    assert side(9) > 0\n")
    assert b.mutant(py, tmp_path, mu, ["test_a.py"]) == "survived"
    (tmp_path / "test_a.py").write_text("def test_nothing():\n    assert True\n")
    assert b.mutant(py, tmp_path, mu, ["test_a.py"]) == "survived"  # the entry point reaches it, the tests do not
    assert b.mutant(py, tmp_path, mu | {"run": "-c pass"}, ["test_a.py"]) == "n/a"


def test_verdict_skips_inline_json_fence_in_prose(tmp_path):
    path = tmp_path / "v.verdict.md"
    path.write_text('Fences like `` ```json{ `` fall through.\n\n```json\n{"winner": {"overall": "X"}}\n```\n')
    assert bench.verdict(path) == {"winner": {"overall": "X"}}
