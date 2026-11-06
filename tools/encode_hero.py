"""Encodes the captured TV frames (tools/capture_tv.mjs) into the README banner: one animated WebP, looping.

    python tools/encode_hero.py <capture dir> <out.webp> [--width 1280] [--quality 60] [--budget-mb 8.8] [--method 4]

Frames are scaled to --width (Lanczos). The change's frames are softened very slightly before encoding: they are on
screen for about 0.1 s each and in motion, and the softening is what lets the whole rotation fit GitHub's image proxy.
If the file comes out over --budget-mb, the quality steps down by 4 (to 40 at the least) and it is encoded again.
Prints the size, the frame count and the loop length.
"""
import argparse
import io
import json
import os
import sys

from PIL import Image, ImageFilter

BLUR = 0.8   # px at the output width, on the change's frames (each is on screen about 0.4 s, in motion)


def load(cap, width):
    meta = json.load(open(os.path.join(cap, "frames.json"), encoding="utf-8"))
    ims, durs = [], []
    for fr in meta["frames"]:
        im = Image.open(os.path.join(cap, fr["f"])).convert("RGB")
        h = round(im.height * width / im.width)
        im = im.resize((width, h), Image.LANCZOS)
        if fr.get("kind", "change" if fr["ms"] < 1000 else "hold") == "change":   # mid-change frames only: soften
            im = im.filter(ImageFilter.GaussianBlur(BLUR))
        ims.append(im)
        durs.append(max(20, int(round(fr["ms"]))))
    return ims, durs, meta


def encode(ims, durs, q, method):
    buf = io.BytesIO()
    ims[0].save(buf, "WEBP", save_all=True, append_images=ims[1:], duration=durs, loop=0, quality=q, method=method,
                allow_mixed=False, minimize_size=True, kmax=0)
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cap")
    ap.add_argument("out")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--quality", type=int, default=60)
    ap.add_argument("--budget-mb", type=float, default=8.8)
    ap.add_argument("--method", type=int, default=4)   # 6 is ~6x slower for ~4% less
    a = ap.parse_args()
    ims, durs, meta = load(a.cap, a.width)
    q = a.quality
    while True:
        data = encode(ims, durs, q, a.method)
        mb = len(data) / 1e6
        print("quality %d: %.2f MB, %d frames, loop %.1f s" % (q, mb, len(ims), sum(durs) / 1000), flush=True)
        if mb <= a.budget_mb or q - 4 < 40:
            break
        q -= 4
    with open(a.out, "wb") as fh:
        fh.write(data)
    if mb > a.budget_mb:
        print("over budget", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
