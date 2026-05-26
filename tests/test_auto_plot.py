import subprocess
import sys

import pytest

from cli_charts.auto import AutoPlotError, build_auto_plot, parse_input


def test_parse_csv_coerces_numbers():
    rows = parse_input("label,value\nA,1\nB,2.5\n", input_format="csv")
    assert rows == [{"label": "A", "value": 1}, {"label": "B", "value": 2.5}]


def test_parse_tsv():
    rows = parse_input("day\tvalue\nMon\t3\nTue\t5\n", input_format="tsv")
    assert rows == [{"day": "Mon", "value": 3}, {"day": "Tue", "value": 5}]


def test_parse_jsonl():
    rows = parse_input('{"x":1,"y":2}\n{"x":2,"y":4}\n', input_format="jsonl")
    assert rows == [{"x": 1, "y": 2}, {"x": 2, "y": 4}]


def test_auto_numeric_json_becomes_line():
    result = build_auto_plot("[1,2,3]")
    assert result.chart_type == "line"
    assert result.data == [{"label": "value", "y": [1, 2, 3]}]


def test_auto_plain_matrix_stays_heatmap():
    result = build_auto_plot("[[1,2],[3,4]]")
    assert result.chart_type == "heatmap"
    assert result.data == {"matrix": [[1, 2], [3, 4]]}


def test_auto_numeric_stdin_lines_become_line():
    result = build_auto_plot("1\n2\n3\n")
    assert result.chart_type == "line"
    assert result.data == [{"label": "value", "y": [1, 2, 3]}]


def test_auto_categorical_numeric_csv_becomes_bar():
    result = build_auto_plot("label,value\nA,1\nB,2\n")
    assert result.chart_type == "bar"
    assert result.data == {"labels": ["A", "B"], "values": [1, 2]}


def test_auto_two_numeric_columns_becomes_scatter():
    result = build_auto_plot("x,y\n1,2\n2,4\n")
    assert result.chart_type == "scatter"
    assert result.data == [{"label": "y vs x", "x": [1, 2], "y": [2, 4]}]


def test_auto_freq_db_csv_becomes_spectrum():
    result = build_auto_plot("freq,db\n99.1,-80\n99.2,-42\n")
    assert result.chart_type == "spectrum"
    assert result.data == {"freq": [99.1, 99.2], "db": [-80, -42]}


def test_auto_traces_dict_becomes_spectrum():
    result = build_auto_plot('{"traces":[{"freq":[1,2],"db":[-80,-40],"label":"live"}]}')
    assert result.chart_type == "spectrum"
    assert result.data == {"traces": [{"freq": [1, 2], "db": [-80, -40], "label": "live"}]}


def test_auto_time_frequency_bins_csv_becomes_waterfall():
    result = build_auto_plot("time,99.1,99.2\nt0,-80,-70\nt1,-60,-45\n")
    assert result.chart_type == "waterfall"
    assert result.data == {
        "matrix": [[-80, -70], [-60, -45]],
        "freq": ["99.1", "99.2"],
        "time": ["t0", "t1"],
    }


def test_auto_jsonl_string_date_column_uses_index_axis():
    raw = '{"date":"Mon","users":120,"orders":18}\n{"date":"Tue","users":150,"orders":25}\n'
    result = build_auto_plot(raw, input_format="jsonl")
    assert result.chart_type == "line"
    assert result.data == [
        {"label": "users", "x": [0, 1], "y": [120, 150]},
        {"label": "orders", "x": [0, 1], "y": [18, 25]},
    ]


def test_forced_type_normalizes_common_shape():
    result = build_auto_plot("label,value\nA,1\nB,2\n", forced_type="pie")
    assert result.chart_type == "pie"
    assert result.data == {"labels": ["A", "B"], "values": [1, 2]}


def test_ambiguous_input_raises_clear_error():
    with pytest.raises(AutoPlotError, match="could not infer|invalid JSON"):
        build_auto_plot("not chart data")


def _run_plot(args, stdin=""):
    return subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", "plot", *args],
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def test_cli_plot_reads_csv_stdin():
    result = _run_plot(["--no-color", "--width", "40", "--height", "10"], "label,value\nA,1\nB,2\n")
    assert result.returncode == 0, result.stderr
    assert "A" in result.stdout
    assert "B" in result.stdout


def test_cli_plot_as_bar_json():
    result = _run_plot(["--as", "bar", "--json", '{"labels":["A","B"],"values":[1,2]}', "--no-color"])
    assert result.returncode == 0, result.stderr
    assert "A" in result.stdout


def test_cli_plot_bad_input_schema_error():
    result = _run_plot([], "not chart data")
    assert result.returncode == 1
    assert "ERROR:schema:" in result.stderr
