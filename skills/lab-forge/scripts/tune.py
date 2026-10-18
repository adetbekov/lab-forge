"""Write one tune override line, log it, print the diff. Undo reverts the last tune.

Stdlib only. Global overrides live in $LAB_FORGE_HOME/overrides.md (default ~/.lab-forge),
repo overrides in the `## Overrides` section of <repo>/AGENTS.md. At ownership level 0
(no <repo>/.lab-forge/state.md, or it says level 0) nothing is written to the repo: repo lines
go to global overrides with a `[<repo name>]` prefix. Tune never writes CLAUDE.local.md: Claude
reads AGENTS.md through CLAUDE.md, and a local file would split the repo layer in two.

Core rules (C<n>) cannot be tuned: a line that names one, or says the opposite of one (the key phrases
in `<!-- weakens C<n>: ... -->` comments of $LAB_FORGE_HOME/core.md plus WEAKENS below), is refused.
A line with `replaces D<n>` (or P<n>) swaps the earlier override of that rule instead of piling up.

Usage:
    python tune.py add [--scope global|repo] "<line>" [--replace "<old line>"] [--repo DIR]  # scope: repo
    python tune.py undo [--repo DIR]      # a second undo redoes
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / "hooks")]  # the engine's scripts/, or the copy in ~/.lab-forge
from guard import lf_home, on_default_branch  # noqa: E402

SECTION = "## Overrides"
LOG_LINE = re.compile(r"^- (\S+ \S+) tune (global|repo) (\[.*\])$")
CORE_REF = re.compile(r"\bC\d+\b")
REPLACES = re.compile(r"\breplaces ([DP]\d+)\b", re.I)
WEAKENS_NOTE = re.compile(r"<!--\s*weakens\s+(C\d+)\s*:(.*?)-->", re.S)
NEGATION = {"never", "not", "don't", "dont", "no", "avoid"}
WEAKENS = {  # phrases that undo a core rule; core.md may add more. Up to 2 extra words fit between phrase words
    "branch": "commit to main; commit on main; push to main; work on main; commit to master; push to master; "
    "skip the branch",
    "scope": "edit outside the scope; ignore the scope; fix unrelated code",
    "verification": "claim done without; skip verification; skip the check; done without running",
    "methodology": "tune on the test; fit on the test; reuse the validation rows; skip the split",
    "tests": "skip tests; no tests; without tests; tests are optional",
}


def paths(scope, repo):
    if scope == "global":
        return lf_home() / "overrides.md", lf_home() / "state.md"
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


def words(text):
    return re.findall(r"[\w']+", text.lower())


def says(tokens, phrase):
    """True if the phrase words occur in order, at most 2 words apart, and no negation comes just before."""
    want = words(phrase)
    for i, tok in enumerate(tokens):
        if tok != want[0] or NEGATION & set(tokens[max(0, i - 3):i]):
            continue
        at = i
        for w in want[1:]:
            at = next((j for j in range(at + 1, min(at + 4, len(tokens))) if tokens[j] == w), None)
            if at is None:
                break
        else:
            return True
    return False


def weakened_core(line):
    """The core rule the line names or undoes, else None."""
    ref = CORE_REF.search(line)
    if ref:
        return ref[0]
    core = lf_home() / "core.md"
    notes = WEAKENS_NOTE.findall(core.read_text(encoding="utf-8")) if core.exists() else []
    tokens = words(line)
    for rule, phrases in notes + list(WEAKENS.items()):
        if any(p.strip() and says(tokens, p) for p in phrases.split(";")):
            return rule.strip()
    return None


def tag(bullet):
    return re.match(r"(\[[^\]]*\] )?", bullet)[0]


def apply(scope, repo, new, old, ref=None):
    target, state = paths(scope, repo)
    text = target.read_text(encoding="utf-8").splitlines() if target.exists() else []
    text, start, end = section_bounds(text, scope)
    bullets = [line[2:].strip() for line in text[start:end]]
    if new and new in bullets:
        sys.exit(f"already in {target}: {new}")
    if ref and not old:  # one override per D/P rule: the new one takes the old one's place
        same = [b for b in bullets if tag(b) == tag(new) and ref in map(str.upper, REPLACES.findall(b))]
        old = same[0] if same else None
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


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=["add", "undo"])
    parser.add_argument("line", nargs="?")
    parser.add_argument("--scope", choices=["global", "repo"], default="repo")
    parser.add_argument("--replace")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()
    if args.action == "add":
        if not args.line:
            parser.error("add needs a line")
        scope, line, old = args.scope, args.line.strip(), args.replace and args.replace.strip()
        rule = weakened_core(line)
        if rule:
            sys.exit(f"refused: this is core ({rule}); tune cannot weaken it. Ask explicitly in chat if you "
                     "need it for one task.")
        ref = REPLACES.search(line)
        ref = ref and ref[1].upper()
        defaults = lf_home() / "defaults.md"
        if ref and ref[0] == "D" and defaults.exists() and not re.search(rf"\b{ref}\b", defaults.read_text("utf-8")):
            sys.exit(f"refused: no {ref} in {defaults}")
        if scope == "repo" and (repo_level_zero(args.repo) or on_default_branch(args.repo)):
            prefix = f"[{args.repo.resolve().name}] "
            scope, line, old = "global", prefix + line, old and prefix + old
            print("level 0 or default branch: nothing is written to the repo; stored in global overrides")
        apply(scope, args.repo, line, old, ref)
    else:
        scope, (new, old) = last_tune(args.repo)
        apply(scope, args.repo, old, new)


if __name__ == "__main__":
    main()
