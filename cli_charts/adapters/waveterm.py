"""WaveTerm adapter for rich preview blocks."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WaveStatus:
    in_wave: bool
    wsh_path: str
    session: str
    workspace: str
    block: str
    term_program: str

    @property
    def ok(self) -> bool:
        return bool(self.wsh_path)


WAVE_ENV_KEYS = ("WAVETERM", "WAVETERM_SESSIONID", "WAVETERM_WORKSPACEID", "WAVETERM_BLOCKID")
WAVE_FORMAT_EXTENSIONS = {"html": ".html", "txt": ".txt", "ansi": ".ansi"}


def detect_wave() -> WaveStatus:
    term_program = os.environ.get("TERM_PROGRAM", "")
    in_wave = any(os.environ.get(key) for key in WAVE_ENV_KEYS)
    in_wave = in_wave or term_program.lower() in {"waveterm", "wave"}
    return WaveStatus(
        in_wave=in_wave,
        wsh_path=shutil.which("wsh") or shutil.which("wsh.exe") or "",
        session=os.environ.get("WAVETERM_SESSIONID", ""),
        workspace=os.environ.get("WAVETERM_WORKSPACEID", ""),
        block=os.environ.get("WAVETERM_BLOCKID", ""),
        term_program=term_program,
    )


def render_wave_doctor() -> str:
    status = detect_wave()
    lines = ["glyph-arts WaveTerm adapter", ""]
    lines.append(f"{'inside-wave':<13} {'OK' if status.in_wave else 'NO'}")
    lines.append(f"{'wsh':<13} {status.wsh_path or 'MISSING'}")
    lines.append(f"{'session':<13} {status.session or '-'}")
    lines.append(f"{'workspace':<13} {status.workspace or '-'}")
    lines.append(f"{'block':<13} {status.block or '-'}")
    lines.append(f"{'TERM_PROGRAM':<13} {status.term_program or '-'}")
    lines.extend([
        "",
        "Commands:",
        "  glyph-arts wave view --file chart.html",
        "  glyph-arts wave render bar --json '{\"labels\":[\"A\"],\"values\":[3]}'",
    ])
    return "\n".join(lines).rstrip() + "\n"


def build_wsh_view_command(path: str, *, wsh_path: str = "") -> list[str]:
    return [wsh_path or "wsh", "view", str(path)]


def build_chart_export_command(
    chart_type: str,
    chart_args: list[str],
    output: str,
    args,
    *,
    input_file: str = "",
) -> list[str]:
    command = [sys.executable, "-m", "cli_charts.chart", chart_type, *chart_args]
    if input_file:
        command.extend(["--file", input_file])
    elif args.data is not None:
        command.extend(["--json", args.data])
    if args.file:
        command.extend(["--file", args.file])
    if args.title:
        command.extend(["--title", args.title])
    if args.width:
        command.extend(["--width", str(args.width)])
    if args.height:
        command.extend(["--height", str(args.height)])
    if args.theme:
        command.extend(["--theme", args.theme])
    if args.no_color:
        command.append("--no-color")
    command.extend(["--output", output, "--no-splash"])
    return command


def run_wave_command(args) -> int:
    action = args.art_text[0] if args.art_text else "doctor"
    rest = list(args.art_text[1:])
    if action in {"doctor", "status"}:
        print(render_wave_doctor(), end="")
        return 0
    if action in {"view", "open"}:
        path = args.file or args.data or (rest[0] if rest else "")
        if not path:
            print("ERROR:schema: wave view needs --file PATH or a trailing path", file=sys.stderr)
            return 1
        return _view_path(path, dry_run=args.dry_run)
    if action == "render":
        if not rest:
            print("ERROR:schema: wave render needs a chart type, e.g. wave render bar --json ...", file=sys.stderr)
            return 1
        chart_type = rest[0]
        chart_args = rest[1:]
        return _render_and_view(chart_type, chart_args, args)

    print("ERROR:schema: wave supports doctor, view, render", file=sys.stderr)
    return 1


def _view_path(path: str, *, dry_run: bool = False) -> int:
    status = detect_wave()
    command = build_wsh_view_command(path, wsh_path=status.wsh_path)
    if dry_run:
        print(_quote_command(command))
        return 0
    if not status.wsh_path:
        print("ERROR:dep: wsh not found; run inside WaveTerm or install WaveTerm shell integration", file=sys.stderr)
        print(_quote_command(command), file=sys.stderr)
        return 2
    result = subprocess.run(command)
    return result.returncode


def _render_and_view(chart_type: str, chart_args: list[str], args) -> int:
    suffix = WAVE_FORMAT_EXTENSIONS.get(args.wave_format, ".html")
    temp_dir = Path(tempfile.mkdtemp(prefix="glyph-arts-wave-"))
    if args.output:
        output = args.output
    else:
        output = str(temp_dir / f"preview{suffix}")
    input_file = ""
    if args.data is not None and not args.file:
        payload = temp_dir / "payload.txt"
        payload.write_text(args.data, encoding="utf-8")
        input_file = str(payload)
    chart_command = build_chart_export_command(chart_type, chart_args, output, args, input_file=input_file)
    view_command = build_wsh_view_command(output, wsh_path=detect_wave().wsh_path)
    if args.dry_run:
        print("chart: " + _quote_command(chart_command))
        print("view:  " + _quote_command(view_command))
        return 0
    chart_result = subprocess.run(chart_command)
    if chart_result.returncode != 0:
        return chart_result.returncode
    if args.wave_stdout:
        print(Path(output).read_text(encoding="utf-8", errors="replace"))
    return _view_path(output)


def _quote_command(command: list[str]) -> str:
    return " ".join(_quote_part(part) for part in command)


def _quote_part(part: str) -> str:
    shell_sensitive = set('{}[],:;|&<>"\'')
    if not part or any(ch.isspace() or ch in shell_sensitive for ch in part):
        return '"' + part.replace('"', '\\"') + '"'
    return part
