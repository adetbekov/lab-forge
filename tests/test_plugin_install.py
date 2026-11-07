"""The engine installed as a Claude Code plugin: no second copy in ~/.claude/skills, real copies elsewhere."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent.parent / "skills" / "lab-forge"


def test_install_from_plugin_cache_skips_claude_skill_link_and_copies_for_codex(tmp_path):
    cache = tmp_path / ".claude" / "plugins" / "cache" / "lab-forge" / "lab-forge" / "0.0.0"
    shutil.copytree(ENGINE, cache)
    env = {"HOME": str(tmp_path), "PATH": os.environ["PATH"], "LAB_FORGE_HOME": str(tmp_path / ".lab-forge")}
    res = subprocess.run([sys.executable, str(cache / "scripts" / "install_global.py"), "install", "--harness",
                          "claude,codex"], env=env, capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    assert not (tmp_path / ".claude" / "skills" / "lab-forge").exists()  # the plugin already loads it
    codex = tmp_path / ".agents" / "skills" / "lab-forge"
    assert codex.is_dir() and not codex.is_symlink() and (codex / "SKILL.md").exists()
    assert (tmp_path / ".claude" / "CLAUDE.md").exists() and (tmp_path / ".lab-forge" / "AGENTS.md").exists()
