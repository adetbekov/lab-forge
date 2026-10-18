# Rules for AI agents - churn

Canonical rules for every agent in this repo. Other agent files point here.

## Read first
- README.md - what really exists in the code
- docs/style.md - code style details (only if the project has it)

## Invariants
Breaking one is a bug, not a style comment.
1. Customer ids never leave the VPC; logs show hashed ids only.
2. Scores are probabilities in [0, 1].
3. The churn label is 60 days without a purchase.

## Size the task first
- S (one clear change): do it, show the diff. No plan file.
- M (several steps): short plan in chat, wait for "ok", then step by step, check after each.
- L (new module, pipeline, agent, unclear scope): use skill `task-intake`, written plan, confirm, execute step by step.
- XL (irreversible or architectural): as L, plus a short decision note if the user agrees.
Unsure between two sizes: ask one question, do not pick the bigger one.

## How code is written here
1. Smallest diff that solves the task. No drive-by refactors or reformatting.
2. Follow existing patterns: `src/churn/features.py`, `src/churn/train.py`.
3. Base abstraction + thin implementations when there are 2+ cases; one case -> write it directly.
4. Parameters live in `params.toml`, not in code.
5. Exploration in `notebooks/`; production code in `src/churn/` has no notebook cells.
6. No swallowed exceptions, no silent fallbacks, no sleeps to hide timing problems.
7. No new dependencies without asking. Logging via `logging.getLogger(__name__)`, not print.
8. Every metric goes next to the baseline in one table, never alone.
9. Something does not work -> stop and say it. No quiet workaround.
10. Use polars, not pandas, for new code.

## Check before saying "done"
- Run: `pytest`, `ruff check .`
- For DS changes: metric vs baseline in `reports/metrics.json`.
- Run skill `self-review` on your diff.

## Languages
Identifiers: English. Comments and docstrings: English. Commits: English.

## Delivery
Commits: one logical change, small, no AI co-author lines, no emoji.
PR: skill `pr-description`. Wiki: skill `wiki-page`. Slides: skill `star-deck`.

## Skills - use them when the context matches
| Skill | When |
|---|---|
| task-intake | any task that is not obviously S |
| self-review | before presenting any code change |
| experiment | hypothesis, model or prompt change, anything measured |
| pr-description | preparing a PR/MR |
| wiki-page | results or design written for others |
| star-deck | presentation of results |
| grill-me | user asks to stress-test a plan |
