"""Heuristic input detection for `glyph-arts auto`."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from typing import Any

AUTO_TYPES = ("sparkline", "bar", "line", "scatter", "table")


@dataclass(frozen=True)
class Detection:
    chart_type: str
    data: Any


def detect_auto(raw: str, prefer: str = "") -> Detection:
    """Parse JSON/CSV/TSV text and return a renderable chart payload."""
    preferred = prefer if prefer in AUTO_TYPES else ""
    text = raw.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        detected = _detect_delimited(text)
    else:
        detected = _detect_json(data)
    if preferred:
        return Detection(preferred, _coerce_for_preferred(detected.data, preferred))
    return detected


def _is_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        try:
            float(value.strip())
        except ValueError:
            return False
        return bool(value.strip())
    return False


def _num(value: Any) -> float:
    return float(value)


def _detect_json(data: Any) -> Detection:
    if isinstance(data, list) and data and all(_is_number(v) for v in data):
        return Detection("sparkline", {"values": [_num(v) for v in data]})

    if isinstance(data, dict):
        if isinstance(data.get("labels"), list) and isinstance(data.get("values"), list):
            return Detection("bar", data)
        if isinstance(data.get("rows"), list):
            return Detection("table", data)
        if "y" in data:
            return Detection("line", data)

    if _is_point_list(data):
        return Detection("scatter", _points_to_scatter(data))

    if isinstance(data, list) and data and all(isinstance(item, dict) and isinstance(item.get("y"), list) for item in data):
        return Detection("line", data)

    return Detection("table", _json_to_table(data))


def _is_point_list(data: Any) -> bool:
    if not isinstance(data, list) or not data:
        return False
    for item in data:
        if isinstance(item, dict):
            if not (_is_number(item.get("x")) and _is_number(item.get("y"))):
                return False
        elif isinstance(item, list | tuple):
            if len(item) < 2 or not (_is_number(item[0]) and _is_number(item[1])):
                return False
        else:
            return False
    return True


def _points_to_scatter(data: list[Any]) -> dict[str, list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    for item in data:
        if isinstance(item, dict):
            xs.append(_num(item["x"]))
            ys.append(_num(item["y"]))
        else:
            xs.append(_num(item[0]))
            ys.append(_num(item[1]))
    return {"x": xs, "y": ys}


def _detect_delimited(text: str) -> Detection:
    sample = text[:2048]
    delimiter = "\t" if sample.count("\t") > sample.count(",") else ","
    rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    rows = [row for row in rows if any(cell.strip() for cell in row)]
    if not rows:
        return Detection("table", {"columns": [], "rows": []})

    has_header = _looks_like_header(rows)
    header = rows[0]
    body = rows[1:] if has_header else rows
    columns = header if has_header else [f"col{i + 1}" for i in range(len(rows[0]))]
    width = max(len(row) for row in body) if body else len(columns)
    body = [row + [""] * (width - len(row)) for row in body]
    columns = columns + [f"col{i + 1}" for i in range(len(columns), width)]

    numeric_cols = [
        idx for idx in range(width)
        if body and all(_is_number(row[idx]) for row in body if row[idx].strip())
    ]
    text_cols = [idx for idx in range(width) if idx not in numeric_cols]

    if len(numeric_cols) == 1 and width == 1:
        col = numeric_cols[0]
        return Detection("sparkline", {"values": [_num(row[col]) for row in body if row[col].strip()]})

    if text_cols and len(numeric_cols) == 1 and not _looks_temporal_column([row[text_cols[0]] for row in body], columns[text_cols[0]]):
        label_col = text_cols[0]
        value_col = numeric_cols[0]
        return Detection("bar", {
            "labels": [row[label_col] for row in body],
            "values": [_num(row[value_col]) for row in body],
        })

    if text_cols and len(numeric_cols) >= 1:
        x_col = text_cols[0]
        return Detection("line", [
            {
                "label": columns[col],
                "x": [row[x_col] for row in body],
                "y": [_num(row[col]) for row in body],
            }
            for col in numeric_cols
        ])

    return Detection("table", {"columns": columns, "rows": body})


def _looks_like_header(rows: list[list[str]]) -> bool:
    if len(rows) < 2:
        return False
    first, second = rows[0], rows[1]
    if len(first) != len(second):
        return True
    if all(cell.strip().replace("_", "").isalpha() for cell in first):
        return True
    return any(not _is_number(a) and _is_number(b) for a, b in zip(first, second, strict=False))


def _looks_temporal_column(values: list[str], name: str = "") -> bool:
    lowered = name.lower()
    if any(token in lowered for token in ("date", "time", "day", "month", "year")):
        return True
    for value in values[:5]:
        text = value.strip()
        if len(text) >= 6 and any(sep in text for sep in ("-", "/", ":")) and any(ch.isdigit() for ch in text):
            return True
    return False


def _json_to_table(data: Any) -> dict[str, Any]:
    if isinstance(data, list) and data and all(isinstance(item, dict) for item in data):
        columns = list(dict.fromkeys(key for item in data for key in item))
        return {"columns": columns, "rows": [[item.get(col, "") for col in columns] for item in data]}
    if isinstance(data, list):
        return {"columns": ["value"], "rows": [[item] for item in data]}
    if isinstance(data, dict):
        return {"columns": ["key", "value"], "rows": [[key, value] for key, value in data.items()]}
    return {"columns": ["value"], "rows": [[data]]}


def _coerce_for_preferred(data: Any, chart_type: str) -> Any:
    values = _extract_values(data)
    if chart_type == "sparkline":
        if values:
            return {"values": values}
    if chart_type == "bar":
        if isinstance(data, dict) and "labels" in data and "values" in data:
            return data
        if isinstance(data, list) and data and isinstance(data[0], dict) and "y" in data[0]:
            return {"labels": data[0].get("x", list(range(len(data[0]["y"])))), "values": data[0]["y"]}
        if values:
            return {"labels": list(range(len(values))), "values": values}
    if chart_type in {"line", "scatter"} and isinstance(data, dict) and "values" in data:
        return {"x": data.get("labels", list(range(len(data["values"])))), "y": data["values"]}
    if chart_type in {"line", "scatter"} and values:
        return {"x": list(range(len(values))), "y": values}
    if chart_type == "table":
        return _json_to_table(data) if not (isinstance(data, dict) and "rows" in data) else data
    return data


def _extract_values(data: Any) -> list[float]:
    if isinstance(data, dict):
        if isinstance(data.get("values"), list):
            return [_num(v) for v in data["values"] if _is_number(v)]
        if isinstance(data.get("y"), list):
            return [_num(v) for v in data["y"] if _is_number(v)]
    if isinstance(data, list):
        if all(_is_number(v) for v in data):
            return [_num(v) for v in data]
        if data and isinstance(data[0], dict) and isinstance(data[0].get("y"), list):
            return [_num(v) for v in data[0]["y"] if _is_number(v)]
    return []
