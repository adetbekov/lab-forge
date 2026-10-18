"""Build routed-v2 prompts and follow-up messages. Usage: rprompt.py OUT WS STEP ROLE [TIER]

Roles: main (the user's session, routing rule inline), worker TIER (quick/build subagent), hook (run the
Stop hook, print the block message or nothing), verify (verifier subagent, L/XL only), relay (worker report
back to the main session).
"""

import json
import re
import subprocess
import sys
from pathlib import Path

out, ws, step, role = Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3], sys.argv[4]
tier = sys.argv[5] if len(sys.argv) > 5 else None
base = (out / "prompts" / f"{ws}__{step}.md").read_text()
replies = out / "replies"
home, proj = out / "home" / ws, out / "ws" / ws
request = re.search(r'User request:\n"(.*)"\n', base, re.DOTALL)[1]
SUB = (
    "Subagents in this experiment: the harness runs them for you. If your rules hand the task to a subagent, do "
    "not edit or run anything for the task: reply exactly `DELEGATE: <agent>` on line 1, then a handoff note of at "
    "most 5 lines (files, constraints, what must not change), write that reply to {file} and stop. The subagent's "
    "report will come back to you in a follow-up message. If you do the task yourself, follow the instructions "
    "above as usual; if your rules then call for `verifier`, write your report as instructed, then reply "
    "`DELEGATE: verifier` instead of starting it yourself."
)
if role == "main":
    body = (
        base.replace("No multica CLI, no subagents,", "No multica CLI,")
        + "\n"
        + SUB.format(file=replies / f"{ws}__{step}.main.md")
    )
elif role == "worker":
    hand = (replies / f"{ws}__{step}.main.md").read_text()
    body = (
        f"You run as the `{tier}` subagent: your instructions are the body of HOME/.claude/agents/{tier}.md (read it "
        f"first and follow it; skip HOME/.claude/CLAUDE.md routing rules, they are for the main session). Handoff from "
        f"the main session:\n{hand}\n\n" + base.replace(f"{ws}__{step}.md", f"{ws}__{step}.{tier}.md")
    )
elif role == "hook":
    script = home / ".lab-forge" / "hooks" / "verify_stop.py"
    res = subprocess.run(
        [sys.executable, str(script)],
        check=False,
        input=json.dumps({"cwd": str(proj)}),
        capture_output=True,
        text=True,
        env={"HOME": str(home), "PATH": "/usr/bin:/bin:/usr/local/bin"},
    )
    if res.stdout.strip():
        print(
            "Stop hook (blocked, exit not allowed yet): "
            + json.loads(res.stdout)["reason"]
            + "\nFix it, then reply again exactly as instructed (same reply file)."
        )
    sys.exit(0)
elif role == "verify":
    body = (
        f"You run as the `verifier` subagent in a Claude Code session. PROJECT={proj}, HOME={home}. Your instructions "
        f"are the body of HOME/.claude/agents/verifier.md: read it first and follow it. Python = PROJECT/.venv/bin/python. "
        f"Work only inside PROJECT (read-only; you may create temp files only under /tmp). No subagents, no network, no "
        f'Skill tool.\n\nTask:\n"{request}"\n\nReport of the session that did it:\n'
        f"{next(p for p in (replies / f'{ws}__{step}.md', replies / f'{ws}__{step}.main.md') if p.exists()).read_text()}\n\n"
        f"Write your reply verbatim to {replies}/{ws}__{step}.verify.md and return it."
    )
elif role == "relay":
    print(
        f"Subagent `{tier}` finished. Its report is in {replies / f'{ws}__{step}.{tier}.md'} (read it). Finish the "
        f"turn as you normally would (if it says ESCALATE, the task moves up to you). Then reply to the user as the "
        f"original instructions say and write that reply verbatim to {replies / f'{ws}__{step}.md'}."
    )
    sys.exit(0)
dest = out / "prompts" / f"{ws}__{step}.{role}{'-' + tier if tier else ''}.md"
dest.write_text(body)
print(dest)
