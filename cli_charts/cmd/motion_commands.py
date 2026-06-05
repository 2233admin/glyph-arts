"""Animation, recording, and motion-export command handlers."""

import json
import os
import sys
import tempfile


def dispatch_motion_command(
    args,
    *,
    load_ascii_motion_adapter,
    require_ascii_motion_npx,
    render_ascii_motion_frames,
):
    if args.type == 'animate':
        if not args.art_text:
            print('ERROR:schema: animate needs a chart type '
                  '(line, bar, scatter, sparkline)', file=sys.stderr)
            return 1
        chart_type = args.art_text[0]
        no_color = args.no_color or bool(os.environ.get('NO_COLOR'))
        if args.file:
            with open(args.file) as file_obj:
                raw = file_obj.read().strip()
        elif args.data:
            raw = args.data
        else:
            raw = sys.stdin.read().strip()
        if not raw:
            print('ERROR:schema: Provide --json, --file, or pipe JSON to stdin',
                  file=sys.stderr)
            return 1
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f'ERROR:json: {exc}', file=sys.stderr)
            return 1
        from cli_charts.render.animate_engine import render_animate

        return render_animate(
            chart_type,
            data,
            args.duration,
            args.frames,
            title=args.title,
            width=args.width,
            height=args.height,
            theme=args.theme,
            xlabel=args.xlabel,
            ylabel=args.ylabel,
            xlim=args.xlim,
            ylim=args.ylim,
            xscale=args.xscale,
            yscale=args.yscale,
            orientation=args.orientation,
            no_color=no_color,
            spinner=args.spinner,
        )

    if args.type == 'record':
        if not args.art_text:
            print('ERROR:schema: record needs an output .cast path', file=sys.stderr)
            return 1
        from cli_charts.render.record_engine import record

        return record(args.art_text[0], args.cmd, args.duration)

    if args.type == 'record-replay':
        if not args.art_text:
            print('ERROR:schema: record-replay needs an input .cast path', file=sys.stderr)
            return 1
        from cli_charts.render.record_engine import record_replay

        return record_replay(args.art_text[0], args.output)

    if args.type == 'to-hyperframes':
        if not args.data:
            print('ERROR:schema: to-hyperframes needs --json SERIES_JSON', file=sys.stderr)
            return 1
        if not args.output_dir:
            print('ERROR:schema: to-hyperframes needs --output-dir DIR', file=sys.stderr)
            return 1
        from cli_charts.adapters.hyperframes import to_hyperframes

        no_color = args.no_color or bool(os.environ.get('NO_COLOR'))
        return to_hyperframes(
            args.data,
            args.frames,
            args.duration,
            args.output_dir,
            width=args.width,
            height=args.height,
            title=args.title,
            theme=args.theme,
            no_color=no_color,
        )

    if args.type == 'to-ascii-motion':
        if not args.data and not args.file:
            print('ERROR:schema: to-ascii-motion needs --json SERIES_JSON or --file PATH', file=sys.stderr)
            return 1
        if not args.output_dir:
            print('ERROR:schema: to-ascii-motion needs --output-dir DIR', file=sys.stderr)
            return 1
        adapter = load_ascii_motion_adapter()
        require_ascii_motion_npx()
        if args.file:
            with open(args.file) as file_obj:
                raw = file_obj.read().strip()
        else:
            raw = args.data
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f'ERROR:json: {exc}', file=sys.stderr)
            return 1
        frames = render_ascii_motion_frames(
            args.art_text[0] if args.art_text else 'line',
            data,
            args,
            adapter,
            no_color=args.no_color or bool(os.environ.get('NO_COLOR')),
        )
        formats = [fmt.strip().lower() for fmt in args.formats.split(',') if fmt.strip()]
        project_dir = tempfile.mkdtemp(prefix='glyph-arts-ascii-motion-')
        import asyncio

        asyncio.run(adapter.to_ascii_motion(
            project_dir,
            frames,
            formats,
            args.output_dir,
            int(max(args.duration, 0.1) * 1000 / max(args.frames, 1)),
        ))
        return 0

    return None
