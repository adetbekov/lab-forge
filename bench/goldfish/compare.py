"""Goldfish arms against the JEB-1915 baseline, coding steps only (P1, P2). Stdlib only.

    python bench/goldfish/compare.py OUT bench/results/2026-10-20-sonnet-hard/runs.tsv > table.md

OUT is the bench out dir of the goldfish run: its runs.tsv plus the session transcripts in OUT/home, which
give the goldfish subagent's share of tokens and how often it ran.
"""

import csv
import json
import sys
from pathlib import Path

ARMS = [("v041gf", "v041gf"), ("v041", "v041"), ("baregf", "baregf"), ("bare", "bare"), ("opus", "bare opus")]
CODE = ("P1", "P2")
USAGE = ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")


def rows(path):
    with open(path) as f:
        return [r for r in csv.DictReader(f, delimiter="\t") if r["step"] in CODE]


def usage_tokens(path):
    seen = {}
    for line in path.read_text().splitlines():
        msg = json.loads(line).get("message") or {}
        if msg.get("usage"):
            seen[msg.get("id")] = msg["usage"]
    return sum(u.get(k) or 0 for u in seen.values() for k in USAGE)


def goldfish(out, ws):
    """{"deploy"|"code": (runs, tokens)} of goldfish subagents in one workspace, by the step that launched them."""
    found = {"deploy": [0, 0], "code": [0, 0]}
    for session in (out / "home" / ws / ".claude" / "projects").glob(f"*-ws-{ws}/*.jsonl"):
        kind = "deploy" if "Use the lab-forge skill" in session.read_text().split("\n", 1)[0] else "code"
        for sub in session.with_suffix("").glob("subagents/*.jsonl"):
            if json.loads(sub.with_suffix(".meta.json").read_text()).get("agentType") == "goldfish":
                found[kind][0] += 1
                found[kind][1] += usage_tokens(sub)
    return found


def main(out, base):
    out = Path(out)
    data = rows(out / "runs.tsv") + [r for r in rows(base) if r["arm"] in ("v041", "bare", "opus")]
    by = {a: [r for r in data if r["arm"] == a] for a, _ in ARMS}
    gf = {a: [goldfish(out, ws) for ws in {r["ws"] for r in by[a]}] for a in ("v041gf", "baregf")}

    def n(rs, key):
        return sum(r[key] == "True" for r in rs)

    def num(rs, key):
        return sum(int(r[key]) for r in rs if r[key] not in ("", "—"))

    def usd(rs):
        return sum(float(r["cost_usd"]) for r in rs)

    def gf_sum(kind, i):
        return lambda _, a: sum(g[kind][i] for g in gf[a]) if a in gf else "—"

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
        "Tokens, k (P1+P2, goldfish included)": lambda rs, _: round(num(rs, "tokens") / 1000),
        "of which goldfish, k": lambda rs, a: round(gf_sum("code", 1)(rs, a) / 1000) if a in gf else "—",
        "Goldfish runs in P1+P2": gf_sum("code", 0),
        "Goldfish in deploy (P0, not in the rows above): runs, k tokens": lambda rs, a: (
            f"{gf_sum('deploy', 0)(rs, a)}, {round(gf_sum('deploy', 1)(rs, a) / 1000)}" if a in gf else "—"
        ),
        "`cost_usd`, P1+P2": lambda rs, _: f"{usd(rs):.2f}",
        "`cost_usd` per solved coding step": lambda rs, _: f"{usd(rs) / max(n(rs, 'solved'), 1):.2f}",
    }
    lines = ["| Metric | " + " | ".join(h for _, h in ARMS) + " |", "|---" * (len(ARMS) + 1) + "|"]
    lines += [f"| {name} | " + " | ".join(str(f(by[a], a)) for a, _ in ARMS) + " |" for name, f in metrics.items()]
    print("\n".join(lines))


if __name__ == "__main__":
    main(*sys.argv[1:3])
