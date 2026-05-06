def test_gauge_total_zero_no_zero_division_and_zero_pct():
    from cli_charts.dashboard import render_gauge

    out = render_gauge({"label": "X", "value": 5, "total": 0})

    assert "ZeroDivisionError" not in out
    assert "inf" not in out.lower()
    assert "█" not in out
