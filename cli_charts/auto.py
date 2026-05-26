"""Automatic input parsing and chart inference for ``glyph-arts plot``."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from io import StringIO
from typing import Any


class AutoPlotError(ValueError):
    """Raised when input can be parsed but not sensibly plotted."""


@dataclass(frozen=True)
class AutoPlotResult:
    chart_type: str
    data: Any


_DATE_KEYS = {"date", "time", "timestamp", "datetime", "day", "month", "year", "x"}
_FREQ_KEYS = {"freq", "frequency", "hz", "mhz", "bin", "bins", "x"}
_POWER_KEYS = {"db", "power", "magnitude", "level", "amplitude", "y"}
_EXPLICIT_FREQ_KEYS = _FREQ_KEYS - {"x"}
_EXPLICIT_POWER_KEYS = _POWER_KEYS - {"y"}
_TIME_KEYS = {"time", "timestamp", "frame", "frames", "t"}


def build_auto_plot(raw: str, *, input_format: str | None = None, forced_type: str | None = None) -> AutoPlotResult:
    parsed = parse_input(raw, input_format=input_format)
    chart_type = forced_type or infer_chart_type(parsed)
    return AutoPlotResult(chart_type=chart_type, data=normalize_data(parsed, chart_type))


def parse_input(raw: str, *, input_format: str | None = None) -> Any:
    raw = raw.strip()
    if not raw:
        raise AutoPlotError("plot needs --json, --file, or piped data")

    fmt = (input_format or "auto").lower()
    if fmt == "auto":
        numeric = _parse_numeric_lines(raw)
        if numeric is not None:
            return numeric
        fmt = _detect_format(raw)

    if fmt == "json":
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AutoPlotError(f"invalid JSON: {exc}") from exc

    if fmt == "jsonl":
        rows = []
        for line_no, line in enumerate(raw.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise AutoPlotError(f"invalid JSONL on line {line_no}: {exc}") from exc
        if not rows:
            raise AutoPlotError("JSONL input has no rows")
        return rows

    if fmt in {"csv", "tsv"}:
        delimiter = "\t" if fmt == "tsv" else ","
        rows = list(csv.DictReader(StringIO(raw), delimiter=delimiter))
        if not rows:
            raise AutoPlotError(f"{fmt.upper()} input has no data rows")
        return [_coerce_row(row) for row in rows]

    raise AutoPlotError(f"unsupported --format {input_format!r}; use auto, json, jsonl, csv, or tsv")


def infer_chart_type(parsed: Any) -> str:
    if _is_numeric_sequence(parsed):
        return "line"

    if _is_matrix(parsed):
        return "heatmap"

    if isinstance(parsed, list) and parsed and all(isinstance(row, dict) for row in parsed):
        columns = _columns(parsed)
        numeric = [col for col in columns if _is_numeric_column(parsed, col)]
        categorical = [col for col in columns if col not in numeric]
        date_like = [col for col in columns if col.lower() in _DATE_KEYS]
        freq_like = [col for col in columns if col.lower() in _EXPLICIT_FREQ_KEYS]
        power_like = [col for col in columns if col.lower() in _EXPLICIT_POWER_KEYS]

        if freq_like and power_like:
            return "spectrum"
        if len(numeric) >= 2 and any(col.lower() in _TIME_KEYS for col in columns):
            return "waterfall"

        if len(numeric) == 2 and len(columns) == 2:
            return "scatter"
        if date_like and numeric:
            return "line"
        if len(numeric) == 1 and categorical:
            return "bar"
        if len(numeric) >= 2:
            return "line"

    if isinstance(parsed, dict):
        if isinstance(parsed.get("traces"), list) and parsed["traces"]:
            return "spectrum"
        if _looks_like_spectrum(parsed):
            return "spectrum"
        if _looks_like_waterfall(parsed) and _has_any_key(parsed, _FREQ_KEYS | _TIME_KEYS | {"xlabels", "ylabels"}):
            return "waterfall"
        if "matrix" in parsed:
            return "heatmap"
        if "labels" in parsed and "values" in parsed:
            return "bar"
        if "values" in parsed and _is_numeric_sequence(parsed["values"]):
            return "line"
        if "y" in parsed and _is_numeric_sequence(parsed["y"]):
            return "line"

    raise AutoPlotError("could not infer a chart; use --as bar, line, scatter, or heatmap")


def normalize_data(parsed: Any, chart_type: str) -> Any:
    if chart_type in {"line", "step", "uniplot"}:
        return _normalize_line(parsed)
    if chart_type == "scatter":
        return _normalize_scatter(parsed)
    if chart_type in {"bar", "pie"}:
        return _normalize_bar(parsed)
    if chart_type == "heatmap":
        return _normalize_heatmap(parsed)
    if chart_type == "hist":
        if _is_numeric_sequence(parsed):
            return {"values": parsed}
        if isinstance(parsed, dict) and _is_numeric_sequence(parsed.get("values")):
            return parsed
    if chart_type == "sparkline":
        if _is_numeric_sequence(parsed):
            return {"values": parsed}
        if isinstance(parsed, dict) and _is_numeric_sequence(parsed.get("values")):
            return parsed
    if chart_type == "spectrum":
        return _normalize_spectrum(parsed)
    if chart_type == "waterfall":
        return _normalize_waterfall(parsed)
    raise AutoPlotError(f"auto plot cannot normalize input as {chart_type!r}")


def _detect_format(raw: str) -> str:
    first = raw.lstrip()[:1]
    if first in {"[", "{"}:
        return "json"
    lines = [line for line in raw.splitlines() if line.strip()]
    if lines and all(line.lstrip().startswith(("{", "[")) for line in lines):
        return "jsonl"
    header = lines[0] if lines else ""
    if "\t" in header:
        return "tsv"
    if "," in header:
        return "csv"
    return "json"


def _parse_numeric_lines(raw: str) -> list[int | float] | None:
    values: list[int | float] = []
    for token in raw.replace(",", "\n").split():
        try:
            values.append(_coerce_scalar(token))
        except ValueError:
            return None
    if values and all(_is_number(value) for value in values):
        return values
    return None


def _coerce_row(row: dict[str, str]) -> dict[str, Any]:
    return {key: _coerce_scalar(value) for key, value in row.items()}


def _coerce_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return None
    try:
        if any(ch in value for ch in ".eE"):
            return float(value)
        return int(value)
    except ValueError:
        return value


def _columns(rows: list[dict[str, Any]]) -> list[str]:
    cols: list[str] = []
    for row in rows:
        for key in row:
            if key not in cols:
                cols.append(key)
    return cols


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _is_numeric_sequence(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(_is_number(item) for item in value)


def _is_matrix(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(row, list) and row and all(_is_number(item) for item in row) for row in value)
    )


def _is_numeric_column(rows: list[dict[str, Any]], column: str) -> bool:
    values = [row.get(column) for row in rows if row.get(column) is not None]
    return bool(values) and all(_is_number(value) for value in values)


def _normalize_line(parsed: Any) -> list[dict[str, Any]]:
    if _is_numeric_sequence(parsed):
        return [{"label": "value", "y": parsed}]
    if isinstance(parsed, dict):
        if "y" in parsed:
            return [parsed]
        if "values" in parsed and _is_numeric_sequence(parsed["values"]):
            return [{"label": parsed.get("label", "value"), "y": parsed["values"]}]
    if isinstance(parsed, list) and parsed and all(isinstance(row, dict) for row in parsed):
        columns = _columns(parsed)
        numeric = [col for col in columns if _is_numeric_column(parsed, col)]
        x_col = _pick_x_column(columns, numeric)
        x_values = [row.get(x_col) for row in parsed] if x_col else []
        x = x_values if x_values and all(_is_number(value) for value in x_values) else list(range(len(parsed)))
        return [{"label": col, "x": x, "y": [row.get(col) for row in parsed]} for col in numeric if col != x_col]
    raise AutoPlotError("line needs numbers, {y:[...]}, {values:[...]}, or tabular numeric columns")


def _normalize_scatter(parsed: Any) -> list[dict[str, Any]]:
    if isinstance(parsed, list) and parsed and all(isinstance(row, dict) for row in parsed):
        columns = _columns(parsed)
        numeric = [col for col in columns if _is_numeric_column(parsed, col)]
        if len(numeric) >= 2:
            return [{"label": f"{numeric[1]} vs {numeric[0]}", "x": [row.get(numeric[0]) for row in parsed], "y": [row.get(numeric[1]) for row in parsed]}]
    if isinstance(parsed, dict) and "x" in parsed and "y" in parsed:
        return [parsed]
    raise AutoPlotError("scatter needs two numeric columns or {x:[...], y:[...]}")


def _normalize_bar(parsed: Any) -> dict[str, Any]:
    if isinstance(parsed, dict) and "labels" in parsed and "values" in parsed:
        return parsed
    if isinstance(parsed, list) and parsed and all(isinstance(row, dict) for row in parsed):
        columns = _columns(parsed)
        numeric = [col for col in columns if _is_numeric_column(parsed, col)]
        labels = [col for col in columns if col not in numeric]
        if numeric and labels:
            return {"labels": [str(row.get(labels[0], "")) for row in parsed], "values": [row.get(numeric[0]) for row in parsed]}
    raise AutoPlotError("bar needs labels plus one numeric column")


def _normalize_heatmap(parsed: Any) -> dict[str, Any]:
    if isinstance(parsed, dict) and "matrix" in parsed:
        return parsed
    if _is_matrix(parsed):
        return {"matrix": parsed}
    raise AutoPlotError("heatmap needs a numeric matrix or {matrix:[[...]]}")


def _normalize_spectrum(parsed: Any) -> dict[str, Any]:
    if _is_numeric_sequence(parsed):
        return {"bins": list(range(len(parsed))), "power": parsed}

    if isinstance(parsed, dict):
        if isinstance(parsed.get("traces"), list) and parsed["traces"]:
            return parsed
        x_key = _first_key(parsed, _FREQ_KEYS)
        y_key = _first_key(parsed, _POWER_KEYS)
        if x_key and y_key and _is_numeric_sequence(parsed[x_key]) and _is_numeric_sequence(parsed[y_key]):
            result = dict(parsed)
            result["freq"] = parsed[x_key]
            result["db"] = parsed[y_key]
            _copy_first_alias(result, parsed, "center", ["center", "center_freq", "carrier", "tuned", "vfo"])
            _copy_first_alias(result, parsed, "bandwidth", ["bandwidth", "bw", "span", "filter_width", "passband"])
            return result

    if isinstance(parsed, list) and parsed and all(isinstance(row, dict) for row in parsed):
        columns = _columns(parsed)
        freq_col = _pick_named_column(columns, _FREQ_KEYS)
        power_col = _pick_named_column(columns, _POWER_KEYS)
        if freq_col and power_col and _is_numeric_column(parsed, freq_col) and _is_numeric_column(parsed, power_col):
            return {
                "freq": [row.get(freq_col) for row in parsed],
                "db": [row.get(power_col) for row in parsed],
            }

    raise AutoPlotError("spectrum needs freq/db, frequency/power, bins/power, CSV columns, or a numeric sequence")


def _normalize_waterfall(parsed: Any) -> dict[str, Any]:
    if isinstance(parsed, dict) and _looks_like_waterfall(parsed):
        result = dict(parsed)
        if "matrix" not in result:
            row_key = _first_key(result, _POWER_KEYS)
            if row_key and _is_matrix(result[row_key]):
                result["matrix"] = result[row_key]
        _copy_first_alias(result, result, "freq", ["freq", "frequency", "xlabels"])
        _copy_first_alias(result, result, "time", ["time", "frames", "ylabels"])
        _copy_first_alias(result, result, "min", ["min", "min_db"])
        _copy_first_alias(result, result, "max", ["max", "max_db"])
        return result

    if _is_matrix(parsed):
        return {"matrix": parsed}

    if isinstance(parsed, list) and parsed and all(isinstance(row, dict) for row in parsed):
        rows = []
        freq = None
        time = []
        for idx, row in enumerate(parsed):
            row_key = _first_key(row, _POWER_KEYS)
            if row_key and _is_numeric_sequence(row[row_key]):
                rows.append(row[row_key])
                if freq is None:
                    freq_key = _first_key(row, _FREQ_KEYS)
                    freq = row.get(freq_key) if freq_key else None
                time_key = _first_key(row, _TIME_KEYS)
                time.append(row.get(time_key, idx) if time_key else idx)

        if rows:
            result = {"matrix": rows}
            if freq:
                result["freq"] = freq
            if time:
                result["time"] = time
            return result

        columns = _columns(parsed)
        time_col = _pick_named_column(columns, _TIME_KEYS)
        value_cols = [col for col in columns if col != time_col and _is_numeric_column(parsed, col)]
        if value_cols:
            result = {
                "matrix": [[row.get(col) for col in value_cols] for row in parsed],
                "freq": value_cols,
            }
            if time_col:
                result["time"] = [row.get(time_col) for row in parsed]
            return result

    raise AutoPlotError("waterfall needs matrix data or rows with time plus numeric frequency-bin columns")


def _pick_x_column(columns: list[str], numeric: list[str]) -> str | None:
    for column in columns:
        if column.lower() in _DATE_KEYS:
            return column
    return None if len(numeric) == 1 else columns[0]


def _pick_named_column(columns: list[str], names: set[str]) -> str | None:
    for column in columns:
        if column.lower() in names:
            return column
    return None


def _first_key(mapping: dict[str, Any], names: set[str]) -> str | None:
    for key in mapping:
        if key.lower() in names:
            return key
    return None


def _copy_first_alias(target: dict[str, Any], source: dict[str, Any], dest: str, aliases: list[str]) -> None:
    if dest in target:
        return
    for alias in aliases:
        if alias in source:
            target[dest] = source[alias]
            return


def _looks_like_spectrum(value: dict[str, Any]) -> bool:
    x_key = _first_key(value, _EXPLICIT_FREQ_KEYS)
    y_key = _first_key(value, _EXPLICIT_POWER_KEYS)
    return bool(x_key and y_key and _is_numeric_sequence(value.get(x_key)) and _is_numeric_sequence(value.get(y_key)))


def _looks_like_waterfall(value: dict[str, Any]) -> bool:
    if "matrix" in value and _is_matrix(value["matrix"]):
        return True
    row_key = _first_key(value, _POWER_KEYS)
    return bool(row_key and _is_matrix(value.get(row_key)))


def _has_any_key(mapping: dict[str, Any], names: set[str]) -> bool:
    return any(key.lower() in names for key in mapping)
