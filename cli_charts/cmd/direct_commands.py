"""Direct command handlers that bypass the generic JSON chart renderer."""

import os
import subprocess
import sys


def dispatch_direct_command(args, calibrate_func=None):
    if args.type == 'live':
        from cli_charts.live_engine import run_live

        source = args.art_text[0] if args.art_text else 'random'
        no_color = args.no_color or bool(os.environ.get('NO_COLOR'))
        return run_live(
            source,
            window=args.window,
            interval=args.interval,
            duration=args.duration,
            title=args.title,
            width=args.width,
            height=args.height,
            theme=args.theme,
            no_color=no_color,
        )

    if args.type == 'code':
        if not args.file:
            print('ERROR:schema: code needs --file PATH', file=sys.stderr)
            return 1
        if not args.lang:
            print('ERROR:schema: code needs --lang LANG', file=sys.stderr)
            return 1
        from cli_charts.render.code_engine import render_code

        no_color = args.no_color or bool(os.environ.get('NO_COLOR'))
        code_theme = 'monokai' if args.theme == 'pro' else args.theme
        return render_code(args.file, args.lang, theme=code_theme, no_color=no_color)

    if args.type == 'status':
        from cli_charts.render.status_engine import render_status

        no_color = args.no_color or bool(os.environ.get('NO_COLOR'))
        return render_status(
            args.kind,
            args.message or args.title or args.kind,
            spinner=args.spinner or 'dots',
            no_color=no_color,
        )

    if args.type == 'dashboard' and args.demo:
        dash_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dashboard.py')
        cmd = [sys.executable, dash_script, '--demo']
        if args.no_interactive:
            cmd.append('--no-interactive')
        result = subprocess.run(cmd)
        return result.returncode

    if args.type == 'art':
        from cli_charts.render.art_engine import list_decors, list_fonts, render_art

        no_color = args.no_color or bool(os.environ.get('NO_COLOR'))
        if args.list_fonts:
            list_fonts()
            return 0
        if args.list_decors:
            list_decors()
            return 0
        return render_art(
            ' '.join(args.art_text),
            args.font,
            args.decor,
            args.frame,
            args.gradient,
            args.theme,
            args.width,
            args.height,
            no_color,
            args.output,
            args.justify,
            args.anim,
        )

    if args.type == 'calibrate':
        if calibrate_func is None:
            raise RuntimeError('calibrate_func is required for TYPE=calibrate')
        calibrate_func(
            {},
            args.title,
            args.width,
            args.height,
            args.theme,
            calibrate_from=args.calibrate_from,
            calibrate_to=args.calibrate_to,
            calibrate_step=args.calibrate_step,
            calibrate_glyph=args.calibrate_glyph,
            terminal=args.terminal,
            recommend=args.recommend,
        )
        return 0

    return None
