import importlib
import os
from pathlib import Path
from typing import Any

ClientSession: Any = None
StdioServerParameters: Any = None
stdio_client: Any = None

try:
    _mcp = importlib.import_module("mcp")
    _stdio = importlib.import_module("mcp.client.stdio")
    ClientSession = _mcp.ClientSession
    StdioServerParameters = _mcp.StdioServerParameters
    stdio_client = _stdio.stdio_client
except ImportError:
    pass


DEFAULT_PACKAGE = "@next-ai-drawio/mcp-server@latest"


class MissingMcpPackageError(RuntimeError):
    pass


class DrawioMcpClient:
    def __init__(self, *, package=DEFAULT_PACKAGE, drawio_base_url=None, port=None):
        self.package = package
        self.drawio_base_url = drawio_base_url
        self.port = port
        self._stdio_cm = None
        self._session_cm = None
        self.session = None

    async def __aenter__(self):
        if ClientSession is None or StdioServerParameters is None or stdio_client is None:
            raise MissingMcpPackageError("mcp package is not installed")
        env = {**os.environ}
        if self.drawio_base_url:
            env["DRAWIO_BASE_URL"] = str(self.drawio_base_url)
        if self.port:
            env["PORT"] = str(self.port)
        params = StdioServerParameters(
            command="npx",
            args=[self.package],
            env=env,
        )
        self._stdio_cm = stdio_client(params)
        read, write = await self._stdio_cm.__aenter__()
        self._session_cm = ClientSession(read, write)
        self.session = await self._session_cm.__aenter__()
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._session_cm is not None:
            await self._session_cm.__aexit__(exc_type, exc, tb)
        if self._stdio_cm is not None:
            await self._stdio_cm.__aexit__(exc_type, exc, tb)
        self.session = None
        return None

    async def initialize(self):
        return await self.session.initialize()

    async def call(self, tool, args=None):
        return await self.session.call_tool(tool, args or {})

    async def start_session(self):
        return await self.call("start_session")

    async def create_new_diagram(self, mxgraph_model):
        return await self.call("create_new_diagram", {"xml": mxgraph_model})

    async def get_diagram(self):
        return await self.call("get_diagram")

    async def export_diagram(self, path, format_name=None):
        args = {"path": str(Path(path))}
        if format_name:
            args["format"] = format_name
        return await self.call("export_diagram", args)
