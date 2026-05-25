from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, cast

from cli_charts.auto_detect import detect_auto

INCPLOT_TYPES = {
    "auto",
    "sparkline",
    "bar",
    "multibar",
    "stackedbar",
    "line",
    "scatter",
    "hist",
    "table",
    "kline",
    "candlestick",
}

DATE_FORMATS = (
    "%d/%m/%Y",
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
)


@dataclass(frozen=True)
class IncplotDetection:
    chart_type: str
    data: Any


def detect_incplot(raw: Any, prefer: str = "") -> IncplotDetection:
    """incplot-style automatic plotting over JSON, JSONL, CSV, and TSV."""
    preferred = prefer if prefer in INCPLOT_TYPES and prefer != "auto" else ""
    if not isinstance(raw, str):
        return _detect_object(raw, preferred)
    text = raw.lstrip("\ufeff").strip()
    if not text:
        raise ValueError("incplot input must not be empty")
    parsed = _parse_json_or_jsonl(text)
    if parsed is not None:
        return _detect_object(parsed, preferred)
    return _detect_delimited(text, preferred)


def _parse_json_or_jsonl(text: str) -> Any | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    rows: list[Any] = []
    for line in text.splitlines():
        clean = line.strip()
        if not clean:
            continue
        try:
            rows.append(json.loads(clean))
        except json.JSONDecodeError:
            return None
    return rows if rows else None


def _detect_object(data: Any, prefer: str = "") -> IncplotDetection:
    if isinstance(data, list) and data and all(isinstance(item, dict) for item in data):
        detection = _detect_records(data, prefer)
    elif prefer == "hist" and isinstance(data, list) and all(_is_number(item) for item in data):
        detection = IncplotDetection("hist", {"values": [_num(item) for item in data]})
    else:
        base = detect_auto(json.dumps(data, ensure_ascii=False), _auto_prefer(prefer))
        detection = IncplotDetection(base.chart_type, base.data)
    return _coerce(detection, prefer)


def _detect_delimited(text: str, prefer: str = "") -> IncplotDetection:
    sample = text[:2048]
    delimiter = "\t" if sample.count("\t") > sample.count(",") else ","
    rows = [row for row in csv.reader(io.StringIO(text), delimiter=delimiter) if any(cell.strip() for cell in row)]
    if not rows:
        return IncplotDetection("table", {"columns": [], "rows": []})
    has_header = _has_header(rows)
    columns = rows[0] if has_header else [f"col{i + 1}" for i in range(len(rows[0]))]
    body = rows[1:] if has_header else rows
    width = max(len(row) for row in body) if body else len(columns)
    body = [row + [""] * (width - len(row)) for row in body]
    columns = columns + [f"col{i + 1}" for i in range(len(columns), width)]
    records = [{columns[idx]: row[idx] for idx in range(width)} for row in body]
    return _detect_records(records, prefer)


def _detect_records(records: list[dict[str, Any]], prefer: str = "") -> IncplotDetection:
    if not records:
        return IncplotDetection("table", {"columns": [], "rows": []})
    columns = list(dict.fromkeys(key for row in records for key in row))
    lower = {col.lower(): col for col in columns}
    ohlc = [lower.get(name) for name in ("open", "high", "low", "close")]
    date_col = _first_column(columns, ("date", "time", "day"))
    if all(ohlc) and date_col:
        open_col, high_col, low_col, close_col = cast(list[str], ohlc)
        return _coerce(IncplotDetection("kline", {
            "dates": _normalize_dates([row.get(date_col, "") for row in records]),
            "open": [_num(row.get(open_col)) for row in records],
            "high": [_num(row.get(high_col)) for row in records],
            "low": [_num(row.get(low_col)) for row in records],
            "close": [_num(row.get(close_col)) for row in records],
        }), prefer)

    numeric_cols = [col for col in columns if all(_is_number(row.get(col)) for row in records if row.get(col) not in ("", None))]
    text_cols = [col for col in columns if col not in numeric_cols]
    temporal_col = next((col for col in text_cols if _looks_temporal(col, [str(row.get(col, "")) for row in records])), None)

    if prefer == "table" or not numeric_cols:
        return IncplotDetection("table", {"columns": columns, "rows": [[row.get(col, "") for col in columns] for row in records]})
    if prefer == "hist":
        col = numeric_cols[-1]
        return IncplotDetection("hist", {"values": [_num(row.get(col)) for row in records]})
    if text_cols and len(numeric_cols) == 1 and not temporal_col:
        label_col, value_col = text_cols[0], numeric_cols[0]
        return _coerce(IncplotDetection("bar", {
            "labels": [str(row.get(label_col, "")) for row in records],
            "values": [_num(row.get(value_col)) for row in records],
        }), prefer)
    if text_cols and len(numeric_cols) > 1 and not temporal_col:
        label_col = text_cols[0]
        return _coerce(IncplotDetection("multibar", {
            "labels": [str(row.get(label_col, "")) for row in records],
            "series": [{"label": col, "values": [_num(row.get(col)) for row in records]} for col in numeric_cols],
        }), prefer)
    if temporal_col:
        return _coerce(IncplotDetection("line", [
            {
                "label": col,
                "x": _normalize_dates([row.get(temporal_col, "") for row in records]),
                "y": [_num(row.get(col)) for row in records],
            }
            for col in numeric_cols
        ]), prefer)
    if len(numeric_cols) == 1:
        col = numeric_cols[0]
        return _coerce(IncplotDetection("sparkline", {"values": [_num(row.get(col)) for row in records]}), prefer)
    if len(numeric_cols) == 2:
        x_col, y_col = numeric_cols[:2]
        default = "line" if prefer == "line" else "scatter"
        return _coerce(IncplotDetection(default, {
            "label": y_col,
            "x": [_num(row.get(x_col)) for row in records],
            "y": [_num(row.get(y_col)) for row in records],
        }), prefer)
    x_col = numeric_cols[0]
    return _coerce(IncplotDetection("line", [
        {"label": col, "x": [_num(row.get(x_col)) for row in records], "y": [_num(row.get(col)) for row in records]}
        for col in numeric_cols[1:]
    ]), prefer)


def _coerce(detection: IncplotDetection, prefer: str) -> IncplotDetection:
    if not prefer or prefer == detection.chart_type:
        return detection
    data = detection.data
    values = _values(data)
    if prefer == "hist" and values:
        return IncplotDetection("hist", {"values": values})
    if prefer in {"multibar", "stackedbar"}:
        grouped = _grouped_bars(data)
        if grouped:
            return IncplotDetection(prefer, grouped)
    if prefer == "bar" and values:
        labels = _labels(data) or list(range(len(values)))
        return IncplotDetection("bar", {"labels": labels[:len(values)], "values": values})
    if prefer in {"line", "scatter"} and values:
        return IncplotDetection(prefer, {"x": list(range(len(values))), "y": values})
    if prefer == "sparkline" and values:
        return IncplotDetection("sparkline", {"values": values})
    if prefer == "table":
        return IncplotDetection("table", _table(data))
    return detection


def _values(data: Any) -> list[float]:
    if isinstance(data, dict):
        if isinstance(data.get("values"), list):
            return [_num(v) for v in data["values"] if _is_number(v)]
        if isinstance(data.get("y"), list):
            return [_num(v) for v in data["y"] if _is_number(v)]
        if isinstance(data.get("series"), list) and data["series"]:
            first = data["series"][0]
            if isinstance(first, dict) and isinstance(first.get("values"), list):
                return [_num(v) for v in first["values"] if _is_number(v)]
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return [_num(v) for v in data[0].get("y", []) if _is_number(v)]
    if isinstance(data, list):
        return [_num(v) for v in data if _is_number(v)]
    return []


def _labels(data: Any) -> list[Any]:
    if isinstance(data, dict):
        raw = data.get("labels", data.get("x"))
        if isinstance(raw, list):
            return list(raw)
    if isinstance(data, list) and data and isinstance(data[0], dict):
        raw = data[0].get("x", data[0].get("labels"))
        if isinstance(raw, list):
            return list(raw)
    return []


def _grouped_bars(data: Any) -> dict[str, Any] | None:
    if isinstance(data, dict) and isinstance(data.get("series"), list):
        series = []
        for idx, item in enumerate(data["series"]):
            if not isinstance(item, dict):
                continue
            raw_values = item.get("values", item.get("y", []))
            values = raw_values if isinstance(raw_values, list) else []
            series.append({
                "label": str(item.get("label", f"S{idx + 1}")),
                "values": [_num(value) for value in values if _is_number(value)],
            })
        labels = _labels(data) or list(range(len(series[0]["values"]))) if series else []
        return {"labels": labels, "series": series} if series else None
    if isinstance(data, list) and data and all(isinstance(item, dict) for item in data):
        series = [
            {
                "label": str(item.get("label", f"S{idx + 1}")),
                "values": [_num(value) for value in item.get("y", item.get("values", [])) if _is_number(value)],
            }
            for idx, item in enumerate(data)
        ]
        labels = _labels(data) or list(range(len(series[0]["values"]))) if series else []
        return {"labels": labels, "series": series} if series else None
    values = _values(data)
    if values:
        return {"labels": _labels(data) or list(range(len(values))), "series": [{"label": "value", "values": values}]}
    return None


def _table(data: Any) -> dict[str, Any]:
    if isinstance(data, dict):
        return {"columns": ["key", "value"], "rows": [[key, value] for key, value in data.items()]}
    if isinstance(data, list):
        return {"columns": ["value"], "rows": [[item] for item in data]}
    return {"columns": ["value"], "rows": [[data]]}


def _auto_prefer(prefer: str) -> str:
    return prefer if prefer in {"sparkline", "bar", "line", "scatter", "table"} else ""


def _is_number(value: Any) -> bool:
    if isinstance(value, bool) or value in ("", None):
        return False
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True


def _num(value: Any) -> float:
    return float(value)


def _has_header(rows: list[list[str]]) -> bool:
    if len(rows) < 2:
        return False
    first, second = rows[0], rows[1]
    return any(not _is_number(left) and _is_number(right) for left, right in zip(first, second, strict=False))


def _first_column(columns: list[str], tokens: tuple[str, ...]) -> str | None:
    return next((col for col in columns if any(token in col.lower() for token in tokens)), None)


def _looks_temporal(name: str, values: list[str]) -> bool:
    if any(token in name.lower() for token in ("date", "time", "day", "month", "year")):
        return True
    return any(len(value) >= 6 and any(sep in value for sep in ("-", "/", ":")) for value in values[:5])


def _normalize_dates(values: list[Any]) -> list[str]:
    return [_normalize_date(value) for value in values]


def _normalize_date(value: Any) -> str:
    text = str(value)
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return text
