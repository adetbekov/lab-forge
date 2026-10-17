"""Build routed-arm prompts: triage | worker TIER | verify | escalate TIER. Usage: rprompt.py OUT WS STEP ROLE [TIER]"""

import re
import sys
from pathlib import Path

out, ws, step, role = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
tier = sys.argv[5] if len(sys.argv) > 5 else None
base = (out / "prompts" / f"{ws}__{step}.md").read_text()
reply = out / "replies" / f"{ws}__{step}.md"
home, proj = out / "home" / ws, out / "ws" / ws
request = re.search(r'User request:\n"(.*)"\n', base, re.DOTALL)[1]
if role == "triage":
    body = base.rsplit("Finally,", 1)[0] + (
        f"\nThis session is the MAIN thread with lab-forge routing on. Do the session start, then follow skill `triage` "
        f"(HOME/.claude/skills/triage/SKILL.md; `~` means HOME) sections 1-2 only: pick the tier and write the handoff. "
        f"Subagents are launched by the experiment harness, not by you. Do NOT edit, run or commit anything; read only what "
        f"you need to decide (be quick). Reply exactly: line 1 `TIER: quick|build|deep`, then a handoff note of at most 5 lines. "
        f"Write that reply verbatim to {out}/replies/{ws}__{step}.triage.md and return it."
    )
elif role == "worker":
    hand = (out / "replies" / f"{ws}__{step}.triage.md").read_text()
    body = (
        f"You run as the `{tier}` subagent: your instructions are the body of HOME/.claude/agents/{tier}.md "
        f"(read it first and follow it). Do not run skill `triage` again: it already ran. Handoff from the main thread:\n"
        f"{hand}\n\n" + base
    )
elif role == "escalate":
    ev = (out / "replies" / f"{ws}__{step}.verify.md").read_text()
    prev = reply.read_text() if reply.exists() else ""
    body = (
        f"You run as the `{tier}` subagent: your instructions are the body of HOME/.claude/agents/{tier}.md "
        f"(read it first and follow it). Escalation: a lower tier already worked on this task in PROJECT (its changes are "
        f"in the tree) and verification failed. Fix it. Verifier evidence:\n{ev}\n\nLower tier's report:\n{prev}\n\n"
        + base
    )
elif role == "verify":
    body = (
        f"You run as the `verifier` subagent in a Claude Code session. PROJECT={proj}, HOME={home}. Your instructions are "
        f"the body of HOME/.claude/agents/verifier.md: read it first and follow it. Python = PROJECT/.venv/bin/python. "
        f"Work only inside PROJECT (read-only; you may create temp files only under /tmp). No subagents, no network, no "
        f'Skill tool.\n\nTask given to the worker:\n"{request}"\n\nWorker report:\n{reply.read_text()}\n\n'
        f"Write your reply verbatim to {out}/replies/{ws}__{step}.verify.md and return it."
    )
dest = out / "prompts" / f"{ws}__{step}.{role}{'-' + tier if tier else ''}.md"
dest.write_text(body)
print(dest)
