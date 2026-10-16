# Results: interview (C4) and tune (C9), 2026-10-17

**Verdict: B (this PR) beats v0.1 on every case it was meant to fix.** Questions
became real choices (blind score 4.4 vs 1.8), and tune now applies from the first
phrase (4/4 vs 2/4). After one fix to the writing rules, B also reads more like
a person (4.3 vs 3.7). n=1 per case and judge noise is about ±1 point, so treat
the per-case scores as direction, not precision.

## Tune: applied from the first phrase (checked on disk)

| Case | A: v0.1 | B: this PR |
|---|---|---|
| T1 меньше тестов | rule added to `CLAUDE.md`, plus "if you meant delete tests, say so" | global override, diff, `undo` |
| T2 пиши короче | asked "записать?", nothing written | global override, diff, `undo` |
| T3 всегда polars (repo) | rule added, two other lines rewritten | repo override, diff, flagged the stale "pandas" line |
| T4 больше не RandomForest | asked about the dependency and about writing a rule; nothing written | repo override plus the code change |
| **Applied with no question** | **2/4** | **4/4** |

## Interview and writing: blind judge (Opus, arms shown as X/Y)

Scores are 1-5 for question quality / human / doubt / brevity.

| Case | A: v0.1 | B: this PR | Winner |
|---|---|---|---|
| I1 фича за N дней | 2/3/3/4, "(рекомендую)" plus a straw man | 4/3/4/3, real options, `1b` | B |
| I2 подготовь к деплою | 1/4/4/3, "мой рекомендованный ответ" | 4/3/4/2, 3 questions with options | B |
| I3 rename | no question | no question, plus one line out of scope | tie (not judged) |
| I4 нормальная валидация | 2/4/4/3, "моя рекомендация (a)" | 5/3/5/4, also caught the feature leak | B |
| S1 сравни модели | 2/4/4/4, ends with a needless question | 5/4/5/4, states assumptions and confidence | B |
| S2 мнение о пайплайне | 2/4/4/2, "если согласны..." | 4/4/4/3 | B |
| **Mean** | **1.8 / 3.8 / 3.8 / 3.2** | **4.4 / 3.4 / 4.4 / 3.2** | **B 5/5** |

Round 1 showed B was less human (3.4 vs 3.8) and no shorter: a `NEEDS_CONTEXT`
line repeated the question, and replies used report headers. Fix: "write like a
colleague in chat, aim for 10 lines, no headers for under 5 facts; a question
needs no status line". Round 2, a fresh judge on I1, I2 and S2:

| Case | A | B after the fix | Winner | Words A → B |
|---|---|---|---|---|
| I1 | 2/3/4/4 | 4/4/4/3 | B | 145 → 168 |
| I2 | 2/4/4/3 | 4/4/4/3 | B | 208 → 211 |
| S2 | 3/4/4/2 | 4/5/5/4 | B | 353 → 242 |
| **Mean** | **2.3 / 3.7 / 4.0 / 3.0** | **4.0 / 4.3 / 4.3 / 3.3** | **B 3/3** | |

## What is still weak

- Questions are not shorter: B asks 2-3 questions with options where A asked one.
  Each is answerable as `1b 2a`, but the message is longer. Tune `пиши короче`
  covers users who want less.
- I4: the time split could be decided from `data/README.md`, and both arms still
  asked. The gate "if one option is clearly right, decide" did not fire there.
- One runner (Sonnet), one fixture, n=1. Rerun on the JEB-1877 bench when it lands.
