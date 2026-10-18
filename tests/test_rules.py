"""Rule templates v0.4: the core budget, the verbatim profile block, the installed global file."""

import re
import subprocess
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent.parent / "skills" / "lab-forge"
VERIFY = ENGINE / "scripts" / "verify_setup.py"
PROFILE = re.compile(r"<!-- lab-forge:begin profile classic-ml .*?<!-- lab-forge:end -->\n", re.S)


def verify(*args):
    return subprocess.run([sys.executable, str(VERIFY), *args], capture_output=True, text=True, check=False)


def project(tmp_path, block):
    """A seeded repo: facts from rules.md, the profile block in place of {{profile_block}}."""
    (tmp_path / ".lab-forge").mkdir()
    (tmp_path / ".lab-forge" / "state.md").write_text(
        "# lab-forge state\n\n- Domain profile: classic-ml\n\n| Path | Kind |\n|---|---|\n| AGENTS.md | rules |\n"
    )
    (tmp_path / "AGENTS.md").write_text(
        f"# churn\n\n## Commands\n- Test: `pytest`\n\n## Invariants (breaking one is a bug)\n{block}"
        "1. Scores are probabilities in [0, 1].\n"
    )
    return tmp_path


def shipped_block():
    return PROFILE.search((ENGINE / "references" / "profiles" / "classic-ml.md").read_text())[0]


def test_engine_budgets_and_profile_shas_hold():
    res = verify("--engine")
    assert res.returncode == 0, res.stdout
    assert len((ENGINE / "assets" / "templates" / "core.md").read_text().splitlines()) <= 30


def test_verbatim_profile_block_passes(tmp_path):
    res = verify(str(project(tmp_path, shipped_block())))
    assert res.returncode == 0, res.stdout


def test_paraphrased_profile_block_fails(tmp_path):
    block = shipped_block().replace("its own split or CV inside the training rows", "nothing chosen on test")
    res = verify(str(project(tmp_path, block)))
    assert res.returncode == 1 and "edited by hand" in res.stdout


def test_missing_profile_block_fails(tmp_path):
    res = verify(str(project(tmp_path, "")))
    assert res.returncode == 1 and "no rules file has its block" in res.stdout


def test_install_renders_core_and_defaults(tmp_path):
    env = {"HOME": str(tmp_path), "PATH": "/usr/bin:/bin", "LAB_FORGE_HOME": str(tmp_path / ".lab-forge")}
    res = subprocess.run(
        [sys.executable, str(ENGINE / "scripts" / "install_global.py"), "install", "--harness", "claude"],
        env=env, capture_output=True, text=True, check=False,
    )
    assert res.returncode == 0, res.stderr
    text = (tmp_path / ".lab-forge" / "AGENTS.md").read_text()
    assert "C5." in text and "D9." in text and "{{" not in text
    assert f"python {(tmp_path / '.lab-forge').as_posix()}/tune.py add" in text
