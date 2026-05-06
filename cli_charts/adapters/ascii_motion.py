import pathlib

from cli_charts.mcp_clients.ascii_motion import AsciiMotionClient

DEFAULT_COLOR = "#ffffff"


def text_to_cells(text, color=DEFAULT_COLOR):
    cells = []
    for y, line in enumerate(text.splitlines()):
        for x, char in enumerate(line):
            if char != " ":
                cells.append({"x": x, "y": y, "char": char, "color": color})
    return cells


async def polish_frames(project_dir, frames, style="retro"):
    async with AsciiMotionClient(project_dir) as client:
        for index, cells in enumerate(frames):
            if index:
                await client.call("add_frame", {"duration": 100, "name": f"frame-{index + 1}"})
                await client.call("go_to_frame", {"index": index})
            await client.set_cells_batch_chunked(cells)
        suggestion = await client.call("suggest_palette_for_style", {"style": style})
        palette_id = _result_value(suggestion).get("colorPaletteId", "retro-8bit")
        palette = _result_value(await client.call("get_color_palette", {"paletteId": palette_id}))
        colors = palette.get("colors", ["#00ff00", "#ffffff"])
        await client.apply_effect("remap-colors", targetPalette=colors)
        await client.apply_effect("levels", brightness=8, contrast=12)


async def to_ascii_motion(project_dir, frames, formats, output_dir, duration_ms=100, name="glyph-chart"):
    out = pathlib.Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    async with AsciiMotionClient(project_dir) as client:
        await client.call("new_project", {"name": name, "template": "wide-120x30"})
        for index, cells in enumerate(frames):
            if index:
                await client.call("add_frame", {"duration": duration_ms, "name": f"frame-{index + 1}"})
            await client.call("go_to_frame", {"index": index})
            await client.set_cells_batch_chunked(cells)
            await client.call("set_frame_duration", {"index": index, "duration": duration_ms})
        for format_name in formats:
            await client.export(format_name, out / f"chart.{format_name}")
        await client.call("save_project", {"filePath": str(out / "chart.asciimtn")})


def _result_value(result):
    if isinstance(result, dict):
        return result
    content = getattr(result, "content", None)
    if content and hasattr(content[0], "text"):
        import json

        return json.loads(content[0].text)
    return {}
