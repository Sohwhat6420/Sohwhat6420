"""Builds every image in ../assets.

    python tools/build.py

  hero.svg               Ethan's TV wallpaper, README-sized: an oil painting, then the name where the TV draws its clock,
                         then the painting's depth cut-out, so the subject sits in front of the letters. Three of the
                         plates he approved crossfade slowly. One file serves both themes (it is a painting).
  widget-*-{dark,light}  the ghost-glass widgets (tools/widgets.py), from the data in ../data

The plates are cut once from the TV project by tools/plates.py (committed in tools/plates/). All text is outlined into
paths and all motion is CSS inside the SVG, because README images are served as <img>, which can't load fonts or
scripts. Under "reduce motion" everything holds still on the first plate.
"""
import base64
import json
import os

from PIL import Image, ImageFilter

import widgets
from svglib import Doc, ROOT, f, font, write_svg

HERE = os.path.dirname(os.path.abspath(__file__))
PLATE_DIR = os.path.join(HERE, "plates")
W, H = 1200, 600

NAME = "ETHAN SOH"
TAGLINE = "APPLIED AI  ·  AGENT ENGINEERING  ·  AI SECURITY"

# The approved plates, from the TV's own settings (xiaomi-tv-revamp/hub/state/config.json, status "keep", all made
# from his own references): the ink is the clock ink he set, the blend is the TV's Ghost material (screen for a light
# ink, multiply for a dark one). porschelake's light-blue ink reads at about 1.5:1 on its sky, so here it takes the
# TV legibility guard's fallback, Charcoal.
SCENES = [
    dict(id="spa", ink="#2b2f33", blend="multiply", op=0.84, tag="#202428"),
    dict(id="nightcity", ink="#f4f2ee", blend="screen", op=0.66, tag="#f4f2ee"),
    dict(id="porschelake", ink="#26303c", blend="multiply", op=0.74, tag="#f7f9fc"),
]
STEP = 9.0                      # seconds each plate holds
FADE = 1.6                      # crossfade, seconds
CYCLE = STEP * len(SCENES)


def uri(path, mime):
    with open(path, "rb") as fh:
        return "data:%s;base64,%s" % (mime, base64.b64encode(fh.read()).decode())


def pct(t):
    return f(100 * t / CYCLE, 3) + "%"


def hero_css(n):
    css = []
    # plate 0 stays underneath; each later plate fades in over the one before, and the last fades out to reveal plate 0
    for i in range(1, n):
        t0 = i * STEP - FADE
        if i < n - 1:
            hold_to = (i + 1) * STEP          # fully covered by the next plate by then
            css.append("@keyframes sc%d{0%%,%s{opacity:0}%s,%s{opacity:1}%s,100%%{opacity:0}}"
                       % (i, pct(t0), pct(t0 + FADE), pct(hold_to), pct(hold_to + 0.01)))
        else:
            css.append("@keyframes sc%d{0%%,%s{opacity:0}%s,%s{opacity:1}100%%{opacity:0}}"
                       % (i, pct(t0), pct(t0 + FADE), pct(CYCLE - FADE)))
        css.append(".s%d{opacity:0;animation:sc%d %ss linear infinite}" % (i, i, f(CYCLE)))
    # the letters settle in as their plate arrives (rise 18 px, one after another), then a sheen crosses them
    settle = 1.4
    for i in range(n):
        t0 = max(0.0, i * STEP - FADE)
        kf = "0%%,%s{opacity:0;transform:translateY(18px)}%s{opacity:1;transform:none}" % (pct(t0), pct(t0 + settle))
        if i == 0:   # plate 0's letters leave while the last plate still covers it, to settle again when it returns
            kf += "%s{opacity:1;transform:none}%s,100%%{opacity:0;transform:none}" % (pct(CYCLE - FADE - 0.3), pct(CYCLE - FADE))
        css.append("@keyframes st%d{%s}" % (i, kf))
        css.append(".s%d .ch{animation:st%d %ss cubic-bezier(.2,.75,.25,1) infinite both}" % (i, i, f(CYCLE)))
        a, b = t0 + settle + 0.5, t0 + settle + 2.7
        css.append("@keyframes sw%d{0%%,%s{transform:translateX(-520px)}%s,100%%{transform:translateX(%dpx)}}"
                   % (i, pct(a), pct(b), W + 120))
        css.append(".s%d .sweep{animation:sw%d %ss cubic-bezier(.45,0,.2,1) infinite both}" % (i, i, f(CYCLE)))
    for k in range(len(NAME)):
        css.append(".ch%d{animation-delay:%sms!important}" % (k, int(k * 55)))
    css.append(".sweep{transform:translateX(-520px)}")
    # depth: the painting breathes slowly while the name drifts the other way, so the name reads as a layer between
    css.append("@keyframes kb{from{transform:scale(1)}to{transform:scale(1.03)}}"
               ".pl{transform-box:view-box;transform-origin:%dpx %dpx;animation:kb 13s ease-in-out infinite alternate}"
               % (W // 2, int(H * 0.62)))
    css.append("@keyframes dr{from{transform:translate(-6px,2px)}to{transform:translate(6px,-2px)}}"
               ".nm{animation:dr 11s ease-in-out infinite alternate}")
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}.s1,.s2{opacity:0!important}"
               ".ch{opacity:1!important;transform:none!important}.sweep{display:none}}")
    return css


def hero(still=None):
    """still=i: plate i alone with no motion (for checking a frame)."""
    meta = {m["id"]: m for m in json.load(open(os.path.join(PLATE_DIR, "plates.json"), encoding="utf-8"))}
    doc = Doc(W, H, "Ethan Soh",
              "Ethan's TV wallpaper as a banner: oil paintings of a Formula 1 car at Spa-Francorchamps, a 911 above a city "
              "at night and a 911 by a lake crossfade slowly. The name ETHAN SOH stands where the TV draws its clock, "
              "behind each painting's subject, under the line: applied AI, agent engineering, AI security.")
    # the name: Big Shoulders Bold (the TV's "Condensed" clock face), stretched 1.3x tall like the TV clock
    disp = font("display")
    size, sy = 236.0, 1.30
    nw = disp.width(NAME, size, 0.01)
    cap = disp.cap * size / disp.upm * sy
    base = 92 + cap                      # cap top at y=92: "pinned high", as on the TV
    letters, _ = doc.letters(NAME, (W - nw) / 2, base, "display", size, tracking=0.01, sy=sy)
    name = "".join(s for s, _, _ in letters)
    tag, _ = doc.text(TAGLINE, W / 2, 64, "sansb", 33, None, tracking=0.1, anchor="middle")

    doc.defs.append('<mask id="nm" maskUnits="userSpaceOnUse" x="0" y="0" width="%d" height="%d"><g fill="#fff">%s</g></mask>'
                    % (W, H, name))
    doc.defs.append('<linearGradient id="sw" x1="0" y1="0" x2="1" y2="0">'
                    '<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".7"/>'
                    '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    doc.defs.append('<filter id="halo" x="-5%" y="-15%" width="110%" height="130%"><feGaussianBlur stdDeviation="9"/></filter>')
    doc.defs.append('<clipPath id="fr"><rect width="%d" height="%d" rx="22"/></clipPath>' % (W, H))
    doc.defs.append('<linearGradient id="vg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity=".2"/>'
                    '<stop offset=".28" stop-color="#000" stop-opacity="0"/><stop offset=".82" stop-color="#000" stop-opacity="0"/>'
                    '<stop offset="1" stop-color="#000" stop-opacity=".22"/></linearGradient>')
    if still is None:
        doc.css.extend(hero_css(len(SCENES)))

    body = ['<rect width="%d" height="%d" rx="22" fill="#0b0d10"/>' % (W, H), '<g clip-path="url(#fr)">']
    for i, sc in enumerate(SCENES):
        if still is not None and i != still:
            continue
        cx, cy, cw, ch = meta[sc["id"]]["cut"]
        plate = uri(os.path.join(PLATE_DIR, sc["id"] + ".plate.webp"), "image/webp")
        cut = uri(os.path.join(PLATE_DIR, sc["id"] + ".cut.webp"), "image/webp")
        body.append('<g class="s%d">' % i)
        # 1 the painting
        body.append('<image class="pl" href="%s" width="%d" height="%d"/>' % (plate, W, H))
        # 2 the name in the TV's Ghost material, and its sheen. A dark ink gets the TV legibility guard's boost: a soft
        #   light halo, invisible on bright sky, that keeps the letters apart from dark trees
        if sc["blend"] == "multiply":
            body.append('<g class="nm" opacity=".42" filter="url(#halo)"><g fill="#f4f2ee">%s</g></g>' % name)
        body.append('<g class="nm" opacity="%s" style="mix-blend-mode:%s"><g fill="%s">%s</g></g>'
                    % (f(sc["op"], 2), sc["blend"], sc["ink"], name))
        body.append('<g class="nm" style="mix-blend-mode:soft-light"><g mask="url(#nm)">'
                    '<rect class="sweep" x="0" y="70" width="420" height="%d" fill="url(#sw)"/></g></g>' % int(cap + 60))
        # 3 the depth cut-out: the subject in front of the name
        body.append('<image class="pl" href="%s" x="%d" y="%d" width="%d" height="%d"/>' % (cut, cx, cy, cw, ch))
        # 4 the line above it, where the TV puts the date (drawn above the cut-out, as on the TV)
        body.append('<g fill="%s" opacity=".92">%s</g>' % (sc["tag"], tag))
        body.append('</g>')
    body.append('<rect width="%d" height="%d" fill="url(#vg)" opacity=".6"/>' % (W, H))
    body.append('</g>')
    body.append('<rect x=".5" y=".5" width="%d" height="%d" rx="21.5" fill="none" stroke="#fff" stroke-opacity=".10"/>' % (W - 1, H - 1))
    doc.body.extend(body)
    return doc


# ----------------------------------------------------------------------------------------------
# frost: blurred slices of the Spa plate behind each widget (dark: the road and wall; light: the sky)
# ----------------------------------------------------------------------------------------------
FROST = {
    # name: (dark box, light box) in the 1200x600 Spa plate
    "tokens": ((0, 380, 600, 600), (0, 0, 600, 190)),
    "github": ((600, 380, 1200, 600), (600, 0, 1200, 190)),
    "htb": ((0, 470, 1200, 600), (0, 20, 1200, 150)),
}


def frosts():
    src = Image.open(os.path.join(PLATE_DIR, "spa.plate.webp")).convert("RGB")
    for name, boxes in FROST.items():
        for theme, box in zip(("dark", "light"), boxes):
            im = src.crop(box).filter(ImageFilter.GaussianBlur(26))
            im.thumbnail((180, 180))
            im.save(os.path.join(PLATE_DIR, "frost-%s-%s.jpg" % (name, theme)), "JPEG", quality=72, optimize=True)


def main():
    import sys
    if "--still" in sys.argv:
        i = int(sys.argv[sys.argv.index("--still") + 1])
        print(write_svg(sys.argv[sys.argv.index("--still") + 2], hero(still=i)))
        return
    out = [write_svg(os.path.join(ROOT, "assets", "hero.svg"), hero())]
    frosts()
    out += widgets.write_widget("widget-tokens", widgets.tokens_svg, widgets.load("tokens.json"))
    out += widgets.write_widget("widget-github", widgets.github_svg, widgets.load("github.json"))
    out += widgets.write_widget("widget-htb", widgets.htb_svg)
    for p, s in out:
        print("%8.1f KB  %s" % (s / 1024, os.path.relpath(p, ROOT)))


if __name__ == "__main__":
    main()
