#!/usr/bin/env python3
"""Fetch Apple-style emoji as PNG for embedding in slides.

The deck design forbids emoji typed as text (they render differently per platform
and break the fixed design). This script downloads the Apple rendering as PNG.

Usage:
    python fetch_apple_emoji.py "🐘" [out_dir] [--size 160]
    python fetch_apple_emoji.py "🐘,💬,🦜" assets/emoji

Fallback protocol (see SKILL.md — ask FIRST, degrade after):
1. emojicdn.elk.sh (Apple style), then emojiapi.dev
2. CDN unreachable -> ASK the user to enable network access (interactive)
3. Declined / batch mode -> npm package emoji-datasource-apple
   (img/apple/64/<codepoints>.png; npm registry is usually allowlisted)
4. All failed: build WITHOUT emoji (never type emoji as text).
Pass --no-ask to run the full chain non-interactively (batch mode); by default
the script exits with code 42 after CDN failure so the caller can ask the user.
"""

import pathlib
import subprocess
import sys
import urllib.parse
import urllib.request


def fetch(
    emoji: str, out_dir: pathlib.Path, size: int = 160, no_ask: bool = False
) -> pathlib.Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    codepoints = "-".join(f"{ord(c):x}" for c in emoji if ord(c) != 0xFE0F)
    out = out_dir / f"emoji_{codepoints}.png"
    urls = [
        f"https://emojicdn.elk.sh/{urllib.parse.quote(emoji)}?style=apple",
        f"https://emojiapi.dev/api/v1/{codepoints}/{size}.png",
    ]
    last_err = None
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "star-deck"})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
            if data[:8].startswith(b"\x89PNG") or data[:3] == b"\xff\xd8\xff":
                out.write_bytes(data)
                return out
            last_err = f"non-image response from {url}"
        except Exception as e:  # noqa: BLE001
            last_err = f"{url}: {e}"
    if not no_ask:
        print(
            f"CDN unreachable ({last_err}).\n"
            "ASK THE USER: enable network access and retry, or approve the "
            "offline npm fallback? Re-run with --no-ask to proceed offline.",
            file=sys.stderr,
        )
        raise SystemExit(42)
    # Fallback (approved/batch): npm emoji-datasource-apple
    try:
        pkg = pathlib.Path("node_modules/emoji-datasource-apple")
        if not pkg.exists():
            subprocess.run(
                ["npm", "install", "--no-save", "emoji-datasource-apple"],
                check=True,
                capture_output=True,
                timeout=120,
            )
        # dataset names files with fully-qualified codepoints (incl. fe0f sometimes)
        for name in (codepoints, "-".join(f"{ord(c):x}" for c in emoji)):
            src = pkg / "img" / "apple" / "64" / f"{name}.png"
            if src.exists():
                out.write_bytes(src.read_bytes())
                return out
        last_err = f"npm dataset has no {codepoints}.png"
    except Exception as e:  # noqa: BLE001
        last_err = f"npm fallback: {e}"
    raise RuntimeError(
        f"Could not fetch emoji {emoji!r}: {last_err}. "
        "All sources exhausted. Interactive session: STOP and ask the user "
        "(build without emoji / user provides assets / retry with network). "
        "Batch mode: build without emoji (never type emoji as text) and "
        "report the degradation."
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    args = [a for a in sys.argv[1:] if a != "--no-ask"]
    no_ask = "--no-ask" in sys.argv
    emojis = [e.strip() for e in args[0].split(",") if e.strip()]
    out_dir = (
        pathlib.Path(args[1])
        if len(args) > 1 and not args[1].startswith("--")
        else pathlib.Path("assets/emoji")
    )
    size = 160
    if "--size" in args:
        size = int(args[args.index("--size") + 1])
    for e in emojis:
        p = fetch(e, out_dir, size, no_ask=no_ask)
        print(p)
