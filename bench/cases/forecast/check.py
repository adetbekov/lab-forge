"""Hidden acceptance check: python check.py P1|P2, run from a copy of the project root.

Besides running the entry point it probes `forecast.features.make_features` for point-in-time correctness:
a day's features may not move when that day's or later sales change (P2: the last `horizon - 1` days before it
too), nor when another store's sales change.
"""

import importlib
import inspect
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


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


def sales(seed=0, stores=4, days=200):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", periods=days, freq="D")
    rows = [
        {"date": d, "store_id": s, "sales": float(rng.poisson(50 + 10 * s + 15 * (d.dayofweek >= 5)))}
        for s in range(stores)
        for d in dates
    ]
    return pd.DataFrame(rows)


def numeric(frame):
    out = pd.DataFrame(frame).select_dtypes(include=["number", "bool"]).astype(float)
    return out.drop(columns=[c for c in out.columns if str(c) in {"store_id", "sales"}])


class Shape(Exception):
    """The function's output does not line up with its input."""


def call(make, frame, horizon):
    out = pd.DataFrame(make(frame.copy()) if horizon is None else make(frame.copy(), horizon=horizon))
    if len(out) != len(frame) or set(out.index) != set(frame.index):
        raise Shape("make_features must return one row per input row, with the input's index")
    return out


def same(a, b, index):
    cols = [c for c in numeric(a).columns if c in numeric(b).columns]
    a, b = numeric(a).loc[index, cols], numeric(b).loc[index, cols]
    return bool(cols) and bool(np.allclose(a.to_numpy(), b.to_numpy(), equal_nan=True, rtol=1e-6, atol=1e-9))


def leaks(make, horizon=None):
    """The first point-in-time violation of `make`, or None. horizon=None calls make(df) as P1 asks."""
    df = sales()
    base = call(make, df, horizon)
    feats = numeric(base)
    if sum(feats[c].nunique(dropna=True) > 1 for c in feats.columns) < 2:
        return "make_features: fewer than two varying numeric features"
    gap = horizon or 1
    cut = df["date"].min() + pd.Timedelta(days=120)
    known = df.index[df["date"] <= cut]
    later = df.copy()
    later.loc[later["date"] > cut - pd.Timedelta(days=gap), "sales"] *= 3
    if not same(base, call(make, later, horizon), known):
        what = "that day's or later sales" if gap == 1 else f"sales less than {gap} days earlier"
        return f"make_features(horizon={horizon}): {what} change a day's features (leak)"
    other = df.assign(sales=np.where(df["store_id"] == 0, df["sales"], df["sales"] * 5))
    if not same(base, call(make, other, horizon), df.index[df["store_id"] == 0]):
        return "make_features: other stores' sales change a store's features"
    return None


def run(*args):
    res = subprocess.run(
        [sys.executable, "-m", "forecast.backtest", *args], capture_output=True, text=True, check=False, timeout=900
    )
    if res.returncode:
        tail = (res.stderr or res.stdout).strip().splitlines()[-1:] or [""]
        return f"`python -m forecast.backtest {' '.join(args)}` exit {res.returncode}: {tail[0][:150]}", None
    path = Path("reports/metrics.json")
    if not path.exists():
        return "no reports/metrics.json after the run", None
    return None, dict(leaves(json.loads(path.read_text())))


def values(flat, name):
    return [v for k, v in flat.items() if name in k and number(v) and v >= 0]


def main(step):
    sys.path[:0] = [str(Path.cwd()), str(Path.cwd() / "src")]
    Path("reports/metrics.json").unlink(missing_ok=True)
    error, flat = run()
    if error:
        return error
    if len(values(flat, "mae")) < 8:  # 2 models x (3 folds + mean)
        return f"reports/metrics.json: {len(values(flat, 'mae'))} MAE values, expected 2 models x (3 folds + mean)"
    try:
        make = importlib.import_module("forecast.features").make_features
    except (ImportError, AttributeError) as exc:
        return f"forecast.features.make_features: {exc}"
    try:
        if step == "P1":
            return leaks(make)
        if "horizon" not in inspect.signature(make).parameters:
            return "make_features has no horizon parameter"
        error = leaks(make, 7)
        if not error:
            try:
                error = leaks(make, 14)
            except ValueError:  # rejected horizon 14 with its default lags, e.g. a lag of 7; `--horizon 14` runs below
                pass
    except (Shape, ValueError) as exc:
        error = str(exc)
    if error:
        return error
    wape = values(flat, "wape")
    if len(wape) < 8:
        return f"reports/metrics.json: {len(wape)} WAPE values, expected 2 models x (3 folds + mean)"
    best = [v for k, v in flat.items() if k.endswith("best_model") and isinstance(v, str) and v]
    if not best:
        return "reports/metrics.json: no best_model"
    error, longer = run("--horizon", "14")
    if error:
        return error
    if sorted(values(longer, "wape")) == sorted(wape):
        return "--horizon 14 gives the same WAPE as the default: the flag is ignored"
    configs = [
        p
        for p in Path.cwd().rglob("*")
        if p.suffix in {".yaml", ".yml", ".toml", ".json"}
        and p.name != "pyproject.toml"
        and "reports" not in p.parts
        and ".git" not in p.parts
        and "horizon" in (text := p.read_text(errors="ignore"))
        and any(h in text for h in ("learning_rate", "max_depth", "max_iter", "n_estimators", "max_leaf_nodes"))
    ]
    return None if configs else "no config file with the horizon and gradient boosting hyperparameters"


if __name__ == "__main__":
    try:
        error = main(sys.argv[1])
    except Exception as exc:  # noqa: BLE001
        error = f"{type(exc).__name__}: {exc}"
    print(error or "ok")
    sys.exit(1 if error else 0)
