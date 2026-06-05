"""Thin command delegates used by the legacy CLI dispatcher."""


def dispatch_tool_command(args, raw_argv):
    if args.type == 'doctor':
        from cli_charts.installers import render_doctor

        print(render_doctor(fix_chat=args.fix_chat), end='')
        return 0

    if args.type == 'install-backends':
        from cli_charts.installers import render_install_plan, run_install_plan

        manager = '' if args.manager == 'auto' else args.manager
        if args.run:
            return run_install_plan(args.target, manager, yes=args.yes)
        print(render_install_plan(args.target, manager), end='')
        return 0

    if args.type == 'fonts':
        from cli_charts.font_downloads import run_fonts_command

        return run_fonts_command(args)

    if args.type == 'chat-health':
        from cli_charts.chat_health import run_chat_health_command

        return run_chat_health_command(args)

    if args.type == 'wave':
        from cli_charts.adapters.waveterm import run_wave_command

        return run_wave_command(args)

    if args.type == 'demo':
        from cli_charts.demo_engine import run_demo

        return run_demo(speed=args.speed, clear=not args.no_clear)

    if args.type == 'gallery':
        from cli_charts.gallery_engine import run_gallery

        return run_gallery(
            output=args.output or None,
            chart=args.chart or None,
            theme=args.theme if '--theme' in raw_argv else None,
        )

    if args.type == 'splash':
        from cli_charts.splash import main as splash_main

        return splash_main(['--no-splash'] if args.no_splash else [])

    return None
