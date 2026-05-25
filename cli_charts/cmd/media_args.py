"""Argument groups for media renderers."""


IMAGE_STYLES = [
    "classic",
    "braille",
    "block",
    "edge",
    "dot-cross",
    "halftone",
    "particles",
    "retro-art",
    "terminal",
]

IMAGE_MODES = ["auto", "raw", "detail", "edge", "silhouette"]
COLOR_MODES = ["grayscale", "original", "full", "matrix", "amber", "custom"]
BACKGROUNDS = ["dark", "light", "transparent"]
RATIOS = ["original", "16:9", "4:3", "1:1", "3:4", "9:16"]
DITHER_MODES = ["none", "floyd-steinberg", "bayer", "atkinson"]
CHAFA_FORMATS = ["auto", "symbols", "sixels", "sixel", "kitty", "iterm"]
CHAFA_COLOR_MODES = ["auto", "none", "2", "16", "240", "256", "full"]


def add_media_arguments(parser):
    """Attach image/video flags to the top-level parser."""
    parser.add_argument(
        "--media-engine",
        choices=["auto", "chafa", "pillow"],
        default="auto",
        help=(
            "TYPE=image media backend. auto uses chafa when available, "
            "or Pillow for chat-safe text fallback."
        ),
    )
    parser.add_argument(
        "--chafa-format",
        choices=CHAFA_FORMATS,
        default="auto",
        help=(
            "TYPE=image/video chafa output format. auto selects terminal-native "
            "kitty/iterm/sixels when safe, otherwise symbols."
        ),
    )
    parser.add_argument(
        "--chafa-colors",
        choices=CHAFA_COLOR_MODES,
        default="auto",
        help="TYPE=image/video chafa color depth. auto uses full color for symbols.",
    )
    parser.add_argument(
        "--chafa-symbols",
        default="",
        help="TYPE=image/video chafa symbol set override, e.g. braille, block, vhalf, sextant, ascii.",
    )
    parser.add_argument(
        "--chafa-arg",
        action="append",
        default=[],
        help="TYPE=image/video advanced raw chafa argument. Repeat as --chafa-arg=--dither=ordered.",
    )
    parser.add_argument(
        "--image-mode",
        choices=IMAGE_MODES,
        default="auto",
        help=(
            "TYPE=image Pillow rendering mode. auto/detail crop the subject, "
            "boost contrast and edges; raw keeps the old whole-image luminance path."
        ),
    )
    parser.add_argument(
        "--image-style",
        choices=IMAGE_STYLES,
        default="classic",
        help="TYPE=image ASCII art style",
    )
    parser.add_argument(
        "--color-mode",
        choices=COLOR_MODES,
        default="grayscale",
        help="TYPE=image color mode for ANSI/HTML/SVG/PNG output",
    )
    parser.add_argument(
        "--custom-color",
        default="",
        help="TYPE=image custom color as hex or named color when --color-mode custom",
    )
    parser.add_argument(
        "--background",
        choices=BACKGROUNDS,
        default="dark",
        help="TYPE=image export background",
    )
    parser.add_argument(
        "--ratio",
        choices=RATIOS,
        default="original",
        help="TYPE=image center-crop aspect ratio preset",
    )
    parser.add_argument(
        "--dither",
        choices=DITHER_MODES,
        default="none",
        help="TYPE=image dithering algorithm",
    )
    parser.add_argument(
        "--dither-strength",
        type=float,
        default=0.8,
        help="TYPE=image dithering strength 0..1",
    )
    parser.add_argument(
        "--font-size",
        type=int,
        default=14,
        help="TYPE=image font size in HTML/SVG/PNG exports",
    )
    parser.add_argument(
        "--image-random",
        action="store_true",
        help="TYPE=image choose a deterministic random style/color/dither preset",
    )
    parser.add_argument(
        "--invert",
        action="store_true",
        help="TYPE=image invert brightness before character mapping",
    )
    parser.add_argument(
        "--chat",
        action="store_true",
        help="Plain text output optimized for AI chat panes and Markdown code blocks",
    )
    parser.add_argument(
        "--no-trim",
        action="store_true",
        help="TYPE=image disable automatic foreground crop",
    )
