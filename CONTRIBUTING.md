# Contributing to glyph-arts

Thanks for your interest in glyph-arts. This project is small, MIT-licensed,
and welcomes both new chart types and bug fixes.

## Setup

```bash
git clone https://github.com/2233admin/glyph-arts.git
cd glyph-arts
uv venv && source .venv/bin/activate   # or `.venv\Scripts\activate` on Windows
uv pip install -e ".[all,test]"
pytest tests/                          # 30 tests; should be all green
```

If you don't have `uv`:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[all,test]"
```

## Optional system dependencies

The `image` and `video` chart types shell out to `chafa` and `ffmpeg`.
See [README.md#system-dependencies](README.md#system-dependencies-image--video-charts-only).

## Project layout

- `cli_charts/chart.py` -- main CLI dispatch + 29 chart-type renderers
- `cli_charts/dashboard.py` -- glyph-arts-dashboard entry (Rich/Textual TUI)
- `cli_charts/themes/` -- 4 brand-inspired color palettes
- `tests/` -- pytest suite (subprocess-based for chart-type smoke; unit
  tests for sampling, doc consistency)
- `SKILL.md` -- AI-agent usage contract (Claude Code / Codex / Gemini)

## Where to start

Good first issues are tagged `good first issue` on the
[Linear project board](https://linear.app/xartpro/project/glyph-arts).
Code-level pointers:

- New chart type: add to `cli_charts/chart.py` `CMDS` dict +
  `CHART_TYPES_BY_ENGINE` constant + write smoke test in
  `tests/test_doc_consistency.py` style.
- Bug fix: add a regression test under `tests/`, fix the code, ensure
  `pytest tests/` is green.

## Pull request flow

1. Open a Linear issue first (or pick an existing one). We track work in
   the `XartPro / glyph-arts` Linear project.
2. Branch from `master` with name like `xar-NNN-short-description`.
3. Use the [PR template](.github/pull_request_template.md); add
   `Closes XAR-NNN` so the issue auto-closes on merge.
4. CI runs ruff + mypy + pytest on 13 OS/Python combos. All must pass.
5. A maintainer reviews. Squash-merge into `master`.

## Commit style

[Conventional Commits](https://www.conventionalcommits.org/):

- `feat: ...` new chart type / capability
- `fix: ...` bug fix
- `docs: ...` README / SKILL.md / CONTRIBUTING
- `ci: ...` CI / workflow changes
- `chore: ...` build, deps, gitignore

## Code style

- Ruff: `ruff check cli_charts tests` -> 0 errors
- Mypy: `mypy cli_charts --ignore-missing-imports` -> 0 errors
- Tests: `pytest tests/` -> green

`ruff` and `mypy` config lives in `pyproject.toml`.

## Releases

Tag `vX.Y.Z`. Push the tag. `release.yml` builds and publishes to PyPI
via Trusted Publishing (no tokens; OIDC). Maintainers only.

## Reporting security issues

See [SECURITY.md](SECURITY.md). Don't open public GitHub issues for
vulnerabilities.
