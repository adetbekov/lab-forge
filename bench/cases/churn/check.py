"""Hidden acceptance check: python check.py P1|P2, run from a copy of the project root."""

import json
import subprocess
import sys
from pathlib import Path

import tomllib


def leaves(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from leaves(v, f"{prefix}.{k}".lower())
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from leaves(v, f"{prefix}.{i}")
    else:
        yield prefix, obj


def files():
    return {p: p.stat().st_mtime_ns for p in Path.cwd().rglob("*") if p.is_file() and ".git" not in p.parts}


def fresh_metrics(before):
    for p, mtime in files().items():
        if p.suffix != ".json" or before.get(p) == mtime:
            continue
        try:
            yield p, dict(leaves(json.loads(p.read_text())))
        except (ValueError, UnicodeDecodeError):
            continue


def has_hyperparams(path):
    """A config file naming GBM hyperparameters; in pyproject.toml only a [tool.*] table counts."""
    text = path.read_text(errors="ignore")
    if path.name == "pyproject.toml":
        text = json.dumps(tomllib.loads(text).get("tool", {}))
    return any(h in text for h in ("learning_rate", "max_depth", "max_iter", "n_estimators"))


def main(step):
    before = files()
    run = subprocess.run(
        [sys.executable, "-m", "churn.train"], capture_output=True, text=True, check=False, timeout=900
    )
    if run.returncode:
        tail = (run.stderr or run.stdout).strip().splitlines()[-1:] or [""]
        return f"`python -m churn.train` exit {run.returncode}: {tail[0][:150]}"
    for path, flat in fresh_metrics(before):
        # deltas such as vs_baseline.*.roc_auc = 0.0 may sit next to the real scores
        # or the metric is named in a value ({"metric": "roc_auc", "models": {"logreg": 0.78, ...}})
        named = any(isinstance(v, str) and "auc" in v.lower() for v in flat.values())
        aucs = [v for k, v in flat.items() if ("auc" in k or named) and isinstance(v, float) and 0.5 < v <= 1]
        if len(aucs) < 2:
            continue
        if step == "P1":
            return None
        missing = [m for m in ("precision", "recall", "f1") if not any(m in k for k in flat)]
        if missing:
            return f"{path.name}: no {missing} in metrics"
        configs = [p for p in before if p.suffix in {".yaml", ".yml", ".toml", ".json"} and has_hyperparams(p)]
        return None if configs else "no config file with GBM hyperparameters"
    return "no JSON with two ROC-AUC values in (0.5, 1] written by the run"


if __name__ == "__main__":
    try:
        error = main(sys.argv[1])
    except Exception as exc:  # noqa: BLE001
        error = f"{type(exc).__name__}: {exc}"
    print(error or "ok")
    sys.exit(1 if error else 0)
