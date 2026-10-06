"""Cut a viewer sprite from a full-resolution persona portrait (art/personas/).

The portrait stands on a flat green chroma background (flux7-studio renders it with a little noise).
The background is removed by a flood fill from the borders, over every pixel close to the border's
median colour or clearly green and dark enough to be the cast shadow; the figure is cropped to what
is left and scaled down without smoothing, so its pixels stay hard.

usage: .venv/bin/python tools/sprites.py art/personas/vesper.png --height 144
       (writes hoshi7/web/sprites/vesper.png)
"""
import argparse
from collections import deque
from pathlib import Path
from statistics import median

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


def background(px: list[tuple[int, int, int, int]], w: int, h: int) -> tuple[int, int, int]:
    border = [px[x] for x in range(w)] + [px[(h - 1) * w + x] for x in range(w)]
    border += [px[y * w] for y in range(h)] + [px[y * w + w - 1] for y in range(h)]
    return tuple(int(median(c[i] for c in border)) for i in range(3))


def is_backdrop(c: tuple[int, int, int, int], bg: tuple[int, int, int], tol: int) -> bool:
    r, g, b = c[:3]
    near = abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) <= tol
    # the shadow on the backdrop: the same green, darker
    shade = g > r + 15 and g > b + 15 and g < bg[1] and abs((g - r) - (bg[1] - bg[0])) < 45
    return near or shade


def cut(src: Path, height: int, tol: int) -> Image.Image:
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    px = list(im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata())
    bg = background(px, w, h)
    seen = bytearray(w * h)
    q = deque(i for i in range(w * h) if (i < w or i >= w * (h - 1) or i % w in (0, w - 1)))
    for i in q:
        seen[i] = 1
    while q:
        i = q.popleft()
        if not is_backdrop(px[i], bg, tol):
            continue
        px[i] = (0, 0, 0, 0)
        x, y = i % w, i // w
        for j in ((i - 1) if x else -1, (i + 1) if x < w - 1 else -1, i - w, i + w):
            if 0 <= j < w * h and not seen[j]:
                seen[j] = 1
                q.append(j)
    im.putdata(px)
    im = im.crop(im.getbbox())
    k = height / im.height
    return im.resize((max(1, round(im.width * k)), height), Image.NEAREST)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("portrait", type=Path)
    ap.add_argument("--height", type=int, required=True, help="sprite height in pixels")
    ap.add_argument("--tol", type=int, default=70, help="colour distance to the backdrop still taken as backdrop")
    a = ap.parse_args()
    out = ROOT / "hoshi7" / "web" / "sprites" / a.portrait.name
    cut(a.portrait, a.height, a.tol).save(out)
    print(out)


if __name__ == "__main__":
    main()
