"""Build README preview images from a real pixipix demo run.

Usage: python3 -I make_previews.py <run_dir> <out_dir>
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RUN = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

BG = (24, 24, 27, 255)  # zinc-900, matches the README badge
CHECK_A = (39, 39, 42, 255)  # transparency checker
CHECK_B = (32, 32, 36, 255)
INK = (228, 228, 231, 255)
MUTED = (161, 161, 170, 255)
ACCENT = (244, 114, 182, 255)

FONT_DIRS = [
    Path("/usr/share/fonts/opentype/inter"),
    Path.home() / "Library/Fonts",
    Path("/Library/Fonts"),
]

# Pillow's bundled font does not include the multiplication sign on every version.
MULTIPLY = (
    "\N{MULTIPLICATION SIGN}"
    if any((directory / "Inter-Medium.otf").exists() for directory in FONT_DIRS)
    else "x"
)


def font(name: str, size: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    # Inter if installed; otherwise Pillow's built-in font (Pillow >= 10.1).
    for directory in FONT_DIRS:
        candidate = directory / name
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default(size=size)


def checker(size: tuple[int, int], cell: int) -> Image.Image:
    im = Image.new("RGBA", size, CHECK_A)
    d = ImageDraw.Draw(im)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if (x // cell + y // cell) % 2:
                d.rectangle([x, y, x + cell - 1, y + cell - 1], fill=CHECK_B)
    return im


def on_checker(sprite: Image.Image, cell: int) -> Image.Image:
    base = checker(sprite.size, cell)
    base.alpha_composite(sprite)
    return base


def before_after() -> None:
    name = "pixi-stand-cube"
    source = Image.open(RUN / "extract/frames" / f"{name}.png").convert("RGBA")
    frame = Image.open(RUN / "align/frames" / f"{name}.png").convert("RGBA")

    panel = 320
    src_scaled = source.copy()
    src_scaled.thumbnail((panel - 40, panel - 40), Image.Resampling.NEAREST)
    out_scaled = frame.resize((256, 256), Image.Resampling.NEAREST)

    width, height = 2 * panel + 120, panel + 110
    im = Image.new("RGBA", (width, height), BG)
    d = ImageDraw.Draw(im)

    left = (40, 70)
    right = (width - 40 - panel, 70)
    for origin in (left, right):
        im.alpha_composite(checker((panel, panel), 16), origin)

    im.alpha_composite(
        on_checker(src_scaled, 16),
        (left[0] + (panel - src_scaled.width) // 2, left[1] + (panel - src_scaled.height) // 2),
    )
    im.alpha_composite(
        on_checker(out_scaled, 16), (right[0] + (panel - 256) // 2, right[1] + (panel - 256) // 2)
    )

    title = font("Inter-SemiBold.otf", 22)
    label = font("Inter-Medium.otf", 15)
    d.text((left[0], 28), "Source pose", font=title, fill=INK)
    d.text((right[0], 28), "PixiPix output", font=title, fill=INK)
    d.text(
        (left[0], 70 + panel + 14),
        f"{source.width}{MULTIPLY}{source.height} image px · 4{MULTIPLY}4 fake pixels",
        font=label,
        fill=MUTED,
    )
    d.text(
        (right[0], 70 + panel + 14),
        f"{frame.width}{MULTIPLY}{frame.height} true pixels · shown at 4{MULTIPLY}",
        font=label,
        fill=MUTED,
    )
    arrow_y = 70 + panel // 2
    d.line([(left[0] + panel + 14, arrow_y), (right[0] - 14, arrow_y)], fill=ACCENT, width=3)
    d.polygon(
        [(right[0] - 14, arrow_y), (right[0] - 26, arrow_y - 8), (right[0] - 26, arrow_y + 8)],
        fill=ACCENT,
    )
    im.convert("RGB").save(OUT / "pixi-before-after.png", optimize=True)


def frame_grid() -> None:
    frames = sorted((RUN / "align/frames").glob("*.png"))
    # Keep the README order identical to the configured reading order.
    order = [
        "pixi-stand-cube",
        "pixi-wave-wand",
        "pixi-point-cube",
        "pixi-walk-side",
        "pixi-stand-back",
        "pixi-cast",
        "pixi-fly-cube",
        "pixi-sit",
        "pixi-leap",
        "pixi-read-map",
        "pixi-fly-wand",
        "pixi-hold-cube",
        "pixi-fly",
        "pixi-crawl",
        "pixi-nap",
        "pixi-hide-wall",
        "pixi-confused",
        "pixi-cheer",
        "pixi-heart",
        "pixi-ready",
        "pixi-magnify",
        "pixi-cry",
        "pixi-present-wand",
        "pixi-point",
        "pixi-magic-circle",
        "pixi-cast-back",
        "pixi-read-book",
        "pixi-cookie",
        "pixi-laptop",
        "pixi-sleep",
    ]
    by_name = {p.stem: p for p in frames}
    assert sorted(by_name) == sorted(order), "unexpected frame set"

    cols, scale, gap, pad = 6, 2, 12, 28
    tile = 64 * scale
    rows = (len(order) + cols - 1) // cols
    width = pad * 2 + cols * tile + (cols - 1) * gap
    height = pad * 2 + 34 + rows * tile + (rows - 1) * gap
    im = Image.new("RGBA", (width, height), BG)
    d = ImageDraw.Draw(im)
    d.text(
        (pad, pad - 4),
        f"30 aligned 64{MULTIPLY}64 frames · shared baseline · shown at 2{MULTIPLY}",
        font=font("Inter-Medium.otf", 16),
        fill=MUTED,
    )
    for i, name in enumerate(order):
        sprite = (
            Image.open(by_name[name]).convert("RGBA").resize((tile, tile), Image.Resampling.NEAREST)
        )
        x = pad + (i % cols) * (tile + gap)
        y = pad + 34 + (i // cols) * (tile + gap)
        im.alpha_composite(on_checker(sprite, 8), (x, y))
    im.convert("RGB").save(OUT / "pixi-aligned-frames.png", optimize=True)


before_after()
frame_grid()
print("wrote", sorted(p.name for p in OUT.glob("*.png")))
