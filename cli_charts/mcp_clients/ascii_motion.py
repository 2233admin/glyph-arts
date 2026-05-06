import os
from pathlib import Path

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None


CHUNK_SIZE = 10_000


class MissingMcpPackageError(RuntimeError):
    pass


class AsciiMotionClient:
    def __init__(self, project_dir):
        self.project_dir = Path(project_dir)
        self._stdio_cm = None
        self._session_cm = None
        self.session = None

    async def __aenter__(self):
        if ClientSession is None or StdioServerParameters is None or stdio_client is None:
            raise MissingMcpPackageError("mcp package is not installed")
        self.project_dir.mkdir(parents=True, exist_ok=True)
        params = StdioServerParameters(
            command="npx",
            args=["ascii-motion-mcp", "--project-dir", str(self.project_dir)],
            env={**os.environ},
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

    async def call(self, tool, args):
        return await self.session.call_tool(tool, args)

    async def set_cells_batch_chunked(self, cells):
        results = []
        for index in range(0, len(cells), CHUNK_SIZE):
            results.append(await self.call("set_cells_batch", {"cells": cells[index:index + CHUNK_SIZE]}))
        return results

    async def apply_effect(self, effect, **params):
        return await self.call("apply_effect", {"effect": effect, **params})

    async def export(self, format_name, path):
        suffix = format_name.lower()
        if suffix == "html":
            return await self.call("export_html", {"filePath": str(path), "loops": "infinite"})
        if suffix == "react":
            return await self.call("export_react", {"filePath": str(path), "includeAnimation": True})
        if suffix in {"svg", "png", "jpg"}:
            return await self.call("export_image", {"filePath": str(path), "format": suffix})
        if suffix in {"mp4", "webm"}:
            return await self.call("export_video", {"filePath": str(path), "format": suffix})
        if suffix == "gif":
            return await self.call("export_video", {"filePath": str(path), "format": "gif"})
        if suffix == "json":
            return await self.call("export_json", {"filePath": str(path), "pretty": True})
        if suffix == "txt":
            return await self.call("export_text", {"filePath": str(path)})
        raise ValueError(f"unsupported ASCII Motion format: {format_name}")
