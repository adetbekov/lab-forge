"""Cost of the coding steps (P1, P2) per arm from sessions.tsv and the bench state. Usage: cost.py OUT

The Agent tool reports one token total per session. Price = list prices with an assumed agentic mix of
80% cache read, 10% cache write, 2% fresh input, 8% output (same as the first routing run).
"""

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

# $/MTok: input, output, cache read, cache write
PRICE = {"opus": (4, 20, 0.20, 5), "sonnet": (2, 10, 0.20, 2.5), "haiku": (0.10, 0.50, 0.01, 0.125)}
MIX = (0.02, 0.08, 0.80, 0.10)
BLEND = {m: sum(p * w for p, w in zip(ps, MIX)) for m, ps in PRICE.items()}

out = Path(sys.argv[1])
states = {p.stem: json.loads(p.read_text()) for p in (out / "state").glob("*.json")}
cost, tokens, roles = defaultdict(float), defaultdict(int), defaultdict(int)
steps = defaultdict(set)
with open(out / "sessions.tsv") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        if row["step"] not in ("P1", "P2"):
            continue
        arm = states[row["ws"]]["arm"]
        cost[arm] += int(row["tokens"]) * BLEND[row["model"]] / 1e6
        tokens[arm] += int(row["tokens"])
        roles[arm, row["role"].split("-")[0]] += int(row["tokens"])
        steps[arm].add((row["ws"], row["step"]))
print("| Metric | " + " | ".join(sorted(cost)) + " |\n|---|" + "---|" * len(cost))
solved = {a: sum(states[w]["steps"][s]["solved"] for w, s in steps[a]) for a in cost}
print("| Solved, hidden checks | " + " | ".join(f"{solved[a]}/{len(steps[a])}" for a in sorted(cost)) + " |")
print("| Tokens, k | " + " | ".join(f"{tokens[a] / 1000:.0f}" for a in sorted(cost)) + " |")
print("| Cost, $ | " + " | ".join(f"{cost[a]:.2f}" for a in sorted(cost)) + " |")
print("| Cost per solved step, $ | " + " | ".join(f"{cost[a] / max(solved[a], 1):.3f}" for a in sorted(cost)) + " |")
print()
for (arm, role), n in sorted(roles.items()):
    print(f"{arm} {role}: {n / 1000:.0f}k")
