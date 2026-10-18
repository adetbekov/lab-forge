# Profile - classic ML (tabular, scoring, forecasting)

## Lifecycle
problem and success metric -> baseline -> data and target -> features ->
split -> train -> evaluate against baseline -> report -> productionize
(scheduled pipeline, inference) -> monitor (quality, drift) -> retrain trigger.

## Unit of decomposition
A stage with declared inputs, outputs and params: feature build for a period,
target build, split, train, evaluate, report, infer. One stage = one module or
script. Stages are wired by the project's orchestrator (DVC, a Flow class,
Airflow, Makefile) - detect which one and use it.

## Done means
- the stage runs from its entry point with params from config;
- outputs land where the next stage expects them;
- metrics are written to a file, compared with the baseline in the report.

## Experiment vs production
Exploration in notebooks (text format). A feature or model change is promoted
only with a metric delta on the same validation setup.

## Repo block
Copied into the repo `AGENTS.md` verbatim, markers included, in deploy and seed mode.
Never paraphrase it; `verify_setup.py` checks the sha.

<!-- lab-forge:begin profile classic-ml sha=d37f00ba73ed -->
P1. Each fitted step (scaling, encoding, calibration, threshold, early stopping, search) learns on rows
    it is not evaluated on: its own split or CV inside the training rows. The threshold is never
    picked on the rows the calibrator was fitted on.
P2. Split and seeds come from config; every compared model gets the same split and metric.
P3. Target and features cover the same period and population; nothing from after the prediction date.
P4. Data, model files and per-run metrics are not committed; only the baseline metrics file is.
P5. Bare `pytest` from the root is green. A new project gets a minimal `pyproject.toml` (name, deps,
    `[tool.pytest.ini_options]` `pythonpath = ["."]`); it is setup, not layout.
<!-- lab-forge:end -->

## Domain slop to forbid in rules
- Changing the split or the metric while comparing models.
- Fitting preprocessing on the full dataset, or calibration and threshold on the same rows.
- Silent row drops or fills without logging counts.
- Re-implementing a metric the project or library already has.
