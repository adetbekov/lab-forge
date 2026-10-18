"""Model-mix A/B on top of bench.py: 4 arms that differ only in which model plays which role.

    mix.py prepare OUT                      # bench.py prepare with the 4 arms, 1 repeat
    mix.py copy-p0 OUT                      # after P0 ran in the `opus` arm: copy it to the other arms, install layouts
    mix.py prompt OUT WS STEP ROLE          # role: main | planner | coder | relay-planner | relay-coder
    mix.py log OUT WS STEP ROLE MODEL TOKENS TOOLS
    mix.py record OUT WS STEP               # sum the step's sessions and record it in bench state
    mix.py pack OUT                         # blind review prompts, every arm against `opus`
    mix.py cost OUT                         # cost per arm and role (sessions.tsv)

Arms (main = the user's session: it takes the task, stores tune, answers questions):
  mix1   Sonnet main, Opus coder subagent
  opus   Opus for everything (baseline)
  sonnet Sonnet for everything
  mix4   Sonnet main, Opus planner subagent (read-only), Sonnet coder subagent

The Agent tool runs every session; subagents are separate sessions the harness (the driver agent) starts.
A main session that delegates is continued by a relay session that gets its earlier reply and the report.
"""

import csv
import json
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent
sys.path.insert(0, str(BENCH))
from bench import Bench  # noqa: E402

ARMS = {
    "mix1": {"main": "sonnet", "coder": "opus"},
    "opus": {"main": "opus"},
    "sonnet": {"main": "sonnet"},
    "mix4": {"main": "sonnet", "planner": "opus", "coder": "sonnet"},
}
BASE_ARM = "opus"
LAYOUT = {
    "mix1": "Every task that edits code goes to the `coder` subagent (HOME/.claude/agents/coder.md). Write it a "
    "handoff (files, constraints, what must not change), then check its report and reply to the user.",
    "mix4": "Every task that edits code goes first to the `planner` subagent (HOME/.claude/agents/planner.md, "
    "read-only), which writes the plan, then to the `coder` subagent (HOME/.claude/agents/coder.md) with that plan. "
    "Write each a handoff (files, constraints, what must not change), then check the coder's report and reply to "
    "the user.",
}
LAYOUT_TAIL = " Questions, preferences and settings you handle yourself, without subagents."
SUB = (
    "Subagents in this experiment: the harness runs them for you. When your rules hand the task to a subagent, do "
    "not edit or run anything for the task: reply exactly `DELEGATE: <agent>` on line 1, then a handoff note of at "
    "most 5 lines (files, constraints, what must not change), write that reply to {file} and stop. The subagent's "
    "report will come back to you in a follow-up message."
)


def sh(*cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True).stdout


def rewrite(root, old, new, skip=()):
    for p in root.rglob("*"):
        if p.is_symlink() or not p.is_file() or any(part in skip for part in p.relative_to(root).parts):
            continue
        try:
            text = p.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        if old in text:
            p.write_text(text.replace(old, new))


def prepare(out):
    skill = str(BENCH.parent / "skills" / "lab-forge")
    args = [sys.executable, str(BENCH / "bench.py"), "prepare", "--out", out, "--reps", "1"]
    for arm in ARMS:
        args += ["--arm", f"{arm}={skill}"]
    subprocess.run(args, check=True)


def copy_p0(b):
    """P0 is the same skill deploy in every arm: run it once (opus arm), copy the result so only the models differ."""
    for case in b.cases:
        for rep in range(1, b.cfg["reps"] + 1):
            src = b.ws_name(case, BASE_ARM, rep)
            sst = b.state(src)
            assert sst["order"] == ["P0"], f"{src}: P0 must be the only recorded step"
            for arm in ARMS:
                if arm == BASE_ARM:
                    continue
                dst = b.ws_name(case, arm, rep)
                droot, sroot = b.out / "ws" / dst, b.out / "ws" / src
                for p in droot.iterdir():
                    if p.name != ".venv":
                        shutil.rmtree(p) if p.is_dir() and not p.is_symlink() else p.unlink()
                for p in sroot.iterdir():
                    if p.name != ".venv":
                        if p.is_dir() and not p.is_symlink():
                            shutil.copytree(p, droot / p.name, symlinks=True)
                        else:
                            shutil.copy2(p, droot / p.name, follow_symlinks=False)
                shutil.rmtree(b.out / "home" / dst)
                shutil.copytree(b.out / "home" / src, b.out / "home" / dst, symlinks=True)
                for root in (droot, b.out / "home" / dst):
                    rewrite(root, src, dst, skip=(".venv", ".git"))
                    rewrite(root, f"/skills/{BASE_ARM}/", f"/skills/{arm}/", skip=(".venv", ".git"))
                dirty = sh("git", "-C", str(droot), "status", "--porcelain").strip()
                if dirty:
                    print(f"warning {dst}: tree differs from the P0 commit after path rewrite:\n{dirty}")
                st = b.state(dst)
                st |= {k: sst[k] for k in ("order", "steps", "head", "base_tree")}
                b.save(dst, json.loads(json.dumps(st)))
                logs = b.out / "logs" / dst
                shutil.rmtree(logs, ignore_errors=True)
                shutil.copytree(b.out / "logs" / src, logs)
                if arm in LAYOUT:
                    install_layout(b.out / "home" / dst, arm)
                print("copied P0", src, "->", dst)


def install_layout(home, arm):
    agents = home / ".claude" / "agents"
    agents.mkdir(parents=True, exist_ok=True)
    for role in ("planner", "coder"):
        if role in ARMS[arm]:
            text = (HERE / "agents" / f"{role}.md").read_text().replace("{model}", ARMS[arm][role])
            (agents / f"{role}.md").write_text(text)
    rules = home / ".claude" / "CLAUDE.md"
    old = rules.read_text() if rules.exists() else ""
    rules.write_text(old.rstrip() + "\n\n## Model layout\n\n" + LAYOUT[arm] + LAYOUT_TAIL + "\n")


def prompt(b, ws, step, role):
    out = b.out
    base = (out / "prompts" / f"{ws}__{step}.md").read_text()
    replies = out / "replies"
    main = base.replace("No multica CLI, no subagents,", "No multica CLI,")

    def reply(name):
        return (replies / f"{ws}__{step}.{name}.md").read_text()

    def as_sub(name, extra):
        head = (
            f"You run as the `{name}` subagent: your instructions are the body of HOME/.claude/agents/{name}.md (read "
            f"it first and follow it; skip the 'Model layout' section of HOME/.claude/CLAUDE.md, it is for the main "
            f"session).{extra}\n\n"
        )
        return head + base.replace(f"{ws}__{step}.md", f"{ws}__{step}.{name}.md")

    if role == "main":
        body = main + "\n" + SUB.format(file=replies / f"{ws}__{step}.main.md")
    elif role == "planner":
        extra = (
            f" You only plan: do not modify, create or commit anything in PROJECT, whatever the request says.\n"
            f"Handoff from the main session:\n{reply('main')}"
        )
        body = as_sub("planner", extra)
    elif role == "coder":
        last = "main2" if (replies / f"{ws}__{step}.main2.md").exists() else "main"
        extra = f"\nHandoff from the main session:\n{reply(last)}"
        if (replies / f"{ws}__{step}.planner.md").exists():
            extra += f"\n\nPlan from the planner subagent:\n{reply('planner')}"
        body = as_sub("coder", extra)
    elif role in ("relay-planner", "relay-coder"):
        sub = role.split("-")[1]
        two = sub == "coder" and (replies / f"{ws}__{step}.main2.md").exists()
        earlier = reply("main") + (f"\n---\n{reply('main2')}" if two else "")
        resume = (
            "\n\nThis continues your session: session start and your earlier turn are already done (do not redo "
            f"them; re-read a file only if you need it now). Your earlier reply:\n<<<\n{earlier}\n>>>\n"
            f"Subagent `{sub}` finished. Its report:\n<<<\n{reply(sub)}\n>>>\n"
        )
        if sub == "planner":
            resume += (
                "Now hand the task with this plan to `coder`: reply exactly `DELEGATE: coder` on line 1, then a "
                f"handoff note of at most 5 lines, write that reply to {replies / f'{ws}__{step}.main2.md'} and stop. "
                "The harness passes the plan to the coder."
            )
        else:
            resume += (
                "Finish the turn as you normally would. Then reply to the user as the original instructions say "
                f"and write that reply verbatim to {replies / f'{ws}__{step}.md'}."
            )
        body = main + resume
    else:
        sys.exit(f"unknown role {role}")
    dest = out / "prompts" / f"{ws}__{step}.{role}.md"
    dest.write_text(body)
    print(dest)


def log(out, ws, step, role, model, tokens, tools):
    path = Path(out) / "sessions.tsv"
    new = not path.exists()
    with open(path, "a") as f:
        if new:
            f.write("ws\tstep\trole\tmodel\ttokens\ttools\n")
        f.write(f"{ws}\t{step}\t{role}\t{model}\t{tokens}\t{tools}\n")


def sessions(out):
    with open(Path(out) / "sessions.tsv") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def record(out, ws, step):
    rows = [r for r in sessions(out) if r["ws"] == ws and r["step"] == step]
    tokens, tools = sum(int(r["tokens"]) for r in rows), sum(int(r["tools"]) for r in rows)
    args = [sys.executable, str(BENCH / "bench.py"), "record", "--out", out, ws, step]
    subprocess.run(args + ["--tokens", str(tokens), "--tools", str(tools)], check=True)


def pack(b):
    """bench.py packs exactly two arms: build one view per pair (symlinks to the shared run) and pack it."""
    for arm in ARMS:
        if arm == BASE_ARM:
            continue
        pair = b.out / "pairs" / f"{arm}-vs-{BASE_ARM}"
        pair.mkdir(parents=True, exist_ok=True)
        cfg = b.cfg | {"arms": {a: b.cfg["arms"][a] for a in (arm, BASE_ARM)}}
        (pair / "bench.json").write_text(json.dumps(cfg, indent=1))
        for name in ("ws", "home", "src", "state", "logs"):
            if (b.out / name).exists() and not (pair / name).exists():
                (pair / name).symlink_to(b.out / name)
        for p in Bench(pair).pack():
            print(p)


# $/MTok: input, output, cache read, cache write. Same prices and mix as bench/routing/cost.py (JEB-1880).
PRICE = {"opus": (4, 20, 0.20, 5), "sonnet": (2, 10, 0.20, 2.5)}
MIX = (0.02, 0.08, 0.80, 0.10)
BLEND = {m: sum(p * w for p, w in zip(ps, MIX)) for m, ps in PRICE.items()}


def cost(b):
    rows = sessions(b.out)
    by = defaultdict(float)
    for r in rows:
        if r["step"] == "P0":
            continue
        arm = b.state(r["ws"])["arm"]
        usd = int(r["tokens"]) * BLEND[r["model"]] / 1e6
        code = r["step"] in ("P1", "P2")
        by[arm, "all"] += usd
        by[arm, "code"] += usd if code else 0
        by[arm, "tok_code"] += int(r["tokens"]) if code else 0
        by[arm, f"{r['role'].split('-')[0]}:{r['model']}"] += usd if code else 0
    solved = defaultdict(int)
    steps = defaultdict(int)
    for ws in b.workspaces():
        st = b.state(ws)
        for sid in ("P1", "P2"):
            if sid in st["steps"]:
                steps[st["arm"]] += 1
                solved[st["arm"]] += st["steps"][sid]["solved"]
    arms = [a for a in ARMS if steps[a]]
    print("| Metric | " + " | ".join(arms) + " |\n|---|" + "---|" * len(arms))
    print("| Solved, hidden checks | " + " | ".join(f"{solved[a]}/{steps[a]}" for a in arms) + " |")
    print("| Coding tokens, k | " + " | ".join(f"{by[a, 'tok_code'] / 1000:.0f}" for a in arms) + " |")
    print("| Coding cost, $ | " + " | ".join(f"{by[a, 'code']:.2f}" for a in arms) + " |")
    print("| $ per solved step | " + " | ".join(f"{by[a, 'code'] / max(solved[a], 1):.3f}" for a in arms) + " |")
    print("| Cost incl. T and P3, $ | " + " | ".join(f"{by[a, 'all']:.2f}" for a in arms) + " |")
    print()
    for (arm, key), v in sorted(by.items()):
        if ":" in key:
            print(f"{arm} {key}: ${v:.2f}")


def main():
    cmd, out = sys.argv[1], sys.argv[2]
    if cmd == "prepare":
        return prepare(out)
    if cmd == "log":
        return log(out, *sys.argv[3:9])
    if cmd == "record":
        return record(out, *sys.argv[3:5])
    b = Bench(out)
    if cmd == "copy-p0":
        copy_p0(b)
    elif cmd == "prompt":
        prompt(b, *sys.argv[3:6])
    elif cmd == "pack":
        pack(b)
    elif cmd == "cost":
        cost(b)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
