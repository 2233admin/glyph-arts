"""Dispatch filesystem media inputs to image/video renderers."""

import os
import sys

from cli_charts.render.media_engine import render_image, render_video


def dispatch_media(args) -> int:
    """Render TYPE=image/video and return a process exit code."""
    path = args.file or args.data
    if not path:
        print(
            f"ERROR:schema: {args.type} needs a path via --file PATH or --json PATH",
            file=sys.stderr,
        )
        return 1
    if not os.path.exists(path):
        print(f"ERROR:schema: file not found: {path}", file=sys.stderr)
        return 1

    no_color = args.no_color or args.chat or bool(os.environ.get("NO_COLOR"))
    if args.type == "image":
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

    return render_video(
        path,
        args.width,
        args.height,
        fps=args.fps,
        symbols=args.symbols or "braille",
        duration=args.duration,
        no_color=no_color,
        chat=args.chat,
        chafa_format=args.chafa_format,
        chafa_colors=args.chafa_colors,
        chafa_symbols=args.chafa_symbols or None,
        chafa_args=args.chafa_arg,
    )
