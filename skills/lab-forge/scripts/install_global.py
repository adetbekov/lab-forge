"""Install the global layer once per machine and point every harness at it. Stdlib only.

~/.lab-forge/ ($LAB_FORGE_HOME) is the one source: AGENTS.md, overrides.md, hooks/guard.py, state.md.
Each harness gets a managed block in its own global file: an import where the harness supports
it (Claude Code), a copy elsewhere. Copies are re-rendered by `sync`; `check` reports drift.
Harnesses with no global file (Cursor, Copilot in VS Code) get the copy in the repo AGENTS.md.

Usage:
    python install_global.py install [--harness claude,codex,copilot,antigravity] [--no-hooks]
    python install_global.py repo DIR     # fallback: principles block in DIR/AGENTS.md
    python install_global.py sync         # re-render every block after an edit or a tune
    python install_global.py check [DIR]  # exit 1 on drift or a missing block
"""

import argparse
import hashlib
import json
import os
import re
import secrets
import shutil
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent.parent
BEGIN, END = "<!-- lab-forge:begin", "<!-- lab-forge:end -->"
BLOCK = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", re.DOTALL)
HOOK_MATCH = {"claude": "Edit|Write|MultiEdit|NotebookEdit|Bash", "codex": ".*"}


def lf_home():
    return Path(os.environ.get("LAB_FORGE_HOME", Path.home() / ".lab-forge"))


def targets():
    """Global instruction file and settings file per harness. None = the harness has no global file."""
    home, codex = Path.home(), Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    return {
        "claude": (home / ".claude" / "CLAUDE.md", home / ".claude" / "settings.json"),
        "codex": (codex / "AGENTS.md", codex / "hooks.json"),
        "copilot": (home / ".copilot" / "copilot-instructions.md", None),
        "antigravity": (home / ".gemini" / "GEMINI.md", home / ".gemini" / "settings.json"),
        "cursor": (None, None),
    }


SKILL_DIRS = {
    "claude": Path.home() / ".claude" / "skills",
    "codex": Path.home() / ".agents" / "skills",
    "copilot": Path.home() / ".copilot" / "skills",
    "antigravity": Path.home() / ".gemini" / "antigravity" / "skills",
}


def read(path):
    return path.read_text(encoding="utf-8") if path.exists() else ""


def state():
    text = read(lf_home() / "state.md")
    canary = re.search(r"^- Canary: (\S+)", text, re.MULTILINE)
    harnesses = re.search(r"^- Harnesses: (.*)$", text, re.MULTILINE)
    repos = re.findall(r"^- Repo copy: (.+)$", text, re.MULTILINE)
    return text, canary and canary[1], harnesses[1].split(", ") if harnesses else [], repos


def save_state(canary, harnesses, repos):
    text = read(lf_home() / "state.md")
    log = text[text.index("## Log") :] if "## Log" in text else "## Log\n"
    head = ["# lab-forge global state", "", f"- Canary: {canary}", f"- Harnesses: {', '.join(harnesses)}"]
    head += [f"- Repo copy: {r}" for r in sorted(set(repos))]
    (lf_home() / "state.md").write_text("\n".join(head) + "\n\n" + log, encoding="utf-8")


def body(kind):
    """What goes inside a block: an import for Claude Code, a full copy for the rest."""
    lf = lf_home()
    if kind == "claude":
        return f"@{lf / 'AGENTS.md'}\n@{lf / 'overrides.md'}\n"
    text = read(lf / "AGENTS.md").rstrip() + "\n"
    overrides = read(lf / "overrides.md").strip()
    if overrides.count("\n- ") or overrides.startswith("- "):
        text += "\n" + overrides + "\n"
    return text.replace("# Working rules", "## Working rules", 1) if kind == "repo" else text


def block(kind):
    text = body(kind)
    digest = hashlib.sha256(text.encode()).hexdigest()[:12]
    return f"{BEGIN} sha={digest}: managed copy of {lf_home()}; edit there or tune, then `sync` -->\n{text}{END}\n"


def put_block(path, kind):
    """Replace our block in place, or append it; text outside the markers is never touched."""
    text, new = read(path), block(kind)
    text = BLOCK.sub(lambda _: new, text, count=1) if BLOCK.search(text) else text + ("\n" if text else "") + new
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"block: {path}")


def put_settings(path, kind, hooks):
    """Guard hook (Claude Code, Codex); Gemini reads only GEMINI.md in a repo unless told to read AGENTS.md."""
    data = json.loads(read(path) or "{}")
    if kind == "antigravity":
        context = data.setdefault("context", {})
        names = context.get("fileName", "GEMINI.md")
        context["fileName"] = [
            "AGENTS.md",
            *[n for n in ([names] if isinstance(names, str) else names) if n != "AGENTS.md"],
        ]
    elif hooks:
        python = getattr(sys, "_base_executable", sys.executable)  # a project venv can disappear
        command = f'"{python}" "{lf_home() / "hooks" / "guard.py"}" hook'
        entries = data.setdefault("hooks", {}).setdefault("PreToolUse", [])
        entries[:] = [e for e in entries if "lab-forge" not in json.dumps(e)]
        entries.append({"matcher": HOOK_MATCH[kind], "hooks": [{"type": "command", "command": command}]})
    else:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"settings: {path}")


def put_engine(skills_dir):
    """The engine itself as a user skill, so tune works in every repo. A link where the OS allows it."""
    dest = skills_dir / "lab-forge"
    if dest.resolve() == ENGINE:
        return
    if dest.is_symlink() or dest.is_file():
        dest.unlink()
    elif dest.exists():
        shutil.rmtree(dest)
    skills_dir.mkdir(parents=True, exist_ok=True)
    try:
        dest.symlink_to(ENGINE, target_is_directory=True)
    except OSError:
        shutil.copytree(ENGINE, dest)
    print(f"skill: {dest}")


def install(harnesses, hooks):
    lf, (_, canary, _, repos) = lf_home(), state()
    canary = canary or f"LF-{secrets.token_hex(4)}"
    (lf / "hooks").mkdir(parents=True, exist_ok=True)
    rules = read(ENGINE / "assets" / "templates" / "global-agents.md").replace("{{canary}}", canary)
    (lf / "AGENTS.md").write_text(rules, encoding="utf-8")
    if not (lf / "overrides.md").exists():
        (lf / "overrides.md").write_text("# Overrides\n", encoding="utf-8")
    shutil.copy(ENGINE / "scripts" / "guard.py", lf / "hooks" / "guard.py")
    save_state(canary, harnesses, repos)
    for skills_dir in {SKILL_DIRS[h] for h in harnesses if h in SKILL_DIRS}:
        put_engine(skills_dir)
    for name in harnesses:
        rules_file, settings = targets()[name]
        if rules_file:
            put_block(rules_file, name)
        else:
            print(f"{name}: no global file; run `install_global.py repo <dir>` in each repo")
        if settings:
            put_settings(settings, name, hooks)
    print(f"canary: {canary}  (smoke test: send `lab-forge ping` in a new chat)")


def sync(check=False, extra_repo=None):
    _, canary, harnesses, repos = state()
    if not canary:
        sys.exit("global layer not installed: run `install_global.py install`")
    files = [(targets()[h][0], h) for h in harnesses if targets()[h][0]]
    files += [(Path(r) / "AGENTS.md", "repo") for r in repos + ([extra_repo] if extra_repo else [])]
    bad = 0
    for path, kind in files:
        found = BLOCK.search(read(path))
        if check:
            ok = found and found[0].rstrip("\n") == block(kind).rstrip("\n")
            bad += not ok
            print(f"{'ok' if ok else 'DRIFT' if found else 'MISSING'}: {path}")
        elif found:
            put_block(path, kind)
    return 1 if bad else 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("action", choices=["install", "repo", "sync", "check"])
    p.add_argument("dir", nargs="?", type=Path)
    p.add_argument("--harness", default="claude,codex,copilot,antigravity")
    p.add_argument("--no-hooks", action="store_true")
    args = p.parse_args()
    if args.action == "install":
        names = [h.strip() for h in args.harness.split(",") if h.strip()]
        unknown = set(names) - set(targets())
        if unknown:
            p.error(f"unknown harness: {', '.join(sorted(unknown))}")
        return install(names, not args.no_hooks)
    if args.action == "repo":
        if not args.dir:
            p.error("repo needs DIR")
        _, canary, harnesses, repos = state()
        if not canary:
            sys.exit("global layer not installed: run `install_global.py install`")
        put_block(args.dir.resolve() / "AGENTS.md", "repo")
        save_state(canary, harnesses, repos + [str(args.dir.resolve())])
        return 0
    return sync(check=args.action == "check", extra_repo=args.dir and str(args.dir.resolve()))


if __name__ == "__main__":
    sys.exit(main())
