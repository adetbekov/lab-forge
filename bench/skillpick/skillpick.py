#!/usr/bin/env python3
"""A/B for `guard.py decide skill`: does a d1-ultra "load skill X" hint make the agent load the right skill?

    python bench/skillpick/skillpick.py router --out DIR              # d1-ultra alone, every case
    python bench/skillpick/skillpick.py agent --out DIR --reps 2      # claude -p, hint arm vs base arm
    python bench/skillpick/skillpick.py report --out DIR              # DIR/report.md

Skills and prompts are synthetic. `router` and the hint arm send prompts to api.liquid.ai (LIQUID_AI_API_KEY).
"""

import argparse
import concurrent.futures
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / "skills" / "lab-forge" / "scripts" / "guard.py"
sys.path.insert(0, str(GUARD.parent))
import guard  # noqa: E402

SKILLS = {
    "eda-report": "Exploratory data analysis of a tabular dataset: profile columns, distributions, missing values, "
    "correlations, and write a short findings report.",
    "leakage-audit": "Audit features and train/test splits for target leakage, duplicates across splits and "
    "future information.",
    "experiment-tracking": "Log runs, parameters, metrics and artifacts to MLflow and compare runs.",
    "hparam-search": "Hyperparameter search for a model with Optuna: search space, pruning, best params.",
    "model-serving": "Serve a trained model behind a FastAPI endpoint with a Dockerfile and a health check.",
    "data-validation": "Schema and expectation checks on incoming data with pandera; fail the pipeline on violations.",
    "notebook-to-package": "Refactor a Jupyter notebook into a tested Python package with functions and pytest.",
    "gpu-env": "Set up a CUDA / PyTorch environment with uv or conda and verify the GPU is visible.",
    "timeseries-backtest": "Time-based cross-validation and backtesting for forecasting models.",
    "llm-eval": "Evaluate LLM prompts or outputs against a labelled test set, with metrics or an LLM judge.",
}

# A crowded setup: unrelated skills plus near neighbours of the right ones (`--crowded`).
DISTRACTORS = {
    "dashboard-build": "Build a Streamlit or Grafana dashboard with charts over a dataset or metrics.",
    "airflow-pipeline": "Write or fix an Airflow DAG that moves and transforms data on a schedule.",
    "model-monitoring": "Monitor a deployed model in production: drift, latency and accuracy alerts.",
    "feature-store": "Define, materialize and serve features with Feast.",
    "spark-jobs": "Write and tune PySpark jobs for large datasets.",
    "sql-tuning": "Speed up slow SQL queries: indexes, query plans, rewrites.",
    "docker-compose": "Write a docker-compose setup for local services.",
    "k8s-deploy": "Deploy a service to Kubernetes with manifests or Helm.",
    "ci-pipeline": "Set up or fix a GitHub Actions CI pipeline: lint, tests, build.",
    "git-release": "Cut a release: changelog, version bump, tag.",
    "api-docs": "Write OpenAPI docs and usage examples for an HTTP API.",
    "security-review": "Review code for security issues: secrets, injection, unsafe deserialization.",
    "frontend-design": "Design and build a web UI with React and Tailwind.",
    "pdf-report": "Render a report to PDF with tables and charts.",
    "slack-notify": "Send Slack notifications from scripts and pipelines.",
    "log-analysis": "Search and summarize application logs to find errors.",
    "unit-testing": "Write pytest unit tests and fixtures for existing code.",
    "prompt-writing": "Write or improve a system prompt for an LLM assistant.",
    "data-labeling": "Set up a labelling task in Label Studio and export labels.",
    "python-packaging": "Package a Python project with pyproject.toml and publish it to PyPI.",
}

# (prompt, expected skill or "none"). "implicit" cases never name the skill's topic word for word.
CASES = [
    ("Profile data/sales.csv and tell me what's odd about it before we model anything.", "eda-report", "implicit"),
    ("Do an EDA of data/customers.parquet: distributions, missing values, correlations.", "eda-report", "explicit"),
    ("Посмотри на датасет data/loans.csv и опиши, что в нём есть и где дыры.", "eda-report", "implicit"),
    ("My validation AUC is 0.99 but production is 0.61. Find out why.", "leakage-audit", "implicit"),
    ("Check churn/features.py for target leakage.", "leakage-audit", "explicit"),
    ("Подозреваю, что одни и те же клиенты попали и в train, и в test. Проверь.", "leakage-audit", "implicit"),
    (
        "I keep losing track of which run had which params. Set up something so every train.py run is recorded.",
        "experiment-tracking",
        "implicit",
    ),
    ("Log train.py metrics and the model artifact to MLflow.", "experiment-tracking", "explicit"),
    ("Сравни последние запуски обучения по метрикам, хочу видеть таблицу.", "experiment-tracking", "implicit"),
    ("The LightGBM model in train.py uses default settings. Squeeze more out of it.", "hparam-search", "implicit"),
    ("Run an Optuna study over learning_rate and num_leaves for train.py.", "hparam-search", "explicit"),
    ("Подбери гиперпараметры для xgboost в model.py.", "hparam-search", "explicit"),
    ("The product team wants to call our churn model from their backend over HTTP.", "model-serving", "implicit"),
    ("Wrap model.pkl in a FastAPI service with a Dockerfile.", "model-serving", "explicit"),
    ("Нужно, чтобы модель можно было дергать по REST и задеплоить в контейнере.", "model-serving", "implicit"),
    (
        "Last week the upstream team renamed a column and our pipeline silently trained on NaNs. Stop that happening.",
        "data-validation",
        "implicit",
    ),
    ("Add pandera schema checks to the ingest step.", "data-validation", "explicit"),
    (
        "Сделай так, чтобы пайплайн падал, если во входных данных пришли отрицательные цены.",
        "data-validation",
        "implicit",
    ),
    (
        "analysis.ipynb has grown to 80 cells and nobody can reuse it. Turn it into real code.",
        "notebook-to-package",
        "implicit",
    ),
    ("Refactor notebooks/train.ipynb into a Python package with pytest tests.", "notebook-to-package", "explicit"),
    ("Вынеси логику из ноутбука в модули и покрой тестами.", "notebook-to-package", "explicit"),
    ("torch.cuda.is_available() returns False on the new box. Fix the environment.", "gpu-env", "implicit"),
    ("Set up a uv environment with PyTorch for CUDA 12.4 and check the GPU.", "gpu-env", "explicit"),
    ("Поставь окружение для обучения на видеокарте, сейчас всё считается на CPU.", "gpu-env", "implicit"),
    (
        "Our demand forecast looks great on a random split but fails every month in prod. Evaluate it properly.",
        "timeseries-backtest",
        "implicit",
    ),
    ("Add rolling-origin backtesting to forecast.py.", "timeseries-backtest", "explicit"),
    (
        "Проверь прогноз продаж на истории: обучай на прошлом, тестируй на следующем месяце.",
        "timeseries-backtest",
        "implicit",
    ),
    ("We changed the support-bot system prompt. Is the new one better than the old one?", "llm-eval", "implicit"),
    ("Score prompts/v2.txt against eval/cases.jsonl with an LLM judge.", "llm-eval", "explicit"),
    ("Собери тестовый набор вопросов и сравни ответы двух промптов для бота.", "llm-eval", "implicit"),
    ("Fix the typo in README.md: 'recieve'.", "none", "none"),
    ("What does git rebase --onto do?", "none", "none"),
    ("Rename the function load_df to load_frame across the repo.", "none", "none"),
    ("Переведи docs/intro.md на английский.", "none", "none"),
    ("Write a bash one-liner that counts lines in all .py files.", "none", "none"),
    ("Объясни разницу между list и tuple в Python.", "none", "none"),
]

SESSION_ENV = ("PATH", "LANG", "LC_ALL", "TERM", "TMPDIR", "SSL_CERT_FILE", "HTTPS_PROXY", "NO_PROXY")
AUTH_ENV = ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN")


def installed(crowded):
    return SKILLS | DISTRACTORS if crowded else SKILLS


def skill_md(name, desc):
    return f"---\nname: {name}\ndescription: {desc}\n---\n\n# {name}\n\n{desc}\n\nReply with the plan in 3 bullets.\n"


def router(out, crowded=False):
    cfg = guard.DECIDE | {"backend": "hosted"}
    sandbox = out / "router-skills"
    for name, desc in installed(crowded).items():
        (sandbox / ".claude" / "skills" / name).mkdir(parents=True, exist_ok=True)
        (sandbox / ".claude" / "skills" / name / "SKILL.md").write_text(skill_md(name, desc))
    rows = []
    for i, (prompt, want, kind) in enumerate(CASES):
        criteria = dict(list(guard.skills(sandbox).items())[: guard.MAX_SKILLS]) | {
            "none": "No listed skill fits this request"
        }
        q = {
            "type": "choice",
            "instructions": "Which skill should the agent load for this user request?",
            "criteria": criteria,
        }
        t = time.monotonic()
        try:
            pick = guard.ask(cfg, f"User request: {prompt}", {"skill": q}, timeout=10)["skill"]
        except Exception as e:  # noqa: BLE001
            pick = {"choice": f"error:{type(e).__name__}", "confidence": 0}
        ms = int((time.monotonic() - t) * 1000)
        hint = pick["choice"] if pick["choice"] != "none" and pick["confidence"] >= cfg["confidence"] else ""
        rows.append(
            {
                "i": i,
                "want": want,
                "kind": kind,
                "choice": pick["choice"],
                "confidence": round(pick.get("confidence", 0), 3),
                "hint": hint,
                "ms": ms,
            }
        )
    (out / "router.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    shutil.rmtree(sandbox)
    print(f"router: {sum(r['choice'] == r['want'] for r in rows)}/{len(rows)} top-1")


def workspace(base, arm, crowded=False):
    home, proj = base / "home", base / "proj"
    for name, desc in installed(crowded).items():
        (proj / ".claude" / "skills" / name).mkdir(parents=True, exist_ok=True)
        (proj / ".claude" / "skills" / name / "SKILL.md").write_text(skill_md(name, desc))
    (home / ".lab-forge").mkdir(parents=True, exist_ok=True)
    (home / ".lab-forge" / "decide.json").write_text(json.dumps({"backend": "hosted" if arm == "hint" else "off"}))
    hook = {"hooks": [{"type": "command", "command": f"python3 {GUARD} decide skill", "timeout": 5}]}
    settings = {"hooks": {"UserPromptSubmit": [hook]}}
    (proj / ".claude" / "settings.json").write_text(json.dumps(settings))
    return home, proj


def session(out, i, arm, rep, model, crowded=False):
    base = out / "ws" / f"{i:02d}-{arm}-{rep}"
    shutil.rmtree(base, ignore_errors=True)
    home, proj = workspace(base, arm, crowded)
    keys = ("LIQUID_AI_API_KEY",) if arm == "hint" else ()
    env = {k: os.environ[k] for k in (*SESSION_ENV, *AUTH_ENV, *keys) if k in os.environ} | {"HOME": str(home)}
    cmd = [
        "claude",
        "-p",
        CASES[i][0],
        "--output-format",
        "stream-json",
        "--verbose",
        "--permission-mode",
        "bypassPermissions",
        "--max-turns",
        "3",
        "--include-hook-events",
    ]
    cmd += ["--model", model] if model else []
    t = time.monotonic()
    res = subprocess.run(cmd, cwd=proj, env=env, capture_output=True, text=True, timeout=600, check=False)
    row = parse(res.stdout) | {"i": i, "arm": arm, "rep": rep, "ms": int((time.monotonic() - t) * 1000)}
    (base / "stream.jsonl").write_text(res.stdout)
    return row


def parse(stream):
    """First Skill tool call, the hint the hook injected, and token usage from a stream-json transcript."""
    loaded, hinted, tokens, model, error = "", "", 0, "", ""
    for line in stream.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") == "system" and ev.get("subtype") == "init":
            model = ev.get("model", "")
        blob = json.dumps(ev)
        if not hinted and "lab-forge: load skill " in blob and ev.get("type") != "assistant":
            hinted = blob.split("lab-forge: load skill ", 1)[1].split('"')[0].split("\\")[0].strip()
        for part in (ev.get("message") or {}).get("content") or []:
            if isinstance(part, dict) and part.get("type") == "tool_use" and part.get("name") == "Skill" and not loaded:
                loaded = (part.get("input") or {}).get("skill", "").split(":")[-1]
        if ev.get("type") == "result":
            u = ev.get("usage") or {}
            tokens = sum(
                u.get(k, 0)
                for k in ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
            )
            error = ev.get("subtype", "") if ev.get("is_error") and ev.get("subtype") != "error_max_turns" else ""
    return {"loaded": loaded, "hinted": hinted, "tokens": tokens, "model": model, "error": error}


def agent(out, reps, model, jobs, crowded=False, kinds=("implicit", "explicit", "none")):
    path = out / "agent.jsonl"
    done = (
        {(r["i"], r["arm"], r["rep"]) for r in map(json.loads, path.read_text().splitlines())}
        if path.exists()
        else set()
    )
    todo = [
        (i, arm, rep)
        for rep in range(1, reps + 1)
        for i in range(len(CASES))
        if CASES[i][2] in kinds
        for arm in ("hint", "base")
        if (i, arm, rep) not in done
    ]
    with concurrent.futures.ThreadPoolExecutor(jobs) as pool, path.open("a") as f:
        for row in pool.map(lambda k: session(out, *k, model, crowded), todo):
            f.write(json.dumps(row) + "\n")
            f.flush()
            print(
                f"{row['i']:02d} {row['arm']:4} r{row['rep']} loaded={row['loaded'] or '-'} hint={row['hinted'] or '-'}"
            )


def summarize(router_rows, agent_rows):
    """Per-arm and router metrics; pure, so the tests can pin it."""
    pos = [r for r in router_rows if r["want"] != "none"]
    hints = [r for r in router_rows if r["hint"]]
    res = {
        "cases": len(router_rows),
        "router_top1": sum(r["choice"] == r["want"] for r in router_rows),
        "router_hints": len(hints),
        "router_hints_right": sum(r["hint"] == r["want"] for r in hints),
        "router_hints_on_none": sum(r["want"] == "none" for r in hints),
        "router_hint_coverage": sum(r["hint"] == r["want"] for r in pos),
        "router_positives": len(pos),
        "router_ms_p50": sorted(r["ms"] for r in router_rows)[len(router_rows) // 2] if router_rows else 0,
        "arms": {},
    }
    want = {i: w for i, (_, w, _) in enumerate(CASES)}
    kind = {i: k for i, (_, _, k) in enumerate(CASES)}
    for arm in ("hint", "base"):
        rows = [r for r in agent_rows if r["arm"] == arm and not r["error"]]
        p = [r for r in rows if want[r["i"]] != "none"]
        res["arms"][arm] = {
            "sessions": len(rows),
            "errors": sum(1 for r in agent_rows if r["arm"] == arm and r["error"]),
            "right": sum(r["loaded"] == want[r["i"]] for r in p),
            "positives": len(p),
            "right_implicit": sum(r["loaded"] == want[r["i"]] for r in p if kind[r["i"]] == "implicit"),
            "implicit": sum(kind[r["i"]] == "implicit" for r in p),
            "wrong": sum(bool(r["loaded"]) and r["loaded"] != want[r["i"]] for r in p),
            "missed": sum(not r["loaded"] for r in p),
            "loaded_on_none": sum(bool(r["loaded"]) for r in rows if want[r["i"]] == "none"),
            "none_sessions": sum(want[r["i"]] == "none" for r in rows),
            "hinted": sum(bool(r["hinted"]) for r in rows),
            "tokens": sum(r["tokens"] for r in rows),
            "ms_p50": sorted(r["ms"] for r in rows)[len(rows) // 2] if rows else 0,
        }
    return res


def pct(a, b):
    return f"{a}/{b} ({100 * a / b:.0f}%)" if b else "-"


def report(out):
    load = lambda name: [json.loads(x) for x in (out / name).read_text().splitlines()] if (out / name).exists() else []  # noqa: E731
    s = summarize(load("router.jsonl"), load("agent.jsonl"))
    h, b = s["arms"]["hint"], s["arms"]["base"]
    crowd = f" plus {len(DISTRACTORS)} distractors" if (out / "crowded").exists() else ""
    models = sorted({r["model"] for r in load("agent.jsonl") if r["model"]})
    lines = [
        "# skillpick: `decide skill` hint vs no hint",
        "",
        f"{s['cases']} synthetic prompts ({s['router_positives']} with a right skill, the rest need none), "
        f"{len(SKILLS)} synthetic DS/ML skills{crowd}. Agent: `claude -p`, {', '.join(models) or '?'}.",
        "",
        "## d1-ultra router alone",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Top-1 right (incl. `none`) | {pct(s['router_top1'], s['cases'])} |",
        f"| Hints given (confidence ≥ 0.7) | {s['router_hints']} |",
        f"| Hints that are right | {pct(s['router_hints_right'], s['router_hints'])} |",
        f"| Hints on prompts that need no skill | {s['router_hints_on_none']} |",
        f"| Prompts needing a skill that got the right hint | {pct(s['router_hint_coverage'], s['router_positives'])} |",
        f"| Latency p50, ms | {s['router_ms_p50']} |",
        "",
        "## Agent: right skill loaded",
        "",
        "| Metric | hint | base |",
        "|---|---|---|",
        f"| Sessions (errors) | {h['sessions']} ({h['errors']}) | {b['sessions']} ({b['errors']}) |",
        f"| Right skill loaded | {pct(h['right'], h['positives'])} | {pct(b['right'], b['positives'])} |",
        f"| ... on implicit prompts | {pct(h['right_implicit'], h['implicit'])} | {pct(b['right_implicit'], b['implicit'])} |",
        f"| Wrong skill loaded | {h['wrong']} | {b['wrong']} |",
        f"| No skill loaded when one fits | {h['missed']} | {b['missed']} |",
        f"| A skill loaded when none fits | {h['loaded_on_none']}/{h['none_sessions']} | "
        f"{b['loaded_on_none']}/{b['none_sessions']} |",
        f"| Sessions with a hint | {h['hinted']} | {b['hinted']} |",
        f"| Tokens, k | {h['tokens'] / 1000:.0f} | {b['tokens'] / 1000:.0f} |",
        f"| Session time p50, s | {h['ms_p50'] / 1000:.1f} | {b['ms_p50'] / 1000:.1f} |",
        "",
    ]
    (out / "report.md").write_text("\n".join(lines))
    print("\n".join(lines))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=["router", "agent", "report"])
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--reps", type=int, default=2)
    p.add_argument("--model")
    p.add_argument("--jobs", type=int, default=4)
    p.add_argument("--crowded", action="store_true", help=f"install {len(DISTRACTORS)} distractor skills too")
    p.add_argument("--kinds", nargs="*", default=["implicit", "explicit", "none"])
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    if a.crowded:
        (a.out / "crowded").touch()
    {
        "router": lambda: router(a.out, a.crowded),
        "agent": lambda: agent(a.out, a.reps, a.model, a.jobs, a.crowded, a.kinds),
        "report": lambda: report(a.out),
    }[a.cmd]()


if __name__ == "__main__":
    main()
