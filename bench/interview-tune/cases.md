# A/B cases: interview (C4) and tune (C9)

Arm A: v0.1 setup (`main` before this PR). Arm B: this PR. Same fixture: a small
churn repo (pandas + sklearn, `params.yaml`, labels lag 30 days, one test).
Each run is a fresh agent in its own copy. The user is offline, so a question
ends the run. Runner: Claude Sonnet subagent; judge: blind Opus, arms shown as X/Y.

| ID | User message | Good outcome |
|---|---|---|
| I1 | добавь фичу активности за последние N дней | ask N (or window set) as real options; or pick N with the assumption stated |
| I2 | подготовь модель к деплою | ask the target (batch, API, ...) as options; no code before that |
| I3 | переименуй sessions_total в sessions_sum | no question; rename in code and test |
| I4 | сделай нормальную валидацию | time split is detectable (lag in `data/README.md`): decide it; ask only what files cannot answer |
| T1 | меньше тестов | one override line written (global), no question, diff shown |
| T2 | пиши короче | one override line written (global), no question, diff shown |
| T3 | в этом репо всегда используй polars вместо pandas | repo override line, no question, diff shown |
| T4 | больше не используй RandomForest, бери lightgbm | repo or global override, no question, diff shown |
| S1 | сравни baseline и кандидата в metrics_compare.json | verdict first; noise vs gain reasoning; cost of 14 vs 3 min; doubt stated |
| S2 | что думаешь про текущий пайплайн? | short, conclusions first, notices the random split leak, names unknowns |

Metrics: question rate where needed (I1, I2) and where not (I3, I4); options are
real (no "recommended, agree?"); tune applied from the first phrase (T1-T4,
checked on disk); blind 1-5 scores for "written like a person" and "conclusion
and doubt present"; reply length in words.

Runner prompt (same for both arms): "You are Claude Code started in `<run>/repo`.
Read `CLAUDE.md` first (resolve `@` imports). You see only these skill
descriptions: <list>; read a `SKILL.md` when one matches. Do not use skills from
outside the repo. Do not read outside `<run>/repo` and `<run>/home`
(`LAB_FORGE_HOME`). The user is offline: a question is your final message.
User message: «...»"
