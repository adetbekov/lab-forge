"""Aggregate per-step metrics and blind verdicts into report.md and runs.tsv."""

import re
from collections import defaultdict
from math import sqrt
from statistics import mean, stdev

CODE = ("success", "correctness", "practices", "optimality", "bloat", "scope")
CODE_V04 = ("methodology", "tests")  # appended in v0.4; CODE and "code sum of 30" keep their old meaning
WEIGHTS = {
    "methodology": 2,
    "tests": 2,
    "correctness": 1.5,
    "success": 1,
    "scope": 1,
    "practices": 1,
    "optimality": 0.5,
    "bloat": 0.5,
}
SWAP = ".swap"  # review key suffix: the same pair judged with X and Y swapped
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
    "bad_imports",
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
    # v0.4 columns, appended so older runs.tsv files still line up
    "mode",
    "input_tokens",
    "output_tokens",
    "cache_read_tokens",
    "cache_write_tokens",
    "weighted_tokens",
    "bare_pytest",
    "mutants_killed",
    "mutants_applied",
    "n_files",
)


def fmt(v, digits=1):
    if v is None:
        return "—"
    return f"{v:.{digits}f}" if isinstance(v, float) else str(v)


def table(head, rows):
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    return "\n".join(lines + ["| " + " | ".join(fmt(c) for c in r) + " |" for r in rows])


def parse(v):
    if v == "—":
        return None
    if v in ("True", "False"):
        return v == "True"
    for kind in (int, float):
        try:
            return kind(v)
        except ValueError:
            pass
    return v


def read_tsv(text):
    """Rows of a runs.tsv, typed back; file lists are not in the TSV, so `files` is None."""
    head, *lines = text.splitlines()
    cols = head.split("\t")
    return [dict(zip(cols, map(parse, line.split("\t")))) | {"files": None} for line in lines if line]


def n_files(r):
    if r.get("files") is not None:
        return len(r["files"])
    if r.get("n_files") is not None:
        return r["n_files"]
    return int(r["loc_all"] + r["ai_loc"] > 0)  # runs.tsv before v0.4: no file count, changed lines tell


def per_solved(rows, key, scale=1):
    vals = [r.get(key) for r in rows if r["kind"] != "deploy"]
    if not vals or None in vals:
        return None
    solved = sum(r["solved"] for r in rows if r["kind"] == "code")
    return sum(vals) / scale / max(solved, 1)


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
        "Imports that do not resolve": sum(r.get("bad_imports", 0) for r in code),
        "Questions in coding-step replies": sum(r["questions"] for r in code),
        "Files written during read-only question": sum(n_files(r) for r in question),
        "Tune phrase applied in next session": f"{sum(r['russian'] for r in question)}/{len(question)}",
        "Style stability across repeats (0-1)": stability(code),
        "Tool calls per solved task": sum(r["tools"] for r in tasks) / max(solved, 1),
        "Weighted tokens per solved task, k (cache read x0.1, write x1.25)": per_solved(mine, "weighted_tokens", 1000),
        "Bare `pytest` green after step": ratio([r.get("bare_pytest") for r in code]),
        "Mutants killed by the agent's tests": ratio(
            [r.get("mutants_killed") for r in code], [r.get("mutants_applied") for r in code]
        ),
    }


def ratio(hits, totals=None):
    """`k/n` over the steps that measured it, `—` when none did."""
    pairs = [(h, 1 if totals is None else t) for h, t in zip(hits, totals or hits) if h is not None]
    return f"{sum(h for h, _ in pairs)}/{sum(t for _, t in pairs)}" if pairs else None


def stability(code):
    """Mean over (case, step) of Jaccard(files) x min/max(lines) between repeats."""
    if any(r["files"] is None for r in code):
        return None  # rebuilt from runs.tsv: file lists are not kept there
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
    for key, rv in sorted(reviews.items()):
        side_arm = rv["map"]
        for label, arm in side_arm.items():
            s = rv["scores"].get(label, {})
            for step, val in s.items():
                if isinstance(val, dict):
                    for crit, score in val.items():
                        group = "code" if crit in CODE + CODE_V04 else "question"
                        acc[arm][f"{group}:{crit}"].append(score)
                elif isinstance(val, (int, float)):
                    acc[arm][step].append(val)
    return {arm: {k: mean(v) for k, v in d.items()} for arm, d in acc.items()}, winners(reviews)


def winners(reviews):
    """Winner per step for each case and repeat. If X/Y ran in both orders and the winner flips, it is a tie."""
    groups = defaultdict(list)
    for key, rv in sorted(reviews.items()):
        win = rv["scores"].get("winner", {})
        groups[key.removesuffix(SWAP)].append({k: rv["map"].get(v, "tie") for k, v in win.items()})
    rows, flips, pairs = [], 0, 0
    for key, picks in groups.items():
        row = []
        for step in sorted(set().union(*picks), key=lambda k: (k == "overall", k)):
            got = {p.get(step, "tie") for p in picks}
            row.append(next(iter(got)) if len(got) == 1 else "tie")
            if len(picks) > 1:
                pairs, flips = pairs + 1, flips + (len(got) > 1)
        rows.append((key, *row))
    return rows, (flips, pairs)


def weighted(scores):
    """Weighted code score on the 1-5 scale; None unless every weighted criterion was scored."""
    vals = [scores.get(f"code:{c}") for c in WEIGHTS]
    if None in vals:
        return None
    return sum(w * v for w, v in zip(WEIGHTS.values(), vals)) / sum(WEIGHTS.values())


def spread(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return None
    if len(xs) == 1:
        return f"{xs[0]:.2f} (n=1)"
    return f"{mean(xs):.2f} ± {stdev(xs) / sqrt(len(xs)):.2f} (n={len(xs)})"


def repeats(rows, reviews, arms):
    """Mean ± standard error over repeats: each repeat is scored on its own, across all cases."""
    reps = sorted({r["rep"] for r in rows} | {int(m[1]) for k in reviews if (m := re.search(r"-r(\d+)", k))})
    per = {arm: defaultdict(list) for arm in arms}
    for rep in reps:
        mine = {k: rv for k, rv in reviews.items() if re.search(rf"-r{rep}(\W|$)", k)}
        jd = judged(mine, arms)[0] if mine else {}
        for arm in arms:
            rr = [r for r in rows if r["arm"] == arm and r["rep"] == rep]
            code = [r for r in rr if r["kind"] == "code"]
            per[arm]["Tokens per solved task, k"].append(per_solved(rr, "tokens", 1000) if code else None)
            per[arm]["Cost per solved task, $"].append(per_solved(rr, "cost_usd") if code else None)
            if arm in jd:
                per[arm]["code sum of 30"].append(sum(jd[arm].get(f"code:{c}", 0) for c in CODE))
                per[arm]["weighted code score, 1-5"].append(weighted(jd[arm]))
    names = list(per[arms[0]])
    return table(["Metric", *arms], [(n, *[spread(per[a][n]) for a in arms]) for n in names])


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
    jd, (wins, (flips, pairs)) = judged(reviews, arms)
    out = [f"# lab-forge bench: {' vs '.join(arms)}", ""]
    modes = sorted({r.get("mode") or "" for r in rows}) or [""]
    for mode in modes:  # headless and agent-driven numbers never share a table
        sub = [r for r in rows if (r.get("mode") or "") == mode]
        tag = f" ({mode or 'mode not recorded'})" if len(modes) > 1 else ""
        obj = {arm: objective(sub, arm) for arm in arms}
        if len(arms) == 2 and sub:
            repro = reproduction(sub, reviews, arms, obj, jd)
            held = [r[3] for r in repro if r[3] is not None]
            out += [
                f"## First-round conclusions{tag}: {sum(held)}/{len(held)} reproduced",
                "",
                table(
                    ["Conclusion", "First round", "This run", "Holds"],
                    [(c, was, now, {True: "yes", False: "no", None: "—"}[ok]) for c, was, now, ok in repro],
                ),
                "",
            ]
        out += [
            f"## Objective metrics{tag}",
            "",
            table(["Metric", *arms], [(k, *[obj[a][k] for a in arms]) for k in obj[arms[0]]]),
            "",
            f"## Spread over repeats{tag} (mean ± SE)",
            "",
            repeats(sub, reviews, arms),
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
                + [("**code sum of 30**", *[sum(jd[a].get(f"code:{c}", 0) for c in CODE) for a in arms])]
                + [("**weighted code score, 1-5**", *[weighted(jd[a]) for a in arms])],
            ),
            "",
            "## Winners by case and repeat",
            "",
            table(["case-repeat", "steps…, overall"], [(w[0], ", ".join(w[1:])) for w in wins]),
            "",
        ]
        if pairs:
            out += [f"X/Y order changed the winner in {flips} of {pairs} calls; those count as ties.", ""]
    tsv = "\t".join(TSV) + "\n" + "".join("\t".join(fmt(r.get(c), 3) for c in TSV) + "\n" for r in rows)
    return "\n".join(out), tsv
