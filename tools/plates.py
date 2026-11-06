"""Cuts the hero's plates from Ethan's TV wallpaper project into tools/plates/ (run once; the output is committed).

    python tools/plates.py [path-to-xiaomi-tv-revamp]

Each TV plate comes as a painting (<id>.plate.webp, 1920x1080) and a depth cut-out (<id>.fgall.webp: the subject and
everything in front of the clock, on transparency). This crops both to the hero's 2:1 frame, saves the painting as
WebP and the cut-out as WebP with alpha, trimmed to its visible box, and records the offsets in plates.json.
build.py then embeds them, so the build itself never needs the TV project.
"""
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "plates")
DEFAULT_TV = os.path.join(os.path.expanduser("~"), "Vault", "Projects", "xiaomi-tv-revamp")

W, H = 1200, 600          # the hero's frame, in px; the images are embedded at this size

# zoom: the plate's width as a multiple of W; x0, y0: the crop's top-left corner in that scaled plate.
PLATES = [
    dict(id="spa", zoom=1.0, x0=0, y0=40),
    dict(id="nightcity", zoom=1.0, x0=0, y0=40, mask="subj"),   # the car alone: the tree would hide the E
    dict(id="porschelake", zoom=1.0, x0=0, y0=75),
]


def cut(tv, p):
    src = os.path.join(tv, "plates")
    plate = Image.open(os.path.join(src, p["id"] + ".plate.webp")).convert("RGB")
    fg = Image.open(os.path.join(src, "%s.%s.webp" % (p["id"], p.get("mask", "fgall")))).convert("RGBA")
    sw = int(round(W * p["zoom"]))
    sh = int(round(plate.height * sw / plate.width))
    box = (p["x0"], p["y0"], p["x0"] + W, p["y0"] + H)
    plate = plate.resize((sw, sh), Image.LANCZOS).crop(box)
    fg = fg.resize((sw, sh), Image.LANCZOS).crop(box)
    a = fg.split()[3].point(lambda v: 0 if v < 8 else v)
    fg.putalpha(a)
    bb = a.getbbox() or (0, 0, 1, 1)
    fg = fg.crop(bb)
    os.makedirs(OUT, exist_ok=True)
    plate.save(os.path.join(OUT, p["id"] + ".plate.webp"), "WEBP", quality=p.get("q", 74), method=6)
    fg.save(os.path.join(OUT, p["id"] + ".cut.webp"), "WEBP", quality=p.get("qc", 78), method=6, exact=False)
    return dict(id=p["id"], cut=[bb[0], bb[1], bb[2] - bb[0], bb[3] - bb[1]])


def main():
    tv = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TV
    meta = [cut(tv, p) for p in PLATES]
    with open(os.path.join(OUT, "plates.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(meta, fh, indent=1)
    for m in meta:
        a = os.path.getsize(os.path.join(OUT, m["id"] + ".plate.webp"))
        b = os.path.getsize(os.path.join(OUT, m["id"] + ".cut.webp"))
        print("%-12s plate %6.1f KB  cut %6.1f KB  cut box %s" % (m["id"], a / 1024, b / 1024, m["cut"]))


if __name__ == "__main__":
    main()
