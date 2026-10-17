"""Smoke test: did each harness really load the rules, and does the branch guard hold? Stdlib only.

Runs every installed harness CLI headless in a throwaway repo, after `install_global.py install`:
- rules: `lab-forge ping` must return the global canary (~/.lab-forge) and the repo canary (AGENTS.md);
- guard: "commit a file" must not land a commit on main.
IDE-only harnesses have no headless CLI: the script prints the manual check instead.

Usage:
    python smoke.py [--harness claude,codex,copilot,cursor,antigravity] [--no-guard] [--timeout 300]
Exit code 1 if any harness that ran failed.
"""

import argparse
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from install_global import BLOCK, block, state, targets

PING = "lab-forge ping"
TASK = "Create a file hello.txt with the text hi and commit it with git."
CLI = {
    "claude": ["claude", "-p", "{prompt}", "--permission-mode", "bypassPermissions"],
    "codex": ["codex", "exec", "--dangerously-bypass-approvals-and-sandbox", "{prompt}"],
    "copilot": ["copilot", "-p", "{prompt}", "--allow-all-tools"],
    "cursor": ["cursor-agent", "-p", "{prompt}", "--force"],
    "antigravity": ["gemini", "-p", "{prompt}", "--skip-trust"],  # Gemini CLI reads the same ~/.gemini/GEMINI.md
}
MANUAL = "open a new agent chat in {repo}, send `lab-forge ping`, expect: pong {canary} {repo_canary}"


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False).stdout.strip()


def make_repo(root, repo_canary, harness):
    repo = root / harness
    repo.mkdir(parents=True)
    git(repo, "init", "-q", "-b", "main")
    (repo / "AGENTS.md").write_text(f"# Smoke repo\n\nlab-forge-canary: {repo_canary}\n", encoding="utf-8")
    (repo / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")
    if harness in ("cursor", "copilot"):  # no global file in the IDE: repo copy is the fallback
        with (repo / "AGENTS.md").open("a", encoding="utf-8") as f:
            f.write("\n" + block("repo"))
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=smoke", "-c", "user.email=smoke@example.com", "commit", "-qm", "init")
    return repo


def run(harness, prompt, repo, timeout):
    cmd = [prompt if a == "{prompt}" else a for a in CLI[harness]]
    try:
        res = subprocess.run(
            cmd,
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env={k: v for k, v in os.environ.items() if not k.startswith("CLAUDE_CODE_")},
        )
    except subprocess.TimeoutExpired:
        return None, "timeout"
    return res.returncode == 0, (res.stdout.strip() or res.stderr.strip())


def smoke(harness, root, canary, guard, timeout):
    repo_canary = f"R-{secrets.token_hex(3)}"
    repo = make_repo(root, repo_canary, harness)
    if not shutil.which(CLI[harness][0]):
        return "skip", "-", MANUAL.format(repo=repo, canary=canary, repo_canary=repo_canary)
    ok, out = run(harness, PING, repo, timeout)
    last = out.splitlines()[-1][:120] if out else ""
    if not ok:
        return "error", "-", last
    rules = "pass" if canary in out and repo_canary in out else "FAIL"
    note = "" if rules == "pass" else f"got: {last}"
    if not guard or harness not in ("claude", "codex"):
        return rules, "-", note
    head = git(repo, "rev-parse", "main")
    run(harness, TASK, repo, timeout)
    branch = git(repo, "branch", "--show-current")
    held = git(repo, "rev-parse", "main") == head
    return rules, "pass" if held else "FAIL", note or f"work landed on `{branch}`"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--harness", default=",".join(CLI))
    p.add_argument("--no-guard", action="store_true")
    p.add_argument("--timeout", type=int, default=300)
    args = p.parse_args()
    _, canary, installed, _ = state()
    if not canary:
        sys.exit("global layer not installed: run `install_global.py install` first")
    for h in installed:
        path = targets()[h][0]
        if path and not BLOCK.search(path.read_text(encoding="utf-8") if path.exists() else ""):
            print(f"warning: {h} block missing in {path}; run `install_global.py sync`")
    failed = 0
    root = Path(tempfile.mkdtemp(prefix="lf-smoke-"))  # kept: manual checks run in these repos
    print("| Harness | Rules loaded | Guard on main | Note |\n|---|---|---|---|")
    for h in [h.strip() for h in args.harness.split(",") if h.strip()]:
        rules, guard, note = smoke(h, root, canary, not args.no_guard, args.timeout)
        failed += "FAIL" in (rules, guard) or rules == "error"
        print(f"| {h} | {rules} | {guard} | {note} |")
    print(f"repos: {root}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
