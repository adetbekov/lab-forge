# Rules for AI agents - {{project_name}}

Canonical rules for every agent in this repo. Other agent files point here.
An explicit requirement in the task (command, path, format, status code) beats every rule below; on conflict follow the task and say which rule you set aside.

## Read first
- {{status_or_readme}} - what really exists in the code
- {{conventions_link}} - code style details (only if the project has it)

## Invariants
Breaking one is a bug, not a style comment.
1. {{invariant_from_restrictions}}
2. {{invariant_from_audit}}

## Size the task first
- S (one clear change): do it, show the diff. No plan file.
- M (several steps): short plan in chat, wait for "ok", then step by step, check after each.
- L (new module, pipeline, agent, unclear scope): use skill `task-intake`, written plan, confirm, execute step by step.
- XL (irreversible or architectural): as L, plus a short decision note if the user agrees.
Unsure between two sizes: ask one question, do not pick the bigger one.

## How code is written here
1. Smallest diff that solves the task. No drive-by refactors or reformatting.
2. Follow existing patterns: {{pattern_examples_with_paths}}.
3. Base abstraction + thin implementations when there are 2+ cases; one case -> write it directly.
4. Parameters live in {{params_file}}, not in code. Its format is one the env can already read (TOML via `tomllib`, JSON; YAML only if PyYAML is installed).
5. Exploration in {{exploration_path}}; production code in {{production_path}} has no notebook cells.
6. No swallowed exceptions, no silent fallbacks, no sleeps to hide timing problems.
7. No new dependencies without asking. Logging via {{logger}}, not print.
8. {{pain_point_rule}}
9. Something does not work -> say it, no quiet workaround. A defect that breaks an explicit requirement is fixed now, not reported for later - even when the user is away.

## Check before saying "done"
- Run: {{test_command}}, {{lint_command}}
- For DS changes: metric vs baseline in {{metrics_location}}. Commit the baseline only; per-run outputs go to a git-ignored folder.
- Run skill `self-review` on your diff.

## Talking to the user
1. Write like a colleague in chat: line one is the verdict, then only what changes a decision. Aim for 10 lines; no headers or tables for under 5 facts.
2. Every number gets a conclusion: what it means and what to do next.
3. Name your assumptions and what you do not know, with how sure you are and what would settle it.
4. Noticed something odd outside the task? One line, do not fix it.
5. After code work, end with `DONE` or `DONE_WITH_CONCERNS` plus the concerns. A question needs no status line.
6. Ask only through skill `grill`: real options, never "I recommend X, agree?".
7. A lasting preference ("always", "never", "fewer tests", "пиши короче") is a tune: apply it at once via skill `lab-forge`, show the diff, `undo` reverts.

## Languages
Identifiers: {{lang_code}}. Comments and docstrings: {{lang_comments}}. Commits: {{lang_commits}}.

## Delivery
Commits: one logical change, small, no emoji. AI co-author trailer: {{coauthor_policy}}; a policy set by the harness or environment wins.
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
| grill | short or ambiguous ask, the user may know more, two approaches differ |

## Overrides
Written by tune. They beat every rule above; only an explicit ask in this session beats them.
