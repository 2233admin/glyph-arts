import asyncio
from pathlib import Path

from cli_charts.mcp_clients.drawio import DEFAULT_PACKAGE, DrawioMcpClient
from cli_charts.render.drawio import extract_mxgraph_model


async def preview_drawio(source, output=None, package=DEFAULT_PACKAGE, drawio_base_url=None, port=None, hold_seconds=0):
    """Open a Next AI Draw.io MCP preview and push the current diagram."""
    graph_model = extract_mxgraph_model(source)
    async with DrawioMcpClient(package=package, drawio_base_url=drawio_base_url, port=port) as client:
        start_result = await client.start_session()
        create_result = await client.create_new_diagram(graph_model)
        export_result = None
        if output:
            export_result = await client.export_diagram(Path(output), _format_from_path(output))
        if hold_seconds and hold_seconds > 0:
            await asyncio.sleep(hold_seconds)
        return {
            "start_session": _result_text(start_result),
            "create_new_diagram": _result_text(create_result),
            "export_diagram": _result_text(export_result) if export_result is not None else "",
        }


def _format_from_path(path):
    suffix = Path(path).suffix.lower().lstrip(".")
    return suffix if suffix in {"drawio", "png", "svg"} else None


def _result_text(result):
    if result is None:
        return ""
    if isinstance(result, dict):
        content = result.get("content")
        if content and isinstance(content, list):
            first = content[0]
            if isinstance(first, dict):
                return first.get("text", "")
        return str(result)
    content = getattr(result, "content", None)
    if content and hasattr(content[0], "text"):
        return content[0].text
    return str(result)
