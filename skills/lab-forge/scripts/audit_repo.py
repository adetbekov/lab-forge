"""Mechanical audit of one project for lab-forge phase 1.

Stdlib only. Reports signals; judgement stays with the agent (references/audit.md).
Never prints secret values - only file names and counts.

Usage:
    python audit_repo.py <project> [--json]
"""

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".mypy_cache",
             ".ruff_cache", ".pytest_cache", "site", "dist", "build", ".dvc", "mlruns",
             ".import_linter_cache", ".tox", ".idea"}
EXPLORATION_DIRS = {"notebooks", "notebook", "sandbox", "scratch", "experiments",
                    "research", "examples", "docs"}
RULE_FILES = ["AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md",
              ".cursorrules"]
DATA_EXT = {".csv", ".parquet", ".pkl", ".pickle", ".joblib", ".h5", ".feather",
            ".xlsx", ".npy", ".npz", ".pt", ".onnx", ".bin"}
SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"\s]{12,}['\"]"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
]
PY_SMELLS = {
    "bare_except": re.compile(r"^\s*except\s*:"),
    "except_pass": re.compile(r"^\s*except[^:]*:\s*pass\b"),
    "print_call": re.compile(r"^\s*print\("),
    "todo_no_ticket": re.compile(r"#\s*TODO(?!\s*\()"),
    "sleep": re.compile(r"\btime\.sleep\("),
    "notebook_cell": re.compile(r"^# %%"),
}
ABC_CLASS = re.compile(r"^class\s+(\w+)\((?:[\w.]*\s*,\s*)*(?:ABC|abc\.ABC)\b")
LARGE_PY = 400
LARGE_DATA_BYTES = 5 * 1024 * 1024


def walk(project):
    for dirpath, dirnames, filenames in os.walk(project):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            yield Path(dirpath) / name


def read_lines(path):
    try:
        return path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []


def in_exploration(rel):
    return any(part.lower() in EXPLORATION_DIRS for part in rel.parts[:-1])


def audit(project):
    project = Path(project).resolve()
    lines_by_ext = Counter()
    md_sizes = {}
    large_py = []
    smells = defaultdict(list)
    abc_names = []
    py_texts = {}
    data_files = []
    secret_hits = []
    ipynb_in_prod = []

    for path in walk(project):
        rel = path.relative_to(project)
        ext = path.suffix.lower()
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if ext in DATA_EXT and size > LARGE_DATA_BYTES:
            data_files.append(f"{rel} ({size // (1024 * 1024)} MB)")
        if ext == ".ipynb" and not in_exploration(rel):
            ipynb_in_prod.append(str(rel))
        if ext not in {".py", ".md", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".env",
                       ".json", ".sh"} and path.name != ".env":
            continue
        lines = read_lines(path)
        lines_by_ext[ext or path.name] += len(lines)
        text = "\n".join(lines)
        if size < 2_000_000 and any(p.search(text) for p in SECRET_PATTERNS):
            secret_hits.append(str(rel))
        if path.name == ".env" and any("=" in l and l.split("=", 1)[1].strip()
                                       for l in lines if not l.startswith("#")):
            secret_hits.append(f"{rel} (non-empty values)")
        if ext == ".md":
            md_sizes[str(rel)] = len(lines)
        if ext == ".py":
            py_texts[str(rel)] = text
            if len(lines) > LARGE_PY:
                large_py.append(f"{rel} ({len(lines)})")
            exploration = in_exploration(rel)
            for i, line in enumerate(lines, 1):
                for name, pattern in PY_SMELLS.items():
                    if name == "notebook_cell" and exploration:
                        continue
                    if name == "print_call" and exploration:
                        continue
                    if pattern.search(line):
                        smells[name].append(f"{rel}:{i}")
                match = ABC_CLASS.match(line)
                if match:
                    abc_names.append((match.group(1), str(rel)))

    single_impl = []
    all_py = "\n".join(py_texts.values())
    for name, rel in abc_names:
        subclasses = len(re.findall(rf"class\s+\w+\([^)]*\b{name}\b", all_py))
        if subclasses <= 1:
            single_impl.append(f"{name} in {rel} ({subclasses} subclass)")

    rule_files, real_seen = {}, {}
    for r in RULE_FILES:
        path = project / r
        if not path.exists():
            continue
        real = path.resolve()
        if real in real_seen:
            continue  # symlink to a file already counted
        real_seen[real] = r
        rule_files[r] = len(read_lines(path))
    rule_lines = defaultdict(set)
    for r in rule_files:
        for line in read_lines(project / r):
            norm = line.strip().lower()
            if len(norm) > 40:
                rule_lines[norm].add(r)
    duplicated_rules = sum(1 for files in rule_lines.values() if len(files) > 1)

    skills_no_desc = []
    for skill in list(project.glob(".claude/skills/*/SKILL.md")) + \
            list(project.glob(".github/skills/*/SKILL.md")) + \
            list(project.glob(".agents/skills/*/SKILL.md")):
        head = "\n".join(read_lines(skill)[:15])
        if "description:" not in head:
            skills_no_desc.append(str(skill.relative_to(project)))

    code_lines = lines_by_ext.get(".py", 0)
    md_lines = sum(md_sizes.values())
    root_md = [p for p in md_sizes if "/" not in p and "\\" not in p]
    has = lambda *names: any((project / n).exists() for n in names)
    pyproject = "\n".join(read_lines(project / "pyproject.toml"))

    return {
        "project": str(project),
        "size": {"py_lines": code_lines, "md_lines": md_lines,
                 "md_to_code_ratio": round(md_lines / code_lines, 2) if code_lines else None,
                 "largest_md": sorted(md_sizes.items(), key=lambda x: -x[1])[:5],
                 "root_md": root_md},
        "ai_setup": {"rule_files": rule_files, "duplicated_rule_lines": duplicated_rules,
                     "skills_without_description": skills_no_desc},
        "structure": {"large_py_files": large_py[:10],
                      "abc_with_single_impl": single_impl[:10],
                      "ipynb_outside_exploration": ipynb_in_prod[:10]},
        "smells": {k: {"count": len(v), "examples": v[:3]} for k, v in smells.items()},
        "experiments": {
            "params_file": any(True for n in ("params.yaml", "params.json", "config.yaml",
                                              "settings.yaml")
                               for _ in project.rglob(n)),
            "dvc": has("dvc.yaml", ".dvc"),
            "mlflow": "mlflow" in all_py,
            "seed_in_code_or_config": bool(re.search(r"(?i)\b(random_state|seed)\b", all_py)),
            "metrics_file_hint": has("metrics.json", "artifacts/evaluation/metrics.json"),
            "eval_dir": has("eval", "evals", "tests/eval"),
            "large_data_files": data_files[:10],
        },
        "tooling": {
            "formatter_linter": bool(re.search(r"\[tool\.(ruff|black|flake8|pylint)", pyproject))
            or has(".flake8", "ruff.toml", ".pylintrc"),
            "pre_commit": has(".pre-commit-config.yaml"),
            "tests_dir": has("tests", "test"),
        },
        "safety": {"files_with_possible_secrets": secret_hits[:10]},
    }


def summary(report):
    s, a, st, e, t = (report["size"], report["ai_setup"], report["structure"],
                      report["experiments"], report["tooling"])
    out = [f"Project: {report['project']}",
           f"Code {s['py_lines']} py lines, docs {s['md_lines']} md lines "
           f"(ratio {s['md_to_code_ratio']}), root md: {len(s['root_md'])}",
           f"Rule files: {a['rule_files'] or 'none'}; duplicated rule lines: "
           f"{a['duplicated_rule_lines']}; skills w/o description: "
           f"{len(a['skills_without_description'])}",
           f"Large py files: {len(st['large_py_files'])}; ABC with single impl: "
           f"{len(st['abc_with_single_impl'])}; ipynb outside exploration: "
           f"{len(st['ipynb_outside_exploration'])}",
           "Smells: " + (", ".join(f"{k}={v['count']}" for k, v in report["smells"].items())
                         or "none"),
           f"Experiments: params={e['params_file']} dvc={e['dvc']} mlflow={e['mlflow']} "
           f"seed={e['seed_in_code_or_config']} eval_dir={e['eval_dir']} "
           f"big_data_files={len(e['large_data_files'])}",
           f"Tooling: lint={t['formatter_linter']} pre-commit={t['pre_commit']} "
           f"tests={t['tests_dir']}",
           f"Possible secrets in: {report['safety']['files_with_possible_secrets'] or 'none'}"]
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = audit(args.project)
    print(json.dumps(report, indent=2, ensure_ascii=False) if args.json else summary(report))


if __name__ == "__main__":
    main()
