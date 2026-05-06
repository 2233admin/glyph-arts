import pytest


def test_rich_live_panel_failure_exits_4(monkeypatch):
    from cli_charts import chart

    def broken_panel(*args, **kwargs):
        raise RuntimeError("broken panel")

    monkeypatch.setitem(chart.CMDS, "broken_panel", broken_panel)

    payload = {
        "panels": [
            {"type": "broken_panel", "title": "Broken", "data": {}},
        ],
    }
    with pytest.raises(SystemExit) as exc:
        chart.rich_live(payload, "", 80, 24, "default")

    assert exc.value.code == 4
