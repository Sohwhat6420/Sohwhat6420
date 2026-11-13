"""Draws the three proposed "Download CV (PDF)" buttons, light and dark, into proposals/cv-button/assets.

    python proposals/cv-button/make_variants.py

Same wording as the live button. What changes is the drawing: the two lines are outlined Instrument Sans (the face the
other cards use), so they are the same width on every device and cannot run into the border; the space left of the
arrow and right of the text is balanced; the arrow nudges on its own while the tray under it stays still.

  a  outline   the present idea, tidied: a gold hairline pill
  b  glass     the same ring, filled with the cards' ghost glass (tools/koi/koilib.py glass(), no shadow)
  c  solid     one pill filled with the page's gold, the page's only filled control
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools", "koi"))
from koilib import Doc, THEMES, f, font, glass  # noqa: E402

TITLE = "Download CV (PDF)"
SUB = "Full version · 2 pages · for ATS or a closer read"
DESC = "Button. Download Ethan Soh's full CV as a PDF, 2 pages."

H = 60                       # the button's height
T_SIZE, S_SIZE = 16, 12      # title and second line
T_BASE, S_BASE = 26, 44      # their baselines: cap top to last baseline is centred in H, a touch high for the descenders
ICON_X = 30                  # centre of the arrow
TEXT_X = 51                  # left edge of both lines
PAD_R = 25                   # from the end of the longer line to the button's right edge

CSS = """
.cvA{animation:cvA 2.4s ease-in-out 3}
@keyframes cvA{0%,70%,100%{transform:translateY(0)}35%{transform:translateY(2.5px)}}
@media (prefers-reduced-motion: reduce){*{animation:none!important}}
"""


def width():
    w = max(font("sansb").width(TITLE, T_SIZE), font("sans").width(SUB, S_SIZE))
    return int(round(TEXT_X + w + PAD_R))


def arrow(colour, sw=1.8):
    x, cy = ICON_X, H / 2
    a = ('<path class="cvA" d="M%s %sv13.5M%s %sl7 7 7-7"/>' % (f(x), f(cy - 10.5), f(x - 7), f(cy - 4)))
    tray = '<path d="M%s %sh16"/>' % (f(x - 8), f(cy + 9.5))
    return '<g fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round">%s%s</g>' % (colour, f(sw), a, tray)


def lines(doc, ink, dim):
    t, _ = doc.text(TITLE, TEXT_X, T_BASE, "sansb", T_SIZE, ink)
    s, _ = doc.text(SUB, TEXT_X, S_BASE, "sans", S_SIZE, dim)
    return t + s


RING = 1                     # the gold ring, on whole pixels so it stays crisp at 100 % scaling (2 is the live weight)


def ring(T, W, sw=None):
    sw = RING if sw is None else sw
    return ('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="none" stroke="%s" stroke-width="%s"/>'
            % (f(sw / 2, 2), f(sw / 2, 2), f(W - sw, 2), f(H - sw, 2), f((H - sw) / 2, 2), T["gold"], f(sw, 2)))


def variant_a(T, sw=None):
    """Outline: a gold hairline pill, nothing else."""
    W = width()
    doc = Doc(W, H, TITLE, DESC)
    doc.css.append(CSS)
    doc.body.append(ring(T, W, sw))
    doc.body.append(arrow(T["gold"]))
    doc.body.append(lines(doc, T["text"], T["dim"]))
    return doc


def variant_b(T):
    """Glass: the same gold ring, filled with the cards' ghost glass (no outer shadow, so it needs no room below)."""
    W = width()
    doc = Doc(W, H, TITLE, DESC)
    doc.css.append(CSS)
    doc.body.append(glass(doc, T, 0, 0, W, H, H / 2, shadow=False))
    doc.body.append(ring(T, W))
    doc.body.append(arrow(T["gold"]))
    doc.body.append(lines(doc, T["text"], T["dim"]))
    return doc


def variant_c(T):
    """Solid: filled with the page's gold in both themes; the type on it is the page colour of that theme."""
    W = width()
    on = "#ffffff" if T["name"] == "light" else "#14161a"
    doc = Doc(W, H, TITLE, DESC)
    doc.css.append(CSS)
    doc.body.append('<rect width="%s" height="%s" rx="%s" fill="%s"/>' % (W, H, H // 2, T["gold"]))
    doc.body.append(arrow(on))
    t, _ = doc.text(TITLE, TEXT_X, T_BASE, "sansb", T_SIZE, on)
    s, _ = doc.text(SUB, TEXT_X, S_BASE, "sans", S_SIZE, on, opacity=0.92)
    doc.body.append(t + s)
    return doc


if __name__ == "__main__":
    out = os.path.join(HERE, "assets")
    os.makedirs(out, exist_ok=True)
    for key, fn in (("a", variant_a), ("b", variant_b), ("c", variant_c)):
        for theme in ("light", "dark"):
            svg = fn(THEMES[theme]).render()
            path = os.path.join(out, "cv-download-%s-%s.svg" % (key, theme))
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(svg + "\n")
            print("wrote", os.path.relpath(path, ROOT), len(svg))
