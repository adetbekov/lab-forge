"""Install the global layer once per machine and point every harness at it. Stdlib plus git.

~/.lab-forge/ ($LAB_FORGE_HOME) is the one source: AGENTS.md (core.md + defaults.md), overrides.md, tune.py,
hooks/guard.py, state.md. Each harness gets a managed block `<!-- lab-forge:begin core v=… sha=… -->` in its
own global file: an import where the harness supports it (Claude Code), a copy elsewhere. Copies are
re-rendered by `sync`; `check` reports drift and hand edits. Harnesses with no global file (Cursor, Copilot
in VS Code) get the copy in the repo AGENTS.md.

Nothing lab-forge owns is overwritten silently: what it rendered last is kept in ~/.lab-forge/base/, and a
file or block the user edited since gets a 3-way merge (`git merge-file`). A conflict leaves the file as it
is and writes the merge next to it as `<file>.rej`. Every changed file is first copied to
~/.lab-forge/backup/<time>/.

Usage:
    python install_global.py install [--harness claude,codex,copilot,antigravity] [--no-hooks]
                                     [--decide off|hosted|local|custom] [--decide-url URL]
                                     [--decide-model NAME] [--decide-key-env VAR]
    python install_global.py repo DIR     # fallback: principles block in DIR/AGENTS.md
    python install_global.py sync         # re-render every block after an edit or a tune
    python install_global.py check [DIR]  # exit 1 on drift, a hand edit or a missing block
    python install_global.py uninstall    # remove blocks, hooks and skill links; ~/.lab-forge stays
"""

import argparse
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import guard

VERSION = "0.4.1"
ENGINE = Path(__file__).resolve().parent.parent
BEGIN, END = "<!-- lab-forge:begin", "<!-- lab-forge:end -->"
# the core block of a harness or repo file: any lab-forge block but a profile (v0.3 wrote no layer name)
BLOCK = re.compile(re.escape(BEGIN) + r"(?! profile )([^>]*)-->\n?(.*?)" + re.escape(END) + r"\n?", re.DOTALL)
SHA = re.compile(r"\bsha=(\w+)")
HOOK_MATCH = {"claude": "Edit|Write|MultiEdit|NotebookEdit|Bash", "codex": ".*"}
DECIDE_HOOKS = {"Stop": "stop", "UserPromptSubmit": "skill"}
DECIDE_OFFER = (
    'decide: off. Optional: a decision model checks "done?" and hints skills; bring your own endpoint and key '
    "(hosted d1-ultra, local d1-omni or any /v1/systemone API): install --decide hosted|local|custom, "
    "see references/generation.md section 8"
)
PENDING = {}  # path -> text to write; read() already sees it, flush() writes it
CONFLICTS = {}  # path -> merge with conflict markers, written as <path>.rej; the file itself stays
SKILLS = []  # (dest, "link" | "remove")


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
    """The text as it will be: a pending write wins over the disk."""
    path = Path(path)
    if path in PENDING:
        return PENDING[path]
    return path.read_text(encoding="utf-8") if path.exists() else ""


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def state():
    text = read(lf_home() / "state.md")
    canary = re.search(r"^- Canary: (\S+)", text, re.MULTILINE)
    harnesses = re.search(r"^- Harnesses: (.*)$", text, re.MULTILINE)
    repos = re.findall(r"^- Repo copy: (.+)$", text, re.MULTILINE)
    return text, canary and canary[1], [h for h in harnesses[1].split(", ") if h] if harnesses else [], repos


def save_state(canary, harnesses, repos):
    text = read(lf_home() / "state.md")
    log = text[text.index("## Log") :] if "## Log" in text else "## Log\n"
    head = ["# lab-forge global state", "", f"- Version: {VERSION}", f"- Canary: {canary}"]
    head += [f"- Harnesses: {', '.join(harnesses)}"] + [f"- Repo copy: {r}" for r in sorted(set(repos))]
    PENDING[lf_home() / "state.md"] = "\n".join(head) + "\n\n" + log


def body(kind, rules=None, overrides=None):
    """What goes inside a block: an import for Claude Code, a full copy for the rest."""
    lf = lf_home()
    if kind == "claude":
        return f"@{lf / 'AGENTS.md'}\n@{lf / 'overrides.md'}\n"
    text = (read(lf / "AGENTS.md") if rules is None else rules).rstrip() + "\n"
    overrides = (read(lf / "overrides.md") if overrides is None else overrides).strip()
    if overrides.count("\n- ") or overrides.startswith("- "):
        text += "\n" + overrides + "\n"
    return text.replace("# Working rules", "## Working rules", 1) if kind == "repo" else text


def marker(digest):
    return f"{BEGIN} core v={VERSION} sha={digest}: managed copy of {lf_home()}; edit there or tune, then `sync` -->\n"


def block(kind):
    """A fresh managed block, for a file lab-forge creates itself (smoke.py's throwaway repo)."""
    text = body(kind)
    return marker(sha(text)) + text + END + "\n"


def base_file(path):
    """Where the last render of a lab-forge-owned file or block is kept, for the next 3-way merge."""
    return lf_home() / "base" / f"{Path(path).name}-{sha(str(Path(path).resolve()))}"


def merge(current, base, new):
    """git merge-file: (merged text, number of conflicts). The user's edits on top of the new render."""
    with tempfile.TemporaryDirectory() as tmp:
        files = []
        for name, text in (("installed", current), ("base", base), ("new", new)):
            files.append(Path(tmp) / name)
            files[-1].write_text(text, encoding="utf-8")
        try:
            res = subprocess.run(
                ["git", "merge-file", "-p", "-L", "yours", "-L", "base", "-L", f"lab-forge {VERSION}", *map(str, files)],
                capture_output=True, text=True, check=False,
            )
        except FileNotFoundError:
            sys.exit("git is needed to merge your edits into lab-forge files")
    if not 0 <= res.returncode < 128:
        sys.exit(f"git merge-file failed: {res.stderr.strip()}")
    return res.stdout, res.returncode


def managed(path, current, new, legacy=None):
    """Text to keep for a lab-forge-owned unit, or None on a conflict (the unit stays as it is).

    current None: not there yet. Unchanged since the last render: the new render. Edited by the user:
    a 3-way merge on the stored base, or on `legacy()` (the v0.3 render, rebuilt) when there is none.
    """
    store = base_file(path)
    base = read(store) if store.exists() or store in PENDING else (legacy() if legacy else None)
    if current is not None and current not in (new, base):
        if base is None:  # nothing to merge on: offer the new render next to it
            CONFLICTS[path] = new
            return None
        merged, conflicts = merge(current, base, new)
        if conflicts:
            CONFLICTS[path] = merged
            return None
        new_text = merged
    else:
        new_text = new
    PENDING[store] = new
    return new_text


def put_file(path, new, legacy=None):
    """A whole file lab-forge owns in ~/.lab-forge; the user's edits survive the next install."""
    kept = managed(path, read(path) if path.exists() or path in PENDING else None, new, legacy)
    if kept is not None:
        PENDING[path] = kept


def put_block(path, kind):
    """Replace our block in place, or append it; text outside the markers is never touched."""
    text, new = read(path), body(kind)
    found = BLOCK.search(text)
    legacy = None
    if found and "v=" not in found[1]:  # v0.3: rebuild what it rendered, picked by the sha in its marker
        def legacy():
            import migrations  # noqa: PLC0415 - only an upgrade from v0.3 needs it

            rules = migrations.global_rules(state()[1] or "")
            bodies = [body(kind, r) for r in rules]
            stored = SHA.search(found[1])
            exact = [b for b in bodies if stored and sha(b) == stored[1]]
            return exact[0] if exact else migrations.closest(found[2], bodies)
    kept = managed(path, found[2] if found else None, new, legacy)
    if kept is None:
        return
    managed_block = marker(sha(new)) + kept + END + "\n"  # the sha is the render's: a merged edit shows in `check`
    if found:
        text = text[: found.start()] + managed_block + text[found.end() :]
    else:
        text += ("\n" if text and not text.endswith("\n") else "") + ("\n" if text else "") + managed_block
    PENDING[path] = text


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
        command = f'"{python}" "{lf_home() / "hooks" / "guard.py"}"'
        entries = data.setdefault("hooks", {}).setdefault("PreToolUse", [])
        entries[:] = [e for e in entries if "lab-forge" not in json.dumps(e)]
        entries.append({"matcher": HOOK_MATCH[kind], "hooks": [{"type": "command", "command": f"{command} hook"}]})
        on = decide_backend() != "off"
        for event, mode in DECIDE_HOOKS.items():  # next to other Stop hooks (the verifier), never instead
            entries = data["hooks"].setdefault(event, [])
            entries[:] = [e for e in entries if not re.search(r"guard\.py\W+decide", json.dumps(e))]
            if on:
                entries.append({"hooks": [{"type": "command", "command": f"{command} decide {mode}", "timeout": 5}]})
            if not entries:
                del data["hooks"][event]
    else:
        return
    PENDING[path] = json.dumps(data, indent=2) + "\n"


def decide_backend():
    try:
        return json.loads(read(lf_home() / "decide.json") or "{}").get("backend", "off")
    except ValueError:
        return "off"


def put_decide(backend, url=None, model=None, key_env=None):
    """Write decide.json; None keeps what is there. Prints where the data goes and whether the key is there."""
    if backend is not None:
        cfg = {"backend": backend, "url": url, "model": model, "key_env": key_env}
        if backend == "custom" and not (url and model):
            sys.exit("--decide custom needs --decide-url and --decide-model")
        cfg = {k: v for k, v in cfg.items() if v}
        lf_home().mkdir(parents=True, exist_ok=True)
        (lf_home() / "decide.json").write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    cfg = guard.decide_config()
    if cfg["backend"] == "off":
        print(DECIDE_OFFER)
        return
    host = re.sub(r"^\w+://([^/]+).*", r"\1", cfg.get("url") or "?")
    print(f"decide: {cfg['backend']} {cfg.get('model')}; each prompt, task and final reply is sent to {host}")
    key_file, env = lf_home() / "decide.key", cfg.get("key_env")
    if env and os.environ.get(env):
        print(f"decide key: found in ${env}")
    elif guard.decide_key(cfg):
        print(f"decide key: found in {cfg.get('key_file') or key_file}")
    elif env:
        print(
            f"decide key: missing. Add your own: export {env}=... where the agent starts, or write it to "
            f"{key_file} (chmod 600). The hooks stay silent until then."
        )
    else:
        print(f"decide key: none sent. If the endpoint needs one, write it to {key_file} (chmod 600).")


def put_engine(skills_dir):
    """The engine itself as a user skill, so tune works in every repo. A link where the OS allows it."""
    dest = skills_dir / "lab-forge"
    if dest.resolve() != ENGINE:
        SKILLS.append((dest, "link"))


def install(harnesses, hooks, decide=None, decide_url=None, decide_model=None, decide_key_env=None):
    """Plan the global layer; flush() writes it. A rerun keeps the canary, harnesses and the user's edits."""
    import migrations  # noqa: PLC0415

    lf, (_, canary, installed, repos) = lf_home(), state()
    canary = canary or f"LF-{secrets.token_hex(4)}"
    harnesses = list(dict.fromkeys([*installed, *harnesses]))  # a partial rerun keeps the others
    rendered = {}
    for name in ("core.md", "defaults.md"):
        text = read(ENGINE / "assets" / "templates" / name)
        rendered[name] = text.replace("{{canary}}", canary).replace("{{tune}}", (lf / "tune.py").as_posix())
        put_file(lf / name, rendered[name])
    rules = rendered["core.md"] + rendered["defaults.md"]
    put_file(lf / "AGENTS.md", rules, lambda: migrations.closest(read(lf / "AGENTS.md"), migrations.global_rules(canary)))
    if not read(lf / "overrides.md"):
        PENDING[lf / "overrides.md"] = "# Overrides\n"
    for src, dest in (("guard.py", "hooks/guard.py"), ("install_global.py", "hooks/install_global.py"),
                      ("tune.py", "tune.py")):  # tune.py finds the other two in hooks/
        PENDING[lf / dest] = read(ENGINE / "scripts" / src)
    put_decide(decide, decide_url, decide_model, decide_key_env)
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
    for repo in repos:
        put_block(Path(repo) / "AGENTS.md", "repo")
    return canary


def block_files(extra_repo=None):
    _, _, harnesses, repos = state()
    files = [(targets()[h][0], h) for h in harnesses if targets()[h][0]]
    return files + [(Path(r) / "AGENTS.md", "repo") for r in repos + ([extra_repo] if extra_repo else [])]


def sync(check=False, extra_repo=None):
    if not state()[1]:
        sys.exit("global layer not installed: run `install_global.py install`")
    bad = 0
    for path, kind in block_files(extra_repo):
        found = BLOCK.search(read(path))
        if check:
            stored = found and SHA.search(found[1])
            edited = found and (not stored or stored[1] != sha(found[2]))
            ok = found and not edited and found[2] == body(kind) and "v=" in found[1]
            bad += not ok
            print(f"{'ok' if ok else 'DRIFT (edited by hand)' if edited else 'DRIFT' if found else 'MISSING'}: {path}")
        elif found:
            put_block(path, kind)
    if not check:
        flush()
    return 1 if bad else 0


def uninstall():
    """Remove what install added outside ~/.lab-forge: blocks, hooks, skill links. Overrides stay for later."""
    _, canary, harnesses, repos = state()
    if not canary:
        sys.exit("global layer not installed")
    for path, _ in block_files():
        if BLOCK.search(read(path)):
            PENDING[path] = BLOCK.sub("", read(path)).rstrip("\n") + "\n"
    for name in harnesses:
        settings = targets()[name][1]
        if settings and read(settings):
            data = json.loads(read(settings))
            for event, entries in list(data.get("hooks", {}).items()):
                entries[:] = [e for e in entries if "lab-forge" not in json.dumps(e)]
                if not entries:
                    del data["hooks"][event]
            PENDING[settings] = json.dumps(data, indent=2) + "\n"
        skills = SKILL_DIRS.get(name)
        if skills and (skills / "lab-forge").resolve() == ENGINE:
            SKILLS.append((skills / "lab-forge", "remove"))
    save_state(canary, [], [])
    flush()
    print(f"kept {lf_home()}: delete it yourself if you do not need your overrides")
    return 0


def changes():
    """Pending writes that differ from the disk."""
    return {p: t for p, t in PENDING.items() if not p.exists() or p.read_text(encoding="utf-8") != t}


def backup(path, stamp):
    """Copy a file (or move a skill folder) to ~/.lab-forge/backup/<stamp>/<its absolute path>."""
    dest = lf_home() / "backup" / stamp / Path(path).resolve().as_posix().replace(":", "").lstrip("/")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if Path(path).is_dir() and not Path(path).is_symlink():
        shutil.move(str(path), dest)
    else:
        shutil.copy2(path, dest)
    return dest


def flush():
    """Write every pending change; each file that exists is backed up first. Conflicts go to <file>.rej."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    for path, text in changes().items():
        if path.exists() and lf_home() / "base" not in path.parents:
            backup(path, stamp)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"wrote: {path}")
    for path, text in CONFLICTS.items():
        rej = path.with_name(path.name + ".rej")
        rej.write_text(text, encoding="utf-8")
        print(f"CONFLICT: {path} kept as is; the merge is in {rej}")
    for dest, action in SKILLS:
        if dest.is_symlink() or dest.is_file():
            dest.unlink()
        elif dest.exists():
            print(f"moved your copy of {dest} to {backup(dest, stamp)}")
        if action == "link":
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                dest.symlink_to(ENGINE, target_is_directory=True)
            except OSError:
                shutil.copytree(ENGINE, dest)
        print(f"skill: {dest} {'removed' if action == 'remove' else ''}".rstrip())
    conflicts = len(CONFLICTS)
    PENDING.clear()
    CONFLICTS.clear()
    SKILLS.clear()
    return conflicts


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("action", choices=["install", "repo", "sync", "check", "uninstall"])
    p.add_argument("dir", nargs="?", type=Path)
    p.add_argument("--harness", default="claude,codex,copilot,antigravity")
    p.add_argument("--no-hooks", action="store_true")
    p.add_argument("--decide", choices=["off", *guard.BACKENDS], help="decision hooks backend (default: keep)")
    p.add_argument("--decide-url", help="/v1/systemone endpoint (local and custom)")
    p.add_argument("--decide-model", help="model name the endpoint expects")
    p.add_argument("--decide-key-env", help="env var that holds your key; the key itself never goes on the CLI")
    args = p.parse_args()
    if args.action == "install":
        names = [h.strip() for h in args.harness.split(",") if h.strip()]
        unknown = set(names) - set(targets())
        if unknown:
            p.error(f"unknown harness: {', '.join(sorted(unknown))}")
        canary = install(names, not args.no_hooks, args.decide, args.decide_url, args.decide_model, args.decide_key_env)
        conflicts = flush()
        print(f"canary: {canary}  (smoke test: send `lab-forge ping` in a new chat)")
        return 1 if conflicts else 0
    if args.action == "uninstall":
        return uninstall()
    if args.action == "repo":
        if not args.dir:
            p.error("repo needs DIR")
        _, canary, harnesses, repos = state()
        if not canary:
            sys.exit("global layer not installed: run `install_global.py install`")
        put_block(args.dir.resolve() / "AGENTS.md", "repo")
        save_state(canary, harnesses, repos + [str(args.dir.resolve())])
        return 1 if flush() else 0
    return sync(check=args.action == "check", extra_repo=args.dir and str(args.dir.resolve()))


if __name__ == "__main__":
    sys.exit(main())
