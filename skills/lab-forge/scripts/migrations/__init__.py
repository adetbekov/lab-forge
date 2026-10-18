"""What lab-forge v0.1-v0.3 installed, and pure functions that move those files to the current format.

v0.1 (b54d002) and v0.2 (06dca67) wrote the whole rule set into the repo rules file, with no markers, plus a
text pointer in the other agent files. v0.3 (8f402c6, 8417b6c) added ~/.lab-forge/AGENTS.md and managed blocks
`<!-- lab-forge:begin sha=… -->` with no layer name. The templates sit next to this file, so no git history
is needed. Stdlib only.
"""

import difflib
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
RULES = [HERE / f"v0.{n}-rules.md" for n in (1, 2, 3)]
GLOBAL_RULES = [HERE / "v0.3-global-8f402c6.md", HERE / "v0.3-global-8417b6c.md"]
LEGACY_MARKER = re.compile(r"<!-- lab-forge:begin sha=")  # v0.3: a block with no layer and no version
POINTER = re.compile(
    r"Read (\S+) in the repository root before any action\. It holds the\s+canonical rules, task sizes and "
    r"the skills list for every agent here\. Not\s+duplicated in this file on purpose, to avoid drift\.\n?"
)
# Sections whose rules now live in the global core and defaults. Lines that only fill a placeholder there
# (patterns, params file, commands) are project facts and stay, except where the section only restated them.
RULE_SECTIONS = {
    "Size the task first",
    "How code is written here",
    'Check before saying "done"',
    "Talking to the user",
    "Delivery",
    "Skills - use them when the context matches",
    "Done means",
}
RESTATED = {"Done means", "Skills - use them when the context matches"}
INTRO = "Project facts for every agent. How to work comes from the global rules; do not repeat them here."
FACTS_HEADING = re.compile(r"^# Rules for AI agents - (.+)$", re.M)
BLOCK = re.compile(r"<!-- lab-forge:begin.*?<!-- lab-forge:end -->", re.S)


def _templates():
    """(regex, has a placeholder) for every non-heading line of the v0.1-v0.3 repo templates."""
    found = {}
    for path in RULES:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                parts = re.split(r"\{\{\w+\}\}", line)
                found[line] = (re.compile(".+?".join(map(re.escape, parts)) + "$"), len(parts) > 1)
    return sorted(found.values(), key=lambda t: t[1])  # an exact template line wins over a placeholder match


def _sections(lines):
    """[(heading or None, [lines])], split at `## ` headings."""
    out = [(None, [])]
    for line in lines:
        if line.startswith("## "):
            out.append((line[3:].strip(), [line]))
        else:
            out[-1][1].append(line)
    return out


def repo_rules(text):
    """A v0.1-v0.3 repo rules file without the rules the core now holds; facts and hand-written lines stay."""
    templates, blocks = _templates(), BLOCK.findall(text)
    text = BLOCK.sub("\0", text)  # managed blocks pass through untouched
    kept = []
    for heading, lines in _sections(text.splitlines()):
        body = []
        for line in lines[1:] if heading else lines:
            hit = next((has for rx, has in templates if rx.match(line.strip())), None)
            if hit is None or (hit and heading not in RESTATED):
                body.append(line)
        if heading in RULE_SECTIONS | {"Overrides"} and not any(line.strip() for line in body):
            continue
        kept += ([lines[0]] if heading else []) + body
    text = "\n".join(kept)
    text = FACTS_HEADING.sub(r"# \1", text)
    if INTRO not in text:
        text = re.sub(r"\A(# .+\n)\n*", rf"\1\n{INTRO}\n\n", text) if text.startswith("# ") else text
    text = re.sub(r"\n{3,}", "\n\n", text).rstrip("\n") + "\n"
    return re.sub("\0", lambda _: blocks.pop(0), text)


def pointer(text):
    """The v0.1 text pointer makes the agent read the file with a tool each session; an import is free."""
    return POINTER.sub(lambda m: f"@{m[1]}\n", text)


def is_rules(text):
    """A v0.1-v0.3 rules file: the v0.1/v0.2 heading or the v0.3 facts intro."""
    return bool(FACTS_HEADING.search(text)) or "Project facts for every agent. How to work (branches" in text


def global_rules(canary):
    """~/.lab-forge/AGENTS.md as each v0.3 release rendered it."""
    return [p.read_text(encoding="utf-8").replace("{{canary}}", canary) for p in GLOBAL_RULES]


def closest(text, candidates):
    """The candidate the text most likely started from: the user's edits are the smallest diff to it."""
    return max(candidates, key=lambda c: difflib.SequenceMatcher(None, c, text, autojunk=False).ratio())
