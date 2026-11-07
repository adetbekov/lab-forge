"""One version everywhere: engine, plugin manifest, SKILL.md front matter, changelog, marketplace entry."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "skills" / "lab-forge"


def engine_version():
    return re.search(r'^VERSION = "([^"]+)"', (ENGINE / "scripts" / "install_global.py").read_text(), re.M)[1]


def test_engine_version_is_semver():
    assert re.fullmatch(r"\d+\.\d+\.\d+", engine_version())


def test_plugin_manifest_matches_engine():
    manifest = json.loads((ENGINE / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "lab-forge"
    assert manifest["version"] == engine_version()
    for key in ("description", "author", "homepage", "repository", "license"):
        assert manifest.get(key), f"plugin.json needs {key}"


def test_skill_front_matter_matches_engine():
    head = (ENGINE / "SKILL.md").read_text().split("---", 2)[1]
    assert re.search(rf'^  version: "{re.escape(engine_version())}"$', head, re.M)
    assert re.search(r"^name: lab-forge$", head, re.M)


def test_changelog_top_release_is_engine_version():
    text = (ROOT / "CHANGELOG.md").read_text()
    releases = re.findall(r"^## \[(\d+\.\d+\.\d+)\] - (\d{4}-\d{2}-\d{2})$", text, re.M)
    assert releases and releases[0][0] == engine_version(), "bump VERSION and add a dated changelog section together"
    assert "## [Unreleased]" in text
    assert [v for v, _ in releases] == sorted({v for v, _ in releases}, key=lambda v: tuple(map(int, v.split("."))),
                                             reverse=True)


def test_marketplace_points_at_the_plugin():
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    assert market["name"] == "lab-forge" and market["owner"]["name"]
    [entry] = market["plugins"]
    assert entry["name"] == "lab-forge" and entry["source"] == "./skills/lab-forge"
    assert "version" not in entry, "plugin.json owns the version; a second copy here only drifts"
    assert (ROOT / entry["source"] / ".claude-plugin" / "plugin.json").exists()
    assert len((ENGINE / "README.md").read_text().split()) >= 40, "the directory needs a README of 40+ words in the plugin folder"
