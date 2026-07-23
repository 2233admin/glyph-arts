"""Cutover script: delete 20 function bodies from _helpers.py (lines 115-713).

Preserves:
- Line 1-114 (imports + _MARKER_SYMBOLS + blank)
- Line 714+ (stubs, CHART_TYPES_BY_ENGINE, CMDS, helpers, main)
"""
import sys
from pathlib import Path

p = Path(r'D:\projects\glyph-arts\cli_charts\cmd\_helpers.py')
text = p.read_text(encoding='utf-8')
lines = text.splitlines(keepends=True)

# Find anchors
def_idx = None
stub_idx = None
for i, ln in enumerate(lines):
    if ln.startswith('def bar(d, title, w, h, theme, **kw):') and def_idx is None:
        def_idx = i
    if ln.startswith('def animate_command(d, title, w, h, theme, **kw):') and stub_idx is None:
        stub_idx = i
        break

print(f'def bar at line {def_idx + 1}', flush=True)
print(f'def animate_command at line {stub_idx + 1}', flush=True)
assert def_idx is not None, "could not find def bar"
assert stub_idx is not None, "could not find def animate_command"
assert stub_idx > def_idx

# The function block to delete: lines [def_idx .. stub_idx-1] inclusive
# That's 115..713 in 1-indexed (we want to KEEP line 114 blank, and KEEP line 714 stub)
to_delete = lines[def_idx:stub_idx]
print(f'deleting lines {def_idx+1}..{stub_idx} ({len(to_delete)} lines)', flush=True)

# Keep one blank line between _MARKER_SYMBOLS end (line 113 = `}`) and the first stub
# Original file has: line 113 = `}`, line 114 = blank, lines 115-713 = fns+markers
# After delete: line 113 = `}`, line 114 = blank, then directly to stubs
# So I need to ensure the line before def_idx (line 114) is blank, and the line at stub_idx starts with def

pre_line = lines[def_idx - 1]  # should be blank
post_line = lines[stub_idx]    # should be def animate_command
print(f'line before def_idx ({def_idx}): {pre_line!r}', flush=True)
print(f'line at stub_idx ({stub_idx}): {post_line!r}', flush=True)

# Build new file
new_lines = lines[:def_idx] + lines[stub_idx:]
new_text = ''.join(new_lines)
p.write_text(new_text, encoding='utf-8')
print(f'wrote {len(new_text)} bytes', flush=True)
print(f'new file has {len(new_lines)} lines', flush=True)
