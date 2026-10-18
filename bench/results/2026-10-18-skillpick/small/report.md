# skillpick: `decide skill` hint vs no hint

36 synthetic prompts (30 with a right skill, the rest need none), 10 synthetic DS/ML skills. Agent: `claude -p`, claude-sonnet-5-5.

## d1-ultra router alone

| Metric | Value |
|---|---|
| Top-1 right (incl. `none`) | 36/36 (100%) |
| Hints given (confidence ≥ 0.7) | 30 |
| Hints that are right | 30/30 (100%) |
| Hints on prompts that need no skill | 0 |
| Prompts needing a skill that got the right hint | 30/30 (100%) |
| Latency p50, ms | 512 |

## Agent: right skill loaded

| Metric | hint | base |
|---|---|---|
| Sessions (errors) | 36 (0) | 36 (0) |
| Right skill loaded | 30/30 (100%) | 28/30 (93%) |
| ... on implicit prompts | 18/18 (100%) | 16/18 (89%) |
| Wrong skill loaded | 0 | 0 |
| No skill loaded when one fits | 0 | 2 |
| A skill loaded when none fits | 0/6 | 0/6 |
| Sessions with a hint | 30 | 0 |
| Tokens, k | 1271 | 1330 |
| Session time p50, s | 11.9 | 12.4 |
