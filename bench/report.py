"""Aggregate per-step metrics and blind verdicts into report.md and runs.tsv."""

from collections import defaultdict
from statistics import mean

CODE = ("success", "correctness", "practices", "optimality", "bloat", "scope")
QUESTION = ("accuracy", "completeness", "conciseness", "usefulness")
TSV = (
    "ws",
    "case",
    "arm",
    "rep",
    "step",
    "tokens",
    "tools",
    "ms",
    "cost_usd",
    "solved",
    "check",
    "pytest",
    "ruff_errors",
    "loc_py",
    "loc_all",
    "ai_loc",
    "tests_added",
    "max_new_file",
    "out_of_scope",
    "committed",
    "on_main",
    "questions",
    "reply_words",
    "russian",
)


def fmt(v, digits=1):
    if v is None:
        return "—"
    return f"{v:.{digits}f}" if isinstance(v, float) else str(v)


def table(head, rows):
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    return "\n".join(lines + ["| " + " | ".join(fmt(c) for c in r) + " |" for r in rows])


def objective(rows, arm):
    mine = [r for r in rows if r["arm"] == arm]
    code = [r for r in mine if r["kind"] == "code"]
    tasks = [r for r in mine if r["kind"] != "deploy"]
    deploy = [r["tokens"] for r in mine if r["kind"] == "deploy"]
    solved = sum(r["solved"] for r in code)
    question = [r for r in mine if r["kind"] == "question"]
    costs = [r["cost_usd"] for r in tasks if r.get("cost_usd") is not None]
    return {
        "Solved, hidden checks": f"{solved}/{len(code)}",
        "Claimed done but check fails (committed, not solved)": sum(r["committed"] and not r["solved"] for r in code),
        "pytest red after step": sum(r["pytest"] is False for r in code),
        "Task tokens, k (all steps except deploy)": sum(r["tokens"] for r in tasks) / 1000,
        "Tokens per solved task, k": sum(r["tokens"] for r in tasks) / 1000 / max(solved, 1),
        "Cost per solved task, $": sum(costs) / max(solved, 1) if costs else None,
        "Task time, min": sum(r["ms"] for r in tasks) / 60000,
        "Deploy tokens per project, k": mean(deploy) / 1000 if deploy else None,
        "Python lines changed (no AI files)": sum(r["loc_py"] for r in code),
        "All lines changed (no AI files)": sum(r["loc_all"] for r in code),
        "Largest new .py file, lines": max((r["max_new_file"] for r in code), default=0),
        "Tests added": sum(r["tests_added"] for r in code),
        "Files changed outside task scope": sum(r["out_of_scope"] for r in code),
        "Coding steps committed straight to main": f"{sum(r['on_main'] for r in code)}/{len(code)}",
        "Coding steps left uncommitted": sum(not r["committed"] for r in code),
        "Ruff errors in changed files": sum(r["ruff_errors"] for r in code),
        "Questions in coding-step replies": sum(r["questions"] for r in code),
        "Files written during read-only question": sum(len(r["files"]) for r in question),
        "Tune phrase applied in next session": f"{sum(r['russian'] for r in question)}/{len(question)}",
        "Style stability across repeats (0-1)": stability(code),
    }


def stability(code):
    """Mean over (case, step) of Jaccard(files) x min/max(lines) between repeats."""
    groups = defaultdict(list)
    for r in code:
        groups[r["case"], r["step"]].append(r)
    scores = []
    for runs in groups.values():
        for i, a in enumerate(runs):
            for b in runs[i + 1 :]:
                fa, fb = set(a["files"]), set(b["files"])
                jac = len(fa & fb) / len(fa | fb) if fa | fb else 1.0
                lo, hi = sorted((a["loc_all"], b["loc_all"]))
                scores.append(jac * (lo / hi if hi else 1.0))
    return mean(scores) if scores else None


def judged(reviews, arms):
    """Per arm: mean of each criterion; also the per-case winners."""
    acc = {arm: defaultdict(list) for arm in arms}
    winners = []
    for key, rv in sorted(reviews.items()):
        side_arm = rv["map"]
        for label, arm in side_arm.items():
            s = rv["scores"].get(label, {})
            for step, val in s.items():
                if isinstance(val, dict):
                    for crit, score in val.items():
                        group = "code" if crit in CODE else "question"
                        acc[arm][f"{group}:{crit}"].append(score)
                elif isinstance(val, (int, float)):
                    acc[arm][step].append(val)
        win = rv["scores"].get("winner", {})
        winners.append(
            (key, *[side_arm.get(win.get(k), "tie") for k in sorted(win, key=lambda k: (k == "overall", k))])
        )
    return {arm: {k: mean(v) for k, v in d.items()} for arm, d in acc.items()}, winners


def reproduction(rows, reviews, arms, obj, jd):
    """Conclusions of the first v0.1 A/B round, checked on this run. Arm 0 = with lab-forge, arm 1 = bare."""
    a, b = arms
    code = {arm: [r for r in rows if r["arm"] == arm and r["kind"] == "code"] for arm in arms}
    loc = {arm: sum(r["loc_py"] for r in code[arm]) for arm in arms}
    tok = {arm: sum(r["tokens"] for r in rows if r["arm"] == arm and r["kind"] != "deploy") for arm in arms}
    dep = obj[a]["Deploy tokens per project, k"]
    total = {arm: sum(jd[arm].get(f"code:{c}", 0) for c in CODE) for arm in arms}
    js = {arm: jd[arm].get("code:success") for arm in arms}
    bloat = {arm: jd[arm].get("code:bloat") for arm in arms}
    llm = [
        rv["map"].get(rv["scores"].get("winner", {}).get("overall"))
        for k, rv in reviews.items()
        if k.startswith("rparse-")
    ]
    return [
        ("Less code with lab-forge (≤ −15%)", "−30%", f"{loc[a] / max(loc[b], 1) - 1:+.0%}", loc[a] <= 0.85 * loc[b]),
        (
            "Blind bloat score higher with lab-forge",
            "4.75 vs 3.6",
            f"{fmt(bloat[a], 2)} vs {fmt(bloat[b], 2)}",
            None if None in bloat.values() else bloat[a] > bloat[b],
        ),
        (
            "Explicit requirements: lab-forge not better",
            "3.75 vs 4.75",
            f"{fmt(js[a], 2)} vs {fmt(js[b], 2)}",
            None if None in js.values() else js[a] <= js[b],
        ),
        (
            "Task tokens within ±15%",
            "+3%",
            f"{tok[a] / max(tok[b], 1) - 1:+.0%}",
            abs(tok[a] / max(tok[b], 1) - 1) <= 0.15,
        ),
        ("Deploy costs 40-100k tokens per project", "48-90k", f"{fmt(dep, 0)}k", dep is not None and 40 <= dep <= 100),
        (
            "Overall quality a tie (±2 of 30)",
            "25.0 vs 24.9",
            f"{total[a]:.1f} vs {total[b]:.1f}",
            abs(total[a] - total[b]) <= 2 if reviews else None,
        ),
        (
            "LLM project won by lab-forge",
            "A won c2",
            f"{llm.count(a)}/{len(llm)} repeats",
            llm.count(a) > len(llm) / 2 if llm else None,
        ),
    ]


def build(rows, reviews, arms):
    obj = {arm: objective(rows, arm) for arm in arms}
    jd, winners = judged(reviews, arms)
    out = [f"# lab-forge bench: {' vs '.join(arms)}", ""]
    if len(arms) == 2 and rows:
        repro = reproduction(rows, reviews, arms, obj, jd)
        held = [r[3] for r in repro if r[3] is not None]
        out += [
            f"## First-round conclusions: {sum(held)}/{len(held)} reproduced",
            "",
            table(
                ["Conclusion", "First round", "This run", "Holds"],
                [(c, was, now, {True: "yes", False: "no", None: "—"}[ok]) for c, was, now, ok in repro],
            ),
            "",
        ]
    out += [
        "## Objective metrics",
        "",
        table(["Metric", *arms], [(k, *[obj[a][k] for a in arms]) for k in obj[arms[0]]]),
        "",
    ]
    if reviews:
        keys = sorted({k for a in arms for k in jd[a]})
        out += [
            f"## Blind review ({len(reviews)} verdicts, 1-5)",
            "",
            table(
                ["Criterion", *arms],
                [(k, *[jd[a].get(k) for a in arms]) for k in keys]
                + [("**code sum of 30**", *[sum(jd[a].get(f"code:{c}", 0) for c in CODE) for a in arms])],
            ),
            "",
            "## Winners by case and repeat",
            "",
            table(["case-repeat", "steps…, overall"], [(w[0], ", ".join(w[1:])) for w in winners]),
            "",
        ]
    tsv = "\t".join(TSV) + "\n" + "".join("\t".join(fmt(r.get(c), 3) for c in TSV) + "\n" for r in rows)
    return "\n".join(out), tsv
