"""Markdown export helpers."""

from __future__ import annotations

from pathlib import Path


def _cell(value: object) -> str:
    text = str(value)
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("\n", "<br>")


def table_to_markdown(data: dict) -> str:
    columns = data.get("columns") or data.get("headers") or []
    rows = data.get("rows") or []
    headers = [col.get("name", "") if isinstance(col, dict) else col for col in columns]
    lines = [
        "| " + " | ".join(_cell(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        values = list(row)
        if len(values) < len(headers):
            values.extend("" for _ in range(len(headers) - len(values)))
        lines.append("| " + " | ".join(_cell(value) for value in values[: len(headers)]) + " |")
    return "\n".join(lines) + "\n"


def export_table(data: dict, output: str | Path) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(table_to_markdown(data), encoding="utf-8")
