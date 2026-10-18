"""Bring a v0.1, v0.2 or v0.3 install up to the engine's version without losing the user's edits. Stdlib plus git.

Dry run by default: a unified diff per file and the conflicts, nothing written. `--apply` copies every file
it changes to ~/.lab-forge/backup/<time>/ first. A second run prints no diff.

Global layer: what `install_global.py install` writes, with the user's edits to ~/.lab-forge/AGENTS.md and
to managed blocks merged in (3-way, on the v0.3 render rebuilt from `migrations/`). A conflict leaves the
file as it is and, with --apply, writes `<file>.rej`.
Each repo (`--repo`, default the current one if it has `.lab-forge/state.md`): the v0.1-v0.3 rules file
loses the rules the core now holds and keeps facts and hand-written lines; the v0.1 text pointer becomes
`@AGENTS.md`; the profile named in state is copied in verbatim; state gets `- Version:`.

Usage:
    python upgrade.py [--repo DIR ...] [--harness claude,codex,...] [--no-hooks] [--dry-run | --apply]
"""

import argparse
import difflib
import re
import sys
from datetime import date
from pathlib import Path

import install_global as ig
import migrations
from verify_setup import engine_profiles

RULE_FILES = ["AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md", ".cursor/rules/main.mdc"]
PROFILE = re.compile(r"<!-- lab-forge:begin profile (\S+) sha=(\w*) -->\n(.*?)<!-- lab-forge:end -->\n?", re.S)
VERSION_LINE = re.compile(r"^- Version: (\S+)$", re.M)


def version(text, rules=""):
    """Version recorded in a state file; older installs by their fingerprints (research section 4)."""
    found = VERSION_LINE.search(text)
    if found:
        return found[1]
    if "- Canary:" in text or "Project facts for every agent. How to work (branches" in rules:
        return "0.3"
    return "0.2" if "- Mode:" in text else "0.1"


def profile_block(name, body):
    return f"<!-- lab-forge:begin profile {name} sha={ig.sha(body)} -->\n{body}<!-- lab-forge:end -->\n"


def put_profiles(path, text, names):
    """The named profiles' blocks, verbatim: refreshed in place, or added under `## Invariants`."""
    shipped = engine_profiles()
    for name in [n for n in shipped if re.search(rf"\b{re.escape(n)}\b", names)]:
        new = profile_block(name, shipped[name])
        found = next((m for m in PROFILE.finditer(text) if m[1] == name), None)
        if found and found[3] == shipped[name]:
            continue
        if found and found[2] != ig.sha(found[3]):  # edited by hand: never overwritten
            ig.CONFLICTS[path] = text[: found.start()] + new + text[found.end() :]
            return None
        if found:
            text = text[: found.start()] + new + text[found.end() :]
            continue
        heading = re.search(r"^## Invariants.*\n", text, re.M)
        at = heading.end() if heading else len(text)
        text = text[:at] + ("" if heading else "\n## Invariants\n") + new + text[at:]
    return text


def plan_repo(repo):
    state_path = repo / ".lab-forge" / "state.md"
    state = ig.read(state_path)
    texts = {rel: ig.read(repo / rel) for rel in RULE_FILES if (repo / rel).exists()}
    old = version(state, "\n".join(texts.values()))
    rules_rel = None
    for rel, text in texts.items():
        new = text
        if old != ig.VERSION:
            new = migrations.pointer(new)
            new = migrations.repo_rules(new) if migrations.is_rules(new) else new
        if rules_rel is None and (PROFILE.search(new) or re.search(r"^## ", new, re.M)):
            rules_rel = rel
            named = re.search(r"^- Domain profile:(.*)$", state, re.M)
            new = put_profiles(repo / rel, new, named[1] if named else "")
        if new is not None:
            ig.PENDING[repo / rel] = new
    if state and old != ig.VERSION and not any(repo in c.parents for c in ig.CONFLICTS):
        line = f"- Version: {ig.VERSION}"
        state = VERSION_LINE.sub(line, state) if VERSION_LINE.search(state) else re.sub(
            r"^(- )", line + r"\n\1", state, count=1, flags=re.M)
        log = f"- {date.today().isoformat()} upgrade {old} -> {ig.VERSION}"
        state = state.rstrip("\n") + "\n" + log + "\n" if "## Log" in state else state + f"\n## Log\n{log}\n"
        ig.PENDING[state_path] = state
    return old


def report():
    """Unified diffs of every pending change (base copies only counted), skill links, conflicts."""
    changes = ig.changes()
    base = ig.lf_home() / "base"
    for path, new in changes.items():
        if base in path.parents:
            continue
        old = path.read_text(encoding="utf-8") if path.exists() else ""
        sys.stdout.writelines(difflib.unified_diff(
            old.splitlines(keepends=True), new.splitlines(keepends=True), str(path) if old else "/dev/null", str(path)))
    for dest, action in ig.SKILLS:
        print(f"skill: {action} {dest}")
    for path in ig.CONFLICTS:
        print(f"CONFLICT: {path}: your edit and the new version overlap; the file stays, the merge goes to "
              f"{path.name}.rej on --apply")
    stored = sum(base in p.parents for p in changes)
    if stored:
        print(f"base copies for the next merge: {stored} file(s) in {base}")
    return bool(changes or ig.SKILLS or ig.CONFLICTS)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo", action="append", type=Path, default=[])
    p.add_argument("--harness", help="harnesses for a machine with no global layer yet (default: the ones present)")
    p.add_argument("--no-hooks", action="store_true")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="the default: show the diff, write nothing")
    mode.add_argument("--apply", action="store_true", help="back up, then write")
    args = p.parse_args()
    repos = [r.resolve() for r in args.repo] or [r for r in [Path.cwd()] if (r / ".lab-forge" / "state.md").exists()]

    lf_state = ig.read(ig.lf_home() / "state.md")
    was = version(lf_state) if lf_state else None
    if args.harness:
        harnesses = [h.strip() for h in args.harness.split(",") if h.strip()]
    elif was:
        harnesses = []  # install keeps the ones in state
    else:
        harnesses = [h for h, (rules, _) in ig.targets().items() if rules and rules.parent.exists()] or ["claude"]
    unknown = set(harnesses) - set(ig.targets())
    if unknown:
        p.error(f"unknown harness: {', '.join(sorted(unknown))}")
    settings = [s for _, s in ig.targets().values() if s]
    hooks = not args.no_hooks and (not was or any("guard.py" in ig.read(s) for s in settings))
    ig.install(harnesses, hooks)
    found = [f"{r}: {plan_repo(r)}" for r in repos]
    print(f"global: {was or 'none'}; repos: {', '.join(found) or 'none'}; engine: {ig.VERSION}")
    if not report():
        print("up to date: no changes")
        return 0
    if not args.apply:
        print("dry run: nothing written. Rerun with --apply to back up and write.")
        return 1 if ig.CONFLICTS else 0
    return 1 if ig.flush() else 0


if __name__ == "__main__":
    sys.exit(main())
