"""Write one tune override line, log it, print the diff. Undo reverts the last tune.

Stdlib only. Global overrides live in $LAB_FORGE_HOME/overrides.md (default ~/.lab-forge),
repo overrides in the `## Overrides` section of <repo>/AGENTS.md. At ownership level 0
(no <repo>/.lab-forge/state.md, or it says level 0) nothing is written to the repo: repo lines
go to global overrides with a `[<repo name>]` prefix.

Usage:
    python tune.py add --scope global|repo "<line>" [--replace "<old line>"] [--repo DIR]
    python tune.py undo [--repo DIR]      # a second undo redoes
    python tune.py routing on|off [--no-hook]  # tier rule, quick/build/verifier subagents, Stop hook
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from guard import on_default_branch  # noqa: E402

SECTION = "## Overrides"
ROUTING = Path(__file__).resolve().parent.parent / "assets" / "routing"
ROUTING_LINE = (
    "Route each coding task by size: S (one clear change in 1-2 files) -> subagent `quick`; M (a feature or fix "
    "over several files of known code) -> subagent `build`; L/XL (new project or module, design choice, unknown "
    "cause) -> do it yourself, then subagent `verifier`. When unsure, pick the lower tier; `ESCALATE` or a second "
    "red test run moves the task one tier up."
)
LOG_LINE = re.compile(r"^- (\S+ \S+) tune (global|repo) (\[.*\])$")


def paths(scope, repo):
    if scope == "global":
        home = Path(os.environ.get("LAB_FORGE_HOME", Path.home() / ".lab-forge"))
        return home / "overrides.md", home / "state.md"
    return repo / "AGENTS.md", repo / ".lab-forge" / "state.md"


def repo_level_zero(repo):
    state = repo / ".lab-forge" / "state.md"
    if not state.exists():
        return True
    level = re.search(r"^- Level:(.*)$", state.read_text(encoding="utf-8"), flags=re.M)
    return bool(level and re.search(r"\b0\b", level[1]))


def section_bounds(text, scope):
    """Line range [start, end) that holds override bullets; adds the section if missing."""
    if scope == "global":
        text = text or ["# Overrides", ""]
        start, end = 1 if text[0].startswith("# ") else 0, len(text)
    else:
        if SECTION not in text:
            text = text + ([""] if text and text[-1].strip() else []) + [SECTION, ""]
        start = text.index(SECTION) + 1
        end = next((i for i in range(start, len(text)) if text[i].startswith("## ")), len(text))
    while end > start and not text[end - 1].strip():
        end -= 1
    return text, start, end


def apply(scope, repo, new, old):
    target, state = paths(scope, repo)
    text = target.read_text(encoding="utf-8").splitlines() if target.exists() else []
    text, start, end = section_bounds(text, scope)
    bullets = [line[2:].strip() for line in text[start:end]]
    if new and new in bullets:
        sys.exit(f"already in {target}: {new}")
    if old:
        if old not in bullets:
            sys.exit(f"not found in {target}: {old}")
        i = start + bullets.index(old)
        text[i:i + 1] = [f"- {new}"] if new else []
    else:
        text.insert(end, f"- {new}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(text) + "\n", encoding="utf-8")
    log(state, scope, new, old)
    if scope == "global":
        resync()
    print(target)
    if old:
        print(f"- {old}")
    if new:
        print(f"+ {new}")


def resync():
    """Harness files that hold a copy of the global rules must follow overrides.md."""
    from install_global import state, sync

    if state()[1]:
        sync()


def log(state, scope, new, old):
    state.parent.mkdir(parents=True, exist_ok=True)
    text = state.read_text(encoding="utf-8").splitlines() if state.exists() else ["## Log"]
    if "## Log" not in text:
        text += ["", "## Log"]
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    end = next((i for i in range(text.index("## Log") + 1, len(text)) if text[i].startswith("## ")),
               len(text))
    text.insert(end, f"- {stamp} tune {scope} {json.dumps([new, old], ensure_ascii=False)}")
    state.write_text("\n".join(text) + "\n", encoding="utf-8")


def last_tune(repo):
    found = []
    for scope in ("global", "repo"):
        state = paths(scope, repo)[1]
        if state.exists():
            lines = state.read_text(encoding="utf-8").splitlines()
            found += [(m[1], i, m[2], m[3]) for i, m in enumerate(map(LOG_LINE.match, lines)) if m]
    if not found:
        sys.exit("nothing to undo")
    _, _, scope, pair = max(found)
    return scope, json.loads(pair)


def codex_agent(md):
    """Codex reads ~/.codex/agents/*.toml. Effort carries over; the model stays the Codex default."""
    head, body = md.split("---", 2)[1:]
    meta = dict(line.split(": ", 1) for line in head.strip().splitlines())
    lines = [f'name = "{meta["name"]}"', f"description = {json.dumps(meta['description'])}"]
    lines += [f'model_reasoning_effort = "{meta["effort"]}"']
    lines += ['sandbox_mode = "read-only"'] if meta["name"] == "verifier" else []
    return "\n".join(lines + [f'developer_instructions = """\n{body.strip()}\n"""']) + "\n"


def stop_hooks(path, cmd, on):
    """Add or remove our Stop and SubagentStop hooks in a Claude settings.json or Codex hooks.json."""
    if not path.exists() and not on:
        return
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    for event in ("Stop", "SubagentStop") if path.name == "settings.json" else ("Stop",):
        groups = data.setdefault("hooks", {}).setdefault(event, [])
        groups[:] = [g for g in groups if not any("verify_stop.py" in h.get("command", "") for h in g.get("hooks", []))]
        if on:
            groups.append({"hooks": [{"type": "command", "command": cmd, "timeout": 600}]})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def routing(on, hook, repo):
    """Install or remove the subagents. Files lab-forge did not write (or the user edited since) stay untouched."""
    home = paths("global", repo)[0].parent
    agents = sorted((ROUTING / "agents").glob("*.md"))
    targets = [(Path.home() / ".claude" / "agents" / a.name, a.read_text(encoding="utf-8")) for a in agents]
    if (Path.home() / ".codex").exists():
        targets += [(Path.home() / ".codex" / "agents" / f"{a.stem}.toml", codex_agent(a.read_text(encoding="utf-8")))
                    for a in agents]
    manifest = home / "routing.json"
    owned = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else {}
    for path, text in targets:
        current = path.read_text(encoding="utf-8") if path.exists() else None
        ours = current is None or owned.get(str(path)) == digest(current) or (on and current == text)
        if not ours:
            print(f"skip {path}: not written by lab-forge, or changed since")
            owned.pop(str(path), None)
        elif on:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            owned[str(path)] = digest(text)
            print(f"+ {path}")
        elif current is not None:
            path.unlink()
            owned.pop(str(path), None)
            print(f"- {path}")
    home.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(owned, indent=1) + "\n", encoding="utf-8")
    if not owned:
        manifest.unlink()
    script = home / "hooks" / "verify_stop.py"
    if on and hook:
        script.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROUTING / "verify_stop.py", script)
    elif not on:
        script.unlink(missing_ok=True)
    cmd = f'python "{script}"'
    stop_hooks(Path.home() / ".claude" / "settings.json", cmd, on and hook)
    if (Path.home() / ".codex").exists():
        stop_hooks(Path.home() / ".codex" / "hooks.json", cmd, on and hook)
    print(("+ " if on and hook else "- ") + f"Stop hook {script}")
    claude_md = Path.home() / ".claude" / "CLAUDE.md"
    text = claude_md.read_text(encoding="utf-8") if claude_md.exists() else ""
    if on and "overrides.md" not in text:  # install_global.py already imports it
        claude_md.parent.mkdir(parents=True, exist_ok=True)
        claude_md.write_text(text + ("\n" if text and not text.endswith("\n") else "") + "@~/.lab-forge/overrides.md\n",
                             encoding="utf-8")
        print(f"+ {claude_md}: @~/.lab-forge/overrides.md")
    bullets = paths("global", repo)[0]
    present = bullets.exists() and f"- {ROUTING_LINE}" in bullets.read_text(encoding="utf-8").splitlines()
    if on != present:
        apply("global", repo, ROUTING_LINE if on else None, None if on else ROUTING_LINE)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=["add", "undo", "routing"])
    parser.add_argument("line", nargs="?")
    parser.add_argument("--scope", choices=["global", "repo"])
    parser.add_argument("--replace")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--no-hook", dest="hook", action="store_false", help="routing on: skip the Stop hook")
    args = parser.parse_args()
    if args.action == "add":
        if not args.line or not args.scope:
            parser.error("add needs a line and --scope")
        scope, line, old = args.scope, args.line.strip(), args.replace and args.replace.strip()
        if scope == "repo" and (repo_level_zero(args.repo) or on_default_branch(args.repo)):
            tag = f"[{args.repo.resolve().name}] "
            scope, line, old = "global", tag + line, old and tag + old
            print("level 0 or default branch: nothing is written to the repo; stored in global overrides")
        apply(scope, args.repo, line, old)
    elif args.action == "routing":
        if args.line not in ("on", "off"):
            parser.error("routing needs on or off")
        routing(args.line == "on", args.hook, args.repo)
    else:
        scope, (new, old) = last_tune(args.repo)
        apply(scope, args.repo, old, new)


if __name__ == "__main__":
    main()
