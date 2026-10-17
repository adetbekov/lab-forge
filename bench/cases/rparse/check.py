"""Hidden acceptance check: python check.py P1|P2, run from a copy of the project root."""

import re
import subprocess
import sys
from pathlib import Path


def main(step):
    if not any(re.search(r"^def parse_receipt\(", p.read_text(), re.MULTILINE) for p in Path("rparse").rglob("*.py")):
        return "no `def parse_receipt(` in rparse/"
    run = subprocess.run(
        [sys.executable, "-m", "rparse.eval"], capture_output=True, text=True, check=False, timeout=600
    )
    out = (run.stdout + run.stderr).lower()
    if run.returncode:
        return f"`python -m rparse.eval` exit {run.returncode}: {out.strip().splitlines()[-1:]}"
    need = ["f1", "total"] if step == "P1" else ["name", "quantity", "unit_price", "line_total"]
    missing = [w for w in need if w not in out]
    if missing:
        return f"eval output lacks {missing}"
    if step == "P2":
        tests = " ".join(p.read_text().lower() for p in Path(".").rglob("test*.py") if ".venv" not in p.parts)
        if not re.search(r"retr|attempt", tests):
            return "no test mentions retry/attempt"
    return None


if __name__ == "__main__":
    try:
        error = main(sys.argv[1])
    except Exception as exc:  # noqa: BLE001
        error = f"{type(exc).__name__}: {exc}"
    print(error or "ok")
    sys.exit(1 if error else 0)
