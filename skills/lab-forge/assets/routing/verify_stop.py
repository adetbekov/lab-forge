"""Stop hook for Claude Code and Codex: no "done" while the tests of the changed code fail.

Reads the hook JSON on stdin. Runs only when the repo changed since the last green run.
Command: `- Test: <cmd>` in .lab-forge/state.md, else pytest on the changed test files.
Red tests block the stop once (stop_hook_active ends the loop); the agent sees the tail.
"""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


def git(root, *args):
    out = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
    return out.stdout if out.returncode == 0 else ""


def test_command(root, changed):
    state = root / ".lab-forge" / "state.md"
    if state.exists():
        found = re.search(r"^- Test: `?([^`\n]+)`?$", state.read_text(encoding="utf-8"), flags=re.MULTILINE)
        if found:
            return found[1].strip()
    tests = [f for f in changed if re.search(r"(^|/)test_[^/]*\.py$", f) and (root / f).exists()]
    if not tests:
        return None
    venv = root / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    return " ".join([str(venv) if venv.exists() else "python", "-m", "pytest", "-q", "-x", *tests])


def main():
    event = json.loads(sys.stdin.read() or "{}")
    root = Path(git(event.get("cwd") or ".", "rev-parse", "--show-toplevel").strip() or ".")
    status = git(root, "status", "--porcelain", "--untracked-files=all")
    head = git(root, "rev-parse", "HEAD").strip()
    stamp = Path(git(root, "rev-parse", "--git-dir").strip() or ".git")
    stamp = (stamp if stamp.is_absolute() else root / stamp) / "lab-forge-verified"
    key = hashlib.sha256(f"{head}\n{status}".encode()).hexdigest()
    seen, last = (stamp.read_text().split() + ["HEAD~1"])[:2] if stamp.exists() else ("", "HEAD~1")
    if event.get("stop_hook_active") or not head or seen == key:
        return
    changed = set(git(root, "diff", "--name-only", last).split()) | {line[3:] for line in status.splitlines()}
    cmd = test_command(root, sorted(changed))
    if cmd:
        try:
            res = subprocess.run(cmd, shell=True, cwd=root, capture_output=True, text=True, check=False, timeout=600)
        except subprocess.TimeoutExpired:
            return
        if res.returncode:
            tail = "\n".join((res.stdout + res.stderr).strip().splitlines()[-8:])
            print(json.dumps({"decision": "block", "reason": f"Tests fail, not done yet: `{cmd}`\n{tail}"}))
            return
    stamp.write_text(f"{key} {head}")


if __name__ == "__main__":
    main()
