# Onboarding audit

Goal: in one pass, see how the user's existing projects are set up, find what
makes the agent produce slop or makes work hard, and propose fixes the user can
pick from. The audit is a conversation starter, not a verdict.

## How to run

1. `scripts/audit_repo.py <project>` - mechanical signals (JSON + short text).
2. Read by hand: the rules files, 2-3 central modules, one pipeline or agent
   entry point, one notebook. Look for the judgement items below.
3. Learn the user's style from their hand-written code: what abstractions they
   use, how they name, how they configure. Style the user already has beats the
   pack's defaults when they conflict - note conflicts and ask.
4. Write the report from `assets/templates/audit-report.md`. At most 10
   findings, highest impact first. Group trivia into one line.

## Problem catalog

Severity: H - agent output gets worse or data/secrets at risk; M - slows work;
L - hygiene. "Lvl" is the ownership level needed to fix.

### A. AI setup
| Signal | Sev | Fix | Lvl |
|---|---|---|---|
| No rules file for the agent in use | H | canonical rules file | 0-1 |
| Two or more full rule files (drift) | H | merge into canonical, others -> pointers | 1 |
| Rules file over ~150 lines or mostly prose | M | cut to numbered rules + links | 1 |
| Skills without "when to use" in description | M | rewrite descriptions with triggers | 1 |
| Same knowledge in skill and rules file | L | keep one, link from the other | 1 |

### B. Docs
| Signal | Sev | Fix | Lvl |
|---|---|---|---|
| Markdown volume close to or above code volume | M | delete or merge; keep what a reader needs | 1 |
| Docs describe code that does not exist | H | move to a plans folder or delete | 1 |
| Many .md files in repo root | L | move under docs/ | 1 |

### C. Structure and style
| Signal | Sev | Fix | Lvl |
|---|---|---|---|
| Files over ~400 lines doing several jobs | M | propose split along stages | 1 |
| Same logic copied in 3+ places | M | extract a base or helper | 1 |
| Abstract class with a single implementation | L | inline, or keep if a second is planned | 1 |
| Parameters hard-coded in logic | M | move to the params/config file | 1 |
| Notebook cells or .ipynb inside production package | M | split exploration from production | 1 |

### D. Experiment hygiene (DS/ML)
| Signal | Sev | Fix | Lvl |
|---|---|---|---|
| No recorded baseline or metrics file | H | add metrics output + baseline step | 1 |
| No seed / non-reproducible split | M | seed in config | 1 |
| Datasets or models committed to git | H | move to data versioning or storage | 1-2 |
| No eval set for an LLM/agent project | H | small golden set + scorer | 1 |

### E. Safety
| Signal | Sev | Fix | Lvl |
|---|---|---|---|
| Secrets, tokens, .env with values in the repo | H | tell the user immediately; rotate; secret scan hook | 2 |
| Internal hosts or personal data in docs | M | remove from AI-visible files | 1 |

### F. Slop smells in code
Bare or swallowed exceptions, `print` in production, TODO without ticket,
sleep-based waits, dead code, deep nesting. Report as one grouped finding with
counts and 2-3 examples; propose a lint rule (level 2) rather than a mass edit.

### G. Tooling
No formatter/linter config, no tests on the critical path, no pre-commit. Offer
only at level 2+, and only the minimum set that matches the stack.

## What not to do in the audit

- Do not fix anything before the user picks.
- Do not report style differences as problems when the code is consistent.
- Do not open secrets files to "check" them; report the file name only.
