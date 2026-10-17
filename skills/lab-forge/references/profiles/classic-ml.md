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

## Invariants worth proposing
- Target and features computed for the same period and population.
- No information from after the prediction date in features (leakage check).
- Split and seeds from config; the same split for every compared model.
- Data, model files and per-run metrics are not committed; only the baseline metrics file is.

## Domain slop to forbid in rules
- Changing the split or the metric while comparing models.
- Fitting preprocessing on the full dataset.
- Silent row drops or fills without logging counts.
- Re-implementing a metric the project or library already has.
