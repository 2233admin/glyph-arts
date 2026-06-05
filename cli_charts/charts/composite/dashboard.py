"""dashboard chart -- extracted from cli_charts.cmd._helpers (Phase 3a)."""

from cli_charts.registry import register

@register("dashboard")

def dashboard(d, title, w, h, theme, **kw):
    """Delegates to cli_charts/dashboard.py via subprocess (Textual TUI or Rich static)."""
    import json
    import os
    import subprocess
    import sys
    config = dict(d)
    if title:
        config['title'] = title
    dash_script = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'dashboard.py')
    cmd = [sys.executable, dash_script, '--json', json.dumps(config)]
    if not sys.stdout.isatty():
        cmd.append('--no-interactive')
    result = subprocess.run(cmd)
    sys.exit(result.returncode)
