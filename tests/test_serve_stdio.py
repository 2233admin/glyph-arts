import json
import subprocess
import sys


def _serve(*requests: dict) -> list[dict]:
    payload = "".join(json.dumps(request, ensure_ascii=False) + "\n" for request in requests)
    result = subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", "serve", "--stdio"],
        input=payload,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
    )
    assert not result.stderr
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]


def test_serve_stdio_handles_multiple_chart_requests() -> None:
    responses = _serve(
        {
            "argv": [
                "chat",
                "mermaid",
                "--json",
                "graph LR\nA[Start] --> B[Done]",
            ]
        },
        {
            "argv": [
                "bar",
                "--json",
                '{"labels":["A","B"],"values":[3,7]}',
                "--no-color",
            ]
        },
    )

    assert len(responses) == 2
    assert all(response["ok"] for response in responses)
    assert responses[0]["returncode"] == 0
    assert "Start" in responses[0]["stdout"]
    assert "B" in responses[1]["stdout"]
    assert all(response["duration_ms"] >= 0 for response in responses)


def test_serve_stdio_passes_request_stdin() -> None:
    responses = _serve({"argv": ["auto", "--no-color"], "stdin": "[1,2,3]"})

    assert responses[0]["ok"] is True
    assert responses[0]["stdout"].strip()


def test_serve_stdio_accepts_utf8_bom_prefix() -> None:
    payload = "\ufeff" + json.dumps({"argv": ["auto", "--no-color"], "stdin": "[1,2,3]"}) + "\n"
    result = subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", "serve", "--stdio"],
        input=payload,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
    )
    response = json.loads(result.stdout)

    assert response["ok"] is True
    assert response["stdout"].strip()


def test_serve_stdio_reports_invalid_requests() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", "serve", "--stdio"],
        input='{"argv":"bar"}\n',
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
    )
    response = json.loads(result.stdout)

    assert response["ok"] is False
    assert response["returncode"] == 2
    assert "request.argv" in response["stderr"]
