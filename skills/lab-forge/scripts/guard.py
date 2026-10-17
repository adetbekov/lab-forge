"""Tool checks behind the global rules: branch, scope, imports. Stdlib only.

Usage:
    python guard.py branch [DIR]            # exit 1 on the default branch
    python guard.py scope [DIR] [--base REF] # exit 1 if changed files are outside .lab-forge/scope
    python guard.py imports [DIR] [FILE...]  # exit 1 if an import does not resolve in the project Python
    python guard.py hook                     # PreToolUse hook: JSON on stdin, exit 2 blocks the call

A repo opts out of the branch rule with `git config lab-forge.allowMain true`.
"""

import ast
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit", "apply_patch", "edit", "write"}
COMMIT = re.compile(r"\bgit\b[^;&|]*\b(commit|merge|cherry-pick|rebase)\b")


def git(cwd, *args):
    res = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=False)
    return res.stdout.strip() if res.returncode == 0 else None


def on_default_branch(cwd):
    """Branch name if cwd is in a git repo on its default branch, else None."""
    branch = git(cwd, "branch", "--show-current")
    if not branch or git(cwd, "config", "--bool", "lab-forge.allowMain") == "true":
        return None
    default = (git(cwd, "symbolic-ref", "--short", "refs/remotes/origin/HEAD") or "").removeprefix("origin/")
    return branch if branch in {default, "main", "master"} else None


def branch_msg(branch):
    return (
        f"lab-forge guard: you are on `{branch}`. Start a branch first: git switch -c <feat|fix|docs|chore|exp>/<slug>"
    )


def changed_files(cwd, base):
    out = git(cwd, "diff", "--name-only", base) or ""
    untracked = git(cwd, "ls-files", "--others", "--exclude-standard") or ""
    return sorted(set(out.splitlines()) | set(untracked.splitlines()))


def check_scope(cwd, base):
    plan = Path(cwd) / ".lab-forge" / "scope"
    if not plan.exists():
        print("no .lab-forge/scope: write the planned file globs there to check scope")
        return 0
    globs = [l.strip() for l in plan.read_text(encoding="utf-8").splitlines() if l.strip() and l[0] != "#"]
    outside = [
        f
        for f in changed_files(cwd, base)
        if not f.startswith(".lab-forge/") and not any(fnmatch.fnmatch(f, g) for g in globs)
    ]
    for f in outside:
        print(f"outside scope: {f}")
    return 1 if outside else 0


def project_python(cwd):
    for rel in (".venv/bin/python", ".venv/Scripts/python.exe", "venv/bin/python"):
        if (Path(cwd) / rel).exists():
            return str(Path(cwd) / rel)
    return sys.executable


def check_imports(cwd, files):
    files = files or [f for f in changed_files(cwd, "HEAD") if f.endswith(".py")]
    names = set()
    for f in files:
        path = Path(cwd) / f
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
        except (OSError, SyntaxError) as err:
            print(f"skipped {f}: {err}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                names.add(node.module.split(".")[0])
    probe = (
        "import importlib.util as u, importlib.metadata as m, json, sys\n"
        "out = {}\n"
        "for n in sys.argv[1:]:\n"
        "    if u.find_spec(n) is None: out[n] = None; continue\n"
        "    try: out[n] = m.version(m.packages_distributions().get(n, [n])[0])\n"
        "    except Exception: out[n] = ''\n"
        "print(json.dumps(out))"
    )
    res = subprocess.run(
        [project_python(cwd), "-c", probe, *sorted(names)], cwd=cwd, capture_output=True, text=True, check=False
    )
    found = json.loads(res.stdout or "{}")
    missing = [n for n, v in found.items() if v is None]
    for n, v in sorted(found.items()):
        if v:
            print(f"{n} {v}: read the docs for this version")
    for n in missing:
        print(f"does not resolve: {n}")
    return 1 if missing else 0


def hook():
    """Claude Code / Codex style PreToolUse: block edits and commits on the default branch."""
    event = json.load(sys.stdin)
    tool, args = event.get("tool_name", ""), event.get("tool_input") or {}
    cwd = Path(event.get("cwd") or ".")
    if tool in EDIT_TOOLS:
        target = args.get("file_path") or args.get("notebook_path")
        if target:  # the file's own repo decides, not the session's cwd
            cwd = (cwd / target).parent
            while not cwd.exists():
                cwd = cwd.parent
    elif not (tool in {"Bash", "shell"} and COMMIT.search(str(args.get("command", "")))):
        return 0
    branch = on_default_branch(cwd)
    if branch:
        print(branch_msg(branch), file=sys.stderr)
        return 2
    return 0


def main():
    cmd, rest = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else ("", [])
    cwd = rest[0] if rest and not rest[0].startswith("-") and cmd != "imports" else "."
    if cmd == "branch":
        branch = on_default_branch(cwd)
        print(branch_msg(branch) if branch else "ok: not on the default branch")
        return 1 if branch else 0
    if cmd == "scope":
        return check_scope(cwd, rest[rest.index("--base") + 1] if "--base" in rest else "HEAD")
    if cmd == "imports":
        cwd, files = (rest[0], rest[1:]) if rest and Path(rest[0]).is_dir() else (".", rest)
        return check_imports(cwd, files)
    if cmd == "hook":
        return hook()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
