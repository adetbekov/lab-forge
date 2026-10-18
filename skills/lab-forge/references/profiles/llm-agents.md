# Profile - LLM applications and AI agents

## Lifecycle
use case and success metric -> small golden set with expected answers ->
baseline (simplest prompt or pipeline) -> iterate one change at a time
(prompt, retrieval, tool, model, graph) -> measure on the golden set ->
inspect traces for failures -> promote -> keep the eval as a regression gate.

## Four modes - do not mix them
| Mode | Tool | Answers |
|---|---|---|
| Explore | notebook / scratch script | what if I change X? |
| Spot-check | chat UI, a few manual examples | how does it look live? |
| Measure | eval runner on the golden set | better on average? anything broken? |
| Observe | tracing (Langfuse, LangSmith, OTel, logs) | why did it do that? |
Spot-checks are necessary but never proof. A change ships on the eval number.

## Unit of decomposition
One of: a tool (function with a typed contract and its own tests), a prompt
change, a retrieval change behind a stable `search()`-like signature, a new
scenario added to the golden set, a graph step or handoff. Each unit is changed
and measured on its own.

## Done means
- the unit has a clear contract (inputs, outputs, errors);
- eval run reported with the delta against the committed baseline; per-run
  outputs stay git-ignored, the baseline is updated only on promotion;
- failures on the golden set are either fixed or listed with a reason.

## Repo block
Copied into the repo `AGENTS.md` verbatim, markers included, in deploy and seed mode.
Never paraphrase it; `verify_setup.py` checks the sha.

<!-- lab-forge:begin profile llm-agents sha=d52e32ae8aeb -->
P1. Prompts live in dedicated files or modules, versioned, not inline strings scattered in code.
P2. Tools validate inputs and return explicit errors; the agent never gets a raw stack trace.
P3. Agents write only drafts where a human must approve (data, KB, external actions).
P4. No secrets or personal data in prompts, traces or eval sets.
P5. An eval report has the delta vs the committed baseline, plus cost and latency.
P6. Bare `pytest` from the root is green. A new project gets a minimal `pyproject.toml` (name, deps,
    `[tool.pytest.ini_options]` `pythonpath = ["."]`); it is setup, not layout.
<!-- lab-forge:end -->

## Domain slop to forbid in rules
- Changing prompt, model and retrieval in one step.
- Adding a framework or wrapper layer for one call.
- "Fixing" a failure by special-casing the golden example.
- Retries and fallbacks that hide model errors instead of logging them.
