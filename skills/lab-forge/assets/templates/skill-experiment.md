---
name: experiment
description: Runs a DS/ML or LLM change as a measured experiment - hypothesis, baseline, one change at a time, metric delta, then promote or drop. Use this whenever the user wants to try a model, feature, prompt, retrieval or tool change, compare approaches, improve a metric, or says "experiment", "hypothesis", "try", "compare", "is it better".
---

# experiment

Profile: {{domain_profile}}. Tracker/orchestrator: {{tracking_and_orchestration}}.

1. **Hypothesis** - one sentence: "Changing X will improve metric M on set S,
   because ...". No metric -> ask for it before anything else.
2. **Baseline** - find the last recorded result in {{metrics_location}}. None ->
   the first step is to produce it with the current code.
3. **One change** - change a single thing. Several ideas -> several runs.
4. **Run where experiments live** - {{exploration_path}} for exploration;
   parameters through {{params_file}}; same data split / eval set as baseline.
5. **Measure** - report `baseline -> new` for the main metric plus cost/latency
   or runtime where relevant. Look at failures, not only the average.
6. **Decide** - better: propose promotion into {{production_path}} behind the
   existing interface, with the metric in the PR. Not better: record the result
   in one line and drop the code.
