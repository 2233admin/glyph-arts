"""Newline-delimited JSON stdio worker for repeated chart renders."""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import time
from collections.abc import Callable
from typing import TextIO


def _error(message: str, *, returncode: int = 2, duration_ms: float = 0.0) -> dict:
    return {
        "ok": False,
        "returncode": returncode,
        "stdout": "",
        "stderr": f"ERROR:serve: {message}\n",
        "duration_ms": round(duration_ms, 3),
    }


def _coerce_request(line: str) -> tuple[list[str], str] | dict:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError as exc:
        return _error(f"invalid JSON: {exc}")
    if not isinstance(payload, dict):
        return _error("request must be a JSON object")

    argv = payload.get("argv")
    if not isinstance(argv, list) or not all(isinstance(item, str) for item in argv):
        return _error("request.argv must be a list of strings")
    if argv and argv[0] == "serve":
        return _error("nested serve requests are not supported")

    stdin_text = payload.get("stdin", "")
    if stdin_text is None:
        stdin_text = ""
    if not isinstance(stdin_text, str):
        return _error("request.stdin must be a string when provided")
    return argv, stdin_text


def _run_request(runner: Callable[[list[str]], object], argv: list[str], stdin_text: str) -> dict:
    stdout = io.StringIO()
    stderr = io.StringIO()
    old_stdin = sys.stdin
    old_no_splash = os.environ.get("GLYPH_ARTS_NO_SPLASH")
    start = time.perf_counter()
    returncode = 0
    try:
        sys.stdin = io.StringIO(stdin_text)
        os.environ["GLYPH_ARTS_NO_SPLASH"] = "1"
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                runner(argv)
            except SystemExit as exc:
                if exc.code is None:
                    returncode = 0
                elif isinstance(exc.code, int):
                    returncode = exc.code
                else:
                    print(exc.code, file=sys.stderr)
                    returncode = 1
            except Exception:
                import traceback

                traceback.print_exc(file=sys.stderr)
                returncode = 4
    finally:
        sys.stdin = old_stdin
        if old_no_splash is None:
            os.environ.pop("GLYPH_ARTS_NO_SPLASH", None)
        else:
            os.environ["GLYPH_ARTS_NO_SPLASH"] = old_no_splash

    duration_ms = (time.perf_counter() - start) * 1000
    return {
        "ok": returncode == 0,
        "returncode": returncode,
        "stdout": stdout.getvalue(),
        "stderr": stderr.getvalue(),
        "duration_ms": round(duration_ms, 3),
    }


def run_stdio_server(
    runner: Callable[[list[str]], object],
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
) -> int:
    input_stream = input_stream or sys.stdin
    output_stream = output_stream or sys.stdout
    for line in input_stream:
        line = line.strip().lstrip("\ufeff")
        if not line:
            continue
        request = _coerce_request(line)
        if isinstance(request, dict):
            response = request
        else:
            argv, stdin_text = request
            response = _run_request(runner, argv, stdin_text)
        print(json.dumps(response, ensure_ascii=False), file=output_stream, flush=True)
    return 0
