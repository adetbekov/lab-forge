"""Upgrade from v0.1/v0.2/v0.3 and the install it builds on: merges, conflicts, dry run, idempotence. Offline."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ENGINE = Path(__file__).resolve().parent.parent / "skills" / "lab-forge"
SCRIPTS = ENGINE / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
HAND = ["10. Use polars, not pandas, for new code.", "3. The churn label is 60 days without a purchase."]
CANARY = "LF-0a0b0c0d"


def script(name, *args, home, cwd=None, stdin=None):
    env = {"HOME": str(home), "PATH": os.environ["PATH"], "LAB_FORGE_HOME": str(home / ".lab-forge")}
    return subprocess.run([sys.executable, str(SCRIPTS / name), *args], cwd=cwd, env=env, input=stdin,
                          capture_output=True, text=True, check=False)


def upgrade(home, *args):
    return script("upgrade.py", *args, home=home)


def snapshot(root):
    """Every file under root with its bytes; symlinks by target. Equal snapshots = nothing written."""
    found = {}
    for dirpath, dirs, files in os.walk(root):
        for name in files + [d for d in dirs if os.path.islink(os.path.join(dirpath, d))]:
            path = Path(dirpath, name)
            found[str(path)] = os.readlink(path) if path.is_symlink() else path.read_bytes()
    return found


def hook(home, path, tool="Edit", **tool_input):
    event = {"tool_name": tool, "tool_input": {"file_path": str(path)} | tool_input, "cwd": str(path.parent)}
    return script("guard.py", "hook", home=home, stdin=json.dumps(event))


def legacy_v03(home, codex_extra=""):
    """What v0.3 (8417b6c) left on a machine: global rules, overrides, legacy blocks, the guard hook."""
    sys.path.insert(0, str(SCRIPTS))
    import migrations

    lf = home / ".lab-forge"
    (lf / "hooks").mkdir(parents=True)
    rules = migrations.global_rules(CANARY)[1]
    (lf / "AGENTS.md").write_text(rules)
    (lf / "overrides.md").write_text("# Overrides\n- Answer in Russian.\n")
    (lf / "state.md").write_text(f"# lab-forge global state\n\n- Canary: {CANARY}\n- Harnesses: claude, codex\n\n"
                                 "## Log\n")
    shutil.copy(SCRIPTS / "guard.py", lf / "hooks" / "guard.py")

    def block(body):
        import hashlib

        digest = hashlib.sha256(body.encode()).hexdigest()[:12]
        return f"<!-- lab-forge:begin sha={digest}: managed copy of {lf}; edit there or tune, then `sync` -->\n" \
               f"{body}<!-- lab-forge:end -->\n"

    claude = home / ".claude"
    claude.mkdir()
    (claude / "CLAUDE.md").write_text("my own line\n\n" + block(f"@{lf / 'AGENTS.md'}\n@{lf / 'overrides.md'}\n"))
    command = f'"{sys.executable}" "{lf / "hooks" / "guard.py"}" hook'
    settings = {"hooks": {"PreToolUse": [{"matcher": "Edit|Write", "hooks": [{"type": "command", "command": command}]}]}}
    (claude / "settings.json").write_text(json.dumps(settings))
    (home / ".codex").mkdir()
    copy = rules.rstrip() + "\n\n# Overrides\n- Answer in Russian.\n"  # v0.3 body(): rules, then overrides
    (home / ".codex" / "AGENTS.md").write_text(block(copy).replace("# Working rules (lab-forge, global)\n",
                                                                   "# Working rules (lab-forge, global)\n" + codex_extra))
    return lf


@pytest.mark.parametrize("version", ["0.1", "0.2"])
def test_upgrade_from_repo_only_versions_keeps_facts_and_hand_lines(tmp_path, version):
    home, repo = tmp_path / "home", tmp_path / "home" / "churn"
    (home / ".claude").mkdir(parents=True)
    shutil.copytree(FIXTURES / f"v{version}", repo)
    before = snapshot(home)

    res = upgrade(home, "--dry-run", "--repo", str(repo))
    assert res.returncode == 0, res.stderr
    assert f"global: none; repos: {repo}: {version}" in res.stdout and "+## Core" in res.stdout
    assert snapshot(home) == before  # the dry run writes nothing

    res = upgrade(home, "--apply", "--repo", str(repo))
    assert res.returncode == 0, res.stderr
    agents = (repo / "AGENTS.md").read_text()
    assert agents.startswith("# churn\n") and all(line in agents for line in HAND)
    assert "Customer ids never leave the VPC" in agents and "`params.toml`" in agents and "- Run: `pytest`" in agents
    assert "Size the task first" not in agents and "| task-intake |" not in agents
    assert agents.count("<!-- lab-forge:begin profile classic-ml ") == 1
    assert (repo / "CLAUDE.md").read_text() == "@AGENTS.md\n"
    assert "- Version: 0.4.1" in (repo / ".lab-forge" / "state.md").read_text()
    lf = home / ".lab-forge"
    assert "C5." in (lf / "core.md").read_text() and "C5." in (lf / "AGENTS.md").read_text()
    claude_md = (home / ".claude" / "CLAUDE.md").read_text()
    assert claude_md.startswith("<!-- lab-forge:begin core v=0.4.1 sha=") and f"@{lf / 'AGENTS.md'}" in claude_md
    backups = list((lf / "backup").glob("*/**/churn/AGENTS.md"))
    assert len(backups) == 1 and backups[0].read_bytes() == before[str(repo / "AGENTS.md")]
    verify = subprocess.run([sys.executable, str(SCRIPTS / "verify_setup.py"), str(repo)], capture_output=True,
                            text=True, check=False)
    assert verify.returncode == 0, verify.stdout

    after = snapshot(home)
    res = upgrade(home, "--dry-run", "--repo", str(repo))
    assert res.returncode == 0 and "up to date: no changes" in res.stdout and "+++" not in res.stdout
    assert snapshot(home) == after
    settings = json.loads((home / ".claude" / "settings.json").read_text())
    assert len(settings["hooks"]["PreToolUse"]) == 1 and claude_md.count("lab-forge:begin") == 1
    assert [p.name for p in (home / ".claude" / "skills").iterdir()] == ["lab-forge"]

    res = hook(home, home / ".claude" / "CLAUDE.md", old_string="@", new_string="@@")
    assert res.returncode == 2 and "lab-forge core block" in res.stderr
    res = hook(home, repo / "AGENTS.md", old_string="P1. Each fitted step", new_string="P1. Any step")
    assert res.returncode == 2 and "lab-forge profile block" in res.stderr
    assert hook(home, repo / "AGENTS.md", old_string="10. Use polars", new_string="10. Use pandas").returncode == 0


def test_upgrade_from_v03_replaces_legacy_blocks_once(tmp_path):
    lf = legacy_v03(tmp_path)
    res = upgrade(tmp_path, "--apply")
    assert res.returncode == 0, res.stdout + res.stderr
    assert "global: 0.3" in res.stdout
    claude_md = (tmp_path / ".claude" / "CLAUDE.md").read_text()
    assert claude_md.startswith("my own line\n\n<!-- lab-forge:begin core v=0.4.1 ") and claude_md.count("begin") == 1
    codex = (tmp_path / ".codex" / "AGENTS.md").read_text()
    assert f"pong {CANARY}" in codex and "C5." in codex and "- Answer in Russian." in codex
    assert "- Version: 0.4.1" in (lf / "state.md").read_text() and f"- Canary: {CANARY}" in (lf / "state.md").read_text()
    hooks = json.loads((tmp_path / ".claude" / "settings.json").read_text())["hooks"]["PreToolUse"]
    assert len(hooks) == 1
    assert script("install_global.py", "check", home=tmp_path).returncode == 0
    assert "up to date" in upgrade(tmp_path).stdout


def test_edit_inside_v03_block_merges(tmp_path):
    legacy_v03(tmp_path, codex_extra="Team rule: answer in Kazakh to Aigerim.\n")
    res = upgrade(tmp_path, "--apply")
    assert res.returncode == 0, res.stdout + res.stderr
    codex = (tmp_path / ".codex" / "AGENTS.md").read_text()
    assert "Team rule: answer in Kazakh to Aigerim." in codex and "C5." in codex and "<<<<<<<" not in codex
    assert codex.count("lab-forge:begin core v=0.4.1") == 1
    assert "DRIFT (edited by hand)" in script("install_global.py", "check", home=tmp_path).stdout
    assert "up to date" in upgrade(tmp_path).stdout  # the merged edit is not merged again


def test_conflicting_edit_writes_rej_and_keeps_the_file(tmp_path):
    lf = legacy_v03(tmp_path)
    agents = lf / "AGENTS.md"
    edited = agents.read_text().replace("not every edge case.", "plus one edge case per branch.")
    agents.write_text(edited)
    res = upgrade(tmp_path, "--dry-run")
    assert res.returncode == 1 and f"CONFLICT: {agents}" in res.stdout
    assert not (lf / "AGENTS.md.rej").exists()
    res = upgrade(tmp_path, "--apply")
    assert res.returncode == 1 and agents.read_text() == edited
    rej = (lf / "AGENTS.md.rej").read_text()
    assert "<<<<<<< yours" in rej and "plus one edge case per branch." in rej and "C6." in rej
    assert (lf / "core.md").exists()  # the rest of the upgrade went through


def test_install_merges_edits_and_tune_runs_from_the_copy(tmp_path):
    assert script("install_global.py", "install", "--harness", "claude", home=tmp_path).returncode == 0
    lf = tmp_path / ".lab-forge"
    agents = lf / "AGENTS.md"
    agents.write_text(agents.read_text() + "\nMy own rule: never use sklearn pipelines.\n")
    assert script("install_global.py", "install", home=tmp_path).returncode == 0
    assert "My own rule: never use sklearn pipelines." in agents.read_text()
    tune = subprocess.run([sys.executable, str(lf / "tune.py"), "add", "--scope", "global", "Answer in Russian."],
                          env={"HOME": str(tmp_path), "PATH": os.environ["PATH"], "LAB_FORGE_HOME": str(lf)},
                          cwd=tmp_path, capture_output=True, text=True, check=False)
    assert tune.returncode == 0, tune.stderr
    assert "- Answer in Russian." in (lf / "overrides.md").read_text()


def test_uninstall_removes_blocks_hooks_and_links_only(tmp_path):
    claude_md = tmp_path / ".claude" / "CLAUDE.md"
    claude_md.parent.mkdir()
    claude_md.write_text("my own line\n")
    script("install_global.py", "install", "--harness", "claude", home=tmp_path)
    assert script("install_global.py", "uninstall", home=tmp_path).returncode == 0
    assert claude_md.read_text() == "my own line\n"
    assert json.loads((tmp_path / ".claude" / "settings.json").read_text()) == {"hooks": {}}
    assert not (tmp_path / ".claude" / "skills" / "lab-forge").exists()
    assert (tmp_path / ".lab-forge" / "overrides.md").exists()
