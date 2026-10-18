# {{project_name}}

Project facts for every agent. How to work (branches, scope, task size, style)
comes from the global rules in `~/.lab-forge/AGENTS.md`; do not repeat them here.

## Read first
- {{status_or_readme}} - what really exists in the code

## Commands
Copied from the project, never invented.
- Test: `{{test_command}}`
- Lint: `{{lint_command}}`
- Run: `{{run_command}}`

## Map
- Production code: {{production_path}}. Exploration: {{exploration_path}}; production has no notebook cells.
- Parameters: {{params_file}}, not code, in a format the env already reads (TOML via `tomllib`,
  JSON; YAML only if PyYAML is installed). Metrics vs baseline: {{metrics_location}}.
- Follow these patterns: {{pattern_examples_with_paths}}. Logging: {{logger}}, not print.

## Invariants
Breaking one is a bug, not a style comment.
1. {{invariant_from_restrictions}}
2. {{invariant_from_audit}}
3. {{pain_point_rule}}

## Words
- {{domain_term}}: {{meaning}}

## Done means
`{{test_command}}` and `{{lint_command}}` pass, a DS change has its metric vs
baseline in {{metrics_location}} (commit the baseline only; per-run outputs go to a
git-ignored folder), and skill `self-review` ran on the diff.

## Languages
Identifiers: {{lang_code}}. Comments and docstrings: {{lang_comments}}. Commits: {{lang_commits}}.

## Delivery
AI co-author trailer: {{coauthor_policy}}; a policy set by the harness or environment wins.
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
