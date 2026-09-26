"""Energy drawn from the aether: procedural lightning, plasma streams, mist and sparks converging on an orb.

Everything is generated here, from a seed, and added on top of the ORAC artwork (additive light, then a soft
tone curve), so it never needs an outside image service and the same seed always gives the same picture.
Colours are the ORAC palette: white-hot cores, electric blue (#60a5fa) and violet (#c084fc).
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

CORE = np.array([0.90, 0.93, 1.00])
BLUE = np.array([0.38, 0.65, 0.98])
VIOLET = np.array([0.75, 0.52, 0.99])
DEEP = np.array([0.42, 0.22, 0.78])


def _bolt(p0, p1, rng, rough=0.17, min_len=11.0):
    """Midpoint displacement: each segment's midpoint is pushed sideways by a share of the segment's length."""
    pts = [np.asarray(p0, float), np.asarray(p1, float)]
    while True:
        out, split = [pts[0]], False
        for a, b in zip(pts, pts[1:]):
            d = b - a
            length = float(np.hypot(*d))
            if length > min_len:
                split = True
                normal = np.array([-d[1], d[0]]) / length
                out += [(a + b) / 2 + normal * rng.normal(0, rough * length), b]
            else:
                out.append(b)
        pts = out
        if not split:
            return pts


def _branches(path, rng, depth, bolts, width):
    """Forks off a bolt: shorter, thinner, dimmer, heading off at an angle from the parent's direction."""
    if depth == 0 or len(path) < 8:
        return
    for _ in range(rng.integers(1, 4)):
        i = int(rng.integers(len(path) // 6, len(path) - 2))
        a, ahead = path[i], path[min(len(path) - 1, i + len(path) // 6)]
        heading = math.atan2(*(ahead - a)[::-1]) + rng.choice([-1, 1]) * rng.uniform(0.35, 0.9)
        remaining = float(np.hypot(*(path[-1] - a)))
        reach = remaining * rng.uniform(0.18, 0.45)
        end = a + reach * np.array([math.cos(heading), math.sin(heading)])
        sub = _bolt(a, end, rng, rough=0.2)
        bolts.append((sub, max(1, width - 1), 0.55 ** (4 - depth)))
        _branches(sub, rng, depth - 1, bolts, max(1, width - 1))


def _crosses(path, rects):
    return any(x0 <= x <= x1 and y0 <= y <= y1 for x, y in path for x0, y0, x1, y1 in rects)


def _curve(points, n=400):
    """Catmull-Rom through the control points: the smooth path of a plasma stream."""
    p = [points[0]] + list(points) + [points[-1]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = (np.asarray(v, float) for v in p[i - 1:i + 3])
        for t in np.linspace(0, 1, n // (len(p) - 3), endpoint=False):
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(np.asarray(points[-1], float))
    return out


def _fractal(size, rng, octaves=4, cell=220):
    w, h = size
    acc = np.zeros((h, w))
    for o in range(octaves):
        cw, ch = max(2, w // (cell >> o)), max(2, h // (cell >> o))
        layer = Image.fromarray((rng.random((ch, cw)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += (np.asarray(layer, float) / 255 - 0.5) * (0.55 ** o)
    return acc / np.abs(acc).max()


def _blur(mask: Image.Image, radius: float) -> np.ndarray:
    return np.asarray(mask.filter(ImageFilter.GaussianBlur(radius)), float) / 255


def aether(base: Image.Image, center, radius, *, seed=1, bolts=5, streams=6, sparks=380, avoid=(),
           strength=1.0, violet_only=False) -> Image.Image:
    """`base` with energy arriving from the dark around it and converging on the orb at `center` (radius `radius`).
    `avoid` lists rectangles (x0, y0, x1, y1), such as a title, that no bolt may cross."""
    rng = np.random.default_rng(seed)
    core_c, blue_c = (np.array([0.96, 0.88, 1.0]), np.array([0.66, 0.50, 0.98])) if violet_only else (CORE, BLUE)
    w, h = base.size
    cx, cy = center
    img = np.asarray(base.convert("RGB"), float) / 255
    light = np.zeros_like(img)
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.hypot(xx - cx, yy - cy)

    # 1. Aether haze: soft nebula clouds that gather toward the orb and fade to black far out.
    cloud = np.clip(_fractal((w, h), rng) * 0.5 + 0.5 - 0.45, 0, None) * 1.8
    pull = np.exp(-(dist / (radius * 3.6)) ** 2)
    light += cloud[..., None] * pull[..., None] * (0.16 * VIOLET + 0.06 * blue_c) * strength

    # 2. Currents: wide, soft streams of light flowing in from the far dark to the orb's rim.
    s_mask = Image.new("L", (w, h))
    dm = ImageDraw.Draw(s_mask)
    for _ in range(streams):
        for _try in range(30):
            ang = rng.uniform(0, 2 * math.pi)
            reach = rng.uniform(0.4, 0.75) * h / 2
            start = (cx + math.cos(ang) * reach, cy + math.sin(ang) * reach)
            end_ang = ang + rng.normal(0, 0.35)
            end = (cx + math.cos(end_ang) * radius * 0.98, cy + math.sin(end_ang) * radius * 0.98)
            ctrl = [start]
            for k in (0.33, 0.66):
                mid = (start[0] + (end[0] - start[0]) * k, start[1] + (end[1] - start[1]) * k)
                ctrl.append((mid[0] + rng.normal(0, 70 * (1 - k)), mid[1] + rng.normal(0, 70 * (1 - k))))
            ctrl.append(end)
            path = _curve(ctrl)
            if not _crosses(path, avoid):
                break
        else:
            continue
        pts = [tuple(p) for p in path]
        dm.line(pts, fill=int(255 * rng.uniform(0.4, 0.8)), width=int(rng.integers(12, 22)))
    light += (_blur(s_mask, 22)[..., None] * VIOLET * 0.35 + _blur(s_mask, 48)[..., None] * DEEP * 0.8) * strength

    # 3. Lightning: a few main bolts out of the dark, each forking, all ending on the orb's rim.
    paths, origins = [], []
    for b in range(bolts):
        for _try in range(40):
            ang = rng.uniform(0, 2 * math.pi)
            far = radius + rng.uniform(0.18, 0.42) * h / 2
            start = np.array([cx + math.cos(ang) * far, cy + math.sin(ang) * far])
            start = np.clip(start, [-40, -40], [w + 40, h + 40])
            end_ang = ang + rng.normal(0, 0.25)
            end = np.array([cx + math.cos(end_ang) * radius, cy + math.sin(end_ang) * radius])
            main = _bolt(start, end, rng)
            if not _crosses(main, avoid):
                break
        else:
            continue
        width = 3 if b < 2 else 2
        paths.append((main, width, 1.0 if b < 2 else 0.75))
        origins.append(main[0])  # where the energy condenses out of the aether
        tree: list = []
        _branches(main, rng, 3, tree, width)
        paths += [t for t in tree if not _crosses(t[0], avoid)]
    core, glow = Image.new("L", (w, h)), Image.new("L", (w, h))
    dc, dg = ImageDraw.Draw(core), ImageDraw.Draw(glow)
    for path, width, bright in paths:
        pts = [tuple(p) for p in path]
        dc.line(pts, fill=int(255 * bright), width=width)
        dg.line(pts, fill=int(255 * bright), width=width + 2)
    for x, y in origins:  # a bright point where each bolt condenses, with a halo from the glow layers
        dc.ellipse((x - 3, y - 3, x + 3, y + 3), fill=255)
        dg.ellipse((x - 9, y - 9, x + 9, y + 9), fill=200)
    light += (_blur(core, 0.7)[..., None] * core_c * 1.4 + _blur(glow, 4)[..., None] * blue_c * 1.5
              + _blur(glow, 16)[..., None] * VIOLET * 1.3 + _blur(glow, 48)[..., None] * DEEP * 1.1) * strength

    # 4. Sparks: motes of the aether, thicker near the orb.
    sp = Image.new("L", (w, h))
    ds = ImageDraw.Draw(sp)
    for _ in range(sparks):
        r_ = radius * (1.1 + rng.exponential(2.2))
        a_ = rng.uniform(0, 2 * math.pi)
        x, y = cx + math.cos(a_) * r_, cy + math.sin(a_) * r_
        if 0 <= x < w and 0 <= y < h and not _crosses([(x, y)], avoid):
            s = rng.uniform(0.6, 1.8)
            ds.ellipse((x - s, y - s, x + s, y + s), fill=int(255 * rng.uniform(0.3, 1.0)))
    light += (_blur(sp, 0.8)[..., None] * core_c * 0.9 + _blur(sp, 5)[..., None] * VIOLET * 1.2) * strength

    # 5. Where it all arrives: a soft aura around the orb.
    light += (np.exp(-((dist - radius) / (radius * 0.35)) ** 2) * (dist > radius * 0.8))[..., None] * VIOLET * 0.22 * strength

    out = 1 - (1 - img) * np.exp(-light * 1.25)  # additive light with a soft shoulder: bright, never clipped flat
    return Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))
