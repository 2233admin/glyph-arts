from cli_charts.auto_detect import detect_auto


def test_json_numeric_list_to_sparkline():
    detected = detect_auto("[1, 2, 3]")
    assert detected.chart_type == "sparkline"
    assert detected.data == {"values": [1.0, 2.0, 3.0]}


def test_json_labels_values_to_bar():
    detected = detect_auto('{"labels":["A","B"],"values":[3,7]}')
    assert detected.chart_type == "bar"
    assert detected.data["labels"] == ["A", "B"]


def test_json_points_to_scatter():
    detected = detect_auto('[{"x":1,"y":2}, {"x":3,"y":4}]')
    assert detected.chart_type == "scatter"
    assert detected.data == {"x": [1.0, 3.0], "y": [2.0, 4.0]}


def test_csv_category_value_to_bar():
    detected = detect_auto("name,value\nA,3\nB,7\n")
    assert detected.chart_type == "bar"
    assert detected.data == {"labels": ["A", "B"], "values": [3.0, 7.0]}


def test_csv_time_value_to_line():
    detected = detect_auto("date,value\n2026-01-01,3\n2026-01-02,7\n")
    assert detected.chart_type == "line"
    assert detected.data == [{"label": "value", "x": ["2026-01-01", "2026-01-02"], "y": [3.0, 7.0]}]


def test_generic_csv_to_table():
    detected = detect_auto("left,right\na,b\nc,d\n")
    assert detected.chart_type == "table"
    assert detected.data == {"columns": ["left", "right"], "rows": [["a", "b"], ["c", "d"]]}


def test_prefer_overrides_inference():
    detected = detect_auto("[1, 2, 3]", prefer="bar")
    assert detected.chart_type == "bar"
    assert detected.data == {"labels": [0, 1, 2], "values": [1.0, 2.0, 3.0]}
