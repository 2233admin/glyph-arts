"""Pre-cutover verification: confirm current CMDS state before touching _helpers.py."""
import sys
print("=== SMOKE #2 (PRE-CUTOVER) ===", flush=True)
try:
    from cli_charts.cmd import bootstrap
    bootstrap()
    from cli_charts.registry import CMDS
    expected = ['bar','hbar','pie','table','tree','gauge','confusion','banner','art_command','diagram','mermaid','plotext','incplot','textplot','turtle','effect','uniplot','hires','radar','plotille_chart']
    missing = [n for n in expected if n not in CMDS]
    non_callable = [n for n in expected if n in CMDS and not callable(CMDS[n])]
    print(f"CMDS count: {len(CMDS)}", flush=True)
    print(f"missing: {missing if missing else 'none'}", flush=True)
    print(f"non_callable: {non_callable if non_callable else 'none'}", flush=True)
except Exception as e:
    print(f"ERR: {type(e).__name__}: {e}", flush=True)
    sys.exit(1)

print("=== SMOKE #1: file count ===", flush=True)
import os
media_dir = r"D:\projects\glyph-arts\cli_charts\charts\media"
files = [f for f in os.listdir(media_dir) if f.endswith('.py') and f != '__init__.py']
print(f"media/ file count: {len(files)}", flush=True)
expected_files = {'bar.py', 'hbar.py', 'pie.py', 'table.py', 'tree.py', 'gauge.py', 'confusion.py', 'banner.py', 'art_command.py', 'diagram.py', 'mermaid.py', 'plotext.py', 'incplot.py', 'textplot.py', 'turtle.py', 'effect.py', 'uniplot.py', 'hires.py', 'radar.py', 'plotille_chart.py'}
print(f"missing files: {expected_files - set(files) if expected_files - set(files) else 'none'}", flush=True)
print(f"extra files: {set(files) - expected_files if set(files) - expected_files else 'none'}", flush=True)

print("=== SMOKE #3: shim import chain ===", flush=True)
try:
    import cli_charts.cmd.bar
    import cli_charts.cmd.hbar
    import cli_charts.cmd.pie
    import cli_charts.cmd.table
    import cli_charts.cmd.tree
    import cli_charts.cmd.gauge
    import cli_charts.cmd.confusion
    import cli_charts.cmd.banner
    import cli_charts.cmd.art
    import cli_charts.cmd.diagram
    import cli_charts.cmd.mermaid
    import cli_charts.cmd.plotext
    import cli_charts.cmd.incplot
    import cli_charts.cmd.textplot
    import cli_charts.cmd.turtle
    import cli_charts.cmd.effect
    import cli_charts.cmd.uniplot
    import cli_charts.cmd.hires
    import cli_charts.cmd.radar
    import cli_charts.cmd.plotille
    print("shim imports: OK (20/20)", flush=True)
except Exception as e:
    print(f"shim ERR: {type(e).__name__}: {e}", flush=True)

print("=== SMOKE #5: line count delta (pre-cutover) ===", flush=True)
import subprocess
result = subprocess.run(
    ['git', '-C', r'D:\projects\glyph-arts', 'show', 'edd9b7b:cli_charts/cmd/_helpers.py'],
    capture_output=True, text=True
)
before = len(result.stdout.splitlines())
import pathlib
after = len(pathlib.Path(r'D:\projects\glyph-arts\cli_charts\cmd\_helpers.py').read_text(encoding='utf-8').splitlines())
print(f"before: {before} | after: {after} | delta: {after - before}", flush=True)
