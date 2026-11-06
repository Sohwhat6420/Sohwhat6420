"""The README's widgets, drawn in the TV wallpaper's ghost-glass style: a frosted slice of the painting behind a tinted
pane with a thin specular rim, an accent ramp taken from the clock's ink, and the clock face for the big numbers.

Each widget is its own file so each can be refreshed on its own:
  widget-tokens-*.svg   tools/refresh-tokens.py, on Ethan's laptop (the data is local)
  widget-github-*.svg   tools/gh_stats.py, from the daily GitHub Action
  widget-htb-*.svg      tools/build.py (a fixed result)
Sizes are chosen for a 375 px phone as well as the desktop: nothing is smaller than 34 units in a 600-unit tile,
which is about 9.5 px when two tiles share a phone's width.
"""
import base64
import datetime as dt
import json
import os

from svglib import Doc, ROOT, esc, f, font, write_svg

ASSETS = os.path.join(ROOT, "assets")
DATA = os.path.join(ROOT, "data")
PLATES = os.path.join(ROOT, "tools", "plates")

THEMES = {
    "dark": dict(name="dark", text="#f3f1ec", dim="#b9bdc4", faint="#8a9099", tint="#090b0f", tintOp=0.5,
                 rimTop=0.42, rimBot=0.06, rimCol="#ffffff", sheen=0.10, ramp="#eef1f5", empty=0.09, signal="#e2553f"),
    "light": dict(name="light", text="#16181c", dim="#41464e", faint="#5d636c", tint="#ffffff", tintOp=0.6,
                  rimTop=0.95, rimBot=0.0, rimCol="#ffffff", sheen=0.35, ramp="#23272c", empty=0.08, signal="#c23a26",
                  edge="#1b1f24", edgeOp=0.10),
}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
REDUCED = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"


def day(iso):
    d = dt.date.fromisoformat(iso[:10])
    return "%d %s %d" % (d.day, MONTHS[d.month - 1], d.year)


def short(n):
    for div, suf in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if n >= div:
            return ("%.1f" % (n / div)).rstrip("0").rstrip(".") + suf
    return str(int(n))


def frost(name, theme):
    """A small, pre-blurred slice of the painting (tools/plates/frost-<name>-<theme>.jpg), upscaled by the browser."""
    with open(os.path.join(PLATES, "frost-%s-%s.jpg" % (name, theme)), "rb") as fh:
        return "data:image/jpeg;base64," + base64.b64encode(fh.read()).decode()


def fit(key, s, size, maxw, tracking=0.0, floor=34):
    w = font(key).width(s, size, tracking)
    while w > maxw and size > floor:
        size -= 1
        w = font(key).width(s, size, tracking)
    return size


def glass(doc, T, w, h, frost_name, r=30):
    """The pane: frost, tint, top sheen and rim. Returns the svg."""
    cid, gid, sid = doc.uid("c"), doc.uid("g"), doc.uid("s")
    doc.defs.append('<clipPath id="%s"><rect width="%d" height="%d" rx="%d"/></clipPath>' % (cid, w, h, r))
    doc.defs.append('<linearGradient id="%s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="%s" stop-opacity="%s"/>'
                    '<stop offset="1" stop-color="%s" stop-opacity="%s"/></linearGradient>'
                    % (gid, T["rimCol"], f(T["rimTop"], 2), T["rimCol"], f(T["rimBot"], 2)))
    doc.defs.append('<linearGradient id="%s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="%s"/>'
                    '<stop offset=".45" stop-color="#fff" stop-opacity="0"/></linearGradient>' % (sid, f(T["sheen"], 2)))
    out = ['<g clip-path="url(#%s)">' % cid,
           '<image href="%s" width="%d" height="%d" preserveAspectRatio="xMidYMid slice"/>' % (frost(frost_name, T["name"]), w, h),
           '<rect width="%d" height="%d" fill="%s" opacity="%s"/>' % (w, h, T["tint"], f(T["tintOp"], 2)),
           '<rect width="%d" height="%d" fill="url(#%s)"/>' % (w, h, sid),
           '</g>']
    if T.get("edge"):
        out.append('<rect x=".5" y=".5" width="%d" height="%d" rx="%d" fill="none" stroke="%s" stroke-opacity="%s"/>'
                   % (w - 1, h - 1, r, T["edge"], f(T["edgeOp"], 2)))
    out.append('<rect x="1.25" y="1.25" width="%s" height="%s" rx="%s" fill="none" stroke="url(#%s)" stroke-width="2.5"/>'
               % (f(w - 2.5), f(h - 2.5), f(r - 1.25), gid))
    return "".join(out)


def label(doc, T, s, x, y, anchor="start", maxw=520):
    size = fit("sansb", s, 32, maxw, 0.12, floor=28)
    return doc.text(s, x, y, "sansb", size, T["dim"], tracking=0.12, anchor=anchor)[0]


# ----------------------------------------------------------------------------------------------
# tokens: Claude Code's own count (its /stats cache), all models, cache included
# ----------------------------------------------------------------------------------------------
def tokens_svg(d, T):
    W, H = 600, 380
    total, first, asof = d["total"], d["first"], d["asof"]
    doc = Doc(W, H, "Claude Code tokens: %s" % short(total),
              "%s tokens through Claude Code (input, output and cache, all models) from %s to %s, by Claude Code's own "
              "count. Bars: tokens per day." % ("{:,}".format(total), day(first), day(asof)))
    doc.css.append(".bar{transform-box:fill-box;transform-origin:50% 100%;animation:grow .9s cubic-bezier(.2,.8,.2,1) both}"
                   "@keyframes grow{from{transform:scaleY(0)}}" + REDUCED)
    b = [glass(doc, T, W, H, "tokens")]
    b.append(label(doc, T, "CLAUDE CODE TOKENS", 40, 62))
    big, bw = doc.text(short(total), 36, 212, "display", 132, T["text"], sy=1.08)
    b.append(big)
    # beside the short number: the unit, then the exact count
    x2 = 36 + bw + 24
    b.append(doc.text("tokens", x2, 162, "sans", fit("sans", "tokens", 36, W - 40 - x2, floor=30), T["dim"])[0])
    exact = "{:,}".format(total)
    b.append(doc.text(exact, x2, 208, "mono", fit("mono", exact, 25, W - 40 - x2, floor=18), T["faint"])[0])
    # bars: tokens per day, oldest to newest, every day of the span (a day with none is an empty slot)
    days = d["daily"]
    start, end = dt.date.fromisoformat(first), dt.date.fromisoformat(asof)
    n = (end - start).days + 1
    x0, x1, y0, y1 = 40, W - 40, 236, 306
    step = (x1 - x0) / n
    bwid = max(1.2, step * 0.62)
    top = max(days.values()) or 1
    bars = []
    for i in range(n):
        v = days.get((start + dt.timedelta(days=i)).isoformat(), 0)
        x = x0 + i * step + (step - bwid) / 2
        if v <= 0:
            bars.append('<rect x="%s" y="%s" width="%s" height="2" fill="%s" opacity="%s"/>'
                        % (f(x, 2), f(y1 - 2), f(bwid, 2), T["ramp"], f(T["empty"] * 2, 2)))
            continue
        h = max(3, (y1 - y0) * (v / top) ** 0.5)
        op = 0.28 + 0.72 * (v / top) ** 0.5
        bars.append('<rect class="bar" style="animation-delay:%sms" x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s" opacity="%s"/>'
                    % (int(i * 6), f(x, 2), f(y1 - h, 2), f(bwid, 2), f(h, 2), f(min(2, bwid / 2), 2), T["ramp"], f(op, 2)))
    b.append("".join(bars))
    foot = "%s – %s  ·  all models" % (day(first)[:-5], day(asof))
    b.append(doc.text(foot, 40, 352, "sans", fit("sans", foot, 34, W - 80, floor=30), T["faint"])[0])
    doc.body.extend(b)
    return doc


# ----------------------------------------------------------------------------------------------
# github: contributions, repos, stars and languages, from the GraphQL API (tools/gh_stats.py)
# ----------------------------------------------------------------------------------------------
def github_svg(d, T):
    W, H = 600, 380
    doc = Doc(W, H, "GitHub: %s contributions in the last year" % "{:,}".format(d["contributions"]),
              "%s contributions in the last 12 months; %d public repositories, %d stars earned; top language %s. "
              "Heatmap: the last %d weeks. Read %s." % ("{:,}".format(d["contributions"]), d["repos"], d["stars"],
                                                       d["languages"][0][0] if d["languages"] else "none",
                                                       len(d["weeks"]), day(d["asof"])))
    doc.css.append(".cell{animation:pop .5s ease-out both}@keyframes pop{from{opacity:0}}" + REDUCED)
    b = [glass(doc, T, W, H, "github")]
    b.append(label(doc, T, "GITHUB", 40, 62))
    big, bw = doc.text("{:,}".format(d["contributions"]), 36, 212, "display", 132, T["text"], sy=1.08)
    b.append(big)
    x2 = 36 + bw + 24
    b.append(doc.text("contributions", x2, 162, "sans", fit("sans", "contributions", 36, W - 40 - x2, floor=28), T["dim"])[0])
    span = "12 months to %s" % day(d["asof"])[:-5]
    b.append(doc.text(span, x2, 206, "sans", fit("sans", span, 30, W - 40 - x2, floor=24), T["faint"])[0])
    # heatmap: one column per week, Sunday at the top, the TV's accent ramp
    weeks = d["weeks"]
    cols = len(weeks)
    x0, x1, y0, y1 = 40, W - 40, 222, 312
    gap = 3
    cell = min(((x1 - x0) - gap * (cols - 1)) / cols, ((y1 - y0) - gap * 6) / 7)
    top = max([c for w in weeks for c in w if c is not None] + [1])
    cells = []
    for i, w in enumerate(weeks):
        for j, c in enumerate(w):
            if c is None:
                continue
            x, y = x0 + i * (cell + gap), y0 + j * (cell + gap)
            if c == 0:
                op = T["empty"]
            else:
                q = (c / top) ** 0.5
                op = 0.3 + 0.7 * q
            cells.append('<rect class="cell" style="animation-delay:%sms" x="%s" y="%s" width="%s" height="%s" rx="2" fill="%s" opacity="%s"/>'
                         % (int(i * 18), f(x, 2), f(y, 2), f(cell, 2), f(cell, 2), T["ramp"], f(op, 2)))
    b.append("".join(cells))
    langs = d["languages"][:3]
    foot = "%d public repo%s  ·  %d star%s" % (d["repos"], "" if d["repos"] == 1 else "s", d["stars"], "" if d["stars"] == 1 else "s")
    if langs:
        foot += "  ·  " + langs[0][0]
    b.append(doc.text(foot, 40, 352, "sans", fit("sans", foot, 34, W - 80, floor=30), T["faint"])[0])
    doc.body.extend(b)
    return doc


# ----------------------------------------------------------------------------------------------
# HTB: a fixed result from the CV (Hack The Box Cyber Apocalypse CTF 2026)
# ----------------------------------------------------------------------------------------------
def htb_svg(T):
    W, H = 1200, 200
    doc = Doc(W, H, "Hack The Box Cyber Apocalypse CTF 2026: top 0.5%",
              "Hack The Box Cyber Apocalypse CTF 2026: 30th of 6,744 teams, the top 0.5%, with all 136 flags captured.")
    b = [glass(doc, T, W, H, "htb", r=30)]
    big, bw = doc.text("TOP 0.5%", 40, 148, "display", 128, T["text"], sy=1.08)
    b.append(big)
    x2 = 40 + bw + 44
    b.append('<rect x="%s" y="48" width="2" height="104" fill="%s" opacity=".35"/>' % (f(x2 - 22), T["dim"]))
    b.append(label(doc, T, "HACK THE BOX CYBER APOCALYPSE 2026", x2, 84, maxw=W - 64 - x2))
    l2 = "CTF: 30th of 6,744 teams, all 136 flags"
    b.append(doc.text(l2, x2, 140, "sans", fit("sans", l2, 40, W - 40 - x2, floor=34), T["text"])[0])
    doc.body.extend(b)
    return doc


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def write_widget(name, render, *args):
    out = []
    for t, T in THEMES.items():
        out.append(write_svg(os.path.join(ASSETS, "%s-%s.svg" % (name, t)), render(*args, T)))
    return out
