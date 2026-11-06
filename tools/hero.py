"""The README hero: Ethan's TV home screen (xiaomi-tv-revamp/tv-setup.html), copied as it is, with his name where the
clock is and his own numbers in the widget cards.

    python tools/hero.py [--data DIR] [--out FILE] [--still I]

What it copies, and from where:
  - every plate he approved in DesignConfigurator, in rotation (tools/plates.py, tools/plates.json);
  - for each plate, the clock exactly as the TV page places and colours it (tools/measure_tv.mjs ran the real page and
    wrote tools/tv-layout.json): his face, size, stretch, width, height and depth, its ink, opacity, blend and halo,
    the date line's colour and halo, the painting's accent and glass tint. The clock reads ETHAN SOH (one line where
    that keeps most of his size, otherwise hours-over-minutes as ETHAN over SOH), sized to fit between the columns;
  - the change between plates, with the TV's own timings (tv-setup.html, const T for the TV): the painting dissolves
    in 1050 ms after 160 ms, the incoming camera settles from 1.04 over 1500 ms, the outgoing one pushes in over
    1750 ms, and each letter travels from where it stood on the last plate to where this plate puts it, 1000 ms with
    a 50 ms stagger, dipping 16 % of its height and stepping back to 95.5 % half way (DIP, SHRINK);
  - the widget cards: the TV's two columns, their boxes, radius, baked frost, tint, rim, type sizes and colours
    (measured from the page), filled with his live numbers (data/*.json, tools/refresh.py) and CV facts (facts.py).
All text is outlined into paths and all motion is CSS inside the SVG (a README image is an <img>: no fonts, no
scripts). Under "reduce motion" it holds still on the first plate.
"""
import base64
import datetime as dt
import json
import math
import os
import sys

import facts
from svglib import Doc, ROOT, f, font, write_svg

HERE = os.path.dirname(os.path.abspath(__file__))
PLATES = os.path.join(HERE, "plates")
W, H = 1920, 1080                    # the TV's stage; the plates are embedded at 1024x576 and drawn at this size
IMG = 1920 / 1024

STEP = 6.0                           # each plate holds 6 s: the TV page's "Play the rotation, 6 s each"
T = dict(fadeAt=.16, fade=1.05, settle=1.5, push=1.75, cellAt=.02, cell=1.0, stagger=.05,
         dateOut=.26, dateInAt=.85, dateIn=.65, tintAt=.16, tint=.85)
DIP, SHRINK = .16, .955
EASE = dict(dolly="cubic-bezier(.45,.05,.25,1)", settle="cubic-bezier(.22,1,.36,1)", inout="cubic-bezier(.65,0,.35,1)")
LH = {"row": .8, "stack": .84}

# colours the TV's cards use (measured)
WHITE, BODY, DIM, GREY2, SOFT = "#ffffff", "#e3e5e9", "#aeb3bb", "#b8bcc4", "#d9dce1"
HOT, FULL = "#ffb340", "#ff6a5c"

# the cards' boxes on the 1920x1080 stage (measured); R4 is the one card the TV doesn't have: it continues the right
# column to the left column's bottom edge, for his competitions
CARD_R = 26.88
LX, RX, CW = 69.1, 1486.6, 364.3
CARDS = dict(L1=(LX, 55.7, CW, 254.9), L2=(LX, 322.7, CW, 163.4), L3=(LX, 498.2, CW, 375.3), L4=(LX, 885.7, CW, 138.0),
             R1=(RX, 55.7, CW, 193.2), R2=(RX, 266.5, CW, 201.7), R3=(RX, 485.0, CW, 193.2), R4=(RX, 696.0, CW, 327.7))
LPAD, RPAD = 22.1, 25.4


def uri(path, mime):
    with open(path, "rb") as fh:
        return "data:%s;base64,%s" % (mime, base64.b64encode(fh.read()).decode())


def rgb(s):
    """'rgb(1, 2, 3)' / 'rgba(1,2,3,.4)' / '#abc123' -> (r, g, b, a)."""
    s = s.strip()
    if s.startswith("#"):
        return int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16), 1.0
    v = [float(x) for x in s[s.index("(") + 1:s.index(")")].replace("/", ",").split(",")]
    return int(v[0]), int(v[1]), int(v[2]), (v[3] if len(v) > 3 else 1.0)


def hexc(c):
    return "#%02x%02x%02x" % tuple(int(round(x)) for x in c[:3])


def load(data, name, default=None):
    p = os.path.join(data, name)
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


# ----------------------------------------------------------------------------------------------
# text, the way the TV's CSS lays it out: a line box `lh` tall starting at `top`
# ----------------------------------------------------------------------------------------------
class Ink:
    def __init__(self, doc):
        self.doc = doc

    def line(self, s, x, top, key, size, lh, fill, ls=0.0, anchor="start", opacity=None, cls=None, maxw=None, minsize=None):
        fnt = font(key)
        if maxw:
            while fnt.width(s, size, ls) > maxw and size > (minsize or size * .8):
                size -= .25
        base = fnt.baseline(top, size, lh)
        svg, w = self.doc.text(s, x, base, key, size, fill, tracking=ls, anchor=anchor, opacity=opacity, cls=cls)
        return svg, w

    def width(self, s, key, size, ls=0.0):
        return font(key).width(s, size, ls)


def card_label(ink, s, x, top, fill="url(#acc)", cls="ac"):
    """The cards' caps label: 600 15.36px, letter-spacing .12em (NOVEMBER, NEXT, BUSES · BISHAN, FRIDAY)."""
    return ink.line(s.upper(), x, top, "h6", 15.36, 23, None, ls=.12, cls=cls)[0]


# ----------------------------------------------------------------------------------------------
# the cards' contents (shared by every plate; the accent follows the painting through the "ac" classes)
# ----------------------------------------------------------------------------------------------
def chip_rows(ink, x0, rows, top0, label=None):
    """The bus card's rows: a tinted chip with a bold short name, then the main text and a grey detail."""
    out, top = [], top0
    for chip, main, detail in rows:
        cx = x0
        out.append('<rect class="acf" x="%s" y="%s" width="75.1" height="33.1" rx="6.72" fill-opacity=".24"/>'
                   '<rect class="acs" x="%s" y="%s" width="74" height="32" rx="6.2" fill="none" stroke-opacity=".4" stroke-width="1.15"/>'
                   % (f(cx, 1), f(top, 1), f(cx + .55, 2), f(top + .55, 2)))
        out.append(ink.line(chip, cx + 37.55, top + 4.45, "h7", 16.13 if len(chip) < 5 else 14.5, 24.2, WHITE, ls=.01, anchor="middle")[0])
        tx = x0 + 88.8
        s1, w1 = ink.line(main, tx, top + 4.45, "h6", 16.13, 24.2, WHITE)
        out.append(s1)
        room = x0 + CW - 2 * LPAD - (tx + w1 + 6)
        out.append(ink.line("·  " + detail, tx + w1 + 6, top + 4.45, "h4", 16.13, 24.2, GREY2, maxw=room, minsize=12.5)[0])
        top += 35.7
    return "".join(out), top


def sublabel(ink, s, x, top):
    return ink.line(s.upper(), x, top, "h4", 13.44, 19.5, GREY2, ls=.06)[0]


def card_l1(ink, gh, today):
    """The TV's month calendar, this month, with his GitHub contributions shaded behind each day."""
    x, y, w, h = CARDS["L1"]
    out = [card_label(ink, today.strftime("%B"), x + LPAD, 74.5)]
    out.append(ink.line("GITHUB", x + w - LPAD, 77.7, "h6", 12.67, 19.5, DIM, ls=.08, anchor="end")[0])
    xs = [113.05 + 46.07 * c for c in range(7)]
    for c, d in enumerate("MTWTFSS"):
        out.append(ink.line(d, xs[c], 108.7, "h6", 13.82, 20.7, WHITE, anchor="middle", opacity=.6)[0])
    days = (gh or {}).get("days", {})
    vals = sorted(v for v in days.values() if v)
    q = lambda p: vals[min(len(vals) - 1, int(p * (len(vals) - 1)))] if vals else 0
    cut = [q(.25), q(.5), q(.75)]
    lvl = lambda n: 0 if not n else 1 if n <= cut[0] else 2 if n <= cut[1] else 3 if n <= cut[2] else 4
    first = today.replace(day=1)
    row, col = 0, first.weekday()
    d = first
    while d.month == today.month:
        cx, top = xs[col], 134.7 + 27 * row
        n = days.get(d.isoformat(), 0)
        if d == today:
            out.append('<circle class="acf" cx="%s" cy="%s" r="16.7"/>' % (f(cx, 2), f(top + 10.35, 2)))
            out.append(ink.line(str(d.day), cx, top, "h7", 13.82, 20.7, "#111111", anchor="middle")[0])
        else:
            if n and d < today:
                out.append('<circle class="acf" cx="%s" cy="%s" r="12.6" fill-opacity="%s"/>'
                           % (f(cx, 2), f(top + 10.35, 2), (0, .16, .26, .38, .52)[lvl(n)]))
            out.append(ink.line(str(d.day), cx, top, "h4", 13.82, 20.7, WHITE, anchor="middle",
                                opacity=None if d <= today else .55)[0])
        d += dt.timedelta(days=1)
        col += 1
        if col == 7:
            col, row = 0, row + 1
    return "".join(out)


def card_l2(ink, today):
    x, y, w, h = CARDS["L2"]
    left = (facts.INTERNSHIP_FROM - today).days
    out = [card_label(ink, "Next", x + LPAD, 341.5),
           ink.line(facts.INTERNSHIP, x + LPAD, 373.4, "h6", 20.16, 29.9, WHITE, maxw=w - 2 * LPAD)[0],
           ink.line(facts.INTERNSHIP_LINE, x + LPAD, 408.0, "h4", 16.9, 25.3, WHITE, opacity=.78)[0],
           ink.line("in %d days · applied AI, AI security" % left if left > 0 else "now", x + LPAD, 440.4, "h6", 16.9, 25.3, SOFT,
                    maxw=w - 2 * LPAD)[0]]
    return "".join(out)


def card_l3(ink):
    x, y, w, h = CARDS["L3"]
    out = [card_label(ink, "Credentials", x + LPAD, 517.0), sublabel(ink, "Certified", x + LPAD, 552.3)]
    s, top = chip_rows(ink, x + LPAD, facts.CERTIFIED, 577.0)
    out.append(s)
    out.append(sublabel(ink, "Leadership", x + LPAD, top + 9.0))
    s, top = chip_rows(ink, x + LPAD, facts.LEADERSHIP, top + 33.7)
    out.append(s)
    # the diploma on one line: a grey caps label, the cGPA, then the distinctions
    lab, lw = ink.line("DIPLOMA", x + LPAD, top + 12.0, "h4", 13.44, 19.5, GREY2, ls=.06)
    out.append(lab)
    a, aw = ink.line(facts.DIPLOMA[0], x + LPAD + lw + 12, top + 9.6, "h7", 16.13, 24.2, WHITE)
    out.append(a)
    out.append(ink.line("·  " + facts.DIPLOMA[1], x + LPAD + lw + 12 + aw + 6, top + 9.6, "h4", 16.13, 24.2, GREY2)[0])
    return "".join(out)


ICONS = {   # 24x24 line icons, drawn at the battery ring's centre (the TV draws its device icons the same way)
    "flag": "M7 21V4M7 4h10l-2.2 3.6L17 11H7",
    "cap": "M2.5 9.5 12 5l9.5 4.5L12 14zM6.5 11.6v4.2c1.4 1.4 3.4 2.2 5.5 2.2s4.1-.8 5.5-2.2v-4.2M21.5 9.5v5",
    "book": "M4 5.5C6.5 4.6 9.3 4.8 12 6.4c2.7-1.6 5.5-1.8 8-.9v13c-2.5-.9-5.3-.7-8 .9-2.7-1.6-5.5-1.8-8-.9zM12 6.4v13",
    "trophy": "M8 4h8v5a4 4 0 0 1-8 0zM8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4M12 13v4M8.5 20h7M10 17h4",
}


def card_l4(ink):
    x, y, w, h = CARDS["L4"]
    out = []
    for j, (icon, label, frac) in enumerate(facts.RINGS):
        cx, cy, r = 97.5 + 82.2 * j + 30.4, 908.2 + 30.4, 28.9
        c = 2 * math.pi * r
        out.append('<circle cx="%s" cy="%s" r="%s" fill="none" stroke="#fff" stroke-opacity=".2" stroke-width="3"/>' % (f(cx, 1), f(cy, 1), f(r, 1)))
        out.append('<circle class="acs ring" cx="%s" cy="%s" r="%s" fill="none" stroke-width="3" stroke-linecap="round" '
                   'stroke-dasharray="%s %s" transform="rotate(-90 %s %s)"/>'
                   % (f(cx, 1), f(cy, 1), f(r, 1), f(c * frac, 1), f(c, 1), f(cx, 1), f(cy, 1)))
        out.append('<path d="%s" transform="translate(%s %s)" fill="none" stroke="#fff" stroke-width="1.7" stroke-linecap="round" '
                   'stroke-linejoin="round"/>' % (ICONS[icon], f(cx - 12, 1), f(cy - 12, 1)))
        out.append(ink.line(label, cx, 979.4, "h6", 18.24, 27.6, BODY, anchor="middle")[0])
    return "".join(out)


def utc(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc)


def bar(x, y, w, pct, cls_or_col, pace=None):
    out = ['<rect x="%s" y="%s" width="%s" height="7.5" rx="3.75" fill="#fff" fill-opacity=".16"/>' % (f(x, 1), f(y, 1), f(w, 1))]
    if pct:
        fw = max(7.5, w * min(pct, 100) / 100)
        attr = 'class="acf"' if cls_or_col == "acc" else 'fill="%s"' % cls_or_col
        out.append('<rect %s x="%s" y="%s" width="%s" height="7.5" rx="3.75"/>' % (attr, f(x, 1), f(y, 1), f(fw, 1)))
    if pace is not None:
        px = x + w * max(0, min(1, pace))
        out.append('<rect x="%s" y="%s" width="2.4" height="13" rx="1.2" fill="#fff" stroke="#000" stroke-opacity=".5" stroke-width=".8"/>'
                   % (f(px - 1.2, 1), f(y - 2.75, 1)))
    return "".join(out)


def card_r1(ink, use, now):
    """The TV's Claude card: the 5-hour session and the week, as the plan's limits page shows them."""
    x, y, w, h = CARDS["R1"]
    tx = x + RPAD
    right = x + w - RPAD
    out = ['<rect class="acf" x="%s" y="76.6" width="41.9" height="41.9" rx="9.6" fill-opacity=".45"/>' % f(tx, 1),
           '<rect x="%s" y="76.6" width="41.9" height="41.9" rx="9.6" fill="#000" fill-opacity=".28"/>' % f(tx, 1),
           '<rect class="acs" x="%s" y="77.2" width="40.7" height="40.7" rx="9" fill="none" stroke-opacity=".45" stroke-width="1.15"/>' % f(tx + .6, 1)]
    cx, cy = tx + 20.95, 97.55
    rays = "".join('<line x1="%s" y1="%s" x2="%s" y2="%s"/>' % (f(cx + 2.2 * math.cos(a), 2), f(cy + 2.2 * math.sin(a), 2),
                                                                f(cx + 10.2 * math.cos(a), 2), f(cy + 10.2 * math.sin(a), 2))
                   for a in (k * math.pi / 6 + math.pi / 12 for k in range(12)))
    out.append('<g stroke="#fff" stroke-width="2.3" stroke-linecap="round">%s</g>' % rays)
    out.append(ink.line("Claude", x + 80.6, 83.7, "h6", 18.24, 27.6, WHITE)[0])
    if not use:
        out.append(ink.line("NO READING YET", right, 86.9, "h6", 12.67, 19.5, DIM, ls=.08, anchor="end")[0])
        return "".join(out)
    read = dt.datetime.fromisoformat(use["read_at"].replace("Z", "+00:00"))
    stamp = read.strftime("%H:%M") if (now - read).total_seconds() < 12 * 3600 else read.strftime("%a %H:%M")
    out.append(ink.line("AS OF %s UTC" % stamp.upper(), right, 86.9, "h6", 12.67, 19.5, DIM, ls=.08, anchor="end")[0])
    rows = [("Session", use.get("session"), 5 * 3600, 130.6, 139.1, 156.5), ("Weekly", use.get("weekly"), 7 * 86400, 182.5, 191.0, 208.3)]
    for name, win, span, top, by, stop in rows:
        out.append(ink.line(name, tx, top, "h5", 15.36, 23, BODY)[0])
        if not win:
            continue
        pct = win.get("pct") or 0
        col = FULL if pct >= 90 else HOT if pct >= 60 else "acc"
        ra = win.get("resets_at")
        if ra and ra <= now.timestamp():
            # the window this reading belongs to has closed since: its number no longer holds, so none is shown
            out.append(bar(1604.7, by, 150.2, 0, col))
            out.append(ink.line("–", right, top, "h7", 15.36, 23, WHITE, anchor="end")[0])
            out.append(ink.line("window reset %s UTC" % utc(ra).strftime("%a %H:%M"), 1604.7, stop, "h5", 13.06, 19.6, DIM)[0])
            continue
        pace = 1 - (ra - now.timestamp()) / span if ra else None
        out.append(bar(1604.7, by, 150.2, pct, col, pace if pace is not None and 0 < pace < 1 else None))
        out.append(ink.line("%d%%" % round(pct), right, top, "h7", 15.36, 23, WHITE, anchor="end")[0])
        if ra:
            r = utc(ra)
            txt = ("resets %s UTC" % r.strftime("%H:%M")) if name == "Session" else ("resets %s UTC" % r.strftime("%a %H:%M"))
            out.append(ink.line(txt, 1604.7, stop, "h5", 13.06, 19.6, DIM)[0])
    return "".join(out)


def fmt_tok(n):
    if n >= 1e9:
        return ("%.0f" if n >= 1e11 else "%.1f") % (n / 1e9) + "B"
    if n >= 1e6:
        return ("%.0f" if n >= 1e8 else "%.1f") % (n / 1e6) + "M"
    return "%dk" % round(n / 1e3) if n >= 1e3 else str(n)


def card_r2(ink, act, today):
    """The TV's Claude Code heatmap: the last 22 weeks, Monday at the top, shaded by tokens per day (setActivity)."""
    x, y, w, h = CARDS["R2"]
    tx, right = x + RPAD, x + w - RPAD
    out = [ink.line("Claude Code", tx, 284.0, "h6", 18.24, 27.6, WHITE)[0]]
    tok = (act or {}).get("tokens") or {}
    weeks = 22
    start = today - dt.timedelta(days=today.weekday() + (weeks - 1) * 7)
    days = [start + dt.timedelta(days=i) for i in range(weeks * 7)]
    vals = sorted(v for v in tok.values() if v)
    q = lambda p: vals[min(len(vals) - 1, int(p * (len(vals) - 1)))] if vals else 0
    cut = [q(.25), q(.5), q(.75)]
    lvl = lambda n: 0 if not n else 1 if n <= cut[0] else 2 if n <= cut[1] else 3 if n <= cut[2] else 4
    cells = []
    for i, d in enumerate(days):
        if d > today:
            continue
        cx, cy = 1512 + 14.4 * (i // 7), 322.7 + 14.4 * (i % 7)
        n = tok.get(d.isoformat(), 0)
        L = lvl(n)
        if L:
            cells.append('<rect class="acf" x="%s" y="%s" width="11.1" height="11.1" rx="2.69"%s/>'
                         % (f(cx, 1), f(cy, 1), "" if L == 4 else ' fill-opacity="%s"' % (0, .28, .48, .72)[L]))
        else:
            cells.append('<rect x="%s" y="%s" width="11.1" height="11.1" rx="2.69" fill="#fff" fill-opacity=".09"/>' % (f(cx, 1), f(cy, 1)))
        if d == today:
            cells.append('<rect x="%s" y="%s" width="13.1" height="13.1" rx="3.5" fill="none" stroke="#fff" stroke-width="1.9"/>'
                         % (f(cx - 1, 1), f(cy - 1, 1)))
    out.append("".join(cells))
    past = [tok.get(d.isoformat(), 0) for d in days if d <= today]
    i = len(past) - 1
    if i >= 0 and not past[i]:
        i -= 1
    streak = 0
    while i >= 0 and past[i]:
        streak, i = streak + 1, i - 1
    out.append(ink.line("%d-day streak" % streak if streak else "no streak", right, 288.6, "h5", 13.82, 20.7, DIM, anchor="end")[0])
    out.append(ink.line(start.strftime("%b") + " – now", tx, 429.0, "h5", 13.82, 20.7, DIM)[0])
    total = (act or {}).get("total")
    out.append(ink.line("%s tokens all-time" % fmt_tok(total) if total else "", right, 429.0, "h5", 13.82, 20.7, DIM, anchor="end")[0]
               if total else "")
    return "".join(out), streak


def gh_short(n):
    return ("%.1f" % (n / 1000)).rstrip("0").rstrip(".") if n >= 1000 else str(n), ("k" if n >= 1000 else "")


def card_r3(ink, gh, today):
    """The TV's "usage today" card, carrying his GitHub year: the number in the clock's face (drawn per plate), the
    last seven days on the week bar, the total underneath."""
    x, y, w, h = CARDS["R3"]
    tx = x + RPAD
    out = [ink.line("GITHUB", tx, 502.5, "h6", 15.36, 23, BODY, ls=.12)[0]]
    days = (gh or {}).get("days", {})
    week = [today - dt.timedelta(days=6 - k) for k in range(7)]
    vals = sorted(v for v in days.values() if v)
    q = lambda p: vals[min(len(vals) - 1, int(p * (len(vals) - 1)))] if vals else 0
    cut = [q(.25), q(.5), q(.75)]
    for k, d in enumerate(week):
        cx = 1636.85 + 29.3 * k
        today_k = d == today
        out.append(ink.line("MTWTFSS"[d.weekday()], cx, 538.4, "h7" if today_k else "h6", 12.67, 19.5,
                            None if today_k else "#9ea4ae", anchor="middle", cls="ac" if today_k else None)[0])
        n = days.get(d.isoformat(), 0)
        bx = 1624.1 + 29.35 * k
        if n:
            L = 1 if n <= cut[0] else 2 if n <= cut[1] else 3 if n <= cut[2] else 4
            out.append('<rect class="acf" x="%s" y="587.1" width="25.4" height="9.9" rx="2.69"%s/>'
                       % (f(bx, 1), "" if L == 4 else ' fill-opacity="%s"' % (0, .4, .6, .8)[L]))
        else:
            out.append('<rect x="%s" y="587.1" width="25.4" height="9.9" rx="2.69" fill="#fff" fill-opacity=".15"/>' % f(bx, 1))
    tot = (gh or {}).get("contributions")
    if tot is not None:
        a, aw = ink.line("{:,}".format(tot), tx, 627.7, "h7", 13.82, 20.7, WHITE)
        out.append(a)
        out.append(ink.line(" contributions · %d public repos" % gh.get("repos", 0), tx + aw, 627.7, "h5", 13.82, 20.7, DIM)[0])
    return "".join(out)


def card_r4(ink):
    x, y, w, h = CARDS["R4"]
    tx = x + RPAD
    out = [card_label(ink, "Competitions", tx, y + 18.8), sublabel(ink, "Capture the flag", tx, y + 54.1)]
    s, top = chip_rows(ink, tx, facts.CTF, y + 78.8)
    out.append(s)
    out.append(sublabel(ink, "Hackathons", tx, top + 9.0))
    s, top = chip_rows(ink, tx, facts.HACKATHONS, top + 33.7)
    out.append(s)
    out.append(ink.line(facts.EVENTS, tx, top + 7.5, "h4", 13.44, 19.5, GREY2, maxw=w - 2 * RPAD, minsize=11.0)[0])
    return "".join(out)


# ----------------------------------------------------------------------------------------------
# the clock: ETHAN SOH, letter by letter, where the TV page put each one
# ----------------------------------------------------------------------------------------------
def clock_letters(L):
    """[(char, glyph, transform, ink box)] for one plate, from tv-layout.json."""
    s = L["settings"]
    fnt = font(s["face"])
    fs = float(L["time"]["fontSize"][:-2])
    sy = s["stretch"] / 100
    wx = s["width"] / 100
    lh = LH["stack"] if L["orient"] == "stack" else LH["row"]
    if L["orient"] == "stack" and s["face"] in ("fat", "didone", "soft"):
        lh = .8
    out = []
    for c in L["cells"]:
        ch = c["ch"]
        if not ch.strip() or ch == " ":
            continue
        g = fnt.glyph(ch)
        x, top = c["box"][0], c["box"][1]
        base = top + sy * (fnt.baseline(0, fs, lh * fs))
        k = fs / fnt.upm
        xmin, ymin, xmax, ymax = fnt.bounds(g)
        box = (x + xmin * k * wx, base - ymax * k * sy, (xmax - xmin) * k * wx, (ymax - ymin) * k * sy)
        out.append((ch, g, (x, base, k * wx, k * sy), box))
    return out


def shadow_filter(doc, spec, fid):
    """A CSS drop-shadow()/text-shadow list ('rgba(...) 0px 0px 6.72px, ...') as an SVG filter."""
    parts, depth, cur = [], 0, ""
    for ch in spec:
        depth += ch == "("
        depth -= ch == ")"
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    prims, merge = [], []
    for k, p in enumerate(parts):
        p = p.strip()
        if p.startswith("drop-shadow("):
            p = p[len("drop-shadow("):-1]
        col = p[:p.index(")") + 1]
        nums = [float(v.replace("px", "")) for v in p[p.index(")") + 1:].split()]
        dx, dy, blur = (nums + [0, 0, 0])[:3]
        r, g, b, a = rgb(col)
        prims.append('<feDropShadow dx="%s" dy="%s" stdDeviation="%s" flood-color="%s" flood-opacity="%s" result="s%d"/>'
                     % (f(dx, 2), f(dy, 2), f(blur / 2, 2), hexc((r, g, b)), f(a, 2), k) if k == 0 else
                     '<feDropShadow in="SourceGraphic" dx="%s" dy="%s" stdDeviation="%s" flood-color="%s" flood-opacity="%s" result="s%d"/>'
                     % (f(dx, 2), f(dy, 2), f(blur / 2, 2), hexc((r, g, b)), f(a, 2), k))
        merge.append("s%d" % k)
    if len(prims) == 1:
        body = prims[0]
    else:
        body = "".join(prims) + "<feMerge>%s</feMerge>" % "".join('<feMergeNode in="%s"/>' % m for m in merge)
    doc.defs.append('<filter id="%s" x="-20%%" y="-30%%" width="140%%" height="160%%" color-interpolation-filters="sRGB">%s</filter>'
                    % (fid, body))


# ----------------------------------------------------------------------------------------------
# the timeline
# ----------------------------------------------------------------------------------------------
def build(data, still=None):
    plates = json.load(open(os.path.join(HERE, "plates.json"), encoding="utf-8"))
    lay = json.load(open(os.path.join(HERE, "tv-layout.json"), encoding="utf-8"))["plates"]
    plates = [p for p in plates if p["id"] in lay]
    n = len(plates)
    cyc = STEP * n
    pc = lambda t: f(100 * max(0.0, min(cyc, t)) / cyc, 3) + "%"
    gh = load(data, "github.json")
    act = load(data, "activity.json")
    use = load(data, "usage.json")
    now = dt.datetime.now(dt.timezone.utc)
    today = (now + dt.timedelta(hours=8)).date()      # the TV's day (its activity file counts days in its own zone)

    doc = Doc(W, H, "Ethan Soh",
              "Ethan's TV home screen as a banner: %d oil paintings he approved for his TV rotate every %d seconds, his name "
              "ETHAN SOH standing where the TV draws its clock, behind each painting's subject. Widget cards on both sides: "
              "GitHub contributions this month, his next step (a 44-week internship from April 2027), credentials (Claude "
              "Certified Architect, ISC2 CC, Anthropic Academy, BB Senior Cadet Lieutenant, Founder's Award, cGPA 3.77), "
              "his live Claude plan usage, his Claude Code activity heatmap and tokens, GitHub, and competitions (Hack The "
              "Box 30th of 6,744, Cyber Conquest finalist, BrainHack CDDC finalist, PolyFinTech100 quarterfinal)."
              % (n, STEP))
    ink = Ink(doc)
    css = doc.css
    order = list(range(n)) if still is None else [still]

    # when each change starts: into plate i at i*STEP (i >= 1); into plate 0 just before the loop ends
    ch_in = {i: i * STEP for i in range(1, n)}
    ch_in[0] = cyc - 1.45
    ch_out = {i: ch_in[(i + 1) % n] for i in range(n)}

    # ---- defs: plates, masks, card clip, shadows
    clip = "".join('<rect x="%s" y="%s" width="%s" height="%s" rx="%s"/>' % (f(x, 1), f(y, 1), f(w, 1), f(h, 1), f(CARD_R, 2))
                   for x, y, w, h in CARDS.values())
    doc.defs.append('<clipPath id="cards">%s</clipPath>' % clip)
    doc.defs.append('<filter id="cshadow" x="-20%" y="-20%" width="140%" height="150%"><feGaussianBlur stdDeviation="19"/></filter>')

    letters, boxes = {}, {}
    for i in range(n):
        letters[i] = clock_letters(lay[plates[i]["id"]])
        boxes[i] = [b for _, _, _, b in letters[i]]

    scenes, frosts = [], []
    halos = {}
    for i in order:
        p, L = plates[i], lay[plates[i]["id"]]
        s = L["settings"]
        pid = p["id"]
        doc.defs.append('<image id="p%d" href="%s" width="%d" height="%d" preserveAspectRatio="none"/>'
                        % (i, uri(os.path.join(PLATES, pid + ".plate.webp"), "image/webp"), W, H))
        has_cut = p.get("mask") and s["depth"] != "off" and not L.get("autoPause")
        if has_cut:
            mx, my, mw, mh = p["mask"]
            doc.defs.append('<mask id="m%d" maskUnits="userSpaceOnUse" x="0" y="0" width="%d" height="%d">'
                            '<image href="%s" x="%s" y="%s" width="%s" height="%s" preserveAspectRatio="none"/></mask>'
                            % (i, W, H, uri(os.path.join(PLATES, pid + ".mask.webp"), "image/webp"),
                               f(mx * IMG, 2), f(my * IMG, 2), f(mw * IMG, 2), f(mh * IMG, 2)))
        # the clock's material, as the TV computed it for this painting
        tm = L["time"]
        ink_col = hexc(rgb(tm["color"]))
        op = float(tm["opacity"])
        blend = tm["blend"] if tm["blend"] != "normal" else None
        filt = ""
        if tm.get("filter") and tm["filter"] != "none":
            fid = halos.setdefault(tm["filter"], "hl%d" % len(halos))
            if fid == "hl%d" % (len(halos) - 1) and not any(fid in d for d in doc.defs):
                shadow_filter(doc, tm["filter"], fid)
            filt = ' filter="url(#%s)"' % fid
        glyphs = []
        for k, (ch, g, (x, base, kx, ky), box) in enumerate(letters[i]):
            glyphs.append('<g class="q%d_%d"><use href="#%s" transform="translate(%s %s) scale(%s %s)"/></g>'
                          % (i, k, doc.gid(font(s["face"]), g), f(x, 2), f(base, 2), f(kx, 5), f(-ky, 5)))
        nm = '<g fill="%s" opacity="%s"%s%s>%s</g>' % (ink_col, f(op, 2), ' style="mix-blend-mode:%s"' % blend if blend else "", filt, "".join(glyphs))
        # the date line, above the cut-out (the TV's #dateTop)
        dd = L["date"]
        dcol = hexc(rgb(dd["color"]))
        dfs = float(dd["fontSize"][:-2])
        dfid = halos.setdefault("text:" + dd["shadow"], "hl%d" % len(halos))
        if not any('id="%s"' % dfid in d for d in doc.defs):
            shadow_filter(doc, dd["shadow"], dfid)
        bx = dd["box"]
        date_svg = ink.line(facts.TAGLINE, bx[0] + bx[2] / 2, bx[1], "h6", dfs, bx[3], dcol, ls=.02, anchor="middle")[0]
        body = ['<g class="sc s%d">' % i, '<use class="dl d%d" href="#p%d"/>' % (i, i), nm]
        if has_cut:
            body.append('<use class="dl d%d" href="#p%d" mask="url(#m%d)"/>' % (i, i, i))
        body.append('<g class="dt t%d" filter="url(#%s)">%s</g>' % (i, dfid, date_svg))
        body.append("</g>")
        scenes.append("".join(body))
        # the cards' glass for this painting: its baked frost under its tint, and the GitHub number in its clock face
        tr, tg, tb, ta = rgb(L.get("tint") or "rgba(21,24,25,.46)")
        frost = uri(os.path.join(PLATES, pid + ".frost.webp"), "image/webp")
        g = gh or {}
        big, suf = gh_short(g.get("contributions", 0))
        fnt = font(s["face"])
        bsize = 59.52 * (0.82 if s["face"] == "fat" else 1)
        bsvg, bw = ink.line(big, 1512.0, 533.6, s["face"], bsize, 88.5, None, ls=-.01, cls="ac")
        ssvg = ink.line(suf, 1512.0 + bw + 2, 533.6 + 88.5 * .3, s["face"], bsize * .46, 88.5 * .55, None, cls="ac", opacity=.72)[0]
        frosts.append('<g class="sc s%d"><g clip-path="url(#cards)"><image href="%s" width="%d" height="%d" preserveAspectRatio="none"/>'
                      '<rect width="%d" height="%d" fill="%s" fill-opacity="%s"/></g>%s%s</g>'
                      % (i, frost, W, H, W, H, hexc((tr, tg, tb)), f(ta, 2), bsvg, ssvg if g.get("contributions") else ""))

    # ---- motion
    if still is None:
        for i in range(n):
            t0 = ch_in[i] + T["fadeAt"]
            if i == 0:   # plate 0 lies underneath and is never faded; it only reappears when the last plate goes
                pass
            elif i < n - 1:
                cov = ch_out[i] + T["fadeAt"] + T["fade"]          # fully covered by the next plate by then
                css.append("@keyframes o%d{0%%,%s{opacity:0}%s,%s{opacity:1}%s,100%%{opacity:0}}"
                           % (i, pc(t0), pc(t0 + T["fade"]), pc(cov), pc(cov + .01)))
                css.append(".s%d{opacity:0;animation:o%d %ss infinite;animation-timing-function:%s}" % (i, i, f(cyc), EASE["dolly"]))
            else:        # the last plate dissolves away to reveal plate 0
                out0 = ch_out[i] + T["fadeAt"]
                css.append("@keyframes o%d{0%%,%s{opacity:0}%s,%s{opacity:1}%s,100%%{opacity:0}}"
                           % (i, pc(t0), pc(t0 + T["fade"]), pc(out0), pc(out0 + T["fade"])))
                css.append(".s%d{opacity:0;animation:o%d %ss infinite;animation-timing-function:%s}" % (i, i, f(cyc), EASE["dolly"]))
            # the camera: the incoming painting settles from 1.04, the outgoing one pushes in
            a, b = ch_in[i], ch_out[i]
            kf = []
            if i == 0:
                kf.append("0%%{transform:none}%s{transform:none}%s{transform:translate(-.3%%,-.5%%) scale(1.04)}" % (pc(b), pc(b + T["push"])))
                kf.append("%s{transform:scale(1.04)}100%%{transform:none}" % pc(a))
            else:
                kf.append("0%%,%s{transform:scale(1.04)}%s{transform:none}%s{transform:none}%s,100%%{transform:translate(-.3%%,-.5%%) scale(1.04)}"
                          % (pc(a), pc(a + T["settle"]), pc(b if b > a else cyc - .01), pc(min(cyc, (b if b > a else cyc) + T["push"]))))
            css.append("@keyframes c%d{%s}" % (i, "".join(kf)))
            css.append(".d%d{transform-box:view-box;transform-origin:960px 540px;animation:c%d %ss infinite;animation-timing-function:%s}"
                       % (i, i, f(cyc), EASE["settle"]))
            # the date line: out quickly at the change, in late (dateOut, dateInAt, dateIn)
            kd = ("0%%{opacity:1}%s{opacity:1}%s{opacity:0}" % (pc(b), pc(b + T["dateOut"]))
                  + "%s{opacity:0}%s,100%%{opacity:1}" % (pc(a + T["dateInAt"]) if i == 0 else pc(a + T["dateInAt"]), pc(a + T["dateInAt"] + T["dateIn"]))) \
                if i == 0 else \
                ("0%%,%s{opacity:0}%s{opacity:1}%s{opacity:1}%s,100%%{opacity:0}" % (pc(a + T["dateInAt"]), pc(a + T["dateInAt"] + T["dateIn"]), pc(b), pc(b + T["dateOut"])))
            css.append("@keyframes dt%d{%s}.t%d{animation:dt%d %ss linear infinite}" % (i, kd, i, i, f(cyc)))
            # the letters: each travels from where the last plate had it, and on to where the next plate wants it
            prev, nxt = (i - 1) % n, (i + 1) % n
            for k, R in enumerate(boxes[i]):
                P = boxes[prev][k] if k < len(boxes[prev]) else R
                N = boxes[nxt][k] if k < len(boxes[nxt]) else R
                lag = T["cellAt"] + k * T["stagger"]

                def at(B, u=None):
                    if u is not None:   # a point on the TV's morph path (pathBox): straight, dipping, stepping back
                        kk = 1 - (1 - SHRINK) * math.sin(math.pi * u)
                        bx_ = B[0] + B[2] * (1 - kk) / 2
                        by_ = B[1] + B[3] * (1 - kk) / 2 + DIP * B[3] * math.sin(math.pi * u)
                        B = (bx_, by_, B[2] * kk, B[3] * kk)
                    return "transform:translate(%spx,%spx) scale(%s,%s)" % (f(B[0] - R[0], 2), f(B[1] - R[1], 2),
                                                                         f(B[2] / R[2], 4), f(B[3] / R[3], 4))

                def path(A, B, t_start):
                    stops = []
                    for j in range(7):
                        v = j / 6
                        u = ease_inout(v)
                        M = tuple(A[m] + (B[m] - A[m]) * u for m in range(4))
                        stops.append("%s{%s}" % (pc(t_start + v * T["cell"]), at(M, u)))
                    return "".join(stops)

                ein, eout = ch_in[i] + lag, ch_out[i] + lag
                if i == 0:
                    kf = "0%%{%s}%s{%s}%s%s{%s}%s100%%{%s}" % (
                        at(R), pc(eout), at(R), path(R, N, eout), pc(eout + T["cell"] + .01), at(N),
                        ("%s{%s}%s{%s}" % (pc(ein - .02), at(N), pc(ein), at(P))) + path(P, R, ein), at(R))
                else:
                    kf = "0%%{%s}%s{%s}%s%s{%s}%s100%%{%s}" % (
                        at(P), pc(ein), at(P), path(P, R, ein), pc(ein + T["cell"] + .01), at(R),
                        ("%s{%s}" % (pc(eout), at(R))) + path(R, N, eout), at(N))
                css.append("@keyframes q%d_%d{%s}" % (i, k, kf))
                css.append(".q%d_%d{transform-box:view-box;transform-origin:%spx %spx;animation:q%d_%d %ss linear infinite}"
                           % (i, k, f(R[0], 2), f(R[1], 2), i, k, f(cyc)))
        # the accent glides with the painting (the TV's tint and accent, 850 ms after 160 ms)
        stops = []
        for i in range(n):
            a = ch_in[i] + T["tintAt"]
            prev = plates[(i - 1) % n]["id"]
            c_prev, c_now = hexc(rgb(lay[prev]["acc"])), hexc(rgb(lay[plates[i]["id"]]["acc"]))
            if i == 0:
                continue
            stops.append((a, c_prev))
            stops.append((a + T["tint"], c_now))
        last = hexc(rgb(lay[plates[-1]["id"]]["acc"]))
        first = hexc(rgb(lay[plates[0]["id"]]["acc"]))
        a0 = ch_in[0] + T["tintAt"]
        seq = [(0, first)] + stops + [(a0, last), (min(cyc, a0 + T["tint"]), first), (cyc, first)]
        css.append("@keyframes ac{%s}" % "".join("%s{fill:%s}" % (pc(t), c) for t, c in seq))
        css.append("@keyframes as{%s}" % "".join("%s{stroke:%s}" % (pc(t), c) for t, c in seq))
        css.append(".ac,.acf{fill:%s;animation:ac %ss linear infinite}.acs{stroke:%s;animation:as %ss linear infinite}"
                   % (first, f(cyc), first, f(cyc)))
        css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}.sc:not(.s0){opacity:0!important}"
                   "[class^=q]{transform:none!important}.dl{transform:none!important}}")
    else:
        c = hexc(rgb(lay[plates[still]["id"]]["acc"]))
        css.append(".ac,.acf{fill:%s}.acs{stroke:%s}" % (c, c))

    # ---- the page
    body = ['<rect width="%d" height="%d" fill="#0b0d10"/>' % (W, H)]
    body += scenes
    # the cards' long soft shadow (0 11.5px 38px -19px rgba(0,0,0,.5)), under the glass
    body.append('<g filter="url(#cshadow)" fill="#000" fill-opacity=".5">%s</g>'
                % "".join('<rect x="%s" y="%s" width="%s" height="%s" rx="%s"/>' % (f(x + 19, 1), f(y + 30, 1), f(w - 38, 1), f(h - 38, 1), f(CARD_R, 1))
                          for x, y, w, h in CARDS.values()))
    body += frosts
    # the cards' rim: a light top edge and a faint ring (inset 0 1.15px rgba(255,255,255,.22), inset 0 0 0 1.15px rgba(255,255,255,.1))
    rims = []
    for x, y, w, h in CARDS.values():
        rims.append('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="none" stroke="#fff" stroke-opacity=".1" stroke-width="1.15"/>'
                    % (f(x + .58, 2), f(y + .58, 2), f(w - 1.15, 2), f(h - 1.15, 2), f(CARD_R - .6, 2)))
        rims.append('<path d="M%s %s a%s %s 0 0 1 %s -%s H%s a%s %s 0 0 1 %s %s" fill="none" stroke="#fff" stroke-opacity=".22" stroke-width="1.15"/>'
                    % (f(x + .6, 2), f(y + CARD_R * .5, 2), f(CARD_R - .6, 2), f(CARD_R - .6, 2), f(CARD_R * .6, 2), f(CARD_R * .5 - .58, 2),
                       f(x + w - CARD_R * .6 - .6, 2), f(CARD_R - .6, 2), f(CARD_R - .6, 2), f(CARD_R * .6, 2), f(CARD_R * .5 - .58, 2)))
    body.append("".join(rims))
    r2, streak = card_r2(ink, act, today)
    body += [card_l1(ink, gh, today), card_l2(ink, today), card_l3(ink), card_l4(ink),
             card_r1(ink, use, now), r2, card_r3(ink, gh, today), card_r4(ink)]
    doc.body.extend(body)
    return doc


def ease_inout(v):
    """cubic-bezier(.65,0,.35,1) (the TV's "inout"), solved for y at x = v."""
    x1, y1, x2, y2 = .65, 0, .35, 1
    lo, hi = 0.0, 1.0
    for _ in range(40):
        t = (lo + hi) / 2
        x = 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t * t * x2 + t ** 3
        lo, hi = (t, hi) if x < v else (lo, t)
    t = (lo + hi) / 2
    return 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t * t * y2 + t ** 3


def main():
    a = sys.argv
    data = a[a.index("--data") + 1] if "--data" in a else os.path.join(ROOT, "data")
    out = a[a.index("--out") + 1] if "--out" in a else os.path.join(ROOT, "assets", "hero.svg")
    still = int(a[a.index("--still") + 1]) if "--still" in a else None
    p, s = write_svg(out, build(data, still))
    print("%8.1f KB  %s" % (s / 1024, p))


if __name__ == "__main__":
    main()
