"""Hidden acceptance check: python check.py P1|P2, run from a copy of the project root."""

import importlib
import inspect
import logging
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

SIGNATURE = [
    "self",
    "func",
    "n_trials",
    "timeout",
    "n_jobs",
    "catch",
    "callbacks",
    "gc_after_trial",
    "show_progress_bar",
]


def find_function():
    for path in sorted(Path("optuna").rglob("*.py")):
        if re.search(r"^def find_duplicate_trials\(", path.read_text(), re.MULTILINE):
            module = importlib.import_module(".".join(path.with_suffix("").parts))
            return module.find_duplicate_trials
    return None


def check_p1(optuna):
    fn = find_function()
    if fn is None:
        return "no top-level `def find_duplicate_trials(` under optuna/"
    from optuna.distributions import FloatDistribution
    from optuna.trial import TrialState, create_trial

    dist = {"x": FloatDistribution(0, 10), "y": FloatDistribution(0, 10)}
    specs = [
        ({"x": 1.0, "y": 2.0}, TrialState.COMPLETE),
        ({"x": 2.0, "y": 2.0}, TrialState.COMPLETE),
        ({"y": 2.0, "x": 1.0}, TrialState.COMPLETE),
        ({"x": 2.0, "y": 2.0}, TrialState.FAIL),
        ({"x": 3.0, "y": 3.0}, TrialState.COMPLETE),
        ({"x": 3.0, "y": 3.0}, TrialState.COMPLETE),
        ({"x": 1.0, "y": 2.0}, TrialState.COMPLETE),
    ]
    trials = []
    for number, (params, state) in enumerate(specs):
        value = 0.0 if state == TrialState.COMPLETE else None
        trial = create_trial(params=params, distributions=dist, value=value, state=state)
        trial.number = number
        trials.append(trial)
    got = [sorted(g) for g in fn(trials)]
    if got != [[0, 2, 6], [4, 5]]:
        return f"find_duplicate_trials returned {got}, expected [[0, 2, 6], [4, 5]]"
    if list(fn(trials[:2])) != []:
        return "expected [] when there are no duplicates"
    return None


def run_study(optuna, values):
    records = []
    handler = logging.Handler(logging.WARNING)
    handler.emit = records.append
    logger = logging.getLogger("optuna")
    logger.addHandler(handler)
    try:
        study = optuna.create_study()
        for x in values:
            study.enqueue_trial({"x": x})
        study.optimize(lambda t: t.suggest_float("x", 0, 10), n_trials=len(values))
    finally:
        logger.removeHandler(handler)
    return study, [r for r in records if r.levelno >= logging.WARNING]


def check_p2(optuna):
    params = list(inspect.signature(optuna.study.Study.optimize).parameters)
    if params != SIGNATURE:
        return f"optimize signature changed: {params}"
    study, dup = run_study(optuna, [1.0, 1.0, 2.0])
    if len(dup) != 1:
        return f"expected exactly one warning from optuna loggers, got {len(dup)}"
    if not all(str(n) in dup[0].getMessage() for n in (0, 1)):
        return "warning does not list trial numbers 0 and 1"
    if [t.params["x"] for t in study.trials] != [1.0, 1.0, 2.0]:
        return "trials changed"
    _, dup = run_study(optuna, [1.0, 2.0])
    return f"{len(dup)} warning(s) without duplicates" if dup else None


if __name__ == "__main__":
    import optuna

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    try:
        error = (check_p1 if sys.argv[1] == "P1" else check_p2)(optuna)
    except Exception as exc:  # noqa: BLE001
        error = f"{type(exc).__name__}: {exc}"
    print(error or "ok")
    sys.exit(1 if error else 0)
