import asyncio
import importlib
import subprocess
from pathlib import Path

import pytest


class FakeSession:
    created = 0

    def __init__(self, read, write):
        self.calls = []
        self.initialized = False
        FakeSession.created += 1

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def initialize(self):
        self.initialized = True
        self.calls.append(("initialize", {}))
        return {"serverInfo": {"name": "ascii-motion-mcp"}}

    async def call_tool(self, tool, args):
        self.calls.append((tool, args))
        if tool == "suggest_palette_for_style":
            return {"characterPaletteId": "standard-ascii", "colorPaletteId": "retro-8bit"}
        if tool == "get_color_palette":
            return {"colors": ["#000000", "#00ff00"]}
        return {"ok": True}


class FakeStdioClient:
    def __init__(self, params):
        self.params = params

    async def __aenter__(self):
        return "read", "write"

    async def __aexit__(self, exc_type, exc, tb):
        return None


@pytest.fixture
def fake_mcp(monkeypatch):
    module = importlib.import_module("cli_charts.mcp_clients.ascii_motion")
    FakeSession.created = 0
    sessions = []

    class TrackingSession(FakeSession):
        def __init__(self, read, write):
            super().__init__(read, write)
            sessions.append(self)

    monkeypatch.setattr(module, "ClientSession", TrackingSession)
    monkeypatch.setattr(module, "stdio_client", FakeStdioClient)
    monkeypatch.setattr(module, "StdioServerParameters", lambda **kwargs: kwargs)
    return module, sessions


def run(coro):
    return asyncio.run(coro)


def test_client_initialize_handshake(fake_mcp):
    module, sessions = fake_mcp

    async def scenario():
        async with module.AsciiMotionClient(Path(".")) as client:
            assert client.session.initialized is True

    run(scenario())
    assert sessions[0].calls[0] == ("initialize", {})


def test_set_cells_batch_chunks_at_10k(fake_mcp):
    module, sessions = fake_mcp
    cells = [{"x": i, "y": 0, "char": "#"} for i in range(25_000)]

    async def scenario():
        async with module.AsciiMotionClient(Path(".")) as client:
            await client.set_cells_batch_chunked(cells)

    run(scenario())
    batches = [args["cells"] for tool, args in sessions[0].calls if tool == "set_cells_batch"]
    assert [len(batch) for batch in batches] == [10_000, 10_000, 5_000]


def test_polish_pipeline_calls_suggest_then_remap(fake_mcp):
    module, sessions = fake_mcp
    adapter = importlib.import_module("cli_charts.adapters.ascii_motion")

    run(adapter.polish_frames(Path("."), [[{"x": 0, "y": 0, "char": "A", "color": "#ffffff"}]], style="retro"))

    names = [tool for tool, _args in sessions[0].calls]
    assert names == [
        "initialize",
        "set_cells_batch",
        "suggest_palette_for_style",
        "get_color_palette",
        "apply_effect",
        "apply_effect",
    ]
    assert sessions[0].calls[4][1]["effect"] == "remap-colors"
    assert sessions[0].calls[5][1]["effect"] == "levels"


def test_to_ascii_motion_calls_each_format(fake_mcp):
    _module, sessions = fake_mcp
    adapter = importlib.import_module("cli_charts.adapters.ascii_motion")

    run(adapter.to_ascii_motion(Path("."), [[{"x": 0, "y": 0, "char": "A"}]], ["html", "mp4"], Path(".")))

    names = [tool for tool, _args in sessions[0].calls]
    assert "export_html" in names
    assert "export_video" in names
    assert "export_multi_format" not in names


def test_missing_mcp_package_clean_error(monkeypatch, capsys):
    chart = importlib.import_module("cli_charts.chart")
    real_import = importlib.import_module

    def fake_import(name, package=None):
        if name == "cli_charts.adapters.ascii_motion":
            raise ImportError("No module named 'mcp'")
        return real_import(name, package)

    monkeypatch.setattr(importlib, "import_module", fake_import)

    with pytest.raises(SystemExit) as exc:
        chart.main(["to-ascii-motion", "--json", '[{"label":"x","y":[1]}]', "--output-dir", ".", "--no-splash"])

    assert exc.value.code == 2
    assert "pip install glyph-arts[ai-motion]" in capsys.readouterr().err


def test_npx_not_found_clean_error(monkeypatch, capsys):
    chart = importlib.import_module("cli_charts.chart")
    client = importlib.import_module("cli_charts.mcp_clients.ascii_motion")
    monkeypatch.setattr(client, "ClientSession", object())

    def missing(*args, **kwargs):
        raise FileNotFoundError("npx")

    monkeypatch.setattr(subprocess, "run", missing)

    with pytest.raises(SystemExit) as exc:
        chart.main(["to-ascii-motion", "--json", '[{"label":"x","y":[1]}]', "--output-dir", ".", "--no-splash"])

    assert exc.value.code == 3
    assert "ascii-motion-mcp not found" in capsys.readouterr().err


def test_session_reused_across_calls(fake_mcp):
    _module, _sessions = fake_mcp
    adapter = importlib.import_module("cli_charts.adapters.ascii_motion")

    run(adapter.to_ascii_motion(Path("."), [[{"x": 0, "y": 0, "char": "A"}]], ["html", "svg"], Path(".")))

    assert FakeSession.created == 1
