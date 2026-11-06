"""Copies the hero's plates from Ethan's TV wallpaper project into tools/plates/ (run once per plate change; the output
is committed, so the build never needs the TV project).

    python tools/plates.py [path-to-xiaomi-tv-revamp]

The hero is his TV home screen, so it shows every plate he approved in DesignConfigurator (hub/state/config.json,
status "keep"), each with the depth he chose:
  all  -> <id>.fgall.webp (the subject and the ground in front of the clock)
  on   -> <id>.fg.webp    (the scene's foreground)
  subj -> <id>.subj.webp  (the subject alone)
  off  -> no cut-out
For each plate this writes, at the README's size (the TV's 16:9 frame):
  <id>.plate.webp  the painting
  <id>.mask.webp   the depth cut-out's alpha as a grey mask, trimmed to its box (the hero draws the painting a second
                   time through it, which costs a fraction of a second copy of the pixels)
  <id>.frost.webp  the TV's own baked frost (the painting blurred and saturated once), behind the widget cards
and plates.json: the order, each plate's settings and the mask's box.
"""
import json
import os
import shutil
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "plates")
DEFAULT_TV = os.path.join(os.path.expanduser("~"), "Vault", "Projects", "xiaomi-tv-revamp")

W, H = 1024, 576          # the images' size; the hero draws them over the TV's 1920x1080 stage
Q_PLATE, Q_MASK = 58, 60

# the rotation's order: his F1 plate first, then the set mixed so neighbours differ (all 23 of his keeps)
ORDER = ["spa", "nightcity", "alps", "plane-concorde-climb", "ship", "porschelake", "spartan", "biplane", "monaco",
         "plane-f22-vapour", "snow911", "bronkhorst-skiers", "f1ceiling", "surfers", "planetop", "muse911",
         "plane-typhoon-mist-oil", "gt62", "bronkhorst-streets-s", "plane-airport-impasto", "wave",
         "plane-f22-vapour-oil", "bronkhorst-snowboard"]
CUT = {"all": "fgall", "on": "fg", "subj": "subj"}
# paintings made after a known artist's work (credited in the README)
CREDIT = {"bronkhorst-skiers": "Werner Bronkhorst", "bronkhorst-snowboard": "Werner Bronkhorst",
          "bronkhorst-streets-s": "Werner Bronkhorst"}


def one(tv, pid, choice):
    src = os.path.join(tv, "plates")
    s = choice["settings"]
    plate = Image.open(os.path.join(src, pid + ".plate.webp")).convert("RGB")
    if s.get("flip"):
        plate = plate.transpose(Image.FLIP_LEFT_RIGHT)
    plate.resize((W, H), Image.LANCZOS).save(os.path.join(OUT, pid + ".plate.webp"), "WEBP", quality=Q_PLATE, method=6)
    box = None
    kind = CUT.get(s.get("depth"))
    if kind:
        fg = Image.open(os.path.join(src, "%s.%s.webp" % (pid, kind))).convert("RGBA")
        if s.get("flip"):
            fg = fg.transpose(Image.FLIP_LEFT_RIGHT)
        a = fg.split()[3].resize((W, H), Image.LANCZOS).point(lambda v: 0 if v < 10 else v)
        bb = a.getbbox()
        if bb:
            a.crop(bb).save(os.path.join(OUT, pid + ".mask.webp"), "WEBP", quality=Q_MASK, method=6)
            box = [bb[0], bb[1], bb[2] - bb[0], bb[3] - bb[1]]
    frost = os.path.join(src, pid + (".frost.flip.webp" if s.get("flip") else ".frost.webp"))
    shutil.copy(frost, os.path.join(OUT, pid + ".frost.webp"))
    return dict(id=pid, name=choice.get("name", pid), settings=s, mask=box, credit=CREDIT.get(pid))


def main():
    tv = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TV
    cfg = json.load(open(os.path.join(tv, "hub", "state", "config.json"), encoding="utf-8"))["choices"]
    keep = [k for k, v in cfg.items() if v.get("status") == "keep"]
    missing = [k for k in keep if k not in ORDER]
    ids = [k for k in ORDER if k in keep] + missing
    os.makedirs(OUT, exist_ok=True)
    meta = [one(tv, pid, cfg[pid]) for pid in ids]
    with open(os.path.join(HERE, "plates.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(meta, fh, indent=1)
    tot = 0
    for m in meta:
        sz = [os.path.getsize(os.path.join(OUT, m["id"] + k)) if os.path.exists(os.path.join(OUT, m["id"] + k)) else 0
              for k in (".plate.webp", ".mask.webp", ".frost.webp")]
        tot += sum(sz)
        print("%-24s %-5s plate %5.1f KB  mask %5.1f KB  frost %4.1f KB" % (m["id"], m["settings"]["depth"], *(v / 1024 for v in sz)))
    print("%d plates, %.0f KB (%.0f KB as base64)" % (len(meta), tot / 1024, tot / 1024 * 4 / 3))


if __name__ == "__main__":
    main()
