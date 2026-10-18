"""Global layer, adapters and guard, offline: python -m pytest tests"""

import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
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


def fake_d1(answers, delay=0):
    """Local /v1/systemone stand-in: replies with `answers`, keeps every request body."""
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            seen.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            threading.Event().wait(delay)
            out = json.dumps({"answers": answers}).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_port}/v1/systemone", seen


def decide(home, mode, event, backend="local", url=None):
    (home / ".lab-forge").mkdir(exist_ok=True)
    (home / ".lab-forge" / "decide.json").write_text(json.dumps({"backend": backend, "url": url}))
    res = script("guard.py", "decide", mode, home=home, stdin=json.dumps(event))
    assert res.returncode == 0
    return json.loads(res.stdout) if res.stdout.strip() else None


def test_decide_stop_blocks_unverified_done_once(tmp_path):
    log = tmp_path / "t.jsonl"
    lines = [
        {"message": {"role": "user", "content": "old task"}},
        {"message": {"role": "user", "content": "Add a retry to fetch() and test it."}},
        {"message": {"role": "user", "content": [{"type": "tool_result", "content": "ok"}]}},
        {"message": {"role": "assistant", "content": [{"type": "text", "text": "Done!"}]}},
    ]
    log.write_text("\n".join(map(json.dumps, lines)))
    event = {"hook_event_name": "Stop", "transcript_path": str(log), "stop_hook_active": False}
    url, seen = fake_d1({"done": {"noul": 0.02}, "missing": {"choice": "verification", "confidence": 0.9}})
    out = decide(tmp_path, "stop", event, url=url)
    assert out["decision"] == "block" and out["reason"].startswith("not verified: ")
    assert seen[0]["model"] == "d1-omni:600m" and seen[0]["questions"]["done"]["type"] == "noul"
    assert "Add a retry" in seen[0]["state"] and "old task" not in seen[0]["state"]
    assert decide(tmp_path, "stop", event | {"stop_hook_active": True}, url=url) is None
    url, _ = fake_d1({"done": {"noul": 0.87}, "missing": {"choice": "verification"}})
    assert decide(tmp_path, "stop", event, url=url) is None


def test_decide_fails_open(tmp_path):
    event = {"transcript_path": "", "last_assistant_message": "Done", "prompt": "x"}
    url, seen = fake_d1({"done": {"noul": 0.0}}, delay=3)
    assert decide(tmp_path, "stop", event | {"transcript_path": str(tmp_path)}, url=url) is None
    assert decide(tmp_path, "stop", event, url="http://127.0.0.1:9/v1/systemone") is None
    assert decide(tmp_path, "stop", event, backend="hosted") is None  # no LIQUID_AI_API_KEY
    assert decide(tmp_path, "stop", event, backend="off", url=url) is None and not seen


def test_decide_skill_hints_only_when_confident(tmp_path):
    for name in ("grill", "triage"):
        (tmp_path / ".claude" / "skills" / name).mkdir(parents=True)
        (tmp_path / ".claude" / "skills" / name / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: d {name}\n---\n"
        )
    event = {"hook_event_name": "UserPromptSubmit", "prompt": "Ask me questions first", "cwd": str(tmp_path)}
    url, seen = fake_d1({"skill": {"choice": "grill", "confidence": 0.93}})
    out = decide(tmp_path, "skill", event, url=url)
    assert out["hookSpecificOutput"]["additionalContext"] == "lab-forge: load skill grill"
    assert set(seen[0]["questions"]["skill"]["criteria"]) == {"grill", "triage", "none"}
    url, _ = fake_d1({"skill": {"choice": "grill", "confidence": 0.6}})
    assert decide(tmp_path, "skill", event, url=url) is None
    url, _ = fake_d1({"skill": {"choice": "none", "confidence": 0.99}})
    assert decide(tmp_path, "skill", event, url=url) is None


def test_decide_skill_offers_every_skill_of_a_crowded_setup(tmp_path):
    names = [f"skill-{i:02d}" for i in range(40)]  # was cut to the first 25 by name
    for name in names:
        (tmp_path / ".claude" / "skills" / name).mkdir(parents=True)
        (tmp_path / ".claude" / "skills" / name / "SKILL.md").write_text(f"---\nname: {name}\ndescription: d\n---\n")
    event = {"hook_event_name": "UserPromptSubmit", "prompt": "Backtest the forecast", "cwd": str(tmp_path)}
    url, seen = fake_d1({"skill": {"choice": "skill-39", "confidence": 0.9}})
    assert decide(tmp_path, "skill", event, url=url)["hookSpecificOutput"]["additionalContext"].endswith("skill-39")
    assert set(seen[0]["questions"]["skill"]["criteria"]) == {*names, "none"}


def test_install_decide_adds_hooks_next_to_others(tmp_path):
    settings = tmp_path / ".claude" / "settings.json"
    settings.parent.mkdir()
    verifier = {"hooks": [{"type": "command", "command": "verify.sh"}]}
    settings.write_text(json.dumps({"hooks": {"Stop": [verifier]}}))
    script("install_global.py", "install", "--harness", "claude", home=tmp_path)
    assert json.loads(settings.read_text())["hooks"]["Stop"] == [verifier]
    res = script("install_global.py", "install", "--harness", "claude,codex", "--decide", "hosted", home=tmp_path)
    assert "sent to api.liquid.ai" in res.stdout
    hooks = json.loads(settings.read_text())["hooks"]
    assert hooks["Stop"][0] == verifier and hooks["Stop"][1]["hooks"][0]["command"].endswith("decide stop")
    assert hooks["UserPromptSubmit"][0]["hooks"][0]["command"].endswith("decide skill")
    assert "decide stop" in (tmp_path / ".codex" / "hooks.json").read_text()
    script("install_global.py", "install", "--decide", "hosted", home=tmp_path)
    assert len(json.loads(settings.read_text())["hooks"]["Stop"]) == 2
    script("install_global.py", "install", "--decide", "off", home=tmp_path)
    hooks = json.loads(settings.read_text())["hooks"]
    assert hooks["Stop"] == [verifier] and "UserPromptSubmit" not in hooks
