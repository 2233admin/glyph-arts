"""glyph-arts P7b SYMBOL_SETS - generated 2026-05-07 by background agent.

User Q1 (2026-05-07) confirmed: complete coverage of Unicode blocks, not sample.
GEOMETRIC star-5 #1, BLOCK star-5 #2, BRAILLE star-4 #3, ENCLOSED star-4, BOX_STYLES star-3.

Tier model: every named entry exposes 3 tiers
    ascii   -- single ASCII printable (cp437/IBM-OEM-safe, no control codes)
    unicode -- BMP codepoint, renders in any modern terminal w/ DejaVu/Cascadia
    nerd    -- NerdFont PUA codepoint (U+E000-F8FF). None when not verified
              (codex worker should verify against nerdfonts.com cheat-sheet).

Codepoint references (verified against Unicode 15.1 charts):
    Geometric Shapes      U+25A0..U+25FF
    Geometric Shapes Ext  U+1F780..U+1F7FF (omitted, non-BMP)
    Misc Sym & Arrows     U+2B00..U+2BFF (subset)
    Block Elements        U+2580..U+259F (full 32)
    Braille Patterns      U+2800..U+28FF (full 256, programmatic)
    Enclosed Alphanum     U+2460..U+24FF
    Box Drawing           U+2500..U+257F

The file is import-safe: no top-level I/O, no network, no side effects.
"""

from __future__ import annotations

from cli_charts.font_tier import detect_font_tier as _detect_font_tier

# ============================================================================
# GEOMETRIC -- U+25A0..U+25FF + U+2605..U+2606 + U+272F..U+2738 + U+2B00..U+2B59
# 50+ named entries, each tier a single character.
# Nerd codepoints sourced from Font Awesome / Octicons mappings widely
# documented in nerdfonts/nerd-fonts repo. Uncertain entries left as None.
# TODO: verify Nerd Font PUA mappings against the official generated CSS.
# ============================================================================
GEOMETRIC: dict[str, dict[str, str | None]] = {
    # circles
    'circle':              {'ascii': 'o', 'unicode': '●', 'nerd': ''},  # BLACK CIRCLE
    'circle_outline':      {'ascii': 'O', 'unicode': '○', 'nerd': ''},  # WHITE CIRCLE
    'circle_small':        {'ascii': '.', 'unicode': '•', 'nerd': None},      # BULLET
    'circle_dot':          {'ascii': '*', 'unicode': '◉', 'nerd': None},      # FISHEYE
    'circle_medium':       {'ascii': 'o', 'unicode': '⚫', 'nerd': None},      # MEDIUM BLACK CIRCLE
    'circle_medium_o':     {'ascii': 'O', 'unicode': '⚪', 'nerd': None},      # MEDIUM WHITE CIRCLE
    'circle_inverse':      {'ascii': '@', 'unicode': '◙', 'nerd': None},      # INVERSE WHITE CIRCLE
    # half / quarter circles
    'half_circle_left':    {'ascii': '(', 'unicode': '◖', 'nerd': None},      # LEFT HALF BLACK CIRCLE
    'half_circle_right':   {'ascii': ')', 'unicode': '◗', 'nerd': None},      # RIGHT HALF BLACK CIRCLE
    'half_circle_top':     {'ascii': '_', 'unicode': '◓', 'nerd': None},      # CIRCLE WITH UPPER HALF BLACK
    'half_circle_bottom':  {'ascii': '-', 'unicode': '◒', 'nerd': None},      # CIRCLE WITH LOWER HALF BLACK
    'quarter_circle_tl':   {'ascii': '/', 'unicode': '◜', 'nerd': None},      # UPPER LEFT QUADRANT CIRCULAR ARC
    'quarter_circle_tr':   {'ascii': '\\', 'unicode': '◝', 'nerd': None},
    'quarter_circle_br':   {'ascii': '/', 'unicode': '◞', 'nerd': None},
    'quarter_circle_bl':   {'ascii': '\\', 'unicode': '◟', 'nerd': None},
    # squares
    'square':              {'ascii': '#', 'unicode': '■', 'nerd': ''},  # BLACK SQUARE
    'square_outline':      {'ascii': '[', 'unicode': '□', 'nerd': ''},  # WHITE SQUARE
    'square_small':        {'ascii': '.', 'unicode': '▪', 'nerd': None},      # BLACK SMALL SQUARE
    'square_small_o':      {'ascii': '.', 'unicode': '▫', 'nerd': None},
    'square_rounded':      {'ascii': '#', 'unicode': '▢', 'nerd': None},      # WHITE SQUARE WITH ROUNDED CORNERS
    'square_dotted':       {'ascii': ':', 'unicode': '⬚', 'nerd': None},      # DOTTED SQUARE
    'square_check':        {'ascii': 'X', 'unicode': '▣', 'nerd': None},      # WHITE SQUARE CONTAINING BLACK SMALL SQUARE
    'rectangle':           {'ascii': '=', 'unicode': '▬', 'nerd': None},      # BLACK RECTANGLE
    'rectangle_outline':   {'ascii': '-', 'unicode': '▭', 'nerd': None},
    'rectangle_v':         {'ascii': '|', 'unicode': '▮', 'nerd': None},      # BLACK VERTICAL RECTANGLE
    'rectangle_v_outline': {'ascii': '|', 'unicode': '▯', 'nerd': None},
    # triangles
    'triangle_up':         {'ascii': '^', 'unicode': '▲', 'nerd': ''},  # BLACK UP-POINTING TRIANGLE
    'triangle_up_outline': {'ascii': '^', 'unicode': '△', 'nerd': None},
    'triangle_right':      {'ascii': '>', 'unicode': '▶', 'nerd': ''},
    'triangle_right_o':    {'ascii': '>', 'unicode': '▷', 'nerd': None},
    'triangle_down':       {'ascii': 'v', 'unicode': '▼', 'nerd': ''},
    'triangle_down_o':     {'ascii': 'v', 'unicode': '▽', 'nerd': None},
    'triangle_left':       {'ascii': '<', 'unicode': '◀', 'nerd': ''},
    'triangle_left_o':     {'ascii': '<', 'unicode': '◁', 'nerd': None},
    'triangle_small_up':   {'ascii': '^', 'unicode': '▴', 'nerd': None},
    'triangle_small_down': {'ascii': 'v', 'unicode': '▾', 'nerd': None},
    'triangle_small_left': {'ascii': '<', 'unicode': '◂', 'nerd': None},
    'triangle_small_right': {'ascii': '>', 'unicode': '▸', 'nerd': None},
    # diamonds
    'diamond':             {'ascii': '+', 'unicode': '◆', 'nerd': ''},  # BLACK DIAMOND
    'diamond_outline':     {'ascii': '+', 'unicode': '◇', 'nerd': None},      # WHITE DIAMOND
    'diamond_small':       {'ascii': '.', 'unicode': '⬩', 'nerd': None},      # BLACK SMALL DIAMOND
    'diamond_dot':         {'ascii': '*', 'unicode': '◈', 'nerd': None},      # WHITE DIAMOND CONTAINING BLACK SMALL DIAMOND
    'lozenge':             {'ascii': '+', 'unicode': '◊', 'nerd': None},      # LOZENGE
    # stars
    'star':                {'ascii': '*', 'unicode': '★', 'nerd': ''},  # BLACK STAR
    'star_outline':        {'ascii': '*', 'unicode': '☆', 'nerd': ''},  # WHITE STAR
    'star_4':              {'ascii': '+', 'unicode': '✦', 'nerd': None},      # BLACK FOUR POINTED STAR
    'star_4_outline':      {'ascii': '+', 'unicode': '✧', 'nerd': None},
    'star_6':              {'ascii': '*', 'unicode': '✶', 'nerd': None},      # SIX POINTED BLACK STAR
    'star_8':              {'ascii': '*', 'unicode': '✷', 'nerd': None},
    'star_12':             {'ascii': '*', 'unicode': '✹', 'nerd': None},
    'sparkle':             {'ascii': '*', 'unicode': '❇', 'nerd': None},
    # arrows (selected from Misc Sym & Arrows + general arrows)
    'arrow_up':            {'ascii': '^', 'unicode': '↑', 'nerd': ''},
    'arrow_down':          {'ascii': 'v', 'unicode': '↓', 'nerd': ''},
    'arrow_left':          {'ascii': '<', 'unicode': '←', 'nerd': ''},
    'arrow_right':         {'ascii': '>', 'unicode': '→', 'nerd': ''},
    'arrow_up_heavy':      {'ascii': '^', 'unicode': '⬆', 'nerd': None},
    'arrow_down_heavy':    {'ascii': 'v', 'unicode': '⬇', 'nerd': None},
    'arrow_left_heavy':    {'ascii': '<', 'unicode': '⬅', 'nerd': None},
    'arrow_right_heavy':   {'ascii': '>', 'unicode': '➡', 'nerd': None},
    # misc
    'bullet':              {'ascii': '*', 'unicode': '•', 'nerd': None},
    'middle_dot':          {'ascii': '.', 'unicode': '·', 'nerd': None},
    'check':               {'ascii': 'v', 'unicode': '✓', 'nerd': ''},  # CHECK MARK
    'check_heavy':         {'ascii': 'V', 'unicode': '✔', 'nerd': None},
    'cross':               {'ascii': 'x', 'unicode': '✗', 'nerd': ''},
    'cross_heavy':         {'ascii': 'X', 'unicode': '✘', 'nerd': None},
    'heart':               {'ascii': '<', 'unicode': '♥', 'nerd': ''},
    'heart_outline':       {'ascii': '<', 'unicode': '♡', 'nerd': ''},
    'spade':               {'ascii': 's', 'unicode': '♠', 'nerd': None},
    'club':                {'ascii': 'c', 'unicode': '♣', 'nerd': None},
    'pentagon':            {'ascii': 'p', 'unicode': '⬟', 'nerd': None},      # BLACK PENTAGON
    'pentagon_outline':    {'ascii': 'p', 'unicode': '⬠', 'nerd': None},
    'hexagon':             {'ascii': 'h', 'unicode': '⬢', 'nerd': None},      # BLACK HEXAGON
    'hexagon_outline':     {'ascii': 'h', 'unicode': '⬡', 'nerd': None},
    'plus':                {'ascii': '+', 'unicode': '＋', 'nerd': ''},
    'minus':               {'ascii': '-', 'unicode': '−', 'nerd': ''},
    'multiply':            {'ascii': 'x', 'unicode': '×', 'nerd': None},
    'divide':              {'ascii': '/', 'unicode': '÷', 'nerd': None},
    'warning':             {'ascii': '!', 'unicode': '⚠', 'nerd': ''},
    'info':                {'ascii': 'i', 'unicode': 'ℹ', 'nerd': ''},
    'question':            {'ascii': '?', 'unicode': '？', 'nerd': ''},
    'ellipsis':            {'ascii': '.', 'unicode': '…', 'nerd': None},
}

# ============================================================================
# BLOCK -- U+2580..U+259F (full 32 codepoints, every glyph in the block)
# ============================================================================
BLOCK: dict[str, str] = {
    # halves
    'half_top':            '▀',  # U+2580 UPPER HALF BLOCK
    'half_bottom':         '▄',  # U+2584 LOWER HALF BLOCK
    'half_left':           '▌',  # U+258C LEFT HALF BLOCK
    'half_right':          '▐',  # U+2590 RIGHT HALF BLOCK
    # eighth horizontal (lower)
    'eighth_low_1':        '▁',  # U+2581 LOWER ONE EIGHTH BLOCK
    'eighth_low_2':        '▂',  # U+2582 LOWER ONE QUARTER BLOCK
    'eighth_low_3':        '▃',  # U+2583 LOWER THREE EIGHTHS BLOCK
    'eighth_low_4':        '▄',  # alias of half_bottom
    'eighth_low_5':        '▅',  # U+2585 LOWER FIVE EIGHTHS BLOCK
    'eighth_low_6':        '▆',  # U+2586 LOWER THREE QUARTERS BLOCK
    'eighth_low_7':        '▇',  # U+2587 LOWER SEVEN EIGHTHS BLOCK
    'eighth_low_8':        '█',  # U+2588 FULL BLOCK
    # eighth vertical (left)
    'eighth_left_8':       '█',  # alias full
    'eighth_left_7':       '▉',  # U+2589 LEFT SEVEN EIGHTHS BLOCK
    'eighth_left_6':       '▊',  # U+258A LEFT THREE QUARTERS BLOCK
    'eighth_left_5':       '▋',  # U+258B LEFT FIVE EIGHTHS BLOCK
    'eighth_left_4':       '▌',  # alias half_left
    'eighth_left_3':       '▍',  # U+258D LEFT THREE EIGHTHS BLOCK
    'eighth_left_2':       '▎',  # U+258E LEFT ONE QUARTER BLOCK
    'eighth_left_1':       '▏',  # U+258F LEFT ONE EIGHTH BLOCK
    # shaded
    'shade_light':         '░',  # U+2591 LIGHT SHADE
    'shade_medium':        '▒',  # U+2592 MEDIUM SHADE
    'shade_dark':          '▓',  # U+2593 DARK SHADE
    'full':                '█',  # U+2588 FULL BLOCK
    # eighth horizontal (upper)
    'eighth_high_1':       '▔',  # U+2594 UPPER ONE EIGHTH BLOCK
    # right one eighth
    'eighth_right_1':      '▕',  # U+2595 RIGHT ONE EIGHTH BLOCK
    # quadrants
    'quad_bl':             '▖',  # U+2596 QUADRANT LOWER LEFT
    'quad_br':             '▗',  # U+2597 QUADRANT LOWER RIGHT
    'quad_tl':             '▘',  # U+2598 QUADRANT UPPER LEFT
    'quad_tl_bl_br':       '▙',  # U+2599 QUADRANT UPPER LEFT AND LOWER LEFT AND LOWER RIGHT
    'quad_tl_br':          '▚',  # U+259A QUADRANT UPPER LEFT AND LOWER RIGHT
    'quad_tl_tr_bl':       '▛',  # U+259B QUADRANT UPPER LEFT AND UPPER RIGHT AND LOWER LEFT
    'quad_tl_tr_br':       '▜',  # U+259C QUADRANT UPPER LEFT AND UPPER RIGHT AND LOWER RIGHT
    'quad_tr':             '▝',  # U+259D QUADRANT UPPER RIGHT
    'quad_tr_bl':          '▞',  # U+259E QUADRANT UPPER RIGHT AND LOWER LEFT
    'quad_tr_bl_br':       '▟',  # U+259F QUADRANT UPPER RIGHT AND LOWER LEFT AND LOWER RIGHT
    # progress (octagonal block elements -- U+25B0 NOT in 2580..259F but commonly grouped)
    'progress_full':       '▰',  # BLACK PARALLELOGRAM (used in some progress styles)
    'progress_empty':      '▱',
}

# All 32 raw codepoints exposed as a string for direct iteration (e.g. block-art renderers).
BLOCK_ALL = ''.join(chr(0x2580 + i) for i in range(32))

# ============================================================================
# BRAILLE -- U+2800..U+28FF (256 patterns, helper + spinner subset)
# ============================================================================
def braille_dots(bits: int) -> str:
    """Return the Braille pattern char for the 8-bit dot mask.

    Bit layout (Unicode dot numbering):
        bit 0 = dot 1 (top-left)
        bit 1 = dot 2 (mid-left)
        bit 2 = dot 3 (bottom-left)
        bit 3 = dot 4 (top-right)
        bit 4 = dot 5 (mid-right)
        bit 5 = dot 6 (bottom-right)
        bit 6 = dot 7 (low-left)
        bit 7 = dot 8 (low-right)
    """
    if not 0 <= bits <= 255:
        raise ValueError(f"braille_dots bits must be in [0, 255], got {bits}")
    return chr(0x2800 + bits)


# Pre-rendered 256-char string -- index i == braille_dots(i).
BRAILLE_ALL = ''.join(chr(0x2800 + i) for i in range(256))

# Spinner frame sets -- compatible with cli-spinners (sindresorhus) and
# rich.spinner / bubbles tea Dot. Each list is one full animation cycle.
# Verified against cli-spinners JSON names/frame order for dots/dots2.
# TODO: verify the remaining dots3..dots12 frame sets against upstream JSON.
BRAILLE_SPINNERS: dict[str, list[str]] = {
    # cli-spinners "dots" (10 frames, 80ms)
    'dots':    ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
    # cli-spinners "dots2" (8 frames, 80ms)  -- equivalent to bubbles Dot
    'dots2':   ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷'],
    # cli-spinners "dots3"
    'dots3':   ['⠋', '⠙', '⠚', '⠞', '⠖', '⠦', '⠴', '⠲', '⠳', '⠓'],
    # cli-spinners "dots4" (left-right bounce, 8 frames)
    'dots4':   ['⠄', '⠆', '⠇', '⠋', '⠙', '⠸', '⠰', '⠠'],
    # cli-spinners "dots5"
    'dots5':   ['⠋', '⠙', '⠚', '⠒', '⠂', '⠂', '⠒', '⠲', '⠴', '⠦', '⠖', '⠒'],
    # cli-spinners "dots6"
    'dots6':   ['⠁', '⠂', '⠄', '⡀', '⢀', '⠠', '⠐', '⠈', '⠄', '⠂'],
    # cli-spinners "dots7"
    'dots7':   ['⠈', '⠐', '⠠', '⢀', '⡀', '⠄', '⠂', '⠁'],
    # cli-spinners "dots8"
    'dots8':   ['⠁', '⠁', '⠂', '⠄', '⡀', '⢀', '⠠', '⠐', '⠈', '⠄', '⠂', '⠂'],
    # cli-spinners "dots9"
    'dots9':   ['⢹', '⢺', '⢼', '⣸', '⣴', '⣦', '⣇', '⢏'],
    # cli-spinners "dots10"
    'dots10':  ['⢄', '⢂', '⢁', '⡁', '⡈', '⡐', '⡠'],
    # cli-spinners "dots11" (1 dot orbiting)
    'dots11':  ['⠁', '⠂', '⠄', '⢀', '⡀', '⠠', '⠐', '⠈'],
    # cli-spinners "dots12" (2-column complementary)
    'dots12':  ['⢀⠀', '⡀⠀', '⠄⠀', '⠂⠀', '⠁⠀', '⠁⠀'],
}

# ============================================================================
# ENCLOSED -- U+2460..U+24FF (5 categories as ready-made strings)
# ============================================================================
ENCLOSED: dict[str, str] = {
    # U+2460..U+2473 = 1..20, then U+3251..U+325F = 21..35, U+32B1..U+32BF = 36..50
    'circled_digits':
        '①②③④⑤⑥⑦⑧⑨⑩'
        '⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳'
        '㉑㉒㉓㉔㉕㉖㉗㉘㉙㉚'
        '㉛㉜㉝㉞㉟'
        '㊱㊲㊳㊴㊵㊶㊷㊸㊹㊺'
        '㊻㊼㊽㊾㊿',  # 50 entries (1..50)
    # U+2474..U+2487 = (1)..(20)
    'paren_digits':
        '⑴⑵⑶⑷⑸⑹⑺⑻⑼⑽'
        '⑾⑿⒀⒁⒂⒃⒄⒅⒆⒇',
    # U+2488..U+249B = 1.  ..  20.
    'numbered_dot':
        '⒈⒉⒊⒋⒌⒍⒎⒏⒐⒑'
        '⒒⒓⒔⒕⒖⒗⒘⒙⒚⒛',
    # U+24B6..U+24CF = circled A..Z
    'circled_upper':
        'ⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿ'
        'ⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉ'
        'ⓊⓋⓌⓍⓎⓏ',
    # U+24D0..U+24E9 = circled a..z
    'circled_lower':
        'ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙ'
        'ⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣ'
        'ⓤⓥⓦⓧⓨⓩ',
}

# ============================================================================
# BOX_STYLES -- U+2500..U+257F box drawing + ascii fallback
# 9 frame styles. 6 chars each: h (horizontal), v (vertical),
#                                tl, tr, bl, br (corners).
# ============================================================================
BOX_STYLES: dict[str, dict[str, str]] = {
    # U+2500 / U+2502 / U+250C / U+2510 / U+2514 / U+2518
    'single':   {'h': '─', 'v': '│', 'tl': '┌', 'tr': '┐', 'bl': '└', 'br': '┘'},
    # U+2550 / U+2551 / U+2554 / U+2557 / U+255A / U+255D
    'double':   {'h': '═', 'v': '║', 'tl': '╔', 'tr': '╗', 'bl': '╚', 'br': '╝'},
    # U+2500 / U+2502 / U+256D / U+256E / U+2570 / U+256F
    'rounded':  {'h': '─', 'v': '│', 'tl': '╭', 'tr': '╮', 'bl': '╰', 'br': '╯'},
    # U+2501 / U+2503 / U+250F / U+2513 / U+2517 / U+251B
    'heavy':    {'h': '━', 'v': '┃', 'tl': '┏', 'tr': '┓', 'bl': '┗', 'br': '┛'},
    # dotted: U+2508 / U+250A + single corners
    'dotted':   {'h': '┈', 'v': '┊', 'tl': '┌', 'tr': '┐', 'bl': '└', 'br': '┘'},
    # dashed: U+2504 / U+2506 + single corners
    'dashed':   {'h': '┄', 'v': '┆', 'tl': '┌', 'tr': '┐', 'bl': '└', 'br': '┘'},
    # ornate: half-block + double-corner mash; gives a "framed" look
    'ornate':   {'h': '═', 'v': '║', 'tl': '╒', 'tr': '╕', 'bl': '╘', 'br': '╛'},
    # ascii fallback
    'ascii':    {'h': '-',      'v': '|',      'tl': '+',      'tr': '+',      'bl': '+',      'br': '+'},
    # null/none -- spaces, lays out same width without visible borders
    'none':     {'h': ' ',      'v': ' ',      'tl': ' ',      'tr': ' ',      'bl': ' ',      'br': ' '},
}

# ============================================================================
# Public helpers
# ============================================================================

def get_symbol(name: str, tier: str = 'unicode') -> str:
    """Return a single-char symbol for `name` at `tier`.

    name -- key in GEOMETRIC (e.g. 'circle', 'star', 'arrow_up')
    tier -- 'ascii' | 'unicode' | 'unicode-extended' | 'nerd'

    Falls back: nerd -> unicode -> ascii when requested tier is None.
    Raises KeyError for unknown name; ValueError for unknown tier.
    """
    if tier not in ('ascii', 'unicode', 'unicode-extended', 'nerd'):
        raise ValueError(f"tier must be ascii|unicode|unicode-extended|nerd, got {tier!r}")
    if tier == 'unicode-extended':
        tier = 'unicode'
    entry = GEOMETRIC.get(name)
    if entry is None:
        raise KeyError(f"unknown symbol name: {name!r}")
    val = entry.get(tier)
    if val is not None:
        return val
    # graceful degrade
    for fb in ('unicode', 'ascii'):
        if fb == tier:
            continue
        v = entry.get(fb)
        if v is not None:
            return v
    raise KeyError(f"no usable tier for {name!r}")


def get_box(style: str = 'single') -> dict[str, str]:
    """Return the 6-char dict for box-drawing style.

    style -- key in BOX_STYLES; falls back to 'ascii' on unknown.
    """
    return BOX_STYLES.get(style, BOX_STYLES['ascii'])


def get_legend_label(idx: int, style: str = 'numeric') -> str:
    """Return a label string for legend index `idx` (0-based).

    style -- 'numeric'        -> "1", "2", ... (plain digit string)
             'circled'        -> circled digits 1..50 (ENCLOSED['circled_digits'])
             'paren'          -> (1)..(20)
             'numbered_dot'   -> "1.".."20."
             'circled_upper'  -> circled A..Z
             'circled_lower'  -> circled a..z
    Falls back to numeric string when idx exceeds the style's range.
    """
    if style == 'numeric':
        return str(idx + 1)
    table = ENCLOSED.get(style)
    if table is None:
        return str(idx + 1)
    if 0 <= idx < len(table):
        return table[idx]
    return str(idx + 1)


def detect_font_tier() -> str:
    """Auto-detect the safest tier for the current terminal.

    Returns 'ascii' | 'unicode' | 'unicode-extended' | 'nerd'.
    """
    return _detect_font_tier()


# ============================================================================
# Module-level smoke tests (run only when imported as __main__)
# ============================================================================
if __name__ == '__main__':
    # exhaustive structural checks -- no network, no I/O
    assert len(GEOMETRIC) >= 50, f"GEOMETRIC needs >=50 entries, got {len(GEOMETRIC)}"
    assert len(BLOCK) >= 32, f"BLOCK needs >=32 entries, got {len(BLOCK)}"
    assert len(BLOCK_ALL) == 32, f"BLOCK_ALL must be 32 chars, got {len(BLOCK_ALL)}"
    assert len(BRAILLE_ALL) == 256, f"BRAILLE_ALL must be 256 chars, got {len(BRAILLE_ALL)}"
    assert braille_dots(0) == '⠀'
    assert braille_dots(255) == '⣿'
    try:
        braille_dots(256)
    except ValueError:
        pass
    else:
        raise AssertionError("braille_dots(256) should raise ValueError")
    assert len(ENCLOSED) == 5
    assert len(BOX_STYLES) == 9
    for name, entry in GEOMETRIC.items():
        assert 'ascii' in entry and 'unicode' in entry and 'nerd' in entry, name
        assert entry['ascii'] is not None
        assert entry['unicode'] is not None
        assert len(entry['ascii']) == 1, f"{name} ascii must be single char"
        assert len(entry['unicode']) == 1, f"{name} unicode must be single char"
    for style, m in BOX_STYLES.items():
        assert set(m.keys()) == {'h', 'v', 'tl', 'tr', 'bl', 'br'}, style
    print(f"OK: GEOMETRIC={len(GEOMETRIC)} BLOCK={len(BLOCK)} BRAILLE=256 ENCLOSED={len(ENCLOSED)} BOX={len(BOX_STYLES)}")
    print(f"detect_font_tier() -> {detect_font_tier()}")
