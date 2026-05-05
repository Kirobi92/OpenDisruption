#!/usr/bin/env python3
"""Generate PWA icon set for the Kirobi family web app.

Usage:
    python3 infra/scripts/build-pwa-icons.py [--out apps/web/public]

The script writes:
    icon.svg              vector master
    icon-192.png          standard PWA icon
    icon-512.png          standard PWA icon
    icon-192-maskable.png maskable variant (safe area inside)
    icon-512-maskable.png maskable variant
    apple-touch-icon.png  180x180 iOS icon (rounded by iOS itself)
    favicon.ico           16/32/48 multi-size

Only the Python stdlib + Pillow are required. Pillow is the *only*
non-stdlib dependency for this generator and is already used elsewhere
in the stack (api service depends on pillow).
"""
from __future__ import annotations

import argparse
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError as exc:  # pragma: no cover - generator only
    raise SystemExit("Pillow required: pip install pillow") from exc


# Brand colours (mirrors tailwind.config.js `kirobi-*` scale).
BG_TOP = (15, 23, 42)        # slate-900
BG_BOTTOM = (3, 105, 161)    # kirobi-700
ACCENT = (56, 189, 248)      # kirobi-400
WHITE = (240, 249, 255)


SVG_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-label="Kirobi">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#0369a1"/>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="40%" r="55%">
      <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.55"/>
      <stop offset="100%" stop-color="#38bdf8" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="512" height="512" rx="96" fill="url(#bg)"/>
  <circle cx="256" cy="216" r="180" fill="url(#glow)"/>
  <g fill="#f0f9ff" font-family="-apple-system, Segoe UI, Roboto, sans-serif"
     font-weight="700" text-anchor="middle">
    <text x="256" y="312" font-size="260" letter-spacing="-12">K</text>
  </g>
  <circle cx="372" cy="156" r="22" fill="#38bdf8"/>
</svg>
"""


def _draw_base(size: int, *, padding: int = 0) -> Image.Image:
    """Return a square Kirobi icon canvas of the requested *size*.

    *padding* is the inner safe-area padding (used for maskable icons,
    where the launcher may crop the outer 20%).
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded square background with vertical gradient.
    radius = int(size * 0.19)
    bg = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bg_draw = ImageDraw.Draw(bg)
    for y in range(size):
        t = y / max(1, size - 1)
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
        bg_draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

    # Apply rounded mask.
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [(padding, padding), (size - padding, size - padding)],
        radius=max(0, radius - padding),
        fill=255,
    )
    img.paste(bg, (0, 0), mask)

    # Soft accent glow.
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow)
    g_draw.ellipse(
        [
            (size * 0.10, size * 0.05),
            (size * 0.90, size * 0.65),
        ],
        fill=(ACCENT[0], ACCENT[1], ACCENT[2], 90),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(radius=size // 18))
    img = Image.alpha_composite(img, glow)

    # The "K" monogram.
    draw = ImageDraw.Draw(img)
    font = _load_font(int(size * 0.55))
    text = "K"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (size - tw) // 2 - bbox[0]
    ty = (size - th) // 2 - bbox[1] - int(size * 0.02)
    draw.text((tx, ty), text, fill=WHITE, font=font)

    # Accent dot top-right.
    dot_r = int(size * 0.045)
    dot_cx = int(size * 0.73)
    dot_cy = int(size * 0.30)
    draw.ellipse(
        [(dot_cx - dot_r, dot_cy - dot_r), (dot_cx + dot_r, dot_cy + dot_r)],
        fill=ACCENT,
    )
    return img


def _load_font(size: int) -> ImageFont.ImageFont:
    """Load a bold UI font; fall back to PIL's default."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def write_assets(out: Path) -> list[Path]:
    """Write all icon assets to *out* and return the produced paths."""
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    # SVG master.
    svg = out / "icon.svg"
    svg.write_text(SVG_TEMPLATE, encoding="utf-8")
    written.append(svg)

    # PNG raster icons.
    for size in (192, 512):
        png = out / f"icon-{size}.png"
        _draw_base(size).save(png, "PNG", optimize=True)
        written.append(png)

        m_png = out / f"icon-{size}-maskable.png"
        _draw_base(size, padding=int(size * 0.10)).save(m_png, "PNG", optimize=True)
        written.append(m_png)

    # Apple touch icon.
    apple = out / "apple-touch-icon.png"
    _draw_base(180).save(apple, "PNG", optimize=True)
    written.append(apple)

    # favicon.ico (multi-size).
    fav = out / "favicon.ico"
    base = _draw_base(64)
    base.save(fav, sizes=[(16, 16), (32, 32), (48, 48)])
    written.append(fav)

    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default="apps/web/public",
        help="Destination directory (default: apps/web/public)",
    )
    args = parser.parse_args()
    out = Path(args.out)
    paths = write_assets(out)
    for p in paths:
        print(f"  ✓ {p}")
    print(f"\n{len(paths)} asset(s) written to {out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
