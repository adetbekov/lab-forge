"""Write one tune override line, log it, print the diff. Undo reverts the last tune.

Stdlib only. Global overrides live in $LAB_FORGE_HOME/overrides.md (default ~/.lab-forge),
repo overrides in the `## Overrides` section of <repo>/AGENTS.md.

Usage:
    python tune.py add --scope global|repo "<line>" [--replace "<old line>"] [--repo DIR]
    python tune.py undo [--repo DIR]      # a second undo redoes
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

SECTION = "## Overrides"
LOG_LINE = re.compile(r"^- (\S+ \S+) tune (global|repo) (\[.*\])$")


def paths(scope, repo):
    if scope == "global":
        home = Path(os.environ.get("LAB_FORGE_HOME", Path.home() / ".lab-forge"))
        return home / "overrides.md", home / "state.md"
    return repo / "AGENTS.md", repo / ".lab-forge" / "state.md"


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
    print(target)
    if old:
        print(f"- {old}")
    if new:
        print(f"+ {new}")


def log(state, scope, new, old):
    state.parent.mkdir(parents=True, exist_ok=True)
    text = state.read_text(encoding="utf-8").splitlines() if state.exists() else ["## Log"]
    if "## Log" not in text:
        text += ["", "## Log"]
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=["add", "undo"])
    parser.add_argument("line", nargs="?")
    parser.add_argument("--scope", choices=["global", "repo"])
    parser.add_argument("--replace")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()
    if args.action == "add":
        if not args.line or not args.scope:
            parser.error("add needs a line and --scope")
        apply(args.scope, args.repo, args.line.strip(), args.replace and args.replace.strip())
    else:
        scope, (new, old) = last_tune(args.repo)
        apply(scope, args.repo, old, new)


if __name__ == "__main__":
    main()
