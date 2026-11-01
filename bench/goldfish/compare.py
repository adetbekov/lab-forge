"""Compare arms from several bench runs on their coding steps. Stdlib only.

    python bench/goldfish/compare.py --out lfb --runs lfb/runs.tsv bench/results/2026-10-20-sonnet-hard/runs.tsv \
        --arm v041gf --arm v041 --arm baregf --arm bare --arm "opus=bare opus"

`--out` dirs (repeatable) hold the session transcripts in `home/`, which give each arm's subagent share of
tokens (goldfish, EGM reviewers) and how often they ran; arms without transcripts show "—".
"""

import argparse
import csv
import json
from pathlib import Path

USAGE = ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")


def usage_tokens(path):
    seen = {}
    for line in path.read_text().splitlines():
        msg = json.loads(line).get("message") or {}
        if msg.get("usage"):
            seen[msg.get("id")] = msg["usage"]
    return sum(u.get(k) or 0 for u in seen.values() for k in USAGE)


def subagents(out, ws):
    """{"deploy"|"code": [runs, tokens]} of subagents in one workspace, by the step kind that launched them."""
    found = {"deploy": [0, 0], "code": [0, 0]}
    for session in (out / "home" / ws / ".claude" / "projects").glob(f"*-ws-{ws}/*.jsonl"):
        kind = "deploy" if "Use the lab-forge skill" in session.read_text().split("\n", 1)[0] else "code"
        for sub in session.with_suffix("").glob("subagents/*.jsonl"):
            found[kind][0] += 1
            found[kind][1] += usage_tokens(sub)
    return found


def table(rows, arms, outs):
    by = {a: [r for r in rows if r["arm"] == a] for a, _ in arms}
    sub = {}
    for a, _ in arms:
        homes = [(o, r["ws"]) for r in by[a] for o in outs if (o / "home" / r["ws"]).exists()]
        if homes:
            sub[a] = [subagents(o, ws) for o, ws in dict.fromkeys(homes)]

    def n(rs, key):
        return sum(r[key] == "True" for r in rs)

    def num(rs, key):
        return sum(int(r[key]) for r in rs if r[key] not in ("", "—"))

    def usd(rs):
        return sum(float(r["cost_usd"]) for r in rs)

    def sub_sum(a, kind, i):
        return sum(s[kind][i] for s in sub[a])

    def subs(kind):
        return lambda _, a: f"{sub_sum(a, kind, 0)}, {round(sub_sum(a, kind, 1) / 1000)}" if a in sub else "—"

    metrics = {
        "Solved, hidden checks": lambda rs, _: f"{n(rs, 'solved')}/{len(rs)}",
        "Claimed done but check fails": lambda rs, _: sum(
            r["committed"] == "True" and r["solved"] != "True" for r in rs
        ),
        "Mutants killed by the agent's tests": lambda rs, _: (
            f"{num(rs, 'mutants_killed')}/{num(rs, 'mutants_applied')}"
        ),
        "Bare `pytest` green after step": lambda rs, _: f"{n(rs, 'bare_pytest')}/{len(rs)}",
        "Ruff errors in changed files": lambda rs, _: num(rs, "ruff_errors"),
        "Python lines changed": lambda rs, _: num(rs, "loc_py"),
        "Tokens, k (subagents included)": lambda rs, _: round(num(rs, "tokens") / 1000),
        "Subagents in these steps: runs, k tokens": subs("code"),
        "Subagents in deploy (P0, not counted above): runs, k tokens": subs("deploy"),
        "`cost_usd`": lambda rs, _: f"{usd(rs):.2f}",
        "`cost_usd` per solved coding step": lambda rs, _: (
            f"{usd(rs) / n(rs, 'solved'):.2f}" if n(rs, "solved") else "—"
        ),
    }
    lines = ["| Metric | " + " | ".join(h for _, h in arms) + " |", "|---" * (len(arms) + 1) + "|"]
    lines += [f"| {name} | " + " | ".join(str(f(by[a], a)) for a, _ in arms) + " |" for name, f in metrics.items()]
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument(
        "--runs", nargs="+", required=True, help="runs.tsv files; an arm is taken from the first that has it"
    )
    p.add_argument("--arm", action="append", required=True, help="NAME or NAME=column label, in column order")
    p.add_argument("--out", action="append", default=[], help="bench out dir with home/ transcripts")
    p.add_argument("--steps", nargs="+", default=["P1", "P2"])
    args = p.parse_args()
    arms = [(a.split("=", 1) + [a])[:2] for a in args.arm]
    rows = []
    for path in args.runs:
        with open(path) as f:
            new = [r for r in csv.DictReader(f, delimiter="\t") if r["step"] in args.steps]
        have = {r["arm"] for r in rows}
        rows += [r for r in new if r["arm"] not in have]
    print(table(rows, arms, [Path(o) for o in args.out]))


if __name__ == "__main__":
    main()
