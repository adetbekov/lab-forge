"""Hidden acceptance check: python check.py P1|P2, run from a copy of the project root."""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

import numpy as np
import pandas as pd
from category_encoders import CountEncoder
from sklearn.base import clone

X = pd.DataFrame({"c": ["a", "a", "a", "b", "b", "c"]})
COUNTS = np.array([3, 3, 3, 2, 2, 1])


def encode(**kw):
    return CountEncoder(cols=["c"], **kw).fit(X).transform(X)["c"].to_numpy(dtype=float)


def raises_at_fit(**kw):
    try:
        enc = CountEncoder(cols=["c"], **kw)
    except Exception as exc:  # noqa: BLE001
        return f"{kw} raised {type(exc).__name__} at construction, expected ValueError at fit"
    try:
        enc.fit(X)
    except ValueError:
        return None
    except Exception as exc:  # noqa: BLE001
        return f"{kw} raised {type(exc).__name__} at fit, expected ValueError"
    return f"{kw} did not raise"


def check_p1():
    if not np.allclose(encode(), COUNTS):
        return "default encoding changed"
    if not np.allclose(encode(log_counts=True), np.log1p(COUNTS)):
        return "log_counts=True is not log1p(count)"
    enc = CountEncoder(cols=["c"], log_counts=True)
    if clone(enc).get_params().get("log_counts") is not True:
        return "log_counts lost by clone/get_params"
    return raises_at_fit(log_counts=True, normalize=True)


def check_p2():
    error = check_p1()
    if error:
        return error
    if not np.allclose(encode(log_counts=True, log_base=10), np.log10(1 + COUNTS)):
        return "log_base=10 is not log10(1 + count)"
    if not np.allclose(encode(log_counts=True, log_base=2), np.log2(1 + COUNTS)):
        return "log_base=2 is not log2(1 + count)"
    if not np.allclose(encode(log_counts=True, log_base=math.e), np.log1p(COUNTS)):
        return "log_base=e differs from default"
    for bad in (1, 0.5, 0, -2, "abc", True):
        error = raises_at_fit(log_counts=True, log_base=bad)
        if error:
            return error
    return None


if __name__ == "__main__":
    try:
        error = (check_p1 if sys.argv[1] == "P1" else check_p2)()
    except Exception as exc:  # noqa: BLE001
        error = f"{type(exc).__name__}: {exc}"
    print(error or "ok")
    sys.exit(1 if error else 0)
