"""Global layer, adapters and guard, offline: python -m pytest tests"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "lab-forge" / "scripts"


def sh(*cmd, cwd=None, env=None, stdin=None):
    return subprocess.run(cmd, cwd=cwd, env=env, input=stdin, capture_output=True, text=True, check=False)


def script(name, *args, home, cwd=None, stdin=None):
    env = {"HOME": str(home), "PATH": "/usr/bin:/bin:/usr/local/bin", "LAB_FORGE_HOME": str(home / ".lab-forge")}
    return sh(sys.executable, str(SCRIPTS / name), *args, cwd=cwd, env=env, stdin=stdin)


def repo(path, branch="main"):
    path.mkdir()
    sh("git", "init", "-q", "-b", branch, cwd=path)
    (path / "a.py").write_text("import json\n")
    sh("git", "add", "-A", cwd=path)
    sh("git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init", cwd=path)
    return path


def test_install_writes_one_source_and_blocks(tmp_path):
    claude_md = tmp_path / ".claude" / "CLAUDE.md"
    claude_md.parent.mkdir()
    claude_md.write_text("my own line\n")
    assert script("install_global.py", "install", home=tmp_path).returncode == 0
    lf = tmp_path / ".lab-forge"
    canary = next(line for line in (lf / "state.md").read_text().splitlines() if "Canary" in line).split()[-1]
    assert f"pong {canary}" in (lf / "AGENTS.md").read_text()
    assert len((lf / "AGENTS.md").read_text().splitlines()) <= 60
    text = claude_md.read_text()
    assert text.startswith("my own line") and f"@{lf / 'AGENTS.md'}" in text
    assert canary in (tmp_path / ".codex" / "AGENTS.md").read_text()
    assert canary in (tmp_path / ".gemini" / "GEMINI.md").read_text()
    hooks = json.loads((tmp_path / ".claude" / "settings.json").read_text())["hooks"]["PreToolUse"]
    assert len(hooks) == 1 and "guard.py" in hooks[0]["hooks"][0]["command"]
    assert (tmp_path / ".claude" / "skills" / "lab-forge" / "SKILL.md").exists()
    # idempotent: same canary, one block, one hook
    script("install_global.py", "install", home=tmp_path)
    assert claude_md.read_text().count("lab-forge:begin") == 1
    assert canary in (lf / "AGENTS.md").read_text()
    assert len(json.loads((tmp_path / ".claude" / "settings.json").read_text())["hooks"]["PreToolUse"]) == 1


def test_tune_reaches_copies_and_check_finds_drift(tmp_path):
    script("install_global.py", "install", "--harness", "claude", home=tmp_path)
    script("install_global.py", "install", "--harness", "codex", home=tmp_path)
    assert "- Harnesses: claude, codex" in (tmp_path / ".lab-forge" / "state.md").read_text()
    proj = repo(tmp_path / "proj")
    assert script("install_global.py", "repo", str(proj), home=tmp_path).returncode == 0
    assert script("install_global.py", "check", home=tmp_path).returncode == 0
    script("tune.py", "add", "--scope", "global", "Answer in Russian.", home=tmp_path, cwd=proj)
    assert "- Answer in Russian." in (tmp_path / ".codex" / "AGENTS.md").read_text()
    assert "- Answer in Russian." in (proj / "AGENTS.md").read_text()
    codex = tmp_path / ".codex" / "AGENTS.md"
    codex.write_text(codex.read_text().replace("Russian", "French"))
    res = script("install_global.py", "check", home=tmp_path)
    assert res.returncode == 1 and "DRIFT" in res.stdout


def test_repo_tune_on_main_goes_to_global(tmp_path):
    script("install_global.py", "install", "--harness", "claude", home=tmp_path)
    proj = repo(tmp_path / "proj")
    (proj / ".lab-forge").mkdir()
    (proj / ".lab-forge" / "state.md").write_text("- Level: 1\n")
    script("tune.py", "add", "--scope", "repo", "Answer in Russian.", "--repo", str(proj), home=tmp_path)
    assert not (proj / "AGENTS.md").exists()
    assert "- [proj] Answer in Russian." in (tmp_path / ".lab-forge" / "overrides.md").read_text()


def test_hook_blocks_edits_and_commits_on_main_only(tmp_path):
    main = repo(tmp_path / "m")
    feat = repo(tmp_path / "f", branch="feat/x")

    def hook(tool, cwd, **tool_input):
        event = json.dumps({"tool_name": tool, "tool_input": tool_input, "cwd": str(cwd)})
        return script("guard.py", "hook", home=tmp_path, stdin=event).returncode

    assert hook("Edit", tmp_path, file_path=str(main / "a.py")) == 2
    assert hook("Write", main, file_path="new/dir/b.py") == 2
    assert hook("Bash", main, command="git add -A && git commit -m x") == 2
    assert hook("Bash", main, command="git switch -c feat/y") == 0
    assert hook("Read", main, file_path=str(main / "a.py")) == 0
    assert hook("Edit", main, file_path=str(feat / "a.py")) == 0
    assert hook("Write", main, file_path=str(tmp_path / "outside.txt")) == 0
    sh("git", "config", "lab-forge.allowMain", "true", cwd=main)
    assert hook("Edit", main, file_path=str(main / "a.py")) == 0


def test_scope_and_imports(tmp_path):
    proj = repo(tmp_path / "p", branch="feat/x")
    (proj / ".lab-forge").mkdir()
    (proj / ".lab-forge" / "scope").write_text("src/*.py\n")
    (proj / "src").mkdir()
    (proj / "src" / "ok.py").write_text("import json\nimport no_such_pkg_xyz\n")
    (proj / "README.md").write_text("drive-by\n")
    res = script("guard.py", "scope", str(proj), home=tmp_path)
    assert res.returncode == 1 and "README.md" in res.stdout and "ok.py" not in res.stdout
    res = script("guard.py", "imports", str(proj), "src/ok.py", home=tmp_path)
    assert res.returncode == 1 and "does not resolve: no_such_pkg_xyz" in res.stdout
