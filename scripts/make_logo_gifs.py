"""Turn the static work-experience logos into 250x250 looping GIFs with a
heartbeat (double-pulse scale) and a diagonal shimmer sweep, matching
public/assets/bulfighter.gif.

    python3 scripts/make_logo_gifs.py

Sources live in scripts/logo-src/, output goes to public/assets/.
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "scripts" / "logo-src"
OUT = ROOT / "public" / "assets"

SIZE = 250            # output size
SS = 2                # supersample factor for smooth sub-pixel scaling
FRAMES = 72           # 72 * 20ms = 1.44s loop (same length as bulfighter.gif)
FRAME_MS = 20         # 50fps

# source file -> output name
LOGOS = {
    "realityai.jpg": "realityai.gif",
    "entain.jpg": "entain.gif",
    "uosalford.jfif": "uosalford.gif",
    "indeed.jfif": "indeed.gif",
    "river.jfif": "river.gif",
    "berry.jfif": "berry.gif",
    "trp.png": "trp.gif",
    "ncuk.png": "ncuk.gif",
    "extracare.png": "extracare.gif",
    "no_company.jfif": "no_company.gif",
}


def gauss(t, centre, width):
    return math.exp(-(((t - centre) / width) ** 2))


def heartbeat_scale(t):
    """Lub-dub: two soft pulses early in the loop, then rest. Never < 1 so a
    full-bleed logo never exposes its edges."""
    return 1.0 + 0.07 * gauss(t, 0.10, 0.055) + 0.05 * gauss(t, 0.27, 0.06)


def smoothstep(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def shimmer_position(t):
    """Band centre along the sweep axis (-0.4 .. 1.4), or None while resting."""
    start, end = 0.38, 0.88
    if not start <= t <= end:
        return None
    return -0.4 + 1.8 * smoothstep((t - start) / (end - start))


def edge_colour(im):
    a = np.asarray(im.convert("RGB"))
    edge = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    return tuple(int(v) for v in np.median(edge, axis=0))


def base_canvas(path):
    """Source logo letterboxed onto a SIZE*SS square, padded with its edge colour."""
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    im = bg.convert("RGB")
    pad = edge_colour(im)
    n = SIZE * SS
    scale = n / max(im.size)
    w, h = round(im.width * scale), round(im.height * scale)
    im = im.resize((w, h), Image.LANCZOS)
    canvas = Image.new("RGB", (n, n), pad)
    canvas.paste(im, ((n - w) // 2, (n - h) // 2))
    return canvas


# Diagonal coordinate field (0..1 across the tile), tilted like the original.
_yy, _xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32) / (SIZE - 1)
_ANGLE = math.radians(20)
_U = _xx * math.cos(_ANGLE) - _yy * math.sin(_ANGLE)
_U = (_U - _U.min()) / (_U.max() - _U.min())


def render_frame(base, t):
    n = base.width
    s = heartbeat_scale(t)
    half = n / s / 2
    box = (n / 2 - half, n / 2 - half, n / 2 + half, n / 2 + half)
    frame = base.resize((SIZE, SIZE), Image.LANCZOS, box=box)

    pos = shimmer_position(t)
    if pos is not None:
        width = 0.16
        m = np.clip(1 - np.abs(_U - pos) / width, 0, 1)
        m = (m * m * (3 - 2 * m)) * 0.8          # soft edges, 80% peak
        a = np.asarray(frame).astype(np.float32)
        a = a + (255 - a) * m[..., None]
        frame = Image.fromarray(a.round().astype(np.uint8))
    return frame


def build(src_name, out_name):
    base = base_canvas(SRC / src_name)
    frames = [render_frame(base, i / FRAMES) for i in range(FRAMES)]

    # One shared palette for the whole loop -> no per-frame colour flicker.
    sheet = Image.new("RGB", (SIZE * 6, SIZE * 2))
    for k, i in enumerate(range(0, FRAMES, FRAMES // 12)):
        sheet.paste(frames[i], ((k % 6) * SIZE, (k // 6) * SIZE))
    palette = sheet.quantize(256, method=Image.MEDIANCUT, dither=Image.Dither.NONE)
    # No dithering: error-diffusion noise would change frame to frame (jitter).
    q = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]

    out = OUT / out_name
    q[0].save(
        out,
        save_all=True,
        append_images=q[1:],
        duration=FRAME_MS,
        loop=0,
        disposal=1,
        optimize=False,
    )
    print(f"{out_name}: {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    for src, out in LOGOS.items():
        build(src, out)
