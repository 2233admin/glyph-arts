"""Lead hotfix: re-add @register to 19 new Phase 3a modules.

Root cause: L5 extracted 19 chart fns from _helpers.py into new files via
`from x import y` form. The @register decorator only fires at module-level
`def`, so the new files registered 0 entries, dropping cli_charts.registry.CMDS
from 44 to 32 (loss = 12 L5-introduced + 30 pre-existing Phase 2 L3 gap).

This script is mechanical: insert `from cli_charts.registry import register`
into the import block + insert `@register("<name>")` immediately before
`def <name>(`. Body 0 changes. Mirrors the 092e128 lead fix precedent.
"""
import re
from pathlib import Path

REPO = Path("D:/projects/glyph-arts")

TARGETS = {
    "aggregates": [
        "graph", "comparison", "diverging", "summary", "sparkline_table",
        "cdf_chart", "rank_table", "percentile", "boxplot_comparison",
        "stacked_bar_text",
    ],
    "composite": ["panel", "dashboard", "rich_live"],
    "algebra": [
        "formula", "formula_pretty", "calibrate",
        "status_command", "splash_command", "wave_command",
    ],
}


def patch_file(path: Path, name: str) -> str:
    """Insert @register and the register-import. Return 'patched'|'skipped'|'error:...'."""
    src = path.read_text(encoding="utf-8")
    if "@register" in src:
        return "skipped (already has @register)"

    lines = src.split("\n")

    # 1) Insert `from cli_charts.registry import register` after the last
    #    module-level import. We only treat top-level (no-indent) import
    #    statements as candidates.
    last_import_idx = -1
    for i, line in enumerate(lines):
        if line.startswith((" ", "\t")):
            continue
        stripped = line.lstrip()
        if stripped.startswith("from ") or stripped.startswith("import "):
            last_import_idx = i

    if last_import_idx >= 0:
        # Insert the new import + a blank line AFTER last_import_idx.
        lines = (
            lines[: last_import_idx + 1]
            + ["from cli_charts.registry import register"]
            + lines[last_import_idx + 1 :]
        )
    else:
        # No module-level imports: insert after the docstring (line 1) + blank.
        # Originals are: L1 docstring, L2 blank, L3 def.
        lines = lines[:2] + ["from cli_charts.registry import register"] + lines[2:]

    # 2) Insert `@register("<name>")` immediately before `def <name>(` line.
    joined = "\n".join(lines)
    def_re = re.compile(rf"^def {re.escape(name)}\(", re.MULTILINE)
    m = def_re.search(joined)
    if not m:
        return f"error: no `def {name}(` found"

    # m.start() = char offset in `joined`. Convert to line index by counting
    # newlines in the prefix.
    prefix = joined[: m.start()]
    line_idx = prefix.count("\n")
    # `line_idx` is the 0-based index of the line that contains "def".
    # Insert decorator + blank BEFORE that line.
    lines = lines[:line_idx] + [f'@register("{name}")', ""] + lines[line_idx:]

    path.write_text("\n".join(lines), encoding="utf-8")
    return "patched"


total_patched = 0
total_skipped = 0
for subdir, names in TARGETS.items():
    for name in names:
        f = REPO / "cli_charts" / "charts" / subdir / f"{name}.py"
        if not f.exists():
            print(f"MISSING: {f}")
            continue
        result = patch_file(f, name)
        rel = f.relative_to(REPO)
        if result == "patched":
            print(f"PATCHED: {rel}")
            total_patched += 1
        elif result.startswith("skipped"):
            print(f"SKIP: {rel} ({result})")
            total_skipped += 1
        else:
            print(f"ERROR: {rel}: {result}")

print(f"\nSummary: {total_patched} patched, {total_skipped} skipped")
