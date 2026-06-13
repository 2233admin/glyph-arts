"""Dispatch filesystem media inputs to image/video renderers."""

import os
import sys
import json
from pathlib import Path

from cli_charts.render.media_engine import render_image, render_video

_SUPPORTED_VIDEO_EXT = {".mp4", ".mkv", ".avi", ".mov", ".webm"}


def _validate_video_mode(mode):
    try:
        return int(mode)
    except (TypeError, ValueError):
        print(f"ERROR:schema: invalid video mode: {mode!r}", file=sys.stderr)
        return None


def _build_queue_from_file(path, default_mode, default_pixel):
    if not os.path.exists(path):
        print(f"ERROR:schema: playlist not found: {path}", file=sys.stderr)
        return None
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR:schema: failed to read playlist {path}: {exc}", file=sys.stderr)
        return None
    if not isinstance(raw, list):
        print(f"ERROR:schema: playlist must be a JSON array: {path}", file=sys.stderr)
        return None

    queue = []
    for item in raw:
        if isinstance(item, str):
            entry = item
            mode = default_mode
            pixel = bool(default_pixel)
        elif isinstance(item, dict):
            entry = item.get("video") or item.get("path")
            mode = item.get("mode", default_mode)
            pixel = item.get("pixel", default_pixel)
            if "mode" in item and not isinstance(item["mode"], (int, float, str)):
                print(f"ERROR:schema: playlist entry has invalid mode: {item!r}", file=sys.stderr)
                return None
        else:
            print(f"ERROR:schema: playlist entry invalid: {item!r}", file=sys.stderr)
            return None

        mode = _validate_video_mode(mode)
        if mode is None:
            return None
        if mode == 1 and pixel:
            print("ERROR:schema: --video-pixel requires --video-mode 2-5", file=sys.stderr)
            return None
        if mode not in {1, 2, 3, 4, 5}:
            print(f"ERROR:schema: invalid --video-mode {mode}; use 1-5", file=sys.stderr)
            return None
        if not entry:
            print(f"ERROR:schema: playlist entry missing video path: {item!r}", file=sys.stderr)
            return None
        if not os.path.exists(entry):
            print(f"ERROR:schema: playlist entry file not found: {entry}", file=sys.stderr)
            return None

        queue.append(
            {
                "path": str(entry),
                "mode": mode,
                "pixel": bool(pixel),
            }
        )

    if not queue:
        print(f"ERROR:schema: playlist is empty: {path}", file=sys.stderr)
        return None
    return queue


def _build_queue_from_folder(folder, default_mode, default_pixel):
    if not os.path.isdir(folder):
        print(f"ERROR:schema: folder not found: {folder}", file=sys.stderr)
        return None

    queue = []
    try:
        with os.scandir(folder) as it:
            for entry in it:
                if not entry.is_file():
                    continue
                if Path(entry.name).suffix.lower() not in _SUPPORTED_VIDEO_EXT:
                    continue
                queue.append({"path": entry.path, "mode": default_mode, "pixel": bool(default_pixel)})
    except OSError as exc:
        print(f"ERROR:schema: cannot scan folder {folder}: {exc}", file=sys.stderr)
        return None

    if not queue:
        print(f"ERROR:schema: no supported videos in {folder}", file=sys.stderr)
        return None
    return queue


def _resolve_video_queue(args, path):
    default_mode = int(args.video_mode)
    default_pixel = bool(args.video_pixel)

    if args.video_playlist:
        queue = _build_queue_from_file(args.video_playlist, default_mode, default_pixel)
        if queue is None:
            return None
        return queue

    if args.video_folder:
        queue = _build_queue_from_folder(args.video_folder, default_mode, default_pixel)
        if queue is None:
            return None
        return queue

    if path is None:
        return []
    if not os.path.exists(path):
        print(f"ERROR:schema: video file not found: {path}", file=sys.stderr)
        return None
    mode = _validate_video_mode(default_mode)
    if mode is None or (mode == 1 and default_pixel):
        if mode == 1 and default_pixel:
            print("ERROR:schema: --video-pixel requires --video-mode 2-5", file=sys.stderr)
        return None
    if mode not in {1, 2, 3, 4, 5}:
        print(f"ERROR:schema: invalid --video-mode {mode}; use 1-5", file=sys.stderr)
        return None
    return [{"path": path, "mode": mode, "pixel": bool(default_pixel)}]


def dispatch_media(args) -> int:
    """Render TYPE=image/video and return a process exit code."""
    path = args.file or args.data
    no_color = args.no_color or args.chat or bool(os.environ.get("NO_COLOR"))
    if args.type == "image":
        if not path:
            print(
                "ERROR:schema: image needs a path via --file PATH or --json PATH",
                file=sys.stderr,
            )
            return 1
        if not os.path.exists(path):
            print(f"ERROR:schema: file not found: {path}", file=sys.stderr)
            return 1
        return render_image(
            path,
            args.width,
            args.height,
            symbols=args.symbols or ("ascii" if args.chat else "braille"),
            no_color=no_color,
            output=args.output or None,
            engine=args.media_engine,
            chat=args.chat,
            chafa_format=args.chafa_format,
            chafa_colors=args.chafa_colors,
            chafa_symbols=args.chafa_symbols or None,
            chafa_args=args.chafa_arg,
            mode=args.image_mode,
            trim=not args.no_trim,
            image_style=args.image_style,
            color_mode=args.color_mode,
            custom_color=args.custom_color or None,
            background=args.background,
            ratio=args.ratio,
            dither=args.dither,
            dither_strength=args.dither_strength,
            font_size=args.font_size,
            invert=args.invert,
            random_style=args.image_random,
        )

    queue = _resolve_video_queue(args, path)
    if queue is None:
        return 1
    if not queue:
        print(
            "ERROR:schema: video needs --file PATH, --video-playlist FILE, or --video-folder DIR",
            file=sys.stderr,
        )
        return 1
    if args.output and len(queue) > 1:
        print("ERROR:schema: playlist/folder mode does not support output file export in one call", file=sys.stderr)
        return 1
    if args.video_loop and args.output:
        print("ERROR:schema: --video-loop is not supported with --output", file=sys.stderr)
        return 1

    if args.video_loop:
        try:
            while True:
                for item in queue:
                    rc = render_video(
                        item["path"],
                        args.width,
                        args.height,
                        fps=args.fps,
                        symbols=args.symbols or "",
                        duration=args.duration,
                        max_frames=getattr(args, "max_frames", 0),
                        output=args.output or "",
                        no_color=no_color,
                        chat=args.chat,
                        image_style=getattr(args, "image_style", "classic"),
                        color_mode=getattr(args, "color_mode", "original"),
                        background=getattr(args, "background", "dark"),
                        custom_color=getattr(args, "custom_color", None) or None,
                        dither=getattr(args, "dither", "none"),
                        dither_strength=getattr(args, "dither_strength", 0.8),
                        invert=getattr(args, "invert", False),
                        trim=not getattr(args, "no_trim", True),
                        font_size=getattr(args, "font_size", 14),
                        chafa_format=args.chafa_format,
                        chafa_colors=args.chafa_colors,
                        chafa_symbols=args.chafa_symbols or None,
                        chafa_args=args.chafa_arg,
                        video_mode=item["mode"],
                        pixel_mode=item["pixel"],
                    )
                    if rc != 0:
                        return rc
        except KeyboardInterrupt:
            return 0
        return 0

    for item in queue:
        rc = render_video(
            item["path"],
            args.width,
            args.height,
            fps=args.fps,
            symbols=args.symbols or "",
            duration=args.duration,
            max_frames=getattr(args, "max_frames", 0),
            output=args.output or "",
            no_color=no_color,
            chat=args.chat,
            image_style=getattr(args, "image_style", "classic"),
            color_mode=getattr(args, "color_mode", "original"),
            background=getattr(args, "background", "dark"),
            custom_color=getattr(args, "custom_color", None) or None,
            dither=getattr(args, "dither", "none"),
            dither_strength=getattr(args, "dither_strength", 0.8),
            invert=getattr(args, "invert", False),
            trim=not getattr(args, "no_trim", True),
            font_size=getattr(args, "font_size", 14),
            chafa_format=args.chafa_format,
            chafa_colors=args.chafa_colors,
            chafa_symbols=args.chafa_symbols or None,
            chafa_args=args.chafa_arg,
            video_mode=item["mode"],
            pixel_mode=item["pixel"],
        )
        if rc != 0:
            return rc
    return 0
