"""Build the viewer's pixel tiles from Kenney's isometric packs (CC0, kenney.nl).

Takes ready-made art and pixelates it: half resolution, a reduced palette, and
a tint toward the rooftop's neon night; the viewer doubles it without smoothing.
The packs are not stored here; download them from kenney.nl and point to them:

usage: .venv/bin/python tools/tiles.py --farm DIR --blocks DIR
       (Isometric Miniature Farm 2.0 and Isometric Blocks)
"""
import argparse
import glob
from pathlib import Path

from PIL import Image, ImageEnhance

OUT = Path(__file__).resolve().parent.parent / "hoshi7" / "web" / "tiles"
TW = 64          # the viewer's tile width; sprites are built at half of it


def find(root: str, name: str) -> Path:
    hits = sorted(glob.glob(f"{root}/**/{name}", recursive=True))
    if not hits:
        raise SystemExit(f"{name} not found under {root}")
    return Path(hits[0])


def pixelate(im: Image.Image, scale: float, colors: int = 24, tint=None, dark: float = 1.0, glow: float = 1.0) -> Image.Image:
    im = im.convert("RGBA")
    w, h = max(1, round(im.width * scale / 2)), max(1, round(im.height * scale / 2))
    im = im.resize((w, h), Image.LANCZOS)
    rgb, alpha = im.convert("RGB"), im.getchannel("A").point(lambda a: 255 if a > 110 else 0)
    if dark != 1.0:
        rgb = ImageEnhance.Brightness(rgb).enhance(dark)
    if tint:
        layer = Image.new("RGB", rgb.size, tint)
        rgb = Image.blend(rgb, layer, 0.35)
    if glow != 1.0:
        rgb = ImageEnhance.Color(rgb).enhance(glow)
    rgb = rgb.quantize(colors=colors, method=Image.Quantize.MEDIANCUT).convert("RGB")
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--farm", required=True)
    ap.add_argument("--blocks", required=True)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    cube = TW / 111          # a block is 111 px wide
    flat = TW / 256          # a farm tile is 256 px wide
    jobs = {
        # ground blocks
        "deck": (a.blocks, "platformerTile_35.png", cube, dict(dark=0.55, tint=(20, 30, 60))),
        "soil": (a.blocks, "platformerTile_09.png", cube, dict(dark=0.7, tint=(40, 20, 10))),
        "water": (a.blocks, "voxelTile_24.png", cube, dict(dark=0.8, tint=(0, 120, 160), glow=1.3)),
        "scrap": (a.blocks, "voxelTile_31.png", cube, dict(dark=0.75, tint=(30, 30, 50))),
        "antenna": (a.blocks, "voxelTile_33.png", cube, dict(dark=0.75, tint=(60, 20, 80))),
        "terminal": (a.blocks, "platformerTile_17.png", cube, dict(dark=0.85, tint=(80, 40, 0))),
        # what lies on the soil
        "tilled": (a.farm, "Isometric/dirtFarmland_E.png", flat, dict(dark=0.8)),
        "watered": (a.farm, "Isometric/dirtFarmland_E.png", flat, dict(dark=0.55, tint=(0, 60, 140))),
        "sprout": (a.farm, "Isometric/cornYoung_E.png", flat, dict(tint=(0, 255, 180), glow=1.4)),
        "young": (a.farm, "Isometric/cornYoungDouble_E.png", flat, dict(tint=(0, 255, 180), glow=1.4)),
        "grown": (a.farm, "Isometric/corn_E.png", flat, dict(tint=(0, 255, 200), glow=1.5)),
        "ripe": (a.farm, "Isometric/cornDouble_E.png", flat, dict(tint=(255, 240, 90), glow=1.8)),
    }
    for name, (root, src, scale, kw) in jobs.items():
        im = pixelate(Image.open(find(root, src)), scale, **kw)
        im.save(OUT / f"{name}.png")
        print(f"{name:9} {src:24} {im.size}")
    (OUT / "CREDITS.md").write_text(
        "Tiles pixelated from Kenney's Isometric Miniature Farm 2.0 and Isometric Blocks\n"
        "(www.kenney.nl), CC0 1.0. Built by tools/tiles.py.\n")


if __name__ == "__main__":
    main()
