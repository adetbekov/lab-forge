# {{project_name}}

## Commands
- Test: `{{test_command}}`
- Lint: `{{lint_command}}`
- Run: `{{run_command}}`
- Done: test and lint pass; a DS change has its metric vs baseline in {{metrics_location}}
  (commit the baseline only; per-run outputs go to a git-ignored folder).

## Map
- Read first: {{status_or_readme}}. Production code: {{production_path}}. Exploration:
  {{exploration_path}}; production has no notebook cells.
- Parameters: {{params_file}}, not code, in a format the env already reads (TOML via `tomllib`,
  JSON; YAML only if PyYAML is installed). Metrics vs baseline: {{metrics_location}}.
- Follow these patterns: {{pattern_examples_with_paths}}. Logging: {{logger}}, not print.

## Invariants (breaking one is a bug, not a style comment)
{{profile_block}}
1. {{invariant_from_restrictions}}
2. {{pain_point_rule}}

## Words
- {{domain_term}}: {{meaning}}

## Languages
Identifiers: {{lang_code}}. Comments and docstrings: {{lang_comments}}. Commits: {{lang_commits}}.
AI co-author trailer: {{coauthor_policy}} (a harness or environment policy wins).

## Overrides
Written by tune; a line may replace a D rule, never relax a C or P rule.
