"""Markdown export helpers."""

from __future__ import annotations

from pathlib import Path


def table_to_markdown(data: dict) -> str:
    from cli_charts.markup import render_table
    return render_table(data, format="github")


def export_table(data: dict, output: str | Path) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(table_to_markdown(data), encoding="utf-8")
