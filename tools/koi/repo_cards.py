"""Project cards with a real screenshot, in the README's ghost glass (13 Nov 2026 build).

One card per public repo: a real image from the repo itself (its own README hero or social preview), cropped into a
glass-framed window that drifts slowly, then the eyebrow, title, a two-line description and an "open on GitHub" arrow.
A "building now" card is the same glass with no image and no link (private or unshipped work gets no URL).

    python repo_cards.py <out_dir> <image_dir>

Images are embedded as JPEG data URIs so the SVG still works as a README <img> (GitHub's image proxy blocks external
loads inside SVGs). Each card stays under ~120 KB.
"""
import base64
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image  # noqa: E402

import koilib  # noqa: E402
if os.environ.get("KOI_FONT_DIR"):
    koilib.FONT_DIR = os.environ["KOI_FONT_DIR"]
from koilib import Doc, THEMES, REDUCED, f, font  # noqa: E402
import cards  # noqa: E402

W, H = 430, 366
IX, IY, IW, IH = 14, 14, W - 28, 190   # the image window

CARDS = [
    # slug, eyebrow, title, description, link, status, image file(s), focus (x,y 0..1 of the crop centre)
    ("designyourtv", "GOOGLE TV  ·  OIL PAINTINGS  ·  MIT", "designyourtv",
     "A painted lock screen for Google TV: the clock sits behind the painting's subject, with glass widgets and a remote-driven dock.",
     "https://github.com/Sohwhat6420/designyourtv", "OPEN ON GITHUB", ("dyt-tv.webp",), (0.5, 0.4)),
    ("designyourwindows", "WINDOWS 10 + 11  ·  MIT", "designyourwindows",
     "The depth-clock look on Windows: the time sits behind your wallpaper's subject, with glass widgets and a dock.",
     "https://github.com/Sohwhat6420/designyourwindows", "OPEN ON GITHUB", ("dyw-hero.webp",), (0.5, 0.42)),
    ("sidemic", "ANDROID  ·  RUST  ·  TAURI  ·  MIT", "Sidemic",
     "Your Android phone becomes your PC's wireless microphone, with noise removed on the phone and nothing installed on it.",
     "https://github.com/Sohwhat6420/sidemic", "OPEN ON GITHUB", ("sm-hero-pub.png",), (0.55, 0.42)),
    ("android-film-simulations", "PYTHON  ·  ADB  ·  HOBBY  ·  MIT", "Film simulations",
     "Fujifilm-style looks measured on a stock Android camera: a rig finds the nearest setting and scores it on colour.",
     "https://github.com/Sohwhat6420/android-film-simulations", "OPEN ON GITHUB", ("afs-social.png",), (0.5, 0.55)),
    ("human-llm-council", "LOCAL MODELS  ·  PREVIEW  ·  APACHE-2.0", "Human LLM Council",
     "A benchmark of 375 held-out decisions and a pass mark set before any training. The model is not trained yet.",
     "https://github.com/Sohwhat6420/human-llm-council", "OPEN ON GITHUB", None, (0.5, 0.5)),
    ("detached-run", "WINDOWS 11  ·  NODE  ·  MIT", "detached-run",
     "A Windows nohup that never flashes a window: a background job that outlives its launcher, with status and stop.",
     "https://github.com/Sohwhat6420/detached-run", "OPEN ON GITHUB", ("dr-social.png",), (0.5, 0.5)),
    ("reddit-pull", "NODE  ·  ZERO DEPENDENCIES  ·  MIT", "reddit-pull",
     "Public Reddit as JSON for AI agents: no browser, no sign-in, no API key. It prints one line an agent can check.",
     "https://github.com/Sohwhat6420/reddit-pull", "OPEN ON GITHUB", ("rp-social.png",), (0.5, 0.5)),
]

BUILDING = [
    ("hmos-lite", "WATCH  ·  RELAY  ·  ANDROID", "Claude for HMOS Lite",
     "Answer your coding agent from a Huawei watch: a laptop relay and a phone app, built and tested. The watch app is not done."),
    ("prompt-rambler", "VOICE  ·  PROMPTS  ·  WEB", "Prompt Rambler",
     "Talk your way into a good prompt: rambling in, a clean structured prompt out. In development."),
]


def jpeg_uri(path, focus, out_w=808, out_h=380):
    im = Image.open(path).convert("RGB")
    ar = out_w / out_h
    w, h = im.size
    if w / h > ar:                      # too wide: crop the sides around the focus
        cw = int(h * ar)
        cx = int(w * focus[0])
        x0 = min(max(cx - cw // 2, 0), w - cw)
        box = (x0, 0, x0 + cw, h)
    else:                               # too tall: crop the top and bottom
        ch = int(w / ar)
        cy = int(h * focus[1])
        y0 = min(max(cy - ch // 2, 0), h - ch)
        box = (0, y0, w, y0 + ch)
    im = im.crop(box).resize((out_w, out_h), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=62, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def css(p):
    return """
.%(p)sz{transform-origin:50%% 50%%;transform-box:fill-box;animation:%(p)sz 16s ease-in-out infinite alternate}
@keyframes %(p)sz{from{transform:scale(1.0) translate(0,0)}to{transform:scale(1.07) translate(-5px,-3px)}}
.%(p)ss{animation:%(p)ss 7s ease-in-out infinite}
@keyframes %(p)ss{0%%,35%%{transform:translateX(-120%%)}65%%,100%%{transform:translateX(120%%)}}
.%(p)sc{animation:%(p)sc 4.5s ease-in-out infinite}
@keyframes %(p)sc{0%%,100%%{stroke-opacity:.35}18%%{stroke-opacity:1}}
@media (prefers-reduced-motion: reduce){.%(p)sz,.%(p)ss,.%(p)sc{animation:none}}
""" % {"p": p}


def council_motif(T, p):
    """Five seats round a table, drawn in gold line: no real picture exists for this repo, and its numbers are not
    for the README. Each seat lights in turn, then the centre mark answers."""
    import math
    cx, cy = IX + IW / 2, IY + IH / 2
    R, r = 46, 11
    out = ['<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="none" stroke="%s" stroke-opacity=".5" stroke-width="1.6"/>'
           % (f(cx, 1), f(cy, 1), 40, 24, T["gold"])]
    for k in range(5):
        a = -math.pi / 2 + k * 2 * math.pi / 5
        x, y = cx + R * 1.75 * math.cos(a), cy + R * 1.05 * math.sin(a)
        out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-opacity=".25" stroke-width="1"/>' % (f(cx, 1), f(cy, 1), f(x, 1), f(y, 1), T["gold"]))
        out.append('<circle cx="%s" cy="%s" r="%d" fill="none" stroke="%s" stroke-width="1.8" class="%sc" style="animation-delay:%ss"/>'
                   % (f(x, 1), f(y, 1), r, T["gold"], p, f(k * 0.9, 1)))
    out.append('<circle cx="%s" cy="%s" r="5" fill="%s"/>' % (f(cx, 1), f(cy, 1), T["gold"]))
    return ('<rect x="%d" y="%d" width="%d" height="%d" fill="%s" fill-opacity=".05"/>' % (IX, IY, IW, IH, T["gold"])) + "".join(out)


def repo_card(T, i, slug, eyebrow, title, desc, link, status, img_uri):
    doc = Doc(W, H, title, "%s. %s Opens %s." % (title, desc, link))
    p = "rc%d" % i
    doc.css.append(cards.frame_css())
    doc.css.append(css(p))
    cards.card_frame(doc, T, W, H)
    b = doc.body
    # the image window: a real picture, slowly drifting, with a glass lip and a moving glint
    doc.defs.append('<clipPath id="%sw"><rect x="%d" y="%d" width="%d" height="%d" rx="11"/></clipPath>' % (p, IX, IY, IW, IH))
    doc.defs.append('<linearGradient id="%sf" x1="0" y1="0" x2="0" y2="1"><stop offset=".55" stop-color="#000" stop-opacity="0"/>'
                    '<stop offset="1" stop-color="#000" stop-opacity=".38"/></linearGradient>' % p)
    doc.defs.append('<linearGradient id="%sg" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                    '<stop offset=".5" stop-color="#fff" stop-opacity=".14"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>' % p)
    if img_uri:
        inner = ('<g class="%sz"><image href="%s" x="%d" y="%d" width="%d" height="%d" preserveAspectRatio="xMidYMid slice"/></g>'
                 '<rect x="%d" y="%d" width="%d" height="%d" fill="url(#%sf)"/>' % (p, img_uri, IX, IY, IW, IH, IX, IY, IW, IH, p))
    else:
        inner = council_motif(T, p)
    b.append('<g clip-path="url(#%sw)">%s<g class="%ss"><rect x="%d" y="%d" width="%d" height="%d" fill="url(#%sg)"/></g></g>'
             % (p, inner, p, IX, IY, IW // 2, IH, p))
    b.append('<rect x="%d.5" y="%d.5" width="%d" height="%d" rx="11" fill="none" stroke="%s" stroke-opacity=".28"/>'
             % (IX, IY, IW - 1, IH - 1, T["glint"]))
    # text
    ty = IY + IH + 28
    e, _ = doc.text(eyebrow, 24, ty, "cap", 10.5, T["gold"], tracking=0.12)
    t, _ = doc.text(title, 22, ty + 36, "serif", 31, T["text"])
    lines = "".join(doc.text(s, 24, ty + 62 + 18 * k, "sans", 13.5, T["dim"])[0]
                    for k, s in enumerate(cards.wrap(desc, "sans", 13.5, W - 48)[:3]))
    b.append('<g class="rise" style="animation-delay:%ss">%s%s%s</g>' % (f(0.08 * i, 2), e, t, lines))
    sy = H - 26
    s, sw = doc.text(status, 24, sy + 4, "cap", 11, T["accent"], tracking=0.12)
    b.append(s)
    doc.css.append(".nudge{animation:nudge 1.8s cubic-bezier(.5,0,.3,1) infinite}@keyframes nudge{0%,100%{transform:none}50%{transform:translateX(5px)}}")
    b.append('<g class="nudge"><path d="M%s %sh14m-5-5 5 5-5 5" fill="none" stroke="%s" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></g>'
             % (f(24 + sw + 10), f(sy), T["accent"]))
    doc.css.append(REDUCED)
    return doc


def building_card(T, i, slug, eyebrow, title, desc):
    h = 190
    doc = Doc(W, h, title, "%s. %s Building now, no link yet." % (title, desc))
    doc.css.append(cards.frame_css())
    cards.card_frame(doc, T, W, h)
    b = doc.body
    e, _ = doc.text(eyebrow, 24, 38, "cap", 10.5, T["gold"], tracking=0.12)
    t, _ = doc.text(title, 22, 76, "serif", 31, T["text"])
    lines = "".join(doc.text(s, 24, 104 + 18 * k, "sans", 13.5, T["dim"])[0]
                    for k, s in enumerate(cards.wrap(desc, "sans", 13.5, W - 48)[:3]))
    b.append('<g class="rise" style="animation-delay:%ss">%s%s%s</g>' % (f(0.08 * i, 2), e, t, lines))
    sy = h - 26
    b.append('<circle cx="29" cy="%s" r="4" fill="%s"/><circle cx="29" cy="%s" r="4" fill="%s" class="pulse" style="transform-origin:29px %spx;transform-box:view-box"/>'
             % (f(sy), T["gold"], f(sy), T["gold"], f(sy)))
    s, _ = doc.text("BUILDING NOW", 42, sy + 4, "cap", 11, T["dim"], tracking=0.12)
    b.append(s)
    doc.css.append(REDUCED)
    return doc


def main(out_dir, img_dir):
    os.makedirs(out_dir, exist_ok=True)
    report = []
    for tname, T in THEMES.items():
        for i, (slug, eyebrow, title, desc, link, status, imgs, focus) in enumerate(CARDS):
            uri = jpeg_uri(os.path.join(img_dir, imgs[0]), focus) if imgs else None
            doc = repo_card(T, i, slug, eyebrow, title, desc, link, status, uri)
            p = os.path.join(out_dir, "repo-%s-%s.svg" % (slug, tname))
            with open(p, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(doc.render())
            report.append((os.path.basename(p), os.path.getsize(p)))
        for i, (slug, eyebrow, title, desc) in enumerate(BUILDING):
            doc = building_card(T, i, slug, eyebrow, title, desc)
            p = os.path.join(out_dir, "building-%s-%s.svg" % (slug, tname))
            with open(p, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(doc.render())
            report.append((os.path.basename(p), os.path.getsize(p)))
    for r in report:
        print("%7d  %s" % (r[1], r[0]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
