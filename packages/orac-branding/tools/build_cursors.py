# Developed with the help of Claude Code (https://claude.com/claude-code)
"""Builds the Orac cursor theme from Breeze's scalable cursors.

The white outline becomes the Orac gradient (orange -> pink -> violet), the
dark body becomes Orac's deep purple, and Breeze's teal/pink accents become
Orac violet/pink. Writes SVG cursors (used on Wayland) and Xcursor bitmaps at
several sizes (used on X11).

Usage: python3 -I build_cursors.py [OUT_DIR]
The package copy lives in root/usr/share/icons/Orac; regenerate it with
  python3 -I tools/build_cursors.py root/usr/share/icons/Orac
Needs ffmpeg built with librsvg, and Breeze's cursors installed.
"""
import json
import os
import re
import shutil
import struct
import subprocess
import sys

SRC = '/usr/share/icons/breeze_cursors'
OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.expanduser(
    '~/.local/share/icons/Orac')
SIZES = [24, 32, 48, 64]

GRADIENT = ('<defs><linearGradient id="orac" x1="0" y1="0" x2="1" y2="1">'
            '<stop offset="0" stop-color="#ff7a2f"/>'
            '<stop offset=".55" stop-color="#e0508a"/>'
            '<stop offset="1" stop-color="#8b5cf6"/></linearGradient></defs>')
COLORS = {'#fff': 'url(#orac)', '#ffffff': 'url(#orac)',
          '#46a7ac': '#8b5cf6', '#d4497f': '#e0508a', '#3daee9': '#8b5cf6'}


def recolor(svg):
  svg = re.sub(r'fill="(#[0-9a-fA-F]{3,6})"',
               lambda m: f'fill="{COLORS.get(m.group(1).lower(), m.group(1))}"', svg)
  # Paths with no fill render black: give them Orac's deep purple body.
  svg = re.sub(r'<path(?![^>]*\bfill=)(?![^>]*\bopacity=)', '<path fill="#140f1f"', svg)
  return re.sub(r'(<svg[^>]*>)', r'\1' + GRADIENT, svg, count=1)


def rasterize(svg_path, px):
  raw = subprocess.run(
      ['ffmpeg', '-v', 'error', '-width', str(px), '-height', str(px),
       '-i', svg_path, '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'],
      check=True, capture_output=True).stdout
  out = bytearray()
  for i in range(0, len(raw), 4):  # RGBA -> premultiplied little-endian ARGB
    r, g, b, a = raw[i:i + 4]
    out += struct.pack('<I', (a << 24) | (r * a // 255 << 16) |
                       (g * a // 255 << 8) | (b * a // 255))
  return bytes(out)


def xcursor(frames):
  """frames: list of (nominal, px, xhot, yhot, delay, argb)."""
  header = struct.pack('<4sIII', b'Xcur', 16, 0x10000, len(frames))
  pos = 16 + 12 * len(frames)
  toc, chunks = b'', b''
  for nominal, px, xhot, yhot, delay, argb in frames:
    toc += struct.pack('<III', 0xfffd0002, nominal, pos)
    chunk = struct.pack('<IIIIIIIII', 36, 0xfffd0002, nominal, 1, px, px,
                        xhot, yhot, delay) + argb
    chunks += chunk
    pos += len(chunk)
  return header + toc + chunks


def main():
  shutil.rmtree(OUT, ignore_errors=True)
  os.makedirs(os.path.join(OUT, 'cursors'))
  os.makedirs(os.path.join(OUT, 'cursors_scalable'))
  scalable = os.path.join(SRC, 'cursors_scalable')
  built = {}
  for name in sorted(os.listdir(scalable)):
    src_dir = os.path.join(scalable, name)
    if os.path.islink(src_dir):
      os.symlink(os.readlink(src_dir), os.path.join(OUT, 'cursors_scalable', name))
      continue
    dst_dir = os.path.join(OUT, 'cursors_scalable', name)
    os.makedirs(dst_dir)
    meta = json.load(open(os.path.join(src_dir, 'metadata.json')))
    shutil.copy(os.path.join(src_dir, 'metadata.json'), dst_dir)
    frames = []
    for entry in meta:
      with open(os.path.join(src_dir, entry['filename']), encoding='utf-8') as f:
        svg = recolor(f.read())
      dst_svg = os.path.join(dst_dir, entry['filename'])
      with open(dst_svg, 'w', encoding='utf-8') as f:
        f.write(svg)
      box = float(re.search(r'width="([\d.]+)"', svg).group(1))
      for size in SIZES:
        px = round(size * box / entry['nominal_size'])
        k = px / box
        frames.append((size, px, round(entry['hotspot_x'] * k),
                       round(entry['hotspot_y'] * k), entry.get('delay', 0),
                       rasterize(dst_svg, px)))
    frames.sort(key=lambda f: f[0])  # Group by nominal size, frames in order.
    with open(os.path.join(OUT, 'cursors', name), 'wb') as f:
      f.write(xcursor(frames))
    built[name] = True

  # Breeze's X11 directory also has alias names (symlinks); mirror them.
  for name in os.listdir(os.path.join(SRC, 'cursors')):
    path = os.path.join(SRC, 'cursors', name)
    dst = os.path.join(OUT, 'cursors', name)
    if os.path.islink(path) and not os.path.lexists(dst):
      os.symlink(os.readlink(path), dst)

  with open(os.path.join(OUT, 'index.theme'), 'w') as f:
    f.write('[Icon Theme]\nName=Orac\nComment=Orac gradient cursors, from Breeze\n')
  print(f'Built {len(built)} cursors into {OUT}')


if __name__ == '__main__':
  main()
