"""Detect the machine and projects lab-forge is deploying into.

Stdlib only, works on Windows, macOS and Linux.

Usage:
    python detect_env.py <root> [--json] [--no-network] [--depth N]

<root> is a folder with one or more projects (or a single project).
Prints a short human summary; --json prints the full structure.
"""

import argparse
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from pathlib import Path

TOOLS = ["git", "python", "uv", "poetry", "conda", "pip", "dvc", "pre-commit",
         "docker", "make", "code", "claude", "gh", "glab"]

AGENT_FILES = {
    "AGENTS.md": "generic/codex/copilot",
    "CLAUDE.md": "claude",
    ".github/copilot-instructions.md": "copilot",
    ".github/instructions": "copilot (scoped)",
    ".github/prompts": "copilot (commands)",
    ".github/agents": "copilot (agents)",
    ".github/chatmodes": "copilot (legacy agents)",
    ".github/skills": "copilot (skills)",
    ".claude/skills": "claude/copilot (skills)",
    ".claude/commands": "claude (commands)",
    ".claude/agents": "claude (agents)",
    ".agents/skills": "generic (skills)",
    ".cursor/rules": "cursor",
    ".cursorrules": "cursor (legacy)",
    ".lab-forge/state.md": "lab-forge (already deployed)",
}

STACK_FILES = ["pyproject.toml", "requirements.txt", "setup.py", "environment.yml",
               "uv.lock", "poetry.lock", "dvc.yaml", "params.yaml", "MLproject",
               "Makefile", "Dockerfile", "docker-compose.yml", ".pre-commit-config.yaml",
               ".gitlab-ci.yml", "Jenkinsfile", "mkdocs.yml"]

HOME_AGENT_DIRS = [".claude", ".copilot", ".codex", ".cursor"]

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".mypy_cache",
             ".ruff_cache", ".pytest_cache", "site", "dist", "build", ".dvc", "mlruns"}


def tool_version(name):
    """Return first line of `<tool> --version`, or None if the tool is absent."""
    path = shutil.which(name)
    if not path:
        return None
    try:
        out = subprocess.run([path, "--version"], capture_output=True, text=True,
                             timeout=10)
        line = (out.stdout or out.stderr).strip().splitlines()
        return line[0] if line else "present"
    except (OSError, subprocess.SubprocessError):
        return "present"


def host_reachable(host, port=443, timeout=3.0):
    """True if a TCP connection to host:port succeeds."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def git_remote(repo):
    """Return the origin URL host part only (no credentials, no path)."""
    try:
        out = subprocess.run(["git", "-C", str(repo), "remote", "get-url", "origin"],
                             capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    url = out.stdout.strip()
    if not url:
        return None
    url = url.split("@")[-1]
    for prefix in ("https://", "http://", "ssh://"):
        url = url.replace(prefix, "")
    return url.split("/")[0].split(":")[0]


def count_files(project, suffix):
    total = 0
    for dirpath, dirnames, filenames in os.walk(project):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        total += sum(1 for f in filenames if f.endswith(suffix))
    return total


def find_projects(root, depth):
    """Folders containing .git or a stack file, up to `depth` levels below root."""
    root = Path(root).resolve()
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel_depth = len(Path(dirpath).relative_to(root).parts)
        if rel_depth > depth:
            dirnames[:] = []
            continue
        is_project = ".git" in dirnames or any(f in filenames for f in STACK_FILES[:4])
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        if is_project:
            found.append(Path(dirpath))
            dirnames[:] = []
    return found or [root]


def describe_project(project):
    agent = {rel: kind for rel, kind in AGENT_FILES.items() if (project / rel).exists()}
    stack = [f for f in STACK_FILES if (project / f).exists()]
    codeowners = any((project / p).exists() for p in
                     ("CODEOWNERS", ".github/CODEOWNERS", ".gitlab/CODEOWNERS"))
    ci = [p for p in (".github/workflows", ".gitlab-ci.yml", "Jenkinsfile",
                      "azure-pipelines.yml") if (project / p).exists()]
    return {
        "path": str(project),
        "git_host": git_remote(project) if (project / ".git").exists() else None,
        "agent_files": agent,
        "stack_files": stack,
        "codeowners": codeowners,
        "ci": ci,
        "py_files": count_files(project, ".py"),
        "notebooks": count_files(project, ".ipynb"),
        "md_files": count_files(project, ".md"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-network", action="store_true")
    parser.add_argument("--depth", type=int, default=3)
    args = parser.parse_args()

    home = Path.home()
    result = {
        "os": f"{platform.system()} {platform.release()}",
        "python": sys.version.split()[0],
        "tools": {t: tool_version(t) for t in TOOLS},
        "home_agent_dirs": [d for d in HOME_AGENT_DIRS if (home / d).exists()],
        "network": None if args.no_network else {
            h: host_reachable(h) for h in ("pypi.org", "github.com", "api.anthropic.com")
        },
        "projects": [describe_project(p) for p in find_projects(args.root, args.depth)],
    }

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    print(f"OS: {result['os']} | python {result['python']}")
    present = [t for t, v in result["tools"].items() if v]
    missing = [t for t, v in result["tools"].items() if not v]
    print(f"Tools present: {', '.join(present) or '-'}")
    print(f"Tools missing: {', '.join(missing) or '-'}")
    print(f"User-level agent dirs: {', '.join(result['home_agent_dirs']) or '-'}")
    if result["network"] is not None:
        net = ", ".join(f"{h}={'ok' if ok else 'no'}" for h, ok in result["network"].items())
        print(f"Network: {net}")
    for p in result["projects"]:
        print(f"\n[{p['path']}] git={p['git_host'] or '-'} ci={p['ci'] or '-'} "
              f"codeowners={p['codeowners']}")
        print(f"  agent files: {', '.join(p['agent_files']) or 'none'}")
        print(f"  stack: {', '.join(p['stack_files']) or '-'}")
        print(f"  files: py={p['py_files']} ipynb={p['notebooks']} md={p['md_files']}")


if __name__ == "__main__":
    main()
