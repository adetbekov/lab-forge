#!/usr/bin/env python3
"""Repeatable A/B benchmark for lab-forge. Stdlib only; needs git and uv.

    python bench/bench.py all --out /tmp/lfb                    # headless `claude -p`, one command
    python bench/bench.py prepare --out /tmp/lfb                # then, for agent-driven runs:
    python bench/bench.py next --out /tmp/lfb                   #   prompts to run in fresh sessions
    python bench/bench.py record --out /tmp/lfb WS STEP --tokens N --tools N --ms N --reply FILE
    python bench/bench.py pack --out /tmp/lfb                   #   blind X/Y review prompts
    python bench/bench.py report --out /tmp/lfb                 #   report.md + runs.tsv

See bench/README.md for the protocol and the metric-to-pain map.
"""

import argparse
import fnmatch
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import tomllib

BENCH = Path(__file__).resolve().parent
AI_FILES = [
    "CLAUDE.md",
    "**/CLAUDE.md",
    "AGENTS.md",
    "**/AGENTS.md",
    "GEMINI.md",
    ".claude/**",
    ".agents/**",
    ".lab-forge/**",
    ".cursor/**",
    ".github/copilot-instructions.md",
    ".github/instructions/**",
]
DEPLOY = {
    "new": "Use the lab-forge skill ({skill}/SKILL.md) to set up my AI working environment for this NEW, currently "
    "empty project. The project will be: {brief} Only Claude Code is used. Ownership level 1 (repo files only "
    "— no hooks, no CI). I am not available: run in batch mode, every confirmation (skeleton etc.) is "
    "pre-approved, do not ask questions. Docs and commits in English.",
    "existing": "Use the lab-forge skill ({skill}/SKILL.md) to onboard this existing project: audit it and set up my "
    "AI working environment for it. Only Claude Code is used. Ownership level 1 (repo files only — no "
    "hooks, no CI changes). I am not available: run in batch mode, every confirmation (skeleton, fixes "
    "from the audit limited to AI-setup files) is pre-approved, do not ask questions. Do not change "
    "application code. Docs and commits in English.",
}
REPLY = {
    "deploy": "Follow the skill workflow and commit the result (one commit). When finished, reply with: files "
    "created or changed with line counts, and a 3-line summary.",
    "code": "When finished, reply with: what you changed (files + line counts), how you verified it (commands + "
    "results), and anything you'd flag.",
    "tune": "Reply to the user.",
    "question": "Reply with your answer to the user.",
}
MODE = {
    "deploy": "",
    "code": "The user is not available: do not ask questions, make reasonable decisions and state them; any plan you "
    "would show is pre-approved.",
    "tune": "The user is not available for follow-ups.",
    "question": "Read-only: do not modify, create or commit anything. The user is not available for follow-ups.",
}
SESSION = """You are a participant in a controlled experiment. Simulate a fresh Claude Code session whose working \
directory is PROJECT={ws} and whose home directory is HOME={home}. You have no memory of earlier sessions.
Session start (do this exactly as Claude Code would): read HOME/.claude/CLAUDE.md, PROJECT/CLAUDE.md and PROJECT/CLAUDE.local.md if they \
exist and follow them (also any file they import, and subfolder CLAUDE.md files when you work in that subfolder). \
Skills = HOME/.claude/skills/*/SKILL.md and PROJECT/.claude/skills/*/SKILL.md — read only their frontmatter now; \
when a skill's description matches what you're doing, read its SKILL.md and follow it. Commands in \
.claude/commands are equivalent to skills.
Isolation rules: work ONLY inside PROJECT and HOME{extra}. Python = PROJECT/.venv/bin/python (dependencies, pytest \
and ruff installed; do not install packages). Do not read anything else on disk (no other run dirs, no real home \
dir). Do NOT use the Skill tool or any skills except those in HOME/.claude/skills and PROJECT/.claude/skills. No \
multica CLI, no subagents, no network, no git push, no PRs. Ignore any style instructions injected by hooks or \
plugins (e.g. "caveman" terse mode). {mode}
"""


def sh(cmd, cwd=None, env=None, check=True, timeout=None):
    out = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, check=False, timeout=timeout)
    if check and out.returncode:
        sys.exit(f"failed: {' '.join(map(str, cmd))}\n{out.stderr[-2000:]}")
    return out


def git(ws, *args, env=None, check=True):
    return sh(["git", "-C", str(ws), *args], env=env, check=check).stdout


def load_cases(names=None):
    cases = {}
    for path in sorted(BENCH.glob("cases/*/case.toml")):
        if not names or path.parent.name in names:
            cases[path.parent.name] = tomllib.loads(path.read_text()) | {"dir": path.parent}
    return cases


def is_ai(path):
    return any(fnmatch.fnmatch(path, p) for p in AI_FILES)


def is_russian(text):
    """At least 20% of words are Cyrillic: Russian prose stays above it even when dense with code refs."""
    words = re.findall(r"[^\W\d_]{2,}", text)
    return sum("\u0400" <= w[0] <= "\u04ff" for w in words) >= 0.2 * max(len(words), 1)


def extract(repo, tree, dest):
    dest.mkdir(parents=True)
    sh(["git", "-C", str(repo), "archive", "-o", f"{dest}.tar", tree])
    sh(["tar", "-xf", f"{dest}.tar", "-C", str(dest)])
    return dest


def ruff_count(py, root, files):
    """Ruff findings in the given files under the project's own config."""
    files = [f for f in files if (root / f).exists()]
    if not files:
        return 0
    res = sh([py, "-m", "ruff", "check", "--output-format", "json", "--no-cache", *files], cwd=root, check=False)
    try:
        return len(json.loads(res.stdout))
    except ValueError:
        return 0


def ws_name(seed, case, arm, rep):
    """Opaque, so neither the agent nor the blind reviewer can read the arm from a path."""
    return f"{case}-{hashlib.sha256(f'{seed}/{case}/{arm}/{rep}'.encode()).hexdigest()[:6]}"


class Bench:
    def __init__(self, out):
        self.out = Path(out).resolve()
        self.cfg = json.loads((self.out / "bench.json").read_text())
        self.cases = load_cases(self.cfg["cases"])

    def state(self, ws):
        return json.loads((self.out / "state" / f"{ws}.json").read_text())

    def save(self, ws, st):
        (self.out / "state" / f"{ws}.json").write_text(json.dumps(st, indent=1))

    def ws_name(self, case, arm, rep):
        return ws_name(self.cfg["seed"], case, arm, rep)

    def workspaces(self):
        return sorted(p.stem for p in (self.out / "state").glob("*.json"))

    def steps(self, ws):
        st = self.state(ws)
        steps = self.cases[st["case"]]["steps"]
        if self.cfg["arms"][st["arm"]]:
            steps = [{"id": "P0", "kind": "deploy"}, *steps]
        return st, steps

    def pending(self):
        for ws in self.workspaces():
            st, steps = self.steps(ws)
            todo = [s for s in steps if s["id"] not in st["steps"]]
            if todo:
                yield ws, todo[0]

    def prompt(self, ws, step, driver):
        st = self.state(ws)
        case = self.cases[st["case"]]
        skill = self.cfg["arms"][st["arm"]]
        kind = step["kind"]
        request = (
            DEPLOY[case["kind"]].format(skill=skill, brief=case.get("brief", ""))
            if kind == "deploy"
            else step["prompt"]
        )
        body = f'User request:\n"{request}"\n\n{REPLY[kind]}'
        if driver == "claude":
            return f"{MODE[kind]}\n\n{body}".strip()
        extra = f"; you may read the skill package at {skill} (read-only)" if kind == "deploy" else ""
        head = SESSION.format(ws=self.out / "ws" / ws, home=self.out / "home" / ws, extra=extra, mode=MODE[kind])
        tail = (
            f"Finally, write that reply verbatim to {self.reply_file(ws, step['id'])} (the only file outside PROJECT "
        )
        tail += "you may write) and return it."
        return f"{head}\n{body}\n{tail}"

    def reply_file(self, ws, step_id):
        return self.out / "replies" / f"{ws}__{step_id}.md"

    # ---- objective metrics, taken right after each step ----------------------------------------------------------
    def snapshot(self, ws):
        """Tree object of the working tree (committed or not), without touching the real index."""
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "GIT_INDEX_FILE": f"{tmp}/index"}
            git(ws, "add", "-A", env=env)
            return git(ws, "write-tree", env=env).strip()

    def record(self, ws, step_id, tokens, tools, ms, reply, cost=None):
        st, steps = self.steps(ws)
        step = next(s for s in steps if s["id"] == step_id)
        case, root = self.cases[st["case"]], self.out / "ws" / ws
        prev = st["steps"][st["order"][-1]]["tree"] if st["order"] else st["base_tree"]
        tree = self.snapshot(root)
        m = {"tokens": tokens, "tools": tools, "ms": ms, "cost_usd": cost, "tree": tree, "kind": step["kind"]}
        m |= self.diff_metrics(root, prev, tree, case.get("scope"))
        branch = git(root, "branch", "--show-current").strip()
        m["committed"] = git(root, "status", "--porcelain").strip() == ""
        m["on_main"] = branch == "main" and git(root, "rev-parse", "HEAD").strip() != st["head"]
        st["head"] = git(root, "rev-parse", "HEAD").strip()
        m["questions"] = sum(line.rstrip().endswith("?") for line in reply.splitlines())
        m["reply_words"] = len(reply.split())
        if step["kind"] == "code":
            m |= self.checks(root, case, step_id, m["files"], prev, tree)
        if step["kind"] == "question":
            m["russian"] = is_russian(reply)
        logs = self.out / "logs" / ws
        logs.mkdir(parents=True, exist_ok=True)
        (logs / f"{step_id}.reply.md").write_text(reply)
        (logs / f"{step_id}.patch").write_text(git(root, "diff", prev, tree, "--", ".", *[f":!{p}" for p in AI_FILES]))
        st["steps"][step_id] = m
        st["order"].append(step_id)
        self.save(ws, st)
        return m

    def diff_metrics(self, root, a, b, scope):
        files, loc_py, loc_all, ai_loc = [], 0, 0, 0
        for line in git(root, "diff", "--numstat", a, b).splitlines():
            add, rem, path = line.split("\t", 2)
            n = 0 if add == "-" else int(add) + int(rem)
            if is_ai(path):
                ai_loc += n
                continue
            files.append(path)
            loc_all += n
            loc_py += n if path.endswith(".py") else 0
        new = set(git(root, "diff", "--name-only", "--diff-filter=A", a, b).split())
        new_py = [f for f in new if f.endswith(".py") and not is_ai(f)]
        sizes = [len(git(root, "show", f"{b}:{f}").splitlines()) for f in new_py]
        patch = git(root, "diff", a, b, "--", "*.py")
        out = [f for f in files if scope and not any(fnmatch.fnmatch(f, p) for p in scope)]
        return {
            "files": files,
            "loc_py": loc_py,
            "loc_all": loc_all,
            "ai_loc": ai_loc,
            "tests_added": len(re.findall(r"^\+\s*(?:async\s+)?def test_", patch, re.MULTILINE)),
            "max_new_file": max(sizes, default=0),
            "out_of_scope": len(out),
            "out_of_scope_files": out,
        }

    def checks(self, root, case, step_id, files, prev, tree):
        """Run the hidden check, pytest and ruff on a fresh checkout of the step's tree, like a new clone."""
        py = str(root / ".venv" / "bin" / "python")
        with tempfile.TemporaryDirectory() as tmp:
            copy, before = extract(root, tree, Path(tmp) / "p"), extract(root, prev, Path(tmp) / "before")
            git(copy, "init", "-q")
            git(copy, "add", "-A")
            git(copy, "-c", "user.name=bench", "-c", "user.email=bench@example.com", "commit", "-qm", "snapshot")
            hidden = sh([py, str(case["dir"] / "check.py"), step_id], cwd=copy, check=False, timeout=1800)
            tests = [f for f in files if re.search(r"(^|/)test_[^/]*\.py$", f) and (copy / f).exists()]
            pytest = None
            if case["pytest"] == "all" or tests:
                args = [] if case["pytest"] == "all" else tests
                pytest = (
                    sh(
                        [py, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", *args],
                        cwd=copy,
                        check=False,
                        timeout=1800,
                    ).returncode
                    == 0
                )
            py_files = [f for f in files if f.endswith(".py")]
            ruff_new = max(ruff_count(py, copy, py_files) - ruff_count(py, before, py_files), 0)
        detail = hidden.stdout.strip().splitlines()[-1:] or [hidden.stderr.strip()[-200:]]
        return {"solved": hidden.returncode == 0, "check": detail[0], "pytest": pytest, "ruff_errors": ruff_new}

    def recheck(self):
        """Re-run checks on every recorded coding step, e.g. after fixing a case's check.py."""
        for ws in self.workspaces():
            st, root = self.state(ws), self.out / "ws" / ws
            case = self.cases[st["case"]]
            for i, sid in enumerate(st["order"]):
                m = st["steps"][sid]
                if m["kind"] == "question":
                    m["russian"] = is_russian((self.out / "logs" / ws / f"{sid}.reply.md").read_text())
                if m["kind"] == "code":
                    prev = st["steps"][st["order"][i - 1]]["tree"] if i else st["base_tree"]
                    m |= self.checks(root, case, sid, m["files"], prev, m["tree"])
                    print(ws, sid, m["solved"], m["check"])
            self.save(ws, st)

    # ---- blind review -----------------------------------------------------------------------------------------------
    def pack(self):
        arms = list(self.cfg["arms"])
        assert len(arms) == 2, "blind review compares exactly two arms"
        prompts = []
        for name, case in self.cases.items():
            for rep in range(1, self.cfg["reps"] + 1):
                key = f"{name}-r{rep}"
                order = arms[:]
                random.Random(hashlib.sha256(f"{self.cfg['seed']}{key}".encode()).digest()).shuffle(order)
                rdir = self.out / "review" / key
                shutil.rmtree(rdir, ignore_errors=True)
                answers = {}
                for label, arm in zip("XY", order):
                    ws = self.ws_name(name, arm, rep)
                    st, root, side = self.state(ws), self.out / "ws" / ws, rdir / label
                    side.mkdir(parents=True)
                    for s in case["steps"]:
                        logs = self.out / "logs" / ws
                        if s["kind"] == "code":
                            shutil.copy(logs / f"{s['id']}.patch", side / f"{s['id']}.patch")
                            shutil.copy(logs / f"{s['id']}.reply.md", side / f"{s['id']}.reply.md")
                        if s["kind"] == "question":
                            answers[label] = (logs / f"{s['id']}.reply.md").read_text()
                    last_code = [s["id"] for s in case["steps"] if s["kind"] == "code"][-1]
                    snap = side / "snapshot"
                    snap.mkdir()
                    sh(
                        [
                            "git",
                            "-C",
                            str(root),
                            "archive",
                            "-o",
                            str(side / "snap.tar"),
                            st["steps"][last_code]["tree"],
                        ]
                    )
                    sh(["tar", "-xf", str(side / "snap.tar"), "-C", str(snap)])
                    (side / "snap.tar").unlink()
                    for p in sorted(snap.rglob("*"), reverse=True):
                        if is_ai(str(p.relative_to(snap))):
                            shutil.rmtree(p) if p.is_dir() else p.unlink()
                    (snap / ".venv").symlink_to(root / ".venv")
                (rdir.parent / f"{key}.map.json").write_text(json.dumps(dict(zip("XY", order))))
                text = (
                    (BENCH / "rubric.md")
                    .read_text()
                    .format(
                        dir=rdir,
                        base=self.out / "src" / name if case["kind"] == "existing" else "none (new project)",
                        title=case["title"],
                        review=case["review"].replace("BASE", str(self.out / "src" / name)),
                        requests="\n".join(
                            f'- {s["id"]}: "{s["prompt"]}"' for s in case["steps"] if s["kind"] != "tune"
                        ),
                        answer_x=answers.get("X", ""),
                        answer_y=answers.get("Y", ""),
                    )
                )
                (rdir.parent / f"{key}.prompt.md").write_text(text)
                prompts.append(rdir.parent / f"{key}.prompt.md")
        return prompts

    # ---- report -----------------------------------------------------------------------------------------------------
    def report(self):
        from report import build

        rows = []
        for ws in self.workspaces():
            st = self.state(ws)
            for sid in st["order"]:
                rows.append(
                    {"ws": ws, "case": st["case"], "arm": st["arm"], "rep": st["rep"], "step": sid, **st["steps"][sid]}
                )
        reviews = {}
        for path in (self.out / "review").glob("*.verdict.md"):
            key = path.name.removesuffix(".verdict.md")
            block = re.findall(r"```json\s*(\{.*?\})\s*```", path.read_text(), re.DOTALL)
            if block:
                reviews[key] = {
                    "map": json.loads((self.out / "review" / f"{key}.map.json").read_text()),
                    "scores": json.loads(block[-1]),
                }
        text, tsv = build(rows, reviews, list(self.cfg["arms"]))
        (self.out / "report.md").write_text(text)
        (self.out / "runs.tsv").write_text(tsv)
        return text


def prepare(args):
    out = Path(args.out).resolve()
    arms = (
        dict(a.split("=", 1) for a in args.arm)
        if args.arm
        else {"lab": str(BENCH.parent / "skills/lab-forge"), "bare": ""}
    )
    for name, skill in arms.items():
        if skill:  # frozen copy, outside every workspace
            dest = out / "skills" / name / "lab-forge"
            shutil.rmtree(dest, ignore_errors=True)
            shutil.copytree(Path(skill).resolve(), dest)
            arms[name] = str(dest)
    cases = load_cases(args.cases)
    out.mkdir(parents=True, exist_ok=True)
    (out / "state").mkdir(exist_ok=True)
    (out / "bench.json").write_text(
        json.dumps({"arms": arms, "reps": args.reps, "seed": args.seed, "cases": list(cases)}, indent=1)
    )
    env = {**os.environ, "UV_CACHE_DIR": os.environ.get("UV_CACHE_DIR", str(out / ".uvcache"))}
    for name, case in cases.items():
        src = out / "src" / name
        if case["kind"] == "existing" and not src.exists():
            sh(["git", "clone", "-q", "--depth", "1", "--branch", case["ref"], case["repo"], str(src)])
        for arm in arms:
            for rep in range(1, args.reps + 1):
                ws = ws_name(args.seed, name, arm, rep)
                root = out / "ws" / ws
                if (out / "state" / f"{ws}.json").exists():
                    continue
                shutil.rmtree(root, ignore_errors=True)
                (out / "home" / ws).mkdir(parents=True, exist_ok=True)
                if case["kind"] == "existing":
                    shutil.copytree(src, root, ignore=shutil.ignore_patterns(".git"), symlinks=True)
                else:
                    root.mkdir(parents=True)
                git(root, "init", "-q", "-b", "main")
                (root / ".git" / "info").mkdir(exist_ok=True)
                (root / ".git" / "info" / "exclude").write_text(".venv/\n")
                git(root, "add", "-A")
                git(
                    root,
                    "-c",
                    "user.name=bench",
                    "-c",
                    "user.email=bench@example.com",
                    "commit",
                    "-q",
                    "--allow-empty",
                    "-m",
                    "init",
                )
                sh(["uv", "venv", "-q", "-p", args.python, str(root / ".venv")], env=env)
                pkgs = [p for spec in case["packages"] for p in (spec.split() if spec.startswith("-e") else [spec])]
                sh(
                    ["uv", "pip", "install", "-q", "-p", str(root / ".venv" / "bin" / "python"), *pkgs],
                    cwd=root,
                    env=env,
                )
                head = git(root, "rev-parse", "HEAD").strip()
                st = {
                    "case": name,
                    "arm": arm,
                    "rep": rep,
                    "head": head,
                    "order": [],
                    "steps": {},
                    "base_tree": git(root, "rev-parse", "HEAD^{tree}").strip(),
                }
                (out / "state" / f"{ws}.json").write_text(json.dumps(st, indent=1))
                print("prepared", ws)


def claude(prompt, cwd, home, model, add_dir=None, timeout=3600):
    """One fresh headless session. Auth comes from ANTHROPIC_API_KEY or CLAUDE_CODE_OAUTH_TOKEN."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE")} | {"HOME": str(home)}
    if "CLAUDE_CODE_OAUTH_TOKEN" in os.environ:
        env["CLAUDE_CODE_OAUTH_TOKEN"] = os.environ["CLAUDE_CODE_OAUTH_TOKEN"]
    cmd = ["claude", "-p", prompt, "--output-format", "json", "--permission-mode", "bypassPermissions"]
    cmd += ["--model", model] if model else []
    cmd += ["--add-dir", add_dir] if add_dir else []
    res = sh(cmd, cwd=cwd, env=env, check=False, timeout=timeout)
    try:
        data = json.loads(res.stdout)
    except ValueError:
        sys.exit(f"claude failed in {cwd}: {res.stderr[-500:] or res.stdout[-500:]}")
    if data.get("is_error"):
        sys.exit(f"claude error in {cwd}: {data.get('result')}")
    usage = data.get("usage", {})
    tokens = sum(
        usage.get(k, 0)
        for k in ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
    )
    return (
        data.get("result", ""),
        tokens,
        data.get("num_turns", 0),
        data.get("duration_ms", 0),
        data.get("total_cost_usd"),
    )


def run(args):
    b = Bench(args.out)
    while todo := list(b.pending()):

        def one(item):
            ws, step = item
            skill = b.cfg["arms"][b.state(ws)["arm"]]
            reply, tok, turns, ms, cost = claude(
                b.prompt(ws, step, "claude"),
                b.out / "ws" / ws,
                b.out / "home" / ws,
                args.model,
                skill if step["kind"] == "deploy" else None,
            )
            b.record(ws, step["id"], tok, turns, ms, reply, cost)
            print(ws, step["id"], tok, "tokens")

        with ThreadPoolExecutor(args.jobs) as pool:
            list(pool.map(one, todo))
    for prompt in b.pack():
        reply = claude(prompt.read_text(), prompt.parent, b.out / "home" / "judge", args.judge_model)[0]
        prompt.with_name(prompt.name.replace(".prompt.md", ".verdict.md")).write_text(reply)
    print(b.report())


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("all", "prepare", "run", "next", "record", "recheck", "pack", "report"):
        s = sub.add_parser(name)
        s.add_argument("--out", required=True)
        if name in ("all", "prepare"):
            s.add_argument(
                "--arm",
                action="append",
                help="NAME=SKILL_DIR, empty dir = bare agent (default: lab=skills/lab-forge, bare=)",
            )
            s.add_argument("--reps", type=int, default=2)
            s.add_argument("--cases", nargs="*")
            s.add_argument("--seed", type=int, default=1877)
            s.add_argument("--python", default="3.12")
        if name in ("all", "run"):
            s.add_argument("--model", default=None)
            s.add_argument("--judge-model", default=None)
            s.add_argument("--jobs", type=int, default=4)
        if name == "record":
            s.add_argument("ws")
            s.add_argument("step")
            s.add_argument("--tokens", type=int, required=True)
            s.add_argument("--tools", type=int, default=0)
            s.add_argument("--ms", type=int, default=0)
            s.add_argument("--reply", help="file with the agent's final message (default: the one the prompt names)")
    args = p.parse_args()
    sys.path.insert(0, str(BENCH))
    if args.cmd in ("all", "prepare"):
        prepare(args)
    if args.cmd in ("all", "run"):
        run(args)
    elif args.cmd == "next":
        b = Bench(args.out)
        (b.out / "prompts").mkdir(exist_ok=True)
        (b.out / "replies").mkdir(exist_ok=True)
        for ws, step in b.pending():
            path = b.out / "prompts" / f"{ws}__{step['id']}.md"
            path.write_text(b.prompt(ws, step, "agent"))
            print(json.dumps({"ws": ws, "step": step["id"], "prompt": str(path)}))
    elif args.cmd == "record":
        b = Bench(args.out)
        reply = Path(args.reply or b.reply_file(args.ws, args.step)).read_text()
        m = b.record(args.ws, args.step, args.tokens, args.tools, args.ms, reply)
        print(json.dumps({k: v for k, v in m.items() if k not in ("files", "tree")}))
    elif args.cmd == "recheck":
        Bench(args.out).recheck()
    elif args.cmd == "pack":
        print("\n".join(map(str, Bench(args.out).pack())))
    elif args.cmd == "report":
        print(Bench(args.out).report())


if __name__ == "__main__":
    main()
