"""Render the dashboard's "orac" wordmark as a PNG for the boot and login splashes.

Matches index.html's .wordmark: Inter Bold, letter-spacing -0.04em, filled with
linear-gradient(90deg, #ff7a2f, #e0508a 55%, #8b5cf6). Plymouth cannot draw
gradient text, so the splashes use this picture instead.

Usage: python3 -I build_wordmark.py OUT.png [FONT_PX]
"""
import sys
from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
STOPS = [(0.0, (0xFF, 0x7A, 0x2F)), (0.55, (0xE0, 0x50, 0x8A)), (1.0, (0x8B, 0x5C, 0xF6))]


def colour_at(t):
    for (t0, c0), (t1, c1) in zip(STOPS, STOPS[1:]):
        if t <= t1:
            f = (t - t0) / (t1 - t0)
            return tuple(round(a + (b - a) * f) for a, b in zip(c0, c1))
    return STOPS[-1][1]


def main(out, px=64):
    ss = 4  # supersample, then shrink for clean edges
    font = ImageFont.truetype(FONT, px * ss)
    track = -0.04 * px * ss
    text = "orac"
    widths = [font.getlength(ch) for ch in text]
    width = int(sum(widths) + track * (len(text) - 1)) + 8 * ss
    height = int(px * ss * 1.4)
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    x = 4 * ss
    for ch, w in zip(text, widths):
        draw.text((x, 0), ch, font=font, fill=255)
        x += w + track
    mask = mask.crop(mask.getbbox())
    grad = Image.new("RGB", mask.size)
    for gx in range(mask.width):
        c = colour_at(gx / max(1, mask.width - 1))
        for gy in range(mask.height):
            grad.putpixel((gx, gy), c)
    img = grad.convert("RGBA")
    img.putalpha(mask)
    img = img.resize((mask.width // ss, mask.height // ss), Image.LANCZOS)
    img.save(out)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 64)
