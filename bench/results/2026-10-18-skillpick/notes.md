# skillpick: does the `decide skill` hint load the right skill?

Question: with a d1-ultra hint (`guard.py decide skill`, hosted) does `claude -p` load the right skill more often
than without one, and does it pay for that in tokens or wrong loads?

Setup (`bench/skillpick/skillpick.py`, synthetic only): 10 DS/ML skills, 36 prompts (30 need a skill, 6 need none;
18 implicit, 12 explicit, English and Russian). Each session gets a fresh project with the skills in
`.claude/skills`, its own `HOME`, `--max-turns 3`; the metric is the first `Skill` tool call. Agent model
`claude-sonnet-5-5` (the CLI default here), 1 repeat. The base arm has the same hook with backend `off`.

```bash
with-secrets -- python bench/skillpick/skillpick.py router --out DIR [--crowded]
with-secrets -- python bench/skillpick/skillpick.py agent --out DIR --reps 1 [--crowded --kinds implicit none]
python bench/skillpick/skillpick.py report --out DIR
```

## Results

| Round | Right skill, hint | Right skill, base | Wrong loads | Loads when none fits | Tokens hint vs base |
|---|---|---|---|---|---|
| small: 10 skills, 36 prompts, 72 sessions | 30/30 | 28/30 | 0 / 0 | 0/6 / 0/6 | −4% (1271k vs 1330k) |
| crowded: 30 skills, 24 implicit + none prompts, 48 sessions | 18/18 | 15/18 | 0 / 0 | 0/6 / 0/6 | −4% (882k vs 921k) |

- The router alone: 36/36 top-1 in both rounds, every hint (≥ 0.7) right, no hint on a prompt that needs no skill,
  p50 0.49 s.
- Base misses are always "loaded nothing", never a wrong skill, and always the vaguest prompts: "squeeze more out
  of the default LightGBM" (hparam-search), "is the new system prompt better" (llm-eval), "val AUC 0.99, prod 0.61"
  (leakage-audit). The hint fixes all of them.
- Bug found and fixed: `decide skill` offered only the first 25 skills by name, so in the crowded setup
  `timeseries-backtest` never reached the model (router 33/36, `crowded/router.cap25.jsonl`). The cap is now 60
  (`MAX_SKILLS`): a 60-way choice answers in ~0.5 s, 100 skills reach 1.2 s against the 1.5 s timeout. After the
  fix the two affected hint sessions were rerun; the hint arm without the fix was 18/18 too, the agent found that
  skill on its own.

## Limits

1 repeat, synthetic prompts written with the skill list in view, short sessions (first tool call, not task
outcome). The gain is 5 sessions out of 48 base misses; with Opus or a different skill set the base may already
be at 100%.
