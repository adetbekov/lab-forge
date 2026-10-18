"""Tool checks behind the global rules: branch, scope, imports, core blocks, decide. Stdlib only.

Usage:
    python guard.py branch [DIR]            # exit 1 on the default branch
    python guard.py scope [DIR] [--base REF] # exit 1 if changed files are outside .lab-forge/scope
    python guard.py imports [DIR] [FILE...]  # exit 1 if an import does not resolve in the project Python
    python guard.py hook                     # PreToolUse hook: JSON on stdin, exit 2 blocks the call
                                             # (edits on the default branch, inside core/profile blocks)
    python guard.py decide stop|skill        # Stop / UserPromptSubmit hook backed by a decision model

`decide` reads $LAB_FORGE_HOME/decide.json: {"backend": "off" | "hosted" | "local", "url": ...}.
`hosted` sends the task and reply to api.liquid.ai (d1-ultra, $LIQUID_AI_API_KEY); `local` sends them only
to the given /v1/systemone URL. Any error, timeout or missing key does nothing (fail-open).

A repo opts out of the branch rule with `git config lab-forge.allowMain true`.
Managed blocks (`<!-- lab-forge:begin core|profile ... -->` ... `<!-- lab-forge:end -->`, the one marker
format install, upgrade, verify and the profiles use) and $LAB_FORGE_HOME/core.md change only through
lab-forge install or upgrade, never through an agent edit.
"""

import ast
import fnmatch
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit", "apply_patch", "edit", "write"}
COMMIT = re.compile(r"\bgit\b[^;&|]*\b(commit|merge|cherry-pick|rebase)\b")
# group 1 is the layer; a v0.3 block has none and holds the core
BLOCK = re.compile(r"<!-- lab-forge:begin\b(?: (core|profile)\b)?[^>]*-->.*?<!-- lab-forge:end -->", re.S)
MARKER = re.compile(r"<!-- lab-forge:(?:begin\b(?: (core|profile)\b)?|end -->)")


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


def touched_block(path, tool, args):
    """Name of the core/profile block the edit would change, else None. Text outside the blocks stays free."""
    if path.resolve() == (lf_home() / "core.md").resolve():
        return "core"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        text = ""
    found = [(m[1] or "core", m.start(), m.end()) for m in BLOCK.finditer(text)]
    if tool in {"Write", "write"}:  # a full rewrite must carry every block unchanged
        new = args.get("content") or ""
        kept = [m[0] for m in BLOCK.finditer(new)]
        if kept != [text[s:e] for _, s, e in found] or len(MARKER.findall(new)) != 2 * len(kept):
            return found[0][0] if found else MARKER.search(new)[1] or "core"
        return None
    for edit in args.get("edits") or [args]:  # MultiEdit carries a list, Edit one pair
        old, new = edit.get("old_string") or "", edit.get("new_string") or ""
        marker = MARKER.search(old + "\n" + new)
        if marker:
            return marker[1] or "core"
        at = text.find(old) if old else -1
        while at >= 0:
            hit = next((name for name, s, e in found if at < e and at + len(old) > s), None)
            if hit:
                return hit
            at = text.find(old, at + 1)
    return None


def hook():
    """Claude Code / Codex style PreToolUse: block edits inside core/profile blocks and on the default branch."""
    event = json.load(sys.stdin)
    tool, args = event.get("tool_name", ""), event.get("tool_input") or {}
    cwd = Path(event.get("cwd") or ".")
    if tool in EDIT_TOOLS:
        target = args.get("file_path") or args.get("notebook_path")
        if target:  # the file's own repo decides, not the session's cwd
            block = touched_block(cwd / target, tool, args)
            if block:
                print(
                    f"lab-forge guard: {target} is inside the lab-forge {block} block; only lab-forge upgrade "
                    "changes it. Put the rule outside the block or run tune.py add.",
                    file=sys.stderr,
                )
                return 2
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


MAX_SKILLS = 60  # d1-ultra answers a 60-way choice in ~0.5 s; 100 nears the 1.5 s timeout
DECIDE = {"backend": "off", "threshold": 0.5, "confidence": 0.7}
BACKENDS = {  # any endpoint that takes the /v1/systemone body works as `custom` with your own url, model and key
    "hosted": {
        "url": "https://api.liquid.ai/decisions/v1/systemone",
        "model": "d1-ultra",
        "key_env": "LIQUID_AI_API_KEY",
    },
    "local": {"url": "http://localhost:11434/v1/systemone", "model": "d1-omni:600m"},
    "custom": {},
}
STOP_Q = (
    "Given the task and the agent's final report, is the task actually finished and verified, "
    "with nothing the user asked for left undone?"
)
MISSING = {
    "verification": "no fresh command output, test run or check shows that it works",
    "requirement": "part of what the user asked for is not done",
    "errors": "an error, failing test or open problem is mentioned and not fixed",
    "evidence": "the report claims success without saying what was run or changed",
}


def lf_home():
    return Path(os.environ.get("LAB_FORGE_HOME", Path.home() / ".lab-forge"))


def decide_config():
    try:
        cfg = DECIDE | json.loads((lf_home() / "decide.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return DECIDE
    return BACKENDS.get(cfg["backend"], {}) | {k: v for k, v in cfg.items() if v is not None}


def decide_key(cfg):
    """The user's own key: the env var named in `key_env`, else ~/.lab-forge/decide.key. Never printed."""
    key = os.environ.get(cfg.get("key_env") or "", "")
    if not key:
        path = Path(cfg.get("key_file") or lf_home() / "decide.key").expanduser()
        key = path.read_text(encoding="utf-8").strip() if path.is_file() else ""
    return key


def ask(cfg, state, questions, timeout=1.5):
    """Answers from the decision model; None when the backend is off, unset or lacks its key. Errors raise."""
    if cfg["backend"] not in BACKENDS or not cfg.get("url") or not cfg.get("model"):
        return None
    key = decide_key(cfg)
    if cfg.get("key_env") and not key:
        return None
    headers = {"Content-Type": "application/json"} | ({"Authorization": f"Bearer {key}"} if key else {})
    body = json.dumps({"model": cfg["model"], "state": state, "questions": questions}).encode()
    with urllib.request.urlopen(urllib.request.Request(cfg["url"], body, headers), timeout=timeout) as res:
        return json.load(res)["answers"]


def transcript(path):
    """Latest user prompt and the assistant text after it, from a Claude Code or Codex JSONL transcript."""
    task, reply = "", ""
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except (OSError, TypeError):
        return task, reply
    for line in lines:
        try:
            item = json.loads(line)
            msg = item.get("message") or item.get("payload") or {}
            content = msg.get("content")
        except (ValueError, AttributeError):
            continue
        text = content if isinstance(content, str) else ""
        if isinstance(content, list):  # tool results carry no text part, so they never count as a prompt
            parts = [c.get("text", "") for c in content if isinstance(c, dict) and "text" in str(c.get("type"))]
            text = "\n".join(parts)
        if text and msg.get("role") == "user":
            task, reply = text, ""
        elif text and msg.get("role") == "assistant":
            reply = text
    return task, reply


def decide_stop(event, cfg):
    """Block "done" when the model doubts it; once per turn, so the agent is never stuck."""
    if event.get("stop_hook_active"):
        return None
    task, reply = transcript(event.get("transcript_path"))
    reply = event.get("last_assistant_message") or reply
    if not task or not reply:
        return None
    state = f"Task: {task[:2000]}\n\nAgent final report: {reply[-2000:]}"
    answers = ask(
        cfg,
        state,
        {
            "done": {"type": "noul", "instructions": STOP_Q},
            "missing": {
                "type": "choice",
                "instructions": "What is missing before it counts as done?",
                "criteria": MISSING,
            },
        },
    )
    if not answers or answers["done"]["noul"] >= cfg["threshold"]:
        return None
    why = MISSING.get(answers.get("missing", {}).get("choice"), MISSING["verification"])
    return {"decision": "block", "reason": f"not verified: {why}"}


def skill_meta(path):
    """name and description from SKILL.md front matter; a folded `description: >` block is joined into one line."""
    head = path.read_text(encoding="utf-8", errors="replace").split("---")
    meta, key = {}, None
    for line in (head[1] if len(head) > 2 else "").splitlines():
        found = re.match(r"^(\w[\w-]*):\s*(.*)$", line)
        if found:
            key, value = found[1], found[2].strip()
            meta[key] = "" if re.fullmatch(r"[>|][+-]?", value) else value
        elif key and line[:1].isspace():
            meta[key] = f"{meta[key]} {line.strip()}".strip()
    clean = lambda v: v.strip().strip("\"'").strip()  # noqa: E731
    return clean(meta.get("name") or path.parent.name), clean(meta.get("description", ""))[:300]


def plugin_skill_dirs(cwd):
    """(prefix, skills dir) of each enabled Claude Code plugin; its skills load as `plugin:skill`."""
    claude = Path.home() / ".claude"
    try:
        installed = json.loads((claude / "plugins" / "installed_plugins.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    enabled = {}
    for settings in (claude / "settings.json", Path(cwd) / ".claude" / "settings.json"):
        try:
            enabled |= json.loads(settings.read_text(encoding="utf-8")).get("enabledPlugins") or {}
        except (OSError, ValueError, AttributeError):
            pass
    found = []
    for plugin, entries in (installed.get("plugins") or {}).items():
        for e in entries if enabled.get(plugin, True) else []:
            if e.get("scope", "user") == "user" or Path(e.get("projectPath", "/-")).resolve() == Path(cwd).resolve():
                found.append((plugin.split("@")[0] + ":", Path(e.get("installPath", "/-")) / "skills"))
    return found


def skills(cwd):
    """name -> description of every installed skill the session can load, plugin skills included."""
    home, found = Path.home(), {}
    roots = [
        ("", r / "skills") for r in (Path(cwd) / ".claude", Path(cwd) / ".agents", home / ".claude", home / ".agents")
    ]
    for prefix, root in roots + plugin_skill_dirs(cwd):
        for path in sorted(root.glob("*/SKILL.md")):
            name, desc = skill_meta(path)
            found.setdefault(prefix + name, desc)
    return found


def decide_skill(event, cfg):
    """Hint one skill when the model is confident it fits the prompt; else stay silent."""
    prompt = event.get("prompt") or ""
    criteria = dict(list(skills(event.get("cwd") or ".").items())[:MAX_SKILLS])
    if not prompt.strip() or not criteria:
        return None
    criteria["none"] = "No listed skill fits this request"
    q = {
        "type": "choice",
        "instructions": "Which skill should the agent load for this user request?",
        "criteria": criteria,
    }
    answers = ask(cfg, f"User request: {prompt[:3000]}", {"skill": q})
    pick = (answers or {}).get("skill") or {}
    if pick.get("choice") in (None, "none") or pick.get("confidence", 0) < cfg["confidence"]:
        return None
    context = f"lab-forge: load skill {pick['choice']}"
    return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": context}}


def decide(mode):
    try:
        event = json.load(sys.stdin)
        out = {"stop": decide_stop, "skill": decide_skill}[mode](event, decide_config())
    except Exception:  # noqa: BLE001  fail-open: a timeout or a broken model never blocks the agent
        return 0
    if out:
        print(json.dumps(out))
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
    if cmd == "decide" and rest[:1] in (["stop"], ["skill"]):
        return decide(rest[0])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
