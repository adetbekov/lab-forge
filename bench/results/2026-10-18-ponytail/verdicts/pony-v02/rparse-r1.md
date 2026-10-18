Blind map (added after review): {'X': 'v02', 'Y': 'pony'}

Overall: X: pydantic schema, ParseError with raw reply, versioned prompt, committed baseline, eval survives parse errors. Y barely validates replies, eval aborts on one bad receipt. X P3 refs largely wrong.

```json
{"X": {"P1": {"success": 5, "correctness": 4, "practices": 5, "optimality": 4, "bloat": 4, "scope": 4}, "P2": {"success": 5, "correctness": 4, "practices": 5, "optimality": 5, "bloat": 5, "scope": 5}, "P3": {"accuracy": 2, "completeness": 5, "conciseness": 3, "usefulness": 4}, "clarity": 4, "questions": 5}, "Y": {"P1": {"success": 4, "correctness": 3, "practices": 3, "optimality": 4, "bloat": 5, "scope": 5}, "P2": {"success": 5, "correctness": 3, "practices": 4, "optimality": 4, "bloat": 5, "scope": 5}, "P3": {"accuracy": 5, "completeness": 5, "conciseness": 4, "usefulness": 5}, "clarity": 4, "questions": 5}, "winner": {"P1": "X", "P2": "X", "P3": "Y", "overall": "X"}}
```
