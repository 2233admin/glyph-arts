import asyncio
import importlib
import subprocess

import pytest


class FakeSession:
    def __init__(self, read, write):
        self.calls = []
        self.initialized = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def initialize(self):
        self.initialized = True
        self.calls.append(("initialize", {}))
        return {"serverInfo": {"name": "next-ai-drawio"}}

    async def call_tool(self, tool, args):
        self.calls.append((tool, args))
        return {"content": [{"type": "text", "text": f"{tool}: ok"}]}


class FakeStdioClient:
    def __init__(self, params):
        self.params = params

    async def __aenter__(self):
        return "read", "write"

    async def __aexit__(self, exc_type, exc, tb):
        return None


@pytest.fixture
def fake_drawio_mcp(monkeypatch):
    module = importlib.import_module("cli_charts.mcp_clients.drawio")
    sessions = []
    stdio_clients = []

    class TrackingSession(FakeSession):
        def __init__(self, read, write):
            super().__init__(read, write)
            sessions.append(self)

    class TrackingStdioClient(FakeStdioClient):
        def __init__(self, params):
            super().__init__(params)
            stdio_clients.append(self)

    monkeypatch.setattr(module, "ClientSession", TrackingSession)
    monkeypatch.setattr(module, "stdio_client", TrackingStdioClient)
    monkeypatch.setattr(module, "StdioServerParameters", lambda **kwargs: kwargs)
    return module, sessions, stdio_clients


def run(coro):
    return asyncio.run(coro)


def test_drawio_mcp_client_starts_npx_package(fake_drawio_mcp):
    module, sessions, stdio_clients = fake_drawio_mcp

    async def scenario():
        async with module.DrawioMcpClient(drawio_base_url="http://localhost:8080", port=6010) as client:
            await client.start_session()

    run(scenario())
    assert sessions[0].calls[:2] == [("initialize", {}), ("start_session", {})]
    assert stdio_clients[0].params["command"] == "npx"
    assert stdio_clients[0].params["args"] == ["@next-ai-drawio/mcp-server@latest"]
    assert stdio_clients[0].params["env"]["DRAWIO_BASE_URL"] == "http://localhost:8080"
    assert stdio_clients[0].params["env"]["PORT"] == "6010"


def test_drawio_adapter_pushes_mxgraph_model_and_export(fake_drawio_mcp, tmp_path):
    _module, sessions, _stdio_clients = fake_drawio_mcp
    adapter = importlib.import_module("cli_charts.adapters.drawio")

    result = run(adapter.preview_drawio("A -> B", output=tmp_path / "diagram.drawio"))

    names = [tool for tool, _args in sessions[0].calls]
    assert names == ["initialize", "start_session", "create_new_diagram", "export_diagram"]
    create_args = sessions[0].calls[2][1]
    assert create_args["xml"].startswith("<mxGraphModel")
    assert "<mxfile" not in create_args["xml"]
    assert sessions[0].calls[3][1]["format"] == "drawio"
    assert result["create_new_diagram"] == "create_new_diagram: ok"


def test_to_drawio_missing_mcp_package_clean_error(monkeypatch, capsys):
    chart = importlib.import_module("cli_charts.chart")
    client = importlib.import_module("cli_charts.mcp_clients.drawio")
    monkeypatch.setattr(client, "ClientSession", None)

    with pytest.raises(SystemExit) as exc:
        chart.main(["to-drawio", "--json", "A -> B", "--no-splash"])

    assert exc.value.code == 2
    assert "pip install glyph-arts[drawio-mcp]" in capsys.readouterr().err


def test_to_drawio_npx_not_found_clean_error(monkeypatch, capsys):
    chart = importlib.import_module("cli_charts.chart")
    client = importlib.import_module("cli_charts.mcp_clients.drawio")
    monkeypatch.setattr(client, "ClientSession", object())

    def missing(*args, **kwargs):
        raise FileNotFoundError("npx")

    monkeypatch.setattr(subprocess, "run", missing)

    with pytest.raises(SystemExit) as exc:
        chart.main(["to-drawio", "--json", "A -> B", "--no-splash"])

    assert exc.value.code == 3
    assert "to-drawio requires npx" in capsys.readouterr().err
