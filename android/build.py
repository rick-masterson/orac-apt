#!/usr/bin/env python3
"""ORAC theme for Android, built from the desktop package's own files (packages/orac-branding), so the two stay in
sync. No root and no app install needed:

- wallpapers/: portrait 1440x3200 versions of the ORAC wallpapers (Android scales them to any phone), with energy
  drawn from the aether added by aether.py: lightning, currents of light, haze and sparks converging on each orb. On
  Android 12 and later, "wallpaper colors" (Material You) then turns the system accents ORAC purple.
- termux/: the OracVoid terminal colors, the ORAC login banner, and the fastfetch banner, for the Termux app.

    python3 android/build.py        # -> android/dist/orac-android-theme-<version>.zip
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

from PIL import Image, ImageChops

from aether import aether

VERSION = "1.1.0"
HERE = Path(__file__).resolve().parent
PKG = HERE.parent / "packages" / "orac-branding" / "root" / "usr" / "share"
OUT = HERE / "dist"
W, H = 1440, 3200  # 9:20 portrait, QHD+; Android downscales for 1080p phones
TERMUX_HOME = "/data/data/com.termux/files/home"

# name: (source image, crop box in its pixels, feather share (sides, top, bottom), the orb (x, y, radius) in source
# pixels, rectangles in source pixels that the aether's lightning must not cross, seed)
WALLPAPERS = {
    "orac-orb": ("wallpapers/OracOrb/contents/images/1920x1080.png", (260, 0, 1660, 1080), (0.10, 0.06, 0.06),
                 (958, 540, 220), [], 7),
    "orac-minimal": ("wallpapers/OracMinimal/contents/images/3840x2160.png", (880, 0, 2960, 2160), (0.10, 0.05, 0.05),
                     (1920, 1090, 350), [], 11),
    # the centre column: title line, orb and hooded figure; the full-width status bars at the bottom are left out
    "orac-workstation": ("wallpapers/OracWorkstation/contents/images/3840x2160.png", (900, 30, 2940, 1930),
                         (0.10, 0.0, 0.10), (1926, 480, 285),
                         [(1380, 30, 2480, 130), (1760, 920, 2060, 1180), (1640, 1240, 2220, 1930)], 5),
}


def _ramp(length: int, lo: int, hi: int) -> list[int]:
    """0 -> 255 over the first `lo` pixels, 255 in the middle, 255 -> 0 over the last `hi`."""
    out = []
    for i in range(length):
        v = 1.0
        if lo:
            v = min(v, i / lo)
        if hi:
            v = min(v, (length - 1 - i) / hi)
        out.append(round(255 * max(0.0, v)))
    return out


def placement(box: tuple[int, int, int, int]) -> tuple[float, int]:
    """(scale, top offset) that portrait() uses to put the crop on the phone canvas."""
    scale = W / (box[2] - box[0])
    return scale, (H - round((box[3] - box[1]) * scale)) // 2


def to_phone(box, x: float, y: float) -> tuple[float, float]:
    scale, top = placement(box)
    return (x - box[0]) * scale, (y - box[1]) * scale + top


def portrait(src: Path, box: tuple[int, int, int, int], feather: tuple[float, float, float]) -> Image.Image:
    """Crop the centre of a landscape wallpaper, scale it to the phone's width, and set it on black with the cut
    edges faded out, so the join is invisible (every source has a black background)."""
    im = Image.open(src).convert("RGB").crop(box)
    im = im.resize((W, round(im.height * W / im.width)), Image.LANCZOS)
    side, top, bottom = feather
    h_mask = Image.new("L", (W, 1))
    h_mask.putdata(_ramp(W, round(W * side), round(W * side)))
    v_mask = Image.new("L", (1, im.height))
    v_mask.putdata(_ramp(im.height, round(im.height * top), round(im.height * bottom)))
    mask = ImageChops.multiply(h_mask.resize(im.size), v_mask.resize(im.size))
    canvas = Image.new("RGB", (W, H), (0, 0, 0))
    canvas.paste(im, (0, (H - im.height) // 2), mask)
    return canvas


def termux_colors(scheme: Path) -> str:
    """Konsole's OracVoid scheme as Termux colors.properties: Color0-7 -> color0-7, the Intense ones -> color8-15."""
    rgb, section = {}, None
    for line in scheme.read_text().splitlines():
        if m := re.fullmatch(r"\[(\w+)\]", line.strip()):
            section = m.group(1)
        elif line.startswith("Color=") and section:
            rgb[section] = "#%02x%02x%02x" % tuple(int(x) for x in line[6:].split(","))
    lines = [f"# ORAC Void, from the desktop Konsole scheme (orac-android-theme {VERSION})",
             f"background={rgb['Background']}", f"foreground={rgb['Foreground']}", f"cursor={rgb['Color5']}"]
    lines += [f"color{i}={rgb[f'Color{i}']}" for i in range(8)]
    lines += [f"color{i + 8}={rgb[f'Color{i}Intense']}" for i in range(8)]
    return "\n".join(lines) + "\n"


def termux_motd(motd: str) -> str:
    """The desktop login banner, retitled for the phone; the Shadowfetch and apt lines don't apply to Android."""
    keep = [line for line in motd.splitlines() if "Shadowfetch" not in line and "updates:" not in line
            and "Base OS docs" not in line]
    text = "\n".join(keep).replace("ORAC WORKSTATION", "ORAC MOBILE").replace("NEURAL CORE ONLINE", "NEURAL LINK ONLINE")
    return re.sub(r"\n{3,}", "\n\n", text).rstrip() + "\n\n"


def termux_fastfetch(config: str) -> str:
    """The desktop fastfetch banner with Termux's paths, and only the modules that mean something on a phone."""
    config = config.replace("/usr/share/orac/fastfetch/logo.txt", f"{TERMUX_HOME}/.config/fastfetch/orac-logo.txt")
    config = re.sub(r'"modules": \[.*?\]', '"modules": [\n        "title", "separator",\n        "os", "host", '
                    '"kernel", "uptime", "packages", "shell", "terminal",\n        "cpu", "memory", "disk", "battery",'
                    '\n        "break",\n        "colors"\n    ]', config, flags=re.S)
    return re.sub(r"^// .*\n", "", config, flags=re.M).replace("{\n", "// ORAC banner for fastfetch in Termux "
                                                                "(orac-android-theme).\n{\n", 1)


INSTALL = """#!/data/data/com.termux/files/usr/bin/sh
# ORAC theme for Termux: colours, login banner and fastfetch banner. Run it from the unzipped folder:
#   sh install.sh
# Your previous colours and login banner are kept as .bak files.
set -e
here=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$HOME/.termux" "$HOME/.config/fastfetch"
[ -f "$HOME/.termux/colors.properties" ] && cp "$HOME/.termux/colors.properties" "$HOME/.termux/colors.properties.bak"
cp "$here/colors.properties" "$HOME/.termux/colors.properties"
[ -f "$PREFIX/etc/motd" ] && [ ! -f "$PREFIX/etc/motd.bak" ] && cp "$PREFIX/etc/motd" "$PREFIX/etc/motd.bak"
cp "$here/motd" "$PREFIX/etc/motd"
cp "$here/fastfetch/config.jsonc" "$here/fastfetch/orac-logo.txt" "$HOME/.config/fastfetch/"
command -v termux-reload-settings >/dev/null && termux-reload-settings
echo "ORAC theme applied. For the system banner: pkg install fastfetch, then run fastfetch."
"""


def main() -> None:
    OUT.mkdir(exist_ok=True)
    zpath = OUT / f"orac-android-theme-{VERSION}.zip"
    root = f"orac-android-theme-{VERSION}"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for name, (src, box, feather, (ox, oy, orad), avoid, seed) in WALLPAPERS.items():
            png = OUT / f"{name}-{W}x{H}.png"
            scale, _ = placement(box)
            rects = [(*to_phone(box, x0, y0), *to_phone(box, x1, y1)) for x0, y0, x1, y1 in avoid]
            aether(portrait(PKG / src, box, feather), to_phone(box, ox, oy), orad * scale, seed=seed,
                   avoid=rects, violet_only=name != "orac-orb").save(png, optimize=True)  # only the orb art has blue
            z.write(png, f"{root}/wallpapers/{png.name}")
        z.writestr(f"{root}/termux/colors.properties", termux_colors(PKG / "konsole" / "OracVoid.colorscheme"))
        z.writestr(f"{root}/termux/motd", termux_motd((PKG / "orac" / "motd").read_text()))
        z.writestr(f"{root}/termux/fastfetch/config.jsonc", termux_fastfetch((PKG / "orac/fastfetch/config.jsonc").read_text()))
        logo = (PKG / "orac/fastfetch/logo.txt").read_text()
        z.writestr(f"{root}/termux/fastfetch/orac-logo.txt",
                   logo.replace("ORAC WORKSTATION", "ORAC MOBILE").replace("NEURAL CORE ONLINE", "NEURAL LINK ONLINE"))
        info = zipfile.ZipInfo(f"{root}/termux/install.sh")
        info.external_attr = 0o755 << 16
        z.writestr(info, INSTALL)
        z.write(HERE / "README.md", f"{root}/README.md")
    print(zpath)


if __name__ == "__main__":
    main()
