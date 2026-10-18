"""Routing v3: headless A/B with native subagents, the native Stop hook and real billing (JEB-1892).

    python bench/routing/headless.py run --out /tmp/rv3      # prepare, P0 once per case+rep, routing on, P1+P2
    python bench/routing/headless.py report --out /tmp/rv3   # v3 table from sessions.tsv / steps.tsv

Arms `fixed` and `routed` share one lab-forge deploy: P0 runs once in the fixed workspace, then it is copied into
the routed one (paths rewritten) and `tune.py routing on` runs in the routed HOME. P1 and P2 are real `claude -p`
sessions on the main model with `--output-format stream-json --include-hook-events`, so subagents start from
HOME/.claude/agents/*.md and the Stop/SubagentStop hook fires from HOME/.claude/settings.json. Cost is the
result's `total_cost_usd` and `modelUsage`; the raw stream of every session stays in logs/<ws>/<step>.stream.jsonl.
"""

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import threading
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROUTING = Path(__file__).resolve().parent
BENCH = ROUTING.parent
sys.path.insert(0, str(BENCH))
import bench

AGENTS = ROUTING.parent.parent / "skills" / "lab-forge" / "assets" / "routing" / "agents"
SESSIONS = ("ws", "case", "arm", "rep", "step", "model", "input", "output", "cache_read", "cache_write", "cost_usd")
STEPS = (
    "ws",
    "case",
    "arm",
    "rep",
    "step",
    "solved",
    "cost_usd",
    "turns",
    "ms",
    "agents",
    "agent_models",
    "frontmatter_ok",
    "escalations",
    "stop_blocks",
    "subagent_stop_blocks",
    "error",
)
lock = threading.Lock()


def frontmatter_models():
    """Agent name -> model alias from the routing agents' frontmatter (sonnet, haiku, ...)."""
    out = {}
    for path in AGENTS.glob("*.md"):
        found = re.search(r"^model:\s*(\S+)", path.read_text(), flags=re.MULTILINE)
        out[path.stem] = found[1] if found else None
    return out


def session(prompt, cwd, home, model, stream_file, add_dir=None, timeout=3600):
    """One fresh headless session; returns the result event and the parsed stream."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE")} | {"HOME": str(home)}
    if "CLAUDE_CODE_OAUTH_TOKEN" in os.environ:
        env["CLAUDE_CODE_OAUTH_TOKEN"] = os.environ["CLAUDE_CODE_OAUTH_TOKEN"]
    cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose", "--include-hook-events"]
    cmd += ["--permission-mode", "bypassPermissions", "--model", model]
    cmd += ["--add-dir", str(add_dir)] if add_dir else []
    stream_file.parent.mkdir(parents=True, exist_ok=True)
    with open(stream_file, "w") as fh:
        try:
            subprocess.run(
                cmd,
                cwd=cwd,
                env=env,
                stdout=fh,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            pass
    events = []
    for line in stream_file.read_text().splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            continue
    result = next((e for e in reversed(events) if e.get("type") == "result"), None)
    return result, events


def delegation(events):
    """Native subagent calls, the models they ran on, escalations and hook blocks, from one stream."""
    calls, models = {}, defaultdict(set)
    escalations = stop_blocks = sub_blocks = 0
    for e in events:
        msg = e.get("message") if isinstance(e.get("message"), dict) else {}
        content = msg.get("content") if isinstance(msg.get("content"), list) else []
        if e.get("type") == "assistant":
            parent = e.get("parent_tool_use_id")
            if parent and parent in calls and msg.get("model"):
                models[calls[parent]].add(msg["model"])
            for c in content:
                if c.get("type") == "tool_use" and c.get("name") in ("Agent", "Task"):
                    calls[c["id"]] = (c.get("input") or {}).get("subagent_type") or "general-purpose"
        if e.get("type") == "user" and not e.get("parent_tool_use_id"):
            for c in content:
                if c.get("type") == "tool_result" and c.get("tool_use_id") in calls:
                    text = json.dumps(c.get("content"))
                    escalations += "ESCALATE" in text
        if e.get("type") == "system" and e.get("subtype") == "hook_response" and '"block"' in (e.get("stdout") or ""):
            if e.get("hook_event") == "Stop":
                stop_blocks += 1
            elif e.get("hook_event") == "SubagentStop":
                sub_blocks += 1
    return Counter(calls.values()), {k: sorted(v) for k, v in models.items()}, escalations, stop_blocks, sub_blocks


def append(path, fields, row):
    with lock:
        new = not path.exists()
        with open(path, "a", newline="") as fh:
            w = csv.DictWriter(fh, fields, delimiter="\t", extrasaction="ignore")
            if new:
                w.writeheader()
            w.writerow(row)


def run_step(b, ws, step, model, add_dir=None):
    st = b.state(ws)
    stream = b.out / "logs" / ws / f"{step['id']}.stream.jsonl"
    for attempt in range(3):
        result, events = session(
            b.prompt(ws, step, "claude"), b.out / "ws" / ws, b.out / "home" / ws, model, stream, add_dir
        )
        if result and (result.get("total_cost_usd") or not result.get("is_error")):
            break
        shutil.copy(stream, stream.with_suffix(f".failed{attempt}.jsonl"))
        print(ws, step["id"], "no work done, retry", attempt + 1, flush=True)
    result = result or {"is_error": True, "result": "no result event", "modelUsage": {}}
    usage = result.get("modelUsage") or {}
    tokens = sum(
        u.get(k, 0)
        for u in usage.values()
        for k in ("inputTokens", "outputTokens", "cacheReadInputTokens", "cacheCreationInputTokens")
    )
    cost = result.get("total_cost_usd")
    m = b.record(
        ws,
        step["id"],
        tokens,
        result.get("num_turns", 0),
        result.get("duration_ms", 0),
        result.get("result") or "",
        cost,
    )
    base = {"ws": ws, "case": st["case"], "arm": st["arm"], "rep": st["rep"], "step": step["id"]}
    for name, u in usage.items():
        append(
            b.out / "sessions.tsv",
            SESSIONS,
            base
            | {
                "model": name,
                "input": u.get("inputTokens", 0),
                "output": u.get("outputTokens", 0),
                "cache_read": u.get("cacheReadInputTokens", 0),
                "cache_write": u.get("cacheCreationInputTokens", 0),
                "cost_usd": u.get("costUSD", 0),
            },
        )
    agents, models, esc, stops, subs = delegation(events)
    want = frontmatter_models()
    ok = all(any(want[a] in mdl for mdl in models.get(a, [])) for a in agents if a in want)
    append(
        b.out / "steps.tsv",
        STEPS,
        base
        | {
            "solved": m.get("solved"),
            "cost_usd": cost,
            "turns": result.get("num_turns"),
            "ms": result.get("duration_ms"),
            "agents": json.dumps(dict(agents)),
            "agent_models": json.dumps(models),
            "frontmatter_ok": ok,
            "escalations": esc,
            "stop_blocks": stops,
            "subagent_stop_blocks": subs,
            "error": result.get("result", "")[:200] if result.get("is_error") else "",
        },
    )
    print(ws, step["id"], f"${cost}", dict(agents), "solved" if m.get("solved") else "unsolved", flush=True)


def rewrite_tree(root, old, new):
    """Replace `old` with `new` in every text file and path under root (symlinks and .venv/.git left alone)."""
    for path in sorted(root.rglob("*"), key=lambda p: -len(p.parts)):
        rel = path.relative_to(root).parts
        if ".venv" in rel or ".git" in rel or path.is_symlink():
            continue
        if path.is_file():
            try:
                text = path.read_text()
            except (UnicodeDecodeError, OSError):
                text = None
            if text and old in text:
                path.write_text(text.replace(old, new))
        if old in path.name:
            path.rename(path.with_name(path.name.replace(old, new)))


def clone_deploy(b, src, dst):
    """Copy the fixed arm's P0 result (repo with .git, and HOME) into the routed workspace, then record P0."""
    out = b.out
    for kind in ("ws", "home"):
        target = out / kind / dst
        for p in list(target.iterdir()):
            if p.name != ".venv":
                shutil.rmtree(p) if p.is_dir() and not p.is_symlink() else p.unlink()
        for p in (out / kind / src).iterdir():
            if p.name == ".venv":
                continue
            to = target / p.name
            shutil.copytree(p, to, symlinks=True) if p.is_dir() and not p.is_symlink() else shutil.copy2(
                p, to, follow_symlinks=False
            )
    for old, new in (
        (str(out / "ws" / src), str(out / "ws" / dst)),
        (str(out / "home" / src), str(out / "home" / dst)),
        ("/skills/fixed/", "/skills/routed/"),
        (src, dst),
    ):
        rewrite_tree(out / "home" / dst, old, new)
    leaks = bench.sh(
        ["grep", "-rl", "--exclude-dir=.venv", "--exclude-dir=.git", src, str(out / "ws" / dst)], check=False
    ).stdout.split()
    src_st, dst_st = b.state(src), b.state(dst)
    dst_st["head"] = bench.git(out / "ws" / dst, "rev-parse", "HEAD").strip()
    dst_st["base_tree"] = src_st["base_tree"]
    dst_st["steps"]["P0"] = src_st["steps"]["P0"] | {"copied_from": src, "path_leaks": leaks}
    dst_st["order"] = ["P0"]
    b.save(dst, dst_st)
    for f in (out / "logs" / src).glob("P0.*"):
        (out / "logs" / dst).mkdir(parents=True, exist_ok=True)
        shutil.copy(f, out / "logs" / dst / f.name)


def routing_on(b, ws):
    home, repo = b.out / "home" / ws, b.out / "ws" / ws
    tune = Path(b.cfg["arms"]["routed"]) / "scripts" / "tune.py"
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE")} | {"HOME": str(home)}
    env.pop("LAB_FORGE_HOME", None)
    res = bench.sh([sys.executable, str(tune), "routing", "on", "--repo", str(repo)], cwd=repo, env=env)
    (b.out / "logs" / ws / "routing-on.txt").write_text(res.stdout + res.stderr)


def run(args):
    out = Path(args.out).resolve()
    skill = str(BENCH.parent / "skills" / "lab-forge")
    if not (out / "bench.json").exists():
        cmd = [
            sys.executable,
            str(BENCH / "bench.py"),
            "prepare",
            "--out",
            str(out),
            "--reps",
            str(args.reps),
            "--arm",
            f"fixed={skill}",
            "--arm",
            f"routed={skill}",
            "--cases",
            *args.cases,
        ]
        subprocess.run(cmd, check=True)
    b = bench.Bench(out)
    uv_env = {**os.environ, "UV_CACHE_DIR": os.environ.get("UV_CACHE_DIR", str(out / ".uvcache"))}
    for ws in b.workspaces():  # known env gap: optuna's tests import fakeredis
        if b.state(ws)["case"] == "optuna":
            py = out / "ws" / ws / ".venv" / "bin" / "python"
            bench.sh(["uv", "pip", "install", "-q", "-p", str(py), "fakeredis"], env=uv_env)
    pairs = [
        (b.ws_name(c, "fixed", r), b.ws_name(c, "routed", r)) for c in b.cases for r in range(1, b.cfg["reps"] + 1)
    ]

    def deploy(pair):
        fixed, routed = pair
        if "P0" not in b.state(fixed)["steps"]:
            run_step(b, fixed, {"id": "P0", "kind": "deploy"}, args.deploy_model, b.cfg["arms"]["fixed"])
        if "P0" not in b.state(routed)["steps"]:
            clone_deploy(b, fixed, routed)
            routing_on(b, routed)

    with ThreadPoolExecutor(args.jobs) as pool:
        list(pool.map(deploy, pairs))
    for sid in ("P1", "P2"):
        todo = [
            (ws, s)
            for ws in b.workspaces()
            for s in b.steps(ws)[1]
            if s["id"] == sid and sid not in b.state(ws)["steps"]
        ]
        with ThreadPoolExecutor(args.jobs) as pool:
            list(pool.map(lambda item: run_step(b, item[0], item[1], args.model), todo))


def report(args):
    out = Path(args.out).resolve()
    rows, sess = (
        [r for r in csv.DictReader((out / name).open(), delimiter="\t") if r["step"] in ("P1", "P2")]
        for name in ("steps.tsv", "sessions.tsv")
    )
    for r in rows:  # solved comes from the bench state, so `bench.py recheck` is reflected
        r["solved"] = str(json.loads((out / "state" / f"{r['ws']}.json").read_text())["steps"][r["step"]]["solved"])
    arms = sorted({r["arm"] for r in rows})
    agg = {}
    for a in arms:
        rs = [r for r in rows if r["arm"] == a]
        solved = sum(r["solved"] == "True" for r in rs)
        cost = sum(float(r["cost_usd"] or 0) for r in rs)
        tiers = Counter()
        for r in rs:
            tiers.update(json.loads(r["agents"]))
        agg[a] = {
            "steps": len(rs),
            "solved": solved,
            "cost": cost,
            "per": cost / max(solved, 1),
            "esc": sum(int(r["escalations"]) for r in rs),
            "stop": sum(int(r["stop_blocks"]) for r in rs),
            "sub": sum(int(r["subagent_stop_blocks"]) for r in rs),
            "tiers": tiers,
            "delegated": sum(r["agents"] != "{}" for r in rs),
            "fm_bad": sum(r["frontmatter_ok"] != "True" for r in rs),
            "min": sum(float(r["ms"] or 0) for r in rs) / 60000,
        }
    names = sorted({t for a in arms for t in agg[a]["tiers"]})
    lines = ["| Metric | " + " | ".join(arms) + " |", "|---|" + "---|" * len(arms)]

    def row(label, fn):
        lines.append(f"| {label} | " + " | ".join(fn(agg[a]) for a in arms) + " |")

    row("Solved, hidden checks", lambda g: f"{g['solved']}/{g['steps']}")
    row("Real cost, `total_cost_usd`, $", lambda g: f"{g['cost']:.2f}")
    row("Cost per solved step, $", lambda g: f"{g['per']:.3f}")
    row("Steps with a native subagent call", lambda g: f"{g['delegated']}/{g['steps']}")
    for n in names:
        row(f"Native `{n}` calls", lambda g, n=n: str(g["tiers"].get(n, 0)))
    row("Subagent model differs from frontmatter (steps)", lambda g: str(g["fm_bad"]))
    row("Escalations (`ESCALATE` in a subagent report)", lambda g: str(g["esc"]))
    row("Stop hook blocks / SubagentStop blocks", lambda g: f"{g['stop']} / {g['sub']}")
    row("Session time, min", lambda g: f"{g['min']:.1f}")
    split = defaultdict(lambda: defaultdict(float))
    for r in sess:
        split[r["arm"]][r["model"]] += float(r["cost_usd"])
    lines += ["", "| Arm | " + " | ".join(sorted({m for a in split for m in split[a]})) + " |"]
    models = sorted({m for a in split for m in split[a]})
    lines += ["|---|" + "---|" * len(models)]
    lines += [f"| {a} | " + " | ".join(f"${split[a].get(m, 0):.2f}" for m in models) + " |" for a in arms]
    fixed = {(r["case"], r["rep"], r["step"]): float(r["cost_usd"] or 0) for r in rows if r["arm"] == "fixed"}
    pairs = defaultdict(lambda: [0, 0.0, 0.0])
    for r in rows:
        if r["arm"] == "routed":
            agents = json.loads(r["agents"])
            tier = "L/XL (main + verifier)" if "verifier" in agents else (next(iter(agents), "none"))
            pair = pairs[tier]
            pair[0] += 1
            pair[1] += fixed.get((r["case"], r["rep"], r["step"]), 0)
            pair[2] += float(r["cost_usd"] or 0)
    lines += ["", "| Tier picked in routed | Steps | fixed, $ | routed, $ | Diff |", "|---|---|---|---|---|"]
    lines += [
        f"| {t} | {n} | {f:.2f} | {r:.2f} | {(r / f - 1) * 100:+.0f}% |" for t, (n, f, r) in sorted(pairs.items())
    ]
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=["run", "report"])
    p.add_argument("--out", required=True)
    p.add_argument("--cases", nargs="*", default=["churn", "rparse", "optuna", "encoders"])
    p.add_argument("--reps", type=int, default=2)
    p.add_argument("--jobs", type=int, default=8)
    p.add_argument("--model", default="claude-opus-5-5")
    p.add_argument("--deploy-model", default="claude-sonnet-5-5")
    args = p.parse_args()
    if args.cmd == "run":
        run(args)
    print(report(args))


if __name__ == "__main__":
    main()
