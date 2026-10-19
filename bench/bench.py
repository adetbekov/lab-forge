#!/usr/bin/env python3
"""Repeatable A/B benchmark for lab-forge. Stdlib only; needs git and uv.

    python bench/bench.py all --out /tmp/lfb                    # headless `claude -p`, one command
    python bench/bench.py all --out /tmp/lfb --arm decide=skills/lab-forge --arm main=skills/lab-forge \
        --decide decide=hosted                                  # decision hooks on in one arm only
    python bench/bench.py prepare --out /tmp/lfb                # then, for agent-driven runs:
    python bench/bench.py next --out /tmp/lfb                   #   prompts to run in fresh sessions
    python bench/bench.py record --out /tmp/lfb WS STEP --tokens N --tools N --ms N --reply FILE
    python bench/bench.py pack --out /tmp/lfb                   #   blind X/Y review prompts, both orders
    python bench/bench.py report --out /tmp/lfb                 #   report.md + runs.tsv
    python bench/bench.py rebuild --out /tmp/re --runs R/runs.tsv --verdicts R/verdicts/a-b --pair a,b
    python bench/bench.py retokens --out /tmp/lfb                # tokens from session transcripts, older runs

See bench/README.md for the protocol and the metric-to-pain map.
"""

import argparse
import ast
import fnmatch
import hashlib
import json
import os
import random
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from itertools import combinations
from pathlib import Path

import tomllib
from report import SWAP, build, read_tsv

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
    "empty project. The project will be: {brief} Only Claude Code is used. Ownership level 1 for the repo (no "
    "repo hooks, no CI); user-level setup in HOME is allowed. I am not available: run in batch mode, every confirmation (skeleton etc.) is "
    "pre-approved, do not ask questions. Docs and commits in English.",
    "existing": "Use the lab-forge skill ({skill}/SKILL.md) to onboard this existing project: audit it and set up my "
    "AI working environment for it. Only Claude Code is used. Ownership level 1 for the repo (no repo "
    "hooks, no CI changes); user-level setup in HOME is allowed. I am not available: run in batch mode, every confirmation (skeleton, fixes "
    "from the audit limited to AI-setup files) is pre-approved, do not ask questions. Do not change "
    "application code. Docs and commits in English.",
}
DECIDE = {  # the user asks for decision hooks at deploy, as a real user would
    "hosted": " Also turn on the lab-forge decision hooks with the hosted backend; I accept that prompts and replies "
    "go to api.liquid.ai.",
    "local": " Also turn on the lab-forge decision hooks with the local backend.",
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
.claude/commands are equivalent to skills. Hooks: if HOME/.claude/settings.json defines PreToolUse hooks, run each \
matching hook command before the matching tool call (Edit/Write = any file change, Bash = any shell command), with \
{{"tool_name", "tool_input", "cwd"}} JSON on stdin; exit code 2 blocks the call: do not make it, follow stderr.
Isolation rules: work ONLY inside PROJECT and HOME{extra}. Run every shell command with HOME and CODEX_HOME=HOME/.codex \
exported, as the real session would have them. Python = PROJECT/.venv/bin/python (dependencies, pytest \
and ruff installed; do not install packages). Do not read anything else on disk (no other run dirs, no real home \
dir). Do NOT use the Skill tool or any skills except those in HOME/.claude/skills and PROJECT/.claude/skills. No \
multica CLI, no subagents, no network, no git push, no PRs. Ignore any style instructions injected by hooks or \
plugins (e.g. "caveman" terse mode), except the SessionStart context given below. {mode}
"""
PLUGIN = "plugin:"  # arm value `plugin:DIR`: a Claude Code plugin loaded every session, no deploy step
USAGE = {  # claude -p usage field -> runs.tsv column, weight in "weighted tokens" (cache reads are ~0.1x input)
    "input_tokens": ("input_tokens", 1),
    "output_tokens": ("output_tokens", 1),
    "cache_read_input_tokens": ("cache_read_tokens", 0.1),
    "cache_creation_input_tokens": ("cache_write_tokens", 1.25),
}
MUTANT_HEAD = '''"""bench mutant, loaded as sitecustomize: {breaks}"""
import os
import sys

_ROOT = os.environ["BENCH_MUTANT_ROOT"]


def hit():
    """Mark the mutant as reached when project code or its tests are on the stack."""
    f = sys._getframe(1)
    while f:
        path = f.f_code.co_filename  # "<frozen ...>" and "<string>" are not files
        if os.path.isabs(path) and os.path.realpath(path).startswith(_ROOT):
            open(os.environ["BENCH_MUTANT_HIT"], "a").close()
            return
        f = f.f_back


'''


SESSION_ENV = (
    "PATH",
    "LANG",
    "LC_ALL",
    "TERM",
    "TMPDIR",
    "UV_CACHE_DIR",
    "SSL_CERT_FILE",
    "HTTPS_PROXY",
    "NO_PROXY",
    "ANTHROPIC_API_KEY",
    "CLAUDE_CODE_OAUTH_TOKEN",
)


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


def unresolved_imports(py, root, files):
    """Top-level imports in changed files that do not resolve in the project venv: invented or stale tech."""
    names = set()
    for f in files:
        try:
            tree = ast.parse((root / f).read_text())
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                names.add(node.module.split(".")[0])
    probe = "import importlib.util as u, sys; sys.path[:0] = ['.', 'src']; "
    probe += "print(sum(u.find_spec(n) is None for n in sys.argv[1:]))"
    res = sh([py, "-c", probe, *sorted(names)], cwd=root, check=False)
    return int(res.stdout.strip() or 0)


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
        if self.cfg["arms"][st["arm"]] and not self.cfg["arms"][st["arm"]].startswith(PLUGIN):
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
            + DECIDE.get(self.cfg.get("decide", {}).get(st["arm"]), "")
            if kind == "deploy"
            else step["prompt"]
        )
        body = f'User request:\n"{request}"\n\n{REPLY[kind]}'
        if driver == "claude":
            return f"{MODE[kind]}\n\n{body}".strip()
        extra = f"; you may read the skill package at {skill} (read-only)" if kind == "deploy" else ""
        head = SESSION.format(ws=self.out / "ws" / ws, home=self.out / "home" / ws, extra=extra, mode=MODE[kind])
        if skill.startswith(PLUGIN):
            head += (
                f"SessionStart hook context (the plugin injected this; follow it):\n{self.session_start(ws, skill)}\n"
            )
        tail = (
            f"Finally, write that reply verbatim to {self.reply_file(ws, step['id'])} (the only file outside PROJECT "
        )
        tail += "you may write) and return it."
        return f"{head}\n{body}\n{tail}"

    def session_start(self, ws, plugin):
        """What the plugin's SessionStart hook would inject into a real session in this workspace."""
        root = plugin.removeprefix(PLUGIN)
        env = {**os.environ, "HOME": str(self.out / "home" / ws), "CLAUDE_PLUGIN_ROOT": root}
        out = sh(["node", f"{root}/hooks/ponytail-activate.js"], cwd=self.out / "ws" / ws, env=env, check=False)
        return out.stdout.split("STATUSLINE SETUP NEEDED")[0].strip()  # the nudge is UI noise, not a rule

    def reply_file(self, ws, step_id):
        return self.out / "replies" / f"{ws}__{step_id}.md"

    # ---- objective metrics, taken right after each step ----------------------------------------------------------
    def snapshot(self, ws):
        """Tree object of the working tree (committed or not), without touching the real index."""
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "GIT_INDEX_FILE": f"{tmp}/index"}
            git(ws, "add", "-A", env=env)
            return git(ws, "write-tree", env=env).strip()

    def record(self, ws, step_id, tokens, tools, ms, reply, cost=None, usage=None, mode="agent"):
        st, steps = self.steps(ws)
        step = next(s for s in steps if s["id"] == step_id)
        case, root = self.cases[st["case"]], self.out / "ws" / ws
        prev = st["steps"][st["order"][-1]]["tree"] if st["order"] else st["base_tree"]
        tree = self.snapshot(root)
        m = {"tokens": tokens, "tools": tools, "ms": ms, "cost_usd": cost, "tree": tree, "kind": step["kind"]}
        m["mode"] = mode
        if usage:
            m |= {col: usage.get(field) for field, (col, _) in USAGE.items()}
            m["weighted_tokens"] = weigh(usage)
            if usage.get("reported_tokens"):  # the CLI under-reported; tokens come from the transcript
                m["reported_tokens"] = usage["reported_tokens"]
        m |= self.diff_metrics(root, prev, tree, case.get("scope"))
        m["n_files"] = len(m["files"])
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
            pytest = bare = None
            mutants = {}
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
                if (root / ".venv" / "bin" / "pytest").exists():  # no `-m`: the project must set its own path
                    cmd = [str(root / ".venv" / "bin" / "pytest"), "-q", "-x", "-p", "no:cacheprovider", *args]
                    bare = sh(cmd, cwd=copy, check=False, timeout=1800).returncode == 0
                if pytest:  # a red suite cannot show that it notices a break
                    for mu in case.get("mutants", []):
                        if step_id in mu["steps"]:
                            mutants[mu["id"]] = self.mutant(py, copy, mu, args)
            py_files = [f for f in files if f.endswith(".py")]
            ruff_new = max(ruff_count(py, copy, py_files) - ruff_count(py, before, py_files), 0)
            bad_imports = unresolved_imports(py, copy, [f for f in py_files if (copy / f).exists()])
        detail = hidden.stdout.strip().splitlines()[-1:] or [hidden.stderr.strip()[-200:]]
        return {
            "solved": hidden.returncode == 0,
            "check": detail[0],
            "pytest": pytest,
            "ruff_errors": ruff_new,
            "bad_imports": bad_imports,
            "bare_pytest": bare,
            "mutants": mutants,
            "mutants_killed": sum(v == "killed" for v in mutants.values()) if mutants else None,
            "mutants_applied": sum(v != "n/a" for v in mutants.values()) if mutants else None,
        }

    def mutant(self, py, copy, mu, args):
        """Run the step's tests with one hand-written break patched in through sitecustomize.

        killed: the tests fail and reached the patch; survived: they pass, yet the tests or the case's
        own entry point reach the patched code; n/a: nothing reaches it, so it says nothing about the tests.
        """
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "sitecustomize.py").write_text(MUTANT_HEAD.format(breaks=mu["breaks"]) + mu["patch"])
            hit = Path(tmp) / "hit"
            env = {**os.environ, "PYTHONPATH": tmp, "BENCH_MUTANT_HIT": str(hit)}
            env["BENCH_MUTANT_ROOT"] = os.path.realpath(copy) + os.sep
            cmd = [py, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", *args]
            red = sh(cmd, cwd=copy, env=env, check=False, timeout=1800).returncode != 0
            if hit.exists():
                return "killed" if red else "survived"
            if red:
                return "n/a"  # failed without reaching the patch: not this mutant's doing
            run = shutil.copytree(copy, Path(tmp) / "run")  # the entry point may write outputs
            env["BENCH_MUTANT_ROOT"] = os.path.realpath(run) + os.sep
            sh([py, *shlex.split(mu["run"])], cwd=run, env=env, check=False, timeout=1800)
            return "survived" if hit.exists() else "n/a"

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

    def retokens(self):
        """Recount tokens of recorded steps from their transcripts in HOME, for runs before `honest()`.

        Steps and sessions pair up in start order; a workspace whose session count differs is skipped.
        """
        for ws in self.workspaces():
            st = self.state(ws)
            found = []
            for path in (self.out / "home" / ws / ".claude" / "projects").glob(f"*{ws}/*.jsonl"):  # not smoke.py's
                stamps = [json.loads(line).get("timestamp") for line in path.read_text().splitlines()]
                found.append((min(t for t in stamps if t), path))
            if len(found) != len(st["order"]):
                print(ws, f"{len(found)} transcripts for {len(st['order'])} steps: skipped")
                continue
            for sid, (_, path) in zip(st["order"], sorted(found)):
                m = st["steps"][sid]
                if m.get("reported_tokens") is not None:
                    continue
                usage = {field: m.get(col) for field, (col, _) in USAGE.items()}
                usage, tokens, turns, reported = honest(usage, m["tools"], path)
                if reported:
                    m |= {col: usage[field] for field, (col, _) in USAGE.items()}
                    m |= {
                        "tokens": tokens,
                        "tools": turns,
                        "weighted_tokens": weigh(usage),
                        "reported_tokens": reported,
                    }
                    print(ws, sid, "reported", reported, "transcript", tokens)
            self.save(ws, st)

    # ---- blind review -----------------------------------------------------------------------------------------------
    def pack(self, pair=None):
        arms = pair or list(self.cfg["arms"])
        assert len(arms) == 2, "blind review compares exactly two arms (pass --pair A,B)"
        prompts = []
        for name, case in self.cases.items():
            for rep in range(1, self.cfg["reps"] + 1):
                base = f"{name}-r{rep}" + (f"-{'-'.join(pair)}" if pair else "")
                first = arms[:]
                random.Random(hashlib.sha256(f"{self.cfg['seed']}{base}".encode()).digest()).shuffle(first)
                for key, order in ((base, first), (base + SWAP, first[::-1])):  # position bias: judge both orders
                    prompts.append(self.pack_one(key, name, case, rep, order))
        return prompts

    def pack_one(self, key, name, case, rep, order):
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
                requests="\n".join(f'- {s["id"]}: "{s["prompt"]}"' for s in case["steps"] if s["kind"] != "tune"),
                answer_x=answers.get("X", ""),
                answer_y=answers.get("Y", ""),
            )
        )
        (rdir.parent / f"{key}.prompt.md").write_text(text)
        return rdir.parent / f"{key}.prompt.md"

    # ---- report -----------------------------------------------------------------------------------------------------
    def report(self, pair=None):
        arms = pair or list(self.cfg["arms"])
        rows = []
        for ws in self.workspaces():
            st = self.state(ws)
            if st["arm"] not in arms:
                continue
            for sid in st["order"]:
                rows.append(
                    {"ws": ws, "case": st["case"], "arm": st["arm"], "rep": st["rep"], "step": sid, **st["steps"][sid]}
                )
        reviews = {}
        for path in (self.out / "review").glob("*.verdict.md"):
            key = path.name.removesuffix(".verdict.md")
            amap = json.loads((self.out / "review" / f"{key}.map.json").read_text())
            if (scores := verdict(path)) and set(amap.values()) <= set(arms):
                reviews[key] = {"map": amap, "scores": scores}
        text, tsv = build(rows, reviews, arms)
        suffix = f"-{'-'.join(pair)}" if pair else ""
        (self.out / f"report{suffix}.md").write_text(text)
        (self.out / f"runs{suffix}.tsv").write_text(tsv)
        return text


def verdict(path):
    block = re.findall(r"^```json\s*(\{.*?\})\s*^```", path.read_text(), re.DOTALL | re.MULTILINE)  # fences only
    return json.loads(block[-1]) if block else None


def rebuild(args):
    """Rebuild a report from a committed runs.tsv and verdicts/<pair>/ folders, e.g. to diff it against the original.

    Verdict folders hold `<case>-r<rep>.md` plus `blind-map.json` ({case: {X: arm, Y: arm}}); the review key is
    `<case>-r<rep>-<folder>`, as `pack --pair` names it.
    """
    cases = load_cases()
    rows = read_tsv(Path(args.runs).read_text())
    for r in rows:
        steps = {s["id"]: s["kind"] for s in cases[r["case"]]["steps"]}
        r["kind"] = steps.get(r["step"], "deploy")
    arms = args.pair or list(dict.fromkeys(r["arm"] for r in rows))
    reviews = {}
    for vdir in map(Path, args.verdicts or []):
        amap = json.loads((vdir / "blind-map.json").read_text())
        for path in sorted(vdir.glob("*-r*.md")):
            key = path.stem.removesuffix(SWAP)
            side = amap[key.rsplit("-r", 1)[0]]
            side = {"X": side["Y"], "Y": side["X"]} if path.stem.endswith(SWAP) else side
            if (scores := verdict(path)) and set(side.values()) <= set(arms):
                reviews[f"{key}-{vdir.name}" + SWAP * path.stem.endswith(SWAP)] = {"map": side, "scores": scores}
    text, tsv = build([r for r in rows if r["arm"] in arms], reviews, arms)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.md").write_text(text)
    (out / "runs.tsv").write_text(tsv)
    return text


def prepare(args):
    out = Path(args.out).resolve()
    arms = (
        dict(a.split("=", 1) for a in args.arm)
        if args.arm
        else {"lab": str(BENCH.parent / "skills/lab-forge"), "bare": ""}
    )
    for name, skill in arms.items():
        if skill.startswith(PLUGIN):
            dest = out / "plugins" / name
            shutil.rmtree(dest, ignore_errors=True)
            shutil.copytree(Path(skill.removeprefix(PLUGIN)).resolve(), dest, ignore=shutil.ignore_patterns(".git"))
            arms[name] = PLUGIN + str(dest)
        elif skill:  # frozen copy, outside every workspace
            dest = out / "skills" / name / "lab-forge"
            shutil.rmtree(dest, ignore_errors=True)
            shutil.copytree(Path(skill).resolve(), dest)
            arms[name] = str(dest)
    decide = dict(a.split("=", 1) for a in args.decide or [])
    cases = load_cases(args.cases)
    out.mkdir(parents=True, exist_ok=True)
    (out / "state").mkdir(exist_ok=True)
    (out / "bench.json").write_text(
        json.dumps(
            {"arms": arms, "reps": args.reps, "seed": args.seed, "cases": list(cases), "decide": decide}, indent=1
        )
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
                if arms[arm].startswith(PLUGIN):  # agent-driven sessions read skills from HOME only
                    shutil.copytree(
                        Path(arms[arm].removeprefix(PLUGIN)) / "skills", out / "home" / ws / ".claude" / "skills"
                    )
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


def transcript_usage(path):
    """USAGE fields summed over a session transcript's model calls, and the number of calls.

    `claude -p` reports only the last stretch of a session that a background task resumed; the transcript
    has every call. Streamed blocks of one call repeat its usage, so each message id counts once.
    """
    calls = {}
    for line in Path(path).read_text().splitlines():
        rec = json.loads(line)
        msg = rec.get("message") or {}
        if rec.get("type") == "assistant" and msg.get("usage"):
            calls[msg.get("id")] = msg["usage"]
    return {k: sum(u.get(k) or 0 for u in calls.values()) for k in USAGE}, len(calls)


def weigh(usage):
    return sum(w * (usage.get(field) or 0) for field, (_, w) in USAGE.items())


def honest(usage, turns, path):
    """The transcript's usage when the CLI under-reports it. `total_cost_usd` already covers the whole session.

    Returns (usage, tokens, turns, reported_tokens) where reported_tokens is None if the CLI numbers stood.
    """
    tokens = sum(v or 0 for v in usage.values())
    if not path:
        return usage, tokens, turns, None
    full, calls = transcript_usage(path)
    if sum(full.values()) <= tokens:
        return usage, tokens, turns, None
    return full, sum(full.values()), max(turns, calls), tokens


def claude(prompt, cwd, home, model, add_dir=None, timeout=3600, keys=(), plugin=None):
    """One fresh headless session. Auth comes from ANTHROPIC_API_KEY or CLAUDE_CODE_OAUTH_TOKEN.

    The session and the code it runs see only SESSION_ENV plus `keys`, never the rest of the runner's secrets.
    """
    env = {k: os.environ[k] for k in (*SESSION_ENV, *keys) if k in os.environ} | {"HOME": str(home)}
    cmd = ["claude", "-p", prompt, "--output-format", "json", "--permission-mode", "bypassPermissions"]
    cmd += ["--model", model] if model else []
    cmd += ["--add-dir", add_dir] if add_dir else []
    cmd += ["--plugin-dir", plugin] if plugin else []
    res = sh(cmd, cwd=cwd, env=env, check=False, timeout=timeout)
    try:
        data = json.loads(res.stdout)
    except ValueError:
        sys.exit(f"claude failed in {cwd}: {res.stderr[-500:] or res.stdout[-500:]}")
    if data.get("is_error"):
        sys.exit(f"claude error in {cwd}: {data.get('result')}")
    usage = {k: data.get("usage", {}).get(k) for k in USAGE}
    found = sorted(Path(home, ".claude", "projects").glob(f"*/{data.get('session_id')}.jsonl"))
    usage, tokens, turns, reported = honest(usage, data.get("num_turns", 0), found[0] if found else None)
    if reported:
        usage["reported_tokens"] = reported
    return data.get("result", ""), tokens, turns, data.get("duration_ms", 0), data.get("total_cost_usd"), usage


def run(args):
    b = Bench(args.out)
    while todo := list(b.pending()):

        def one(item):
            ws, step = item
            arm = b.state(ws)["arm"]
            reply, tok, turns, ms, cost, usage = claude(
                b.prompt(ws, step, "claude"),
                b.out / "ws" / ws,
                b.out / "home" / ws,
                args.model,
                b.cfg["arms"][arm] if step["kind"] == "deploy" else None,
                keys=["LIQUID_AI_API_KEY"] if b.cfg.get("decide", {}).get(arm) == "hosted" else [],
                plugin=b.cfg["arms"][arm].removeprefix(PLUGIN) if b.cfg["arms"][arm].startswith(PLUGIN) else None,
            )
            b.record(ws, step["id"], tok, turns, ms, reply, cost, usage, mode="headless")
            print(ws, step["id"], tok, "tokens")

        with ThreadPoolExecutor(args.jobs) as pool:
            list(pool.map(one, todo))
    arms = list(b.cfg["arms"])
    pairs = [None] if len(arms) == 2 else args.pair or [list(p) for p in combinations(arms, 2)]

    def judge(prompt):
        out = prompt.with_name(prompt.name.replace(".prompt.md", ".verdict.md"))
        if out.exists() and verdict(out):  # a resumed run keeps the verdicts it already has
            return
        out.write_text(claude(prompt.read_text(), prompt.parent, b.out / "home" / "judge", args.judge_model)[0])

    for pair in pairs:
        with ThreadPoolExecutor(args.judge_jobs) as pool:
            list(pool.map(judge, b.pack(pair)))
        b.report(pair)
    print(b.report())


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("all", "prepare", "run", "next", "record", "recheck", "retokens", "pack", "report", "rebuild"):
        s = sub.add_parser(name)
        s.add_argument("--out", required=True)
        if name in ("all", "prepare"):
            s.add_argument(
                "--arm",
                action="append",
                help="NAME=SKILL_DIR, NAME=plugin:PLUGIN_DIR, empty = bare agent (default: lab=skills/lab-forge, bare=)",
            )
            s.add_argument("--reps", type=int, default=3)
            s.add_argument("--cases", nargs="*")
            s.add_argument("--seed", type=int, default=1877)
            s.add_argument("--python", default="3.12")
            s.add_argument(
                "--decide", action="append", help="ARM=hosted|local: that arm's deploy asks for decision hooks"
            )
        if name in ("all", "run"):
            s.add_argument("--model", default=None)
            s.add_argument("--judge-model", default="claude-fable-5-1", help="another model line than the agents'")
            s.add_argument("--jobs", type=int, default=4)
            s.add_argument("--judge-jobs", type=int, default=1, help="blind verdicts run in parallel")
            s.add_argument(
                "--pair", action="append", type=lambda v: v.split(","), help="A,B: judge only these pairs (3+ arms)"
            )
        if name in ("pack", "report", "rebuild"):
            s.add_argument("--pair", type=lambda v: v.split(","), help="A,B: the two arms to compare")
        if name == "record":
            s.add_argument("ws")
            s.add_argument("step")
            s.add_argument("--tokens", type=int, required=True)
            s.add_argument("--tools", type=int, default=0)
            s.add_argument("--ms", type=int, default=0)
            s.add_argument("--reply", help="file with the agent's final message (default: the one the prompt names)")
            s.add_argument("--cost", type=float, help="session cost, $, if the driver reports it")
            for field, (col, _) in USAGE.items():
                s.add_argument(f"--{col.replace('_', '-')}", dest=field, type=int, help=f"usage.{field}")
        if name == "rebuild":
            s.add_argument("--runs", required=True, help="a committed runs.tsv")
            s.add_argument("--verdicts", nargs="*", help="verdicts/<pair>/ folders with blind-map.json")
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
        usage = {k: getattr(args, k) for k in USAGE}
        usage = usage if any(v is not None for v in usage.values()) else None
        m = b.record(args.ws, args.step, args.tokens, args.tools, args.ms, reply, args.cost, usage)
        print(json.dumps({k: v for k, v in m.items() if k not in ("files", "tree")}))
    elif args.cmd == "recheck":
        Bench(args.out).recheck()
    elif args.cmd == "retokens":
        Bench(args.out).retokens()
    elif args.cmd == "pack":
        print("\n".join(map(str, Bench(args.out).pack(args.pair))))
    elif args.cmd == "report":
        print(Bench(args.out).report(args.pair))
    elif args.cmd == "rebuild":
        print(rebuild(args))


if __name__ == "__main__":
    main()
