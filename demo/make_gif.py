#!/usr/bin/env python3
"""
Generate demo/glyph-arts-demo.gif by rendering glyph-arts output with PIL.
Runs plotext in-process with a fake TTY stdout so ANSI colors are emitted.
"""
import io, re, os, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
FONT_PATH = r"C:\Windows\Fonts\CascadiaMono.ttf"
OUT_GIF = ROOT / "demo" / "glyph-arts-demo.gif"

# ── Catppuccin Mocha palette ──────────────────────────────────────────────────
BG   = (30,  30,  46)    # #1e1e2e  base
FG   = (205, 214, 244)   # #cdd6f4  text
BLUE = (137, 180, 250)   # #89b4fa  prompt/accent
GREEN= (166, 227, 161)   # #a6e3a1
MAUVE= (203, 166, 247)   # #cba6f7

W, H = 1100, 480
FONT_SIZE = 13
PAD_X, PAD_Y = 20, 20
FRAME_HOLD_MS = 2800     # how long each chart stays visible

# ── 256-colour xterm palette ──────────────────────────────────────────────────
def _ansi256(n: int):
    if n < 16:
        _STD = [
            (0,0,0),(128,0,0),(0,128,0),(128,128,0),
            (0,0,128),(128,0,128),(0,128,128),(192,192,192),
            (128,128,128),(255,0,0),(0,255,0),(255,255,0),
            (0,0,255),(255,0,255),(0,255,255),(255,255,255),
        ]
        return _STD[n]
    if n < 232:
        n -= 16
        b = n % 6; n //= 6
        g = n % 6; r = n // 6
        v = lambda x: 0 if x == 0 else 55 + 40*x
        return (v(r), v(g), v(b))
    val = 8 + (n - 232) * 10
    return (val, val, val)

# ── ANSI parser → [(char, fg, bg, bold)] ─────────────────────────────────────
_ANSI = re.compile(r'\x1b\[([^m]*)m|\x1b\[[^A-Za-z]*[A-Za-z]')

def parse_ansi(text: str):
    fg, bg, bold = FG, BG, False
    pos = 0
    for m in _ANSI.finditer(text):
        for ch in text[pos:m.start()]:
            yield ch, fg, bg, bold
        pos = m.end()
        raw = m.group(1)
        if raw is None:           # non-colour escape — skip
            continue
        codes = raw.split(';') if raw else ['0']
        i = 0
        while i < len(codes):
            c = int(codes[i]) if codes[i].isdigit() else 0
            if c == 0:
                fg, bg, bold = FG, BG, False
            elif c == 1:
                bold = True
            elif c in (22, 21):
                bold = False
            elif c == 39:
                fg = FG
            elif c == 49:
                bg = BG
            elif 30 <= c <= 37:
                fg = _ansi256(c - 30)
            elif 40 <= c <= 47:
                bg = _ansi256(c - 40)
            elif 90 <= c <= 97:
                fg = _ansi256(c - 90 + 8)
            elif 100 <= c <= 107:
                bg = _ansi256(c - 100 + 8)
            elif c == 38 and i + 2 < len(codes) and codes[i+1] == '5':
                fg = _ansi256(int(codes[i+2]))
                i += 2
            elif c == 38 and i + 4 < len(codes) and codes[i+1] == '2':
                fg = (int(codes[i+2]), int(codes[i+3]), int(codes[i+4]))
                i += 4
            elif c == 48 and i + 2 < len(codes) and codes[i+1] == '5':
                bg = _ansi256(int(codes[i+2]))
                i += 2
            elif c == 48 and i + 4 < len(codes) and codes[i+1] == '2':
                bg = (int(codes[i+2]), int(codes[i+3]), int(codes[i+4]))
                i += 4
            i += 1
    for ch in text[pos:]:
        yield ch, fg, bg, bold

# ── Render ANSI string → PIL Image ───────────────────────────────────────────
def render_frame(ansi_text: str, command: str) -> Image.Image:
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Prompt line at top
    prompt_text = f"$ {command}"
    draw.text((PAD_X, PAD_Y), prompt_text, font=font, fill=BLUE)
    cw = font.getlength("M")          # char width (monospace approx)
    ch_h = FONT_SIZE + 3              # line height

    x, y = PAD_X, PAD_Y + ch_h + 4

    # Strip leading/trailing blank lines from chart output
    lines = ansi_text.split('\n')
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    ansi_text = '\n'.join(lines)

    # Render character by character
    for ch, fg, bg, bold in parse_ansi(ansi_text):
        if ch == '\n':
            x = PAD_X
            y += ch_h
            if y + ch_h > H - PAD_Y:
                break
            continue
        if ch == '\r':
            x = PAD_X
            continue
        if ch == '\t':
            x += int(cw * 4)
            continue
        # background cell
        if bg != BG:
            draw.rectangle([x, y, x + int(cw) - 1, y + ch_h - 1], fill=bg)
        draw.text((x, y), ch, font=font, fill=fg)
        x += int(cw)
        if x + cw > W - PAD_X:
            x = PAD_X
            y += ch_h
            if y + ch_h > H - PAD_Y:
                break

    return img

# ── Capture plotext output with fake TTY ─────────────────────────────────────
class _FakeTTY(io.StringIO):
    def isatty(self): return True

def capture(fn) -> str:
    buf = _FakeTTY()
    old_stdout = sys.stdout
    # Force terminal width so charts don't auto-detect terminal size
    old_env = os.environ.copy()
    os.environ['COLUMNS'] = '110'
    os.environ['LINES'] = '35'
    sys.stdout = buf
    try:
        fn()
    finally:
        sys.stdout = old_stdout
        os.environ.clear()
        os.environ.update(old_env)
    return buf.getvalue()

# ── Chart definitions ─────────────────────────────────────────────────────────
def _bar() -> str:
    """plotext bar — capture via fake-TTY stdout."""
    import plotext as plt
    def fn():
        plt.clt(); plt.clf()
        plt.bar(["API", "DB", "Cache"], [42, 18, 76])
        plt.title("Latency ms")
        plt.theme("dark")
        plt.plotsize(108, 30)
        plt.show()
    return capture(fn)

def _sparkline() -> str:
    import plotext as plt
    def fn():
        plt.clt(); plt.clf()
        plt.plot([10, 22, 18, 35, 29, 40, 55, 48])
        plt.title("Requests/s")
        plt.theme("dark")
        plt.plotsize(108, 30)
        plt.show()
    return capture(fn)

def _pie() -> str:
    """Rich-based pie — capture via Rich Console(file=StringIO)."""
    from rich.console import Console
    from rich.table import Table
    from rich import box as rich_box
    labels = ["Stocks", "Bonds", "Cash"]
    values = [60, 30, 10]
    total = sum(values)
    bar_w = 36
    colors = ['red', 'green', 'blue', 'yellow', 'magenta', 'cyan']
    tbl = Table(title="Portfolio", box=rich_box.ROUNDED, show_lines=False)
    tbl.add_column('Label', style='bold')
    tbl.add_column('Pct', justify='right')
    tbl.add_column('Distribution', min_width=bar_w)
    tbl.add_column('Value', justify='right')
    for i, (label, val) in enumerate(zip(labels, values)):
        pct = val / total * 100
        filled = round(pct / 100 * bar_w)
        color = colors[i % len(colors)]
        bar = f'[{color}]{"█" * filled}[/{color}]{"░" * (bar_w - filled)}'
        tbl.add_row(str(label), f'{pct:.1f}%', bar, str(val))
    buf = io.StringIO()
    Console(file=buf, force_terminal=True, width=108).print(tbl)
    return buf.getvalue()

SCENES = [
    ("bar --json '{\"labels\":[\"API\",\"DB\",\"Cache\"],\"values\":[42,18,76]}' --title 'Latency ms'", _bar),
    ("sparkline --json '{\"values\":[10,22,18,35,29,40,55,48]}' --title 'Requests/s'", _sparkline),
    ("pie --json '{\"labels\":[\"Stocks\",\"Bonds\",\"Cash\"],\"values\":[60,30,10]}' --title 'Portfolio'", _pie),
]

# ── Build animated GIF ────────────────────────────────────────────────────────
def main():
    sys.path.insert(0, str(ROOT))
    frames, durations = [], []

    for cmd_suffix, fn in SCENES:
        cmd = f"python -m cli_charts.chart {cmd_suffix}"
        print(f"  rendering: {cmd_suffix.split()[0]} ...", flush=True)
        ansi = fn()
        img  = render_frame(ansi, cmd)

        # Slight fade-in: same frame repeated at short interval, then long hold
        frames.append(img)
        durations.append(80)
        frames.append(img)
        durations.append(FRAME_HOLD_MS)

    # Save
    OUT_GIF.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        OUT_GIF,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=False,
    )
    print(f"\nWritten: {OUT_GIF}  ({OUT_GIF.stat().st_size // 1024} KB)")

if __name__ == "__main__":
    main()
