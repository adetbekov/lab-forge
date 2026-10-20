"""Hidden acceptance check: python check.py P1|P2, run from a copy of the project root.

Besides running the entry point it probes `fraud.features.build_features` for point-in-time correctness:
changing or adding later transactions, flipping labels or changing other users must not move a feature.
"""

import importlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PR_AUC = ("pr_auc", "prauc", "average_precision", "avg_precision", "pr-auc", "auprc", "auc_pr")


def leaves(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from leaves(v, f"{prefix}.{k}".lower())
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from leaves(v, f"{prefix}.{i}")
    else:
        yield prefix, obj


def number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def transactions(seed=0, users=40, n=1500):
    """A small history in the case's schema, sorted by time, with bursts so 24h counts are not all 1."""
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2024-01-01")
    ts = start + pd.to_timedelta(np.sort(rng.uniform(0, 365 * 24 * 3600, n)), unit="s")
    burst = rng.choice(n, 60, replace=False)
    ts = pd.DatetimeIndex(ts).append(ts[burst] + pd.to_timedelta(rng.uniform(60, 3600, 60), unit="s"))
    user = np.concatenate([rng.integers(0, users, n), rng.integers(0, users, 60)])
    user[n:] = user[burst]
    df = pd.DataFrame(
        {
            "user_id": user,
            "timestamp": ts,
            "amount": rng.lognormal(3, 1, len(ts)).round(2),
            "merchant_category": rng.choice(["grocery", "travel", "online", "fuel", "dining"], len(ts)),
            "is_fraud": (rng.random(len(ts)) < 0.02).astype(int),
        }
    )
    df = df.sort_values("timestamp", kind="stable").reset_index(drop=True)
    df.insert(0, "transaction_id", np.arange(len(df)))
    return df


def numeric(frame):
    frame = pd.DataFrame(frame)
    out = frame.select_dtypes(include=["number", "bool"]).astype(float)
    return out.drop(columns=[c for c in out.columns if str(c) in {"transaction_id", "user_id", "is_fraud"}])


def call(build, frame):
    out = pd.DataFrame(build(frame.copy()))
    if len(out) != len(frame) or set(out.index) != set(frame.index):
        raise ValueError("build_features must return one row per input row, with the input's index")
    return out


def same(a, b, index):
    cols = [c for c in numeric(a).columns if c in numeric(b).columns]
    a, b = numeric(a).loc[index, cols], numeric(b).loc[index, cols]
    return bool(cols) and bool(np.allclose(a.to_numpy(), b.to_numpy(), equal_nan=True, rtol=1e-6, atol=1e-9))


def leaks(build, min_features):
    """The first point-in-time violation of `build`, or None."""
    df = transactions()
    base = call(build, df)
    feats = numeric(base)
    varying = [c for c in feats.columns if feats[c].nunique(dropna=True) > 1]
    if len(varying) < min_features:
        return f"build_features: {len(varying)} varying numeric features, expected at least {min_features}"
    cut = df["timestamp"].iloc[len(df) * 2 // 3]
    early = df.index[df["timestamp"] < cut]
    later = df.copy()
    late = later["timestamp"] >= cut
    later.loc[late, "amount"] *= 10
    later.loc[late, "merchant_category"] = "travel"
    extra = df[late].head(200).copy()
    extra["timestamp"] = cut + pd.to_timedelta(np.arange(len(extra)), unit="s")
    extra["transaction_id"] += 10**6
    extra.index = extra.index + 10**6
    later = pd.concat([later, extra]).sort_values("timestamp", kind="stable")
    if not same(base, call(build, later), early):
        return "build_features: later transactions change features of earlier ones (future leak)"
    flipped = df.assign(is_fraud=1 - df["is_fraud"])
    if not same(base, call(build, flipped), df.index):
        return "build_features: features depend on is_fraud (target leak)"
    other = df.copy()
    user = df["user_id"].iloc[0]
    other.loc[other["user_id"] != user, "amount"] *= 7
    if not same(base, call(build, other), df.index[df["user_id"] == user]):
        return "build_features: other users' transactions change a user's features"
    return None


def run(*args):
    res = subprocess.run(
        [sys.executable, "-m", "fraud.train", *args], capture_output=True, text=True, check=False, timeout=900
    )
    if res.returncode:
        tail = (res.stderr or res.stdout).strip().splitlines()[-1:] or [""]
        return f"`python -m fraud.train {' '.join(args)}` exit {res.returncode}: {tail[0][:150]}", None
    path = Path("reports/metrics.json")
    if not path.exists():
        return "no reports/metrics.json after the run", None
    return None, dict(leaves(json.loads(path.read_text())))


def main(step):
    sys.path[:0] = [str(Path.cwd()), str(Path.cwd() / "src")]
    Path("reports/metrics.json").unlink(missing_ok=True)
    error, flat = run()
    if error:
        return error
    aps = [v for k, v in flat.items() if any(m in k for m in PR_AUC) and number(v) and 0 < v <= 1]
    if len(aps) < 2:
        return "reports/metrics.json: fewer than two PR-AUC values in (0, 1]"
    try:
        build = importlib.import_module("fraud.features").build_features
    except (ImportError, AttributeError) as exc:
        return f"fraud.features.build_features: {exc}"
    try:
        error = leaks(build, 2 if step == "P1" else 3)
    except ValueError as exc:
        error = str(exc)
    if error:
        return error
    if step == "P1":
        return None
    for m in ("threshold", "precision", "recall"):
        if not any(m in k and number(v) for k, v in flat.items()):
            return f"reports/metrics.json: no {m}"
    costs = [v for k, v in flat.items() if "cost" in k and number(v)]
    if len(costs) < 2 or not any(v > 0 and v % 50 == 0 for v in costs):
        return "reports/metrics.json: no model cost next to the flag-nothing cost (a positive multiple of 50)"
    n_train = [v for k, v in flat.items() if k.endswith("n_train") and number(v)]
    if not n_train:
        return "reports/metrics.json: no n_train"
    error, past = run("--as-of", "2024-09-01")
    if error:
        return error
    n_past = [v for k, v in past.items() if k.endswith("n_train") and number(v)]
    if not n_past or not 0 < n_past[0] < n_train[0]:
        return f"--as-of 2024-09-01: n_train {n_past[:1]} not below the full run's {n_train[0]}"
    configs = [
        p
        for p in Path.cwd().rglob("*")
        if p.suffix in {".yaml", ".yml", ".toml", ".json"}
        and p.name != "pyproject.toml"
        and "reports" not in p.parts
        and ".git" not in p.parts
        and any(h in p.read_text(errors="ignore") for h in ("learning_rate", "max_depth", "max_iter", "n_estimators"))
    ]
    return None if configs else "no config file with gradient boosting hyperparameters"


if __name__ == "__main__":
    try:
        error = main(sys.argv[1])
    except Exception as exc:  # noqa: BLE001
        error = f"{type(exc).__name__}: {exc}"
    print(error or "ok")
    sys.exit(1 if error else 0)
