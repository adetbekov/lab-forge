"""Verify a lab-forge-generated setup: budgets, links, duplicated rules, skill frontmatter, profile block.

Stdlib only. Checks files listed in .lab-forge/state.md when present; otherwise checks
the usual agent files and warns that ownership is unknown. `--engine` checks the engine's
own templates instead: the core and repo template budgets and the profile block shas.

Usage:
    python verify_setup.py <project> [--skip-skill NAME ...]
    python verify_setup.py --engine
Exit code 1 if any check fails.
"""

import argparse
import hashlib
import re
import sys
from collections import defaultdict
from pathlib import Path

CANONICAL = ["AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md"]
POINTERS_EXTRA = [".cursor/rules/main.mdc"]
SKILL_DIRS = [".claude/skills", ".github/skills", ".agents/skills", ".cursor/skills"]
COMMAND_GLOBS = [".github/prompts/*.prompt.md", ".claude/commands/*.md"]
BUDGET = {"rules": 60, "pointer": 5, "skill": 120, "command": 10, "state": 60}
CORE_BUDGET, ALWAYS_LOADED_BUDGET = 30, 60  # core alone; core plus the repo template
LINK = re.compile(r"\[[^\]]*\]\(([^)#\s]+)(?:#[^)]*)?\)")
GLOBAL_COPY = re.compile(r"<!-- lab-forge:begin(?! profile ).*?<!-- lab-forge:end -->", re.S)
PROFILE = re.compile(r"<!-- lab-forge:begin profile (\S+) sha=(\w*) -->\n(.*?)<!-- lab-forge:end -->", re.S)
ENGINE = Path(__file__).resolve().parent.parent


def lines(path):
    """Lines the repo owns: a managed copy of the global rules (install_global.py repo) is not counted."""
    return GLOBAL_COPY.sub("", path.read_text(encoding="utf-8", errors="ignore")).splitlines()


def body_lines(path):
    """Lines without YAML frontmatter."""
    text = lines(path)
    if text and text[0].strip() == "---":
        for i, line in enumerate(text[1:], 1):
            if line.strip() == "---":
                return text[i + 1:]
    return text


def classify_rule_file(path):
    """Pointer if short and mostly says 'read X'; otherwise a full rules file."""
    body = [l for l in body_lines(path) if l.strip()]
    return "pointer" if len(body) <= 8 else "rules"


def prose(path):
    """File text with fenced and inline code removed (examples are not real links)."""
    text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8", errors="ignore"), flags=re.S)
    return re.sub(r"`[^`]*`", "", text)


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def engine_profiles():
    """Profile name -> repo block body, as shipped in references/profiles/."""
    found = {}
    for path in sorted((ENGINE / "references" / "profiles").glob("*.md")):
        for name, _, body in PROFILE.findall(path.read_text(encoding="utf-8")):
            found[name] = body
    return found


def check_engine():
    """The always-loaded budget and profile block shas, on the engine's own templates."""
    errors = []
    templates = ENGINE / "assets" / "templates"
    core = (templates / "core.md").read_text(encoding="utf-8").splitlines()
    repo = (templates / "rules.md").read_text(encoding="utf-8").splitlines()
    if len(core) > CORE_BUDGET:
        errors.append(f"core.md: {len(core)} lines, budget {CORE_BUDGET}")
    if len(core) + len(repo) > ALWAYS_LOADED_BUDGET:
        errors.append(f"core.md + rules.md: {len(core) + len(repo)} lines, budget {ALWAYS_LOADED_BUDGET}")
    for path in sorted((ENGINE / "references" / "profiles").glob("*.md")):
        blocks = PROFILE.findall(path.read_text(encoding="utf-8"))
        if len(blocks) != 1:
            errors.append(f"{path.name}: expected one profile block, found {len(blocks)}")
        for name, digest, body in blocks:
            if digest != sha(body):
                errors.append(f"{path.name}: block sha={digest}, content sha is {sha(body)}")
    return errors, []


def check_profile(project, rule_files, state_text):
    """Profile blocks are copied verbatim: the marker sha matches the text and the engine's profile."""
    errors, shipped, present = [], engine_profiles(), set()
    for rel in rule_files:
        for name, digest, body in PROFILE.findall((project / rel).read_text(encoding="utf-8")):
            present.add(name)
            if name not in shipped:
                errors.append(f"{rel}: unknown profile block '{name}'")
            elif digest != sha(body):
                errors.append(f"{rel}: profile block '{name}' was edited by hand (sha={digest}, text {sha(body)})")
            elif body != shipped[name]:
                errors.append(f"{rel}: profile block '{name}' differs from references/profiles (sha {sha(body)} "
                              f"vs {sha(shipped[name])}); copy it verbatim")
    named = re.search(r"^- Domain profile:(.*)$", state_text, re.M)
    for name in shipped:
        if named and re.search(rf"\b{re.escape(name)}\b", named[1]) and name not in present:
            errors.append(f"state.md names profile '{name}' but no rules file has its block")
    return errors


def check(project, skip_skills):
    project = Path(project).resolve()
    errors, warnings = [], []

    state = project / ".lab-forge" / "state.md"
    owned = None
    state_text = state.read_text(encoding="utf-8") if state.exists() else ""
    if state.exists():
        owned = set(re.findall(r"^\|\s*([^|\s][^|]*?)\s*\|", state.read_text(encoding="utf-8"),
                               flags=re.M)) - {"Path"}
        if len(lines(state)) > BUDGET["state"]:
            errors.append(f".lab-forge/state.md over {BUDGET['state']} lines")
    else:
        warnings.append("no .lab-forge/state.md - checking all agent files, ownership unknown")

    def is_owned(rel):
        return owned is None or str(rel).replace("\\", "/") in owned

    rule_files = []
    real_paths = {}
    for rel in CANONICAL + POINTERS_EXTRA:
        path = project / rel
        if not path.exists() or not is_owned(rel):
            continue
        real = path.resolve()
        if real in real_paths:
            warnings.append(f"{rel} is a symlink to {real_paths[real]} - fine, counted once")
            continue
        real_paths[real] = rel
        kind = classify_rule_file(path)
        rule_files.append((rel, kind))
        n = (len([l for l in body_lines(path) if l.strip()]) if kind == "pointer"
             else len(lines(path)))
        if n > BUDGET[kind]:
            errors.append(f"{rel}: {n} lines, budget for {kind} is {BUDGET[kind]}")

    errors += check_profile(project, [r for r, _ in rule_files], state_text)

    full = [r for r, k in rule_files if k == "rules"]
    if len(full) > 1:
        errors.append(f"more than one full rules file (drift risk): {full}")

    seen = defaultdict(set)
    for rel, kind in rule_files:
        if kind == "pointer":
            continue
        for l in lines(project / rel):
            norm = l.strip().lower()
            if len(norm) > 40:
                seen[norm].add(rel)
    dups = [l for l, files in seen.items() if len(files) > 1]  # only across full files
    if dups:
        errors.append(f"{len(dups)} rule lines duplicated across files, e.g. '{dups[0][:60]}'")

    for sdir in SKILL_DIRS:
        for skill in sorted((project / sdir).glob("*/SKILL.md")):
            name = skill.parent.name
            rel = skill.relative_to(project)
            if name in skip_skills or not is_owned(rel):
                continue
            text = lines(skill)
            head = "\n".join(text[:10])
            if not re.search(r"^name:\s*\S", head, re.M):
                errors.append(f"{rel}: missing name in frontmatter")
            if not re.search(r"^description:\s*\S", head, re.M):
                errors.append(f"{rel}: missing description in frontmatter")
            if len(text) > BUDGET["skill"]:
                errors.append(f"{rel}: {len(text)} lines, budget {BUDGET['skill']}")
            if "{{" in "\n".join(text):
                errors.append(f"{rel}: unfilled template placeholder")

    for pattern in COMMAND_GLOBS:
        for cmd in project.glob(pattern):
            rel = cmd.relative_to(project)
            if is_owned(rel) and len(lines(cmd)) > BUDGET["command"]:
                errors.append(f"{rel}: over {BUDGET['command']} lines")

    checked = [project / r for r, _ in rule_files]
    for sdir in SKILL_DIRS:
        checked += [p for p in (project / sdir).glob("*/SKILL.md") if p.parent.name not in skip_skills]
    for path in checked:
        for target in LINK.findall(prose(path)):
            if target.startswith(("http://", "https://", "mailto:", "mdc:")):
                target = target[4:] if target.startswith("mdc:") else None
                if target is None:
                    continue
            resolved = (path.parent / target).resolve()
            alt = (project / target).resolve()
            if not resolved.exists() and not alt.exists():
                errors.append(f"{path.relative_to(project)}: broken link -> {target}")
        if "{{" in prose(path):
            errors.append(f"{path.relative_to(project)}: unfilled template placeholder")

    return sorted(set(errors)), warnings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project", nargs="?")
    parser.add_argument("--engine", action="store_true", help="check the engine's templates and profiles")
    parser.add_argument("--skip-skill", nargs="*", default=[],
                        help="bundled skills installed as-is, not subject to budgets")
    args = parser.parse_args()
    if not args.engine and not args.project:
        parser.error("give a project or --engine")
    errors, warnings = check_engine() if args.engine else check(args.project, set(args.skip_skill))
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"FAIL  {e}")
    print("OK" if not errors else f"{len(errors)} problem(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
