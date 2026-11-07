# Changelog

All notable changes to lab-forge. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [SemVer](https://semver.org/): breaking rule or layout change = major, new component = minor,
fix = patch. The engine version lives in `skills/lab-forge/scripts/install_global.py` (`VERSION`) and is
mirrored in `skills/lab-forge/.claude-plugin/plugin.json` and the `SKILL.md` front matter; `tests/test_version.py`
keeps them equal. A merge to `main` with a new version tags `v<version>` and publishes a GitHub release.

## [Unreleased]

## [0.5.0] - 2026-11-08

### Added
- Claude Code plugin manifest (`skills/lab-forge/.claude-plugin/plugin.json`) and a one-plugin marketplace at
  the repo root: `claude plugin marketplace add adetbekov/lab-forge`, then `claude plugin install lab-forge@lab-forge`. JEB-2210
- This changelog, a version sync test and a release workflow that tags `v<version>` on merge to `main`. JEB-2210

### Changed
- `install_global.py` no longer links the engine into `~/.claude/skills/` when it already runs from the Claude
  Code plugin cache (it would load twice and dangle after a plugin update). JEB-2210

## [0.4.1] - 2026-10-20

### Added
- Done check in the core: run the task's entry point and verify every named file, key and metric before "done". JEB-1912

### Changed
- Leaner always-on context; the bench reports honest token counts. JEB-1912

## [0.4.0] - 2026-10-19

### Added
- Core plus defaults split, verbatim profile block in the repo `AGENTS.md`, one-line tune. JEB-1905
- Guard protects the core and profile blocks; tune refuses phrases that weaken a core rule. JEB-1906
- Idempotent `upgrade.py` from v0.1-v0.3, one block marker format. JEB-1908
- Bench: methodology, mutants, honest tokens. JEB-1907

## [0.3.0] - 2026-10-19

### Added
- Global instruction layer with per-harness adapters, branch guard, smoke test. JEB-1879
- Opt-in decision hooks (Stop, skill choice) with a bring-your-own decision model. JEB-1893
- Task-size ladder in the global rules; blind A/B wins vs v0.2, ponytail and bare. JEB-1895

## [0.2.0] - 2026-10-18

### Fixed
- v0.1 defects from the first A/B round: generated rules no longer beat the user's explicit ask. JEB-1878

## [0.1.0] - 2026-10-17

### Added
- First public release: deploy, audit, interview, generate, tune; style pack; bench.

[Unreleased]: https://github.com/adetbekov/lab-forge/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/adetbekov/lab-forge/compare/v0.4.1...v0.5.0
[0.4.1]: https://github.com/adetbekov/lab-forge/releases/tag/v0.4.1
[0.4.0]: https://github.com/adetbekov/lab-forge/commit/20d9d38
[0.3.0]: https://github.com/adetbekov/lab-forge/commit/8417b6c
[0.2.0]: https://github.com/adetbekov/lab-forge/commit/06dca67
[0.1.0]: https://github.com/adetbekov/lab-forge/commit/b54d002
