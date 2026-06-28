"""Handlers for commands that consume raw text or lightweight JSON input."""

import contextlib
import io
import json
import os
import sys

INLINE_TEXT_TYPES = {'incplot', 'textplot', 'turtle', 'formula', 'formula-pretty', 'math', 'math-pretty'}


def _read_text_input(args, *, inline_text=''):
    if args.file:
        with open(args.file, encoding='utf-8-sig') as file_obj:
            return file_obj.read().strip()
    if args.data is not None:
        return args.data
    if inline_text:
        return inline_text
    if args.art_text:
        return ' '.join(args.art_text)
    return sys.stdin.read().strip()


def dispatch_text_input_command(args, *, commands, diagram_func, mermaid_func, effect_func):
    if args.type in INLINE_TEXT_TYPES:
        raw = _read_text_input(args)
        if not raw:
            print(f'ERROR:schema: {args.type} needs --json TEXT, --file PATH, stdin, or trailing text',
                  file=sys.stderr)
            return 1
        data = raw
        if args.type != 'incplot':
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = raw
        no_color = args.no_color or bool(os.environ.get('NO_COLOR'))
        render_kw = dict(
            xlabel=args.xlabel,
            ylabel=args.ylabel,
            xlim=args.xlim,
            ylim=args.ylim,
            xscale=args.xscale,
            yscale=args.yscale,
            orientation=args.orientation,
            output='',
            no_color=no_color,
            prefer=args.prefer,
        )
        if args.output:
            from cli_charts.render.export_engine import export_to_path

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                commands[args.type](data, args.title, args.width, args.height, args.theme, **render_kw)
            export_to_path(buf.getvalue(), args.output, no_color)
        else:
            commands[args.type](data, args.title, args.width, args.height, args.theme, **render_kw)
        return 0

    if args.type == 'diagram':
        kind = args.diagram_kind or (args.art_text[0] if args.art_text else '')
        inline_text = ' '.join(args.art_text[1:]) if args.art_text and kind == args.art_text[0] else ''
        raw = _read_text_input(args, inline_text=inline_text)
        if not raw:
            print('ERROR:schema: diagram needs --json TEXT, --file PATH, stdin, or trailing text',
                  file=sys.stderr)
            return 1
        data = raw
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            data = parsed
            kind = kind or parsed.get('kind') or parsed.get('type') or ''
        if not kind:
            print('ERROR:schema: diagram needs a kind: math, sequence, tree, table, frame, note, flowchart, graphdag, graphplanar, drawio',
                  file=sys.stderr)
            return 1
        return diagram_func(
            data,
            args.title,
            args.width,
            args.height,
            args.theme,
            output=args.output,
            diagram_kind=kind,
            diagram_engine=args.diagram_engine,
            drawio_fragment=args.drawio_fragment,
            drawio_graph_model=args.drawio_graph_model,
            drawio_validate_only=args.drawio_validate_only,
            statusline=args.statusline,
        ) or 0

    if args.type == 'mermaid':
        raw = _read_text_input(args)
        if not raw:
            print('ERROR:schema: mermaid needs --json TEXT, --file PATH, stdin, or trailing text',
                  file=sys.stderr)
            return 1
        return mermaid_func(
            raw,
            args.title,
            args.width,
            args.height,
            args.theme,
            mermaid_theme=args.mermaid_theme,
            mermaid_ascii=args.mermaid_ascii,
            mermaid_padding_x=args.mermaid_padding_x,
            mermaid_padding_y=args.mermaid_padding_y,
            mermaid_box_padding=args.mermaid_box_padding,
        ) or 0

    if args.type == 'effect':
        kind = args.effect_kind or (args.art_text[0] if args.art_text else '')
        inline_text = ' '.join(args.art_text[1:]) if args.art_text and kind == args.art_text[0] else ''
        raw = ''
        if args.file or args.data is not None or inline_text:
            raw = _read_text_input(args, inline_text=inline_text)
        data = {}
        if raw:
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = {'text': raw}
            if isinstance(parsed, dict):
                data = parsed
            else:
                data = {'values': parsed}
        return effect_func(
            data,
            args.title,
            args.width,
            args.height,
            args.theme,
            output=args.output,
            effect_kind=kind or data.get('kind') or data.get('effect') or 'gallery',
            statusline=args.statusline,
        ) or 0

    return None
