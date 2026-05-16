def test_gauge_total_zero_no_zero_division_and_zero_pct():
    from cli_charts.dashboard import render_gauge

    out = render_gauge({"label": "X", "value": 5, "total": 0})

    assert "ZeroDivisionError" not in out
    assert "inf" not in out.lower()
    assert "█" not in out


def test_dashboard_cli_delegates_to_real_dashboard_script():
    import json
    import subprocess
    import sys

    payload = {
        "panels": [
            {
                "type": "gauge",
                "title": "CPU",
                "data": {"label": "CPU", "value": 72, "max": 100},
            }
        ]
    }

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli_charts",
            "dashboard",
            "--json",
            json.dumps(payload),
            "--no-splash",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 0, result.stderr
    assert "CPU" in result.stdout
