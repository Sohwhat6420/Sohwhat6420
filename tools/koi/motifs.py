"""The eight animated motifs under the banner (his picks, 7 Nov 2026), each drawn into a box so it can sit in a section
header's glass window or on its own glass tile.

    f1(...)          an F1 car on a glowing racing line through an S-bend, with light trails       (02 Projects)
    weather(...)     the TV's live weather layer: rain, drifting cloud, a lightning flash, golden hour (divider)
    handshake(...)   SYN, SYN-ACK and ACK between two nodes, then a flag captured                   (03 Track record)
    agent_phone(...) an agent's cursor taps a phone; an R4 action is held at the gate               (01 Now building)
    concorde(...)    Concorde climbing off a wet runway, heat shimmer behind the engines           (footer)
    helmet(...)      an original line drawing of a crested Greek helmet, catching a light sweep     (about tile)
    tokens(...)      odometer digits rolling up to his measured Claude Code token total             (about tile)
    bb_tkd(...)      a Boys' Brigade chevron and a Taekwondo black-belt knot drawing themselves     (about tile)

Every motif is CSS or SMIL inside the SVG (no scripts: GitHub serves README images as <img>). Each one's resting
state, with animation switched off, is a meaningful still: under prefers-reduced-motion the CSS animations stop
(koilib.REDUCED) and SMIL pieces sit in .motion with a posed copy in .still.
Each function takes a doc, the theme, the box (x, y, w, h) and returns SVG; CSS class names carry a per-call prefix.
"""
import math
import random

from koilib import cr, f, font

CAP_LS = 0.12   # the TV's caps label: 600, letter-spacing .12em


def _pfx(doc, p):
    return doc.uid(p)


def _css(doc, tpl, p):
    doc.css.append(tpl.replace("$p", p))


def _len(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def _offset(pts, d):
    out = []
    for i, (x, y) in enumerate(pts):
        a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy) or 1
        out.append((x - dy / n * d, y + dx / n * d))
    return out


def _blur(doc, k, sd):
    doc.defs.append('<filter id="%s" x="-50%%" y="-50%%" width="200%%" height="200%%"><feGaussianBlur stdDeviation="%s"/></filter>'
                    % (k, f(sd, 2)))
    return k


def _clip(doc, k, x, y, w, h, r):
    doc.defs.append('<clipPath id="%s"><rect x="%s" y="%s" width="%s" height="%s" rx="%s"/></clipPath>'
                    % (k, f(x, 2), f(y, 2), f(w, 2), f(h, 2), f(r, 2)))
    return k


def pill(doc, T, label, cx, cy, colour, size=10.5, solid=True):
    """A small packet or action chip, centred on (cx, cy)."""
    w = font("mono").width(label, size) + 18
    t, _ = doc.text(label, cx - w / 2 + 9, cy + size * 0.36, "mono", size, colour)
    return ('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s" stroke="%s" stroke-opacity=".85"/>%s'
            % (f(cx - w / 2, 2), f(cy - 10), f(w, 2), 20, 10, T["card"] if solid else T["chip"], colour, t)), w


def cap(doc, T, s, x, y, size=11, colour=None, anchor="start"):
    return doc.text(s.upper(), x, y, "cap", size, colour or T["dim"], tracking=CAP_LS, anchor=anchor)[0]


# ----------------------------------------------------------------------------------------------
# 1. F1 car on the S-bend
# ----------------------------------------------------------------------------------------------
def f1(doc, T, x, y, w, h):
    p = _pfx(doc, "fa")
    cy = y + h * 0.5
    amp = h * 0.24
    n = 90
    pts = [(x - 50 + (w + 100) * i / n, cy + amp * math.sin(2 * math.pi * 1.2 * i / n + 0.5)) for i in range(n + 1)]
    d = cr(pts, closed=False)
    L = _len(pts)
    tw = min(h * 0.38, 26)
    out = [
        # the asphalt, its two edges, and red-white kerbs on the outside of each bend
        '<path d="%s" fill="none" stroke="%s" stroke-opacity="%s" stroke-width="%s"/>' % (d, T["trk"], f(T["trkOp"] * 1.4, 3), f(tw, 1)),
        '<path d="%s" fill="none" stroke="%s" stroke-width="1"/>' % (cr(_offset(pts, tw / 2), closed=False), T["line"]),
        '<path d="%s" fill="none" stroke="%s" stroke-width="1"/>' % (cr(_offset(pts, -tw / 2), closed=False), T["line"]),
        '<path d="%s" fill="none" stroke="%s" stroke-opacity=".55" stroke-width="2.2" stroke-dasharray="5 5"/>'
        % (cr(_offset(pts, tw / 2 + 1.6), closed=False), T["danger"]),
    ]
    # the racing line, glowing, with a slow flow along it
    gb = _blur(doc, p + "g", 2.2)
    out.append('<path d="%s" fill="none" stroke="%s" stroke-width="3" stroke-opacity=".35" filter="url(#%s)"/>' % (d, T["gold"], gb))
    out.append('<path d="%s" fill="none" stroke="%s" stroke-width="1.1" stroke-opacity=".75" stroke-dasharray="2 7" class="%sr"/>'
               % (d, T["gold"], p))
    _css(doc, ".$pr{animation:$pr 1.6s linear infinite}@keyframes $pr{to{stroke-dashoffset:-18}}", p)
    dur = L / 175.0
    # light trails: a long soft one and a short bright one, each a dash that ends where the car is (same SMIL clock)
    trails = []
    for length, width, op, blur in ((150, 4, .32, True), (64, 1.6, .9, False)):
        trails.append('<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-opacity="%s" stroke-linecap="round" '
                      'stroke-dasharray="%s %s"%s><animate attributeName="stroke-dashoffset" values="%s;%s" dur="%ss" '
                      'repeatCount="indefinite"/></path>'
                      % (d, T["accent"], f(width, 1), f(op, 2), f(length), f(L + 400), ' filter="url(#%s)"' % gb if blur else "",
                         f(length), f(length - L), f(dur, 3)))
    s = min(1.25, h / 56)
    car = ('<g transform="scale(%s)">'
           '<rect x="10.5" y="-6.2" width="2.6" height="12.4" rx=".8" fill="%s"/>'
           '<rect x="-14.6" y="-5.4" width="2.8" height="10.8" rx=".8" fill="%s"/>'
           '<rect x="4.4" y="-7.4" width="5" height="2.8" rx="1" fill="%s"/><rect x="4.4" y="4.6" width="5" height="2.8" rx="1" fill="%s"/>'
           '<rect x="-10.6" y="-7.8" width="5.6" height="3.2" rx="1" fill="%s"/><rect x="-10.6" y="4.6" width="5.6" height="3.2" rx="1" fill="%s"/>'
           '<path d="M15 0L8.5-1.5L-1-2.6L-6.5-4.2L-11.5-3.4L-12.6 0L-11.5 3.4L-6.5 4.2L-1 2.6L8.5 1.5Z" fill="%s"/>'
           '<circle cx="-1.6" cy="0" r="1.5" fill="%s"/></g>'
           % (f(s, 3), T["accent"], T["accent"], T["ink"], T["ink"], T["ink"], T["ink"], T["text"], T["gold"]))
    out.append('<g class="motion">%s<g>%s<animateMotion dur="%ss" repeatCount="indefinite" rotate="auto" path="%s"/></g></g>'
               % ("".join(trails), car, f(dur, 3), d))
    # posed: the car on the second bend, a short trail behind it
    i = int(n * 0.56)
    a = math.degrees(math.atan2(pts[i + 1][1] - pts[i - 1][1], pts[i + 1][0] - pts[i - 1][0]))
    sl = _len(pts[:i + 1])
    out.append('<g class="still"><path d="%s" fill="none" stroke="%s" stroke-width="1.6" stroke-dasharray="64 %s" stroke-dashoffset="%s"/>'
               '<g transform="translate(%s %s) rotate(%s)">%s</g></g>'
               % (d, T["accent"], f(L + 400), f(64 - sl), f(pts[i][0], 1), f(pts[i][1], 1), f(a, 1), car))
    return "".join(out)


# ----------------------------------------------------------------------------------------------
# 2. the TV's live weather layer
# ----------------------------------------------------------------------------------------------
def weather(doc, T, x, y, w, h, label=True):
    p = _pfx(doc, "wx")
    r = random.Random(11)
    dark = T["name"] == "dark"
    out = []
    # golden hour: a warm wash from the horizon and a low sun, in the clear half of the cycle
    doc.defs.append('<linearGradient id="%sgh" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="%s" stop-opacity=".5"/>'
                    '<stop offset=".7" stop-color="%s" stop-opacity="0"/></linearGradient>' % (p, T["accent"], T["accent"]))
    sb = _blur(doc, p + "s", 9)
    out.append('<g class="%sgo"><rect x="%s" y="%s" width="%s" height="%s" fill="url(#%sgh)"/>'
               '<circle cx="%s" cy="%s" r="30" fill="%s" opacity=".5" filter="url(#%s)"/><circle cx="%s" cy="%s" r="13" fill="%s" opacity=".9"/></g>'
               % (p, f(x), f(y), f(w), f(h), p, f(x + w * 0.8), f(y + h * 0.86), T["accent"], sb, f(x + w * 0.8), f(y + h * 0.86), T["gold"]))
    # cloud: soft blurred banks that drift right to left, drawn twice across for a seamless loop
    cb = _blur(doc, p + "c", 7)
    banks = []
    for k in range(5):
        cx, cyc = r.uniform(0, w), y + r.uniform(h * 0.05, h * 0.45)
        for j in range(3):
            banks.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s"/>' % (f(cx + j * 26 - 26), f(cyc + r.uniform(-5, 5)),
                                                                          f(r.uniform(24, 40)), f(r.uniform(9, 15))))
    cloud = "".join(banks)
    out.append('<g fill="%s" fill-opacity="%s" filter="url(#%s)"><g class="%scl"><g transform="translate(%s 0)">%s</g>'
               '<g transform="translate(%s 0)">%s</g></g></g>'
               % ("#ffffff" if dark else "#5a6270", ".12" if dark else ".16", cb, p, f(x), cloud, f(x + w), cloud))
    # rain: the TV's streaks, thin and slanted, each falling on its own clock
    drops = []
    for k in range(int(w / 9)):
        dx = x + r.uniform(0, w)
        ln = r.uniform(9, 20)
        drops.append('<line x1="%s" y1="0" x2="%s" y2="%s" class="%sd" style="animation-duration:%ss;animation-delay:-%ss" stroke-opacity="%s"/>'
                     % (f(dx), f(dx - ln * 0.22), f(ln), p, f(r.uniform(.55, .95), 2), f(r.uniform(0, 1), 2), f(r.uniform(.25, .6), 2)))
    out.append('<g class="%sro" stroke="%s" stroke-width="1.1" stroke-linecap="round">%s</g>'
               % (p, "#dfe6f0" if dark else "#5d6878", "".join(drops)))
    # lightning: a bolt and the sky flashing with it, twice in quick succession
    bx = x + w * 0.34
    bolt = "M%s %sl-9 %sh8l-12 %s" % (f(bx), f(y + 4), f(h * 0.3), f(h * 0.36))
    out.append('<g class="%sfl"><rect x="%s" y="%s" width="%s" height="%s" fill="#fff" opacity="%s"/>'
               '<path d="%s" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/></g>'
               % (p, f(x), f(y), f(w), f(h), ".16" if dark else ".5", bolt))
    _css(doc, """
.$pd{animation:$pd .8s linear infinite}
@keyframes $pd{from{transform:translateY(%sPX)}to{transform:translateY(%sPX)}}
.$pro{animation:$pro 20s ease-in-out infinite}
@keyframes $pro{0%%,44%%{opacity:1}52%%,94%%{opacity:0}100%%{opacity:1}}
.$pgo{opacity:0;animation:$pgo 20s ease-in-out infinite}
@keyframes $pgo{0%%,50%%{opacity:0}62%%,88%%{opacity:1}96%%,100%%{opacity:0}}
.$pfl{opacity:0;animation:$pfl 20s linear infinite}
@keyframes $pfl{0%%,23%%{opacity:0}23.4%%{opacity:1}24.2%%{opacity:0}25%%{opacity:.8}26.4%%,100%%{opacity:0}}
.$pcl{animation:$pcl 60s linear infinite}
@keyframes $pcl{to{transform:translateX(-%sPX)}}
@media (prefers-reduced-motion: reduce){.$pgo{opacity:1}.$pro{opacity:.0}}
""".replace("PX", "px") % (f(y - 24), f(y + h + 4), f(w)), p)
    if label:
        out.append(cap(doc, T, "Live weather layer, from my TV", x + 20, y + 24, 11))
    return "".join(out)


# ----------------------------------------------------------------------------------------------
# 3. packets and a CTF flag
# ----------------------------------------------------------------------------------------------
def handshake(doc, T, x, y, w, h):
    p = _pfx(doc, "hs")
    cy = y + h * 0.6
    xl, xr = x + 34, x + w - 46
    out = ['<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-dasharray="2 5"/>' % (f(xl + 14), f(cy), f(xr - 14), f(cy), T["line"])]
    for cx in (xl, xr):
        out.append('<circle cx="%s" cy="%s" r="13" fill="%s" stroke="%s"/>' % (f(cx), f(cy), T["chip"], T["chipStroke"]))
    # the attacker's terminal and the target's rack
    out.append('<path d="M%s %sl4 3.5-4 3.5M%s %sh6" fill="none" stroke="%s" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'
               % (f(xl - 5), f(cy - 3.5), f(xl), f(cy + 3.5), T["text"]))
    out.append('<g fill="none" stroke="%s" stroke-width="1.4">%s</g>' % (T["text"], "".join(
        '<rect x="%s" y="%s" width="12" height="4" rx="1"/>' % (f(xr - 6), f(cy - 7.5 + 5.5 * j)) for j in range(3))))
    # three packets on one 10 s clock
    run = xr - xl - 60
    legs = [("SYN", T["ok"], 1), ("SYN-ACK", T["ok"], -1), ("ACK", T["ok"], 1)]
    pk, still = [], []
    for i, (lbl, col, sgn) in enumerate(legs):
        c, cw = pill(doc, T, lbl, 0, 0, col)
        x0 = xl + 30 if sgn > 0 else xr - 30
        pk.append('<g transform="translate(%s %s)"><g class="%sk%d">%s</g></g>' % (f(x0), f(cy), p, i, c))
        still.append('<g transform="translate(%s %s)">%s</g>' % (f(xl + 30 + run * (0.15 + 0.35 * i)), f(cy), c))
    out.append('<g class="motion">%s</g><g class="still">%s</g>' % ("".join(pk), "".join(still)))
    # the flag goes up on the target once the handshake is done
    pole_top = y + 6
    fl = ["M%s %sC%s %s %s %s %s %sV%sC%s %s %s %s %s %sZ" % (
        f(xr + 1), f(pole_top), f(xr + 6), f(pole_top - 2 + dy), f(xr + 11), f(pole_top + 2 - dy), f(xr + 17), f(pole_top + dy * .5),
        f(pole_top + 10 + dy * .5), f(xr + 11), f(pole_top + 12 - dy), f(xr + 6), f(pole_top + 8 + dy), f(xr + 1), f(pole_top + 10))
        for dy in (1.4, -1.4)]
    out.append('<g class="%sf"><line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1.4"/>'
               '<path d="%s" fill="%s"><animate attributeName="d" dur="1.2s" repeatCount="indefinite" values="%s;%s;%s"/></path>%s</g>'
               % (p, f(xr + 1), f(cy - 13), f(xr + 1), f(pole_top), T["dim"], fl[0], T["gold"], fl[0], fl[1], fl[0],
                  cap(doc, T, "flag captured", xr - 12, pole_top + 9, 10.5, T["gold"], "end")))
    _css(doc, """
.$pk0,.$pk1,.$pk2{opacity:0}
.$pk0{animation:$pk0 10s cubic-bezier(.45,0,.55,1) infinite}
.$pk1{animation:$pk1 10s cubic-bezier(.45,0,.55,1) infinite}
.$pk2{animation:$pk2 10s cubic-bezier(.45,0,.55,1) infinite}
@keyframes $pk0{0%{opacity:0;transform:none}2%{opacity:1}17%{opacity:1;transform:translateX(RUNpx)}20%,100%{opacity:0;transform:translateX(RUNpx)}}
@keyframes $pk1{0%,21%{opacity:0;transform:none}23%{opacity:1}38%{opacity:1;transform:translateX(-RUNpx)}41%,100%{opacity:0;transform:translateX(-RUNpx)}}
@keyframes $pk2{0%,42%{opacity:0;transform:none}44%{opacity:1}59%{opacity:1;transform:translateX(RUNpx)}62%,100%{opacity:0;transform:translateX(RUNpx)}}
.$pf{transform-box:view-box;transform-origin:XRpx CYpx;animation:$pf 10s cubic-bezier(.2,.8,.2,1) infinite}
@keyframes $pf{0%,62%{opacity:0;transform:scaleY(.2)}70%{opacity:1;transform:none}93%{opacity:1;transform:none}98%,100%{opacity:0;transform:none}}
""".replace("RUN", f(run)).replace("CY", f(cy - 13)).replace("XR", f(xr + 1)), p)
    return "".join(out)


# ----------------------------------------------------------------------------------------------
# 4. an agent drives a phone; R4 is held at the gate
# ----------------------------------------------------------------------------------------------
def agent_phone(doc, T, x, y, w, h):
    p = _pfx(doc, "ap")
    cy = y + h * 0.54
    ax, gx, px = x + 34, x + w * 0.6, x + w - 58
    out = ['<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-dasharray="2 5"/>' % (f(ax + 16), f(cy), f(px - 18), f(cy), T["line"])]
    # the agent: a glass node with a four-point spark
    out.append('<circle cx="%s" cy="%s" r="14" fill="%s" stroke="%s"/>' % (f(ax), f(cy), T["chip"], T["chipStroke"]))
    out.append('<path d="M%s %sq1.2 4.8 6 6-4.8 1.2-6 6q-1.2-4.8-6-6 4.8-1.2 6-6z" fill="%s" class="%ssp"/>' % (f(ax), f(cy - 6), T["gold"], p))
    # the gate
    out.append('<rect x="%s" y="%s" width="4" height="30" rx="2" fill="%s"/>' % (f(gx - 2), f(cy - 15), T["line"]))
    out.append('<rect x="%s" y="%s" width="4" height="30" rx="2" fill="%s" class="%sgf"/>' % (f(gx - 2), f(cy - 15), T["danger"], p))
    out.append('<g class="%sgf">%s</g>' % (p, cap(doc, T, "held for approval", gx + 9, cy - 16, 10, T["danger"])))
    # the phone and its six app tiles
    pw, ph = 28, min(50, h - 10)
    out.append('<rect x="%s" y="%s" width="%s" height="%s" rx="6" fill="%s" stroke="%s" stroke-width="1.3"/>'
               % (f(px - pw / 2), f(cy - ph / 2), pw, f(ph), T["chip"], T["dim"]))
    tiles = []
    for j in range(6):
        tx, ty = px - 8 + (j % 2) * 9, cy - ph / 2 + 9 + (j // 2) * 10
        tiles.append((tx, ty))
        out.append('<rect x="%s" y="%s" width="7" height="7" rx="2" fill="%s" fill-opacity=".22"/>' % (f(tx), f(ty), T["text"]))
    tx, ty = tiles[3]
    out.append('<rect x="%s" y="%s" width="7" height="7" rx="2" fill="%s" class="%slit"/>' % (f(tx), f(ty), T["ok"], p))
    out.append('<g transform="translate(%s %s)"><circle r="7" fill="none" stroke="%s" stroke-width="1.4" class="%stap"/></g>'
               % (f(tx + 3.5), f(ty + 3.5), T["ok"], p))
    # the cursor travels from the agent to that tile and taps it
    cur = ('<path d="M0 0V14L3.6 10.6 6.2 16.2 8.4 15.2 5.8 9.8H10.6Z" fill="%s" stroke="%s" stroke-width="1" stroke-linejoin="round"/>'
           % (T["text"], T["ink"]))
    cx0, cy0, cx1, cy1 = ax + 18, cy - 10, tx + 3.5, ty + 3.5
    out.append('<g transform="translate(%s %s)"><g class="%scu">%s</g></g>' % (f(cx1), f(cy1), p, cur))
    c, cwid = pill(doc, T, "R4 · delete", 0, 0, T["danger"])
    stop = gx - 6 - cwid / 2
    out.append('<g transform="translate(%s %s)"><g class="%sr4">%s</g></g>' % (f(stop), f(cy), p, c))
    _css(doc, """
.$pcu{transform-box:fill-box;transform-origin:0 0;animation:$pcu 11s cubic-bezier(.45,0,.2,1) infinite}
@keyframes $pcu{0%,4%{opacity:0;transform:translate(DXpx,DYpx)}7%{opacity:1;transform:translate(DXpx,DYpx)}23%{transform:none}25%{transform:scale(.88)}28%{transform:none;opacity:1}42%{opacity:1}47%,100%{opacity:0;transform:none}}
.$ptap{transform-box:fill-box;transform-origin:center;opacity:0;animation:$ptap 11s ease-out infinite}
@keyframes $ptap{0%,24%{opacity:0;transform:scale(.3)}25%{opacity:1}34%,100%{opacity:0;transform:scale(1.9)}}
.$plit{animation:$plit 11s ease-in-out infinite}
@keyframes $plit{0%,24%{opacity:0}27%,46%{opacity:1}52%,100%{opacity:0}}
.$pr4{animation:$pr4 11s cubic-bezier(.45,0,.55,1) infinite}
@keyframes $pr4{0%,50%{opacity:0;transform:translateX(-RUNpx)}53%{opacity:1}66%{transform:none;opacity:1}92%{opacity:1;transform:none}96%,100%{opacity:0;transform:none}}
.$pgf{animation:$pgf 11s linear infinite}
@keyframes $pgf{0%,65%{opacity:0}67%,92%{opacity:1}95%,100%{opacity:0}}
.$psp{transform-box:fill-box;transform-origin:center;animation:$psp 3.6s ease-in-out infinite}
@keyframes $psp{50%{transform:rotate(45deg) scale(.8)}}
""".replace("DX", f(cx0 - cx1)).replace("DY", f(cy0 - cy1)).replace("RUN", f(stop - ax - 22 - cwid / 2)), p)
    return "".join(out)


# ----------------------------------------------------------------------------------------------
# 5. Concorde off a wet runway
# ----------------------------------------------------------------------------------------------
CONCORDE = ("M0-1.4L5-2.4 62-2.9 82-2.5 93-1.5 99.5 .2 103 1.6 99 1.9 92 2.3 80 2.6 61 2.8 55 3.2 55 6.4 30 6.4 28 3.4 10 2.6 0 1.6Z"
            "M2.5-2 8.6-15.5H13.6L24-2.6Z")


def concorde(doc, T, x, y, w, h, label=True):
    p = _pfx(doc, "cc")
    ry = y + h * 0.74                          # the runway line
    s = 1.55
    out = []
    # the wet runway: edge lights, their reflections, and a sheen band under the line
    doc.defs.append('<linearGradient id="%sw" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="%s" stop-opacity=".1"/>'
                    '<stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient>' % (p, T["acc"], T["acc"]))
    out.append('<rect x="%s" y="%s" width="%s" height="%s" fill="url(#%sw)"/>' % (f(x), f(ry), f(w), f(y + h - ry), p))
    out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s"/>' % (f(x), f(ry), f(x + w), f(ry), T["line"]))
    lb = _blur(doc, p + "l", 1.6)
    lights = "".join('<circle cx="%s" cy="%s" r="1.6"/>' % (f(x + 14 + 34 * i), f(ry - 2)) for i in range(int(w / 34)))
    refl = "".join('<ellipse cx="%s" cy="%s" rx="1.6" ry="5"/>' % (f(x + 14 + 34 * i), f(ry + 7)) for i in range(int(w / 34)))
    out.append('<g fill="%s">%s</g><g fill="%s" opacity=".35" filter="url(#%s)">%s</g>' % (T["gold"], lights, T["gold"], lb, refl))
    out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-opacity=".5" stroke-dasharray="18 22" class="%scl"/>'
               % (f(x), f(ry + 9), f(x + w), f(ry + 9), T["dim"], p))
    _css(doc, ".$pcl{animation:$pcl 1.1s linear infinite}@keyframes $pcl{to{stroke-dashoffset:40}}"
              ".$psh{animation:$psh .45s ease-in-out infinite alternate}@keyframes $psh{to{transform:translate(-2px,.6px);opacity:.35}}", p)
    # the aircraft, nose right, wheels on the line; heat shimmer behind the four engines
    shimmer = "".join('<path d="M%s %sq-6-1.4-12 0t-12 0" fill="none" stroke="%s" stroke-opacity=".4" stroke-width="1" class="%ssh" '
                      'style="animation-delay:-%ss"/>' % (f(28), f(4 + 1.6 * j), T["dim"], p, f(j * .15, 2)) for j in range(3))
    plane = ('<g transform="translate(%s %s) scale(%s)"><path d="%s" fill="%s"/>'
             '<path d="M24 1.8H64" stroke="%s" stroke-opacity=".25" stroke-width=".8"/>%s</g>'
             % (f(-42 * s), f(-6.4 * s), f(s, 2), CONCORDE, T["text"], T["ink"], shimmer))   # pivots on the main gear
    doc.defs.append('<g id="%sp">%s</g>' % (p, plane))
    # one 12 s take-off: roll, rotate, climb out to the right; the reflection mirrors it in the wet runway
    x0, xr_, x1 = x - 40, x + w * 0.5, x + w + 220
    kt = "0;.42;.52;.9;1"
    tr = "%s %s;%s %s;%s %s;%s %s;%s %s" % (f(x0), f(ry), f(xr_), f(ry), f(xr_ + 90), f(ry - 8), f(x1), f(y - 30), f(x1), f(y - 30))
    rot = "0;0;-9;-13;-13"
    motion = ('<g><animateTransform attributeName="transform" type="translate" values="%s" keyTimes="%s" dur="12s" '
              'repeatCount="indefinite" calcMode="spline" keySplines=".5 0 .9 .6;.3 0 .7 1;.4 0 .7 1;0 0 1 1"/>'
              '<g><animateTransform attributeName="transform" type="rotate" values="%s" keyTimes="%s" dur="12s" repeatCount="indefinite"/>'
              '<use href="#%sp"/></g></g>' % (tr, kt, rot, kt, p))
    rb = _blur(doc, p + "r", 1.2)
    out.append('<g class="motion">%s<g transform="translate(0 %s) scale(1 -1)" opacity=".22" filter="url(#%s)">%s</g></g>'
               % (motion, f(2 * ry), rb, motion))
    out.append('<g class="still"><g transform="translate(%s %s) rotate(-9)"><use href="#%sp"/></g></g>' % (f(xr_ + 120), f(ry - 16), p))
    if label:
        out.append(cap(doc, T, "Concorde, wet runway", x + 20, y + 26, 11))
    return "".join(out)


# ----------------------------------------------------------------------------------------------
# 6. the helmet: original line art (a crested Greek helmet, front view), drawn on, then a light sweep
# ----------------------------------------------------------------------------------------------
def _mirror(pts):
    return [(100 - px, py) for px, py in pts]


HELMET_SHELL_R = [(56.5, 95), (64, 93.5), (71.5, 87), (76.5, 75), (78.8, 61), (78, 46), (74, 34.5), (66.5, 26.5), (58, 22.6), (50, 21.6)]
HELMET_OPEN_R = [(56.4, 95), (55.6, 76), (56, 62), (58.6, 58.4), (67, 57.2), (73.2, 54.2), (73.4, 50.2), (67, 47.6), (58, 47.8), (53, 48.6)]


def helmet(doc, T, x, y, w, h):
    p = _pfx(doc, "hm")
    s = min(w, h) / 100 * 0.92
    ox, oy = x + (w - 100 * s) / 2, y + (h - 100 * s) / 2
    shell = cr(HELMET_SHELL_R + list(reversed(_mirror(HELMET_SHELL_R)))[1:], closed=False)
    # the opening as one stroke: up from the left cheek's tip and round the left eye, down and back up the nose guard,
    # then round the right eye and down to the right cheek's tip (the dash runs on across the subpaths)
    opening = (cr(_mirror(HELMET_OPEN_R), closed=False) + "L47 67L50 69.6L53 67L53 48.6" +
               cr(list(reversed(HELMET_OPEN_R)), closed=False))
    brow = "M23 44.5C35 38 65 38 77 44.5"
    cheek = "M30 64C34 70 37 78 38 88M70 64C66 70 63 78 62 88"
    crest = "M42 22.4C38 12 43 4.2 50 2.6C57 4.2 62 12 58 22.4"
    strands = "M50 21V4.4M46.5 21.4C44.5 14 46 8 48.2 4.4M53.5 21.4C55.5 14 54 8 51.8 4.4"
    paths = [(crest, 0.0), (strands, 0.06), (shell, 0.1), (brow, 0.26), (opening, 0.3), (cheek, 0.42)]
    draw = []
    for k, (d, dl) in enumerate(paths):
        draw.append('<path d="%s" pathLength="1" class="%sd" style="animation-delay:%ss"/>' % (d, p, f(dl * 10, 2)))
    g = "".join(draw)
    # the sweep: a bright band crossing the drawing, masked to the strokes themselves
    doc.defs.append('<linearGradient id="%sb" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                    '<stop offset=".5" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>' % p)
    doc.defs.append('<mask id="%sm" maskUnits="userSpaceOnUse" x="-40" y="-10" width="180" height="120"><g class="%sw">'
                    '<rect x="-60" y="-10" width="34" height="130" fill="url(#%sb)" transform="skewX(-18)"/></g></mask>' % (p, p, p))
    tf = 'transform="translate(%s %s) scale(%s)"' % (f(ox, 2), f(oy, 2), f(s, 4))
    out = ['<g %s fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round">%s</g>'
           % (tf, T["gold"], f(2.0 / s, 3), g),
           '<g %s><g mask="url(#%sm)" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round">%s</g></g>'
           % (tf, p, "#ffffff" if T["name"] == "dark" else T["text"], f(2.6 / s, 3),
              "".join('<path d="%s"/>' % d for d, _ in paths))]
    _css(doc, """
.$pd{stroke-dasharray:1;animation:$pd 10s cubic-bezier(.6,0,.3,1) infinite}
@keyframes $pd{0%{stroke-dashoffset:1;opacity:1}28%{stroke-dashoffset:0}90%{stroke-dashoffset:0;opacity:1}97%,100%{stroke-dashoffset:0;opacity:0}}
.$pw{transform:translateX(200px);animation:$pw 10s ease-in-out infinite}
@keyframes $pw{0%,44%{transform:translateX(0)}70%,100%{transform:translateX(200px)}}
""", p)
    return "".join(out)


# ----------------------------------------------------------------------------------------------
# 7. the token odometer
# ----------------------------------------------------------------------------------------------
def tokens(doc, T, x, y, w, h, total, as_of):
    """Rolls up to the measured total, e.g. 50,419,188,685 -> 50.4 B. Without a number, the wheels just turn."""
    p = _pfx(doc, "tk")
    size = min(h * 0.62, 78)
    num = font("num")
    lh = size * 1.06
    chars = ("%.1f" % (total / 1e9)) if total else "88.8"
    cw = num.width("0", size)
    dw = num.width(".", size)
    widths = [dw if c == "." else cw for c in chars]
    sw = font("cap").width("B", size * 0.36)
    tot_w = sum(widths) + 6 + sw
    x0 = x + (w - tot_w) / 2
    base = y + h * 0.5 + size * 0.36
    gb = _blur(doc, p + "g", 6)
    _clip(doc, p + "c", x0 - 6, base - size * 1.0, tot_w + 12, size * 1.04, 6)   # one digit tall: no neighbour shows
    cols, cx, css = [], x0, []
    for i, (c, cwid) in enumerate(zip(chars, widths)):
        if c == ".":
            cols.append(doc.text(".", cx, base, "num", size, T["text"])[0])
        else:
            dgt = int(c)
            strip = "".join(doc.text(str(k % 10), cx, base - lh * k, "num", size, T["text"])[0] for k in range(0, 21))
            final = dgt + 10                    # one full turn, then land on the digit
            cols.append('<g class="%sc%d" style="transform:translateY(%spx)">%s</g>' % (p, i, f(lh * final, 2), strip))
            if total:
                css.append("@keyframes $pc%d{0%%{transform:translateY(0);opacity:0}3%%{opacity:1}%s%%,94%%{transform:translateY(%spx);opacity:1}"
                           "99%%,100%%{transform:translateY(%spx);opacity:0}}"
                           ".$pc%d{animation:$pc%d 12s cubic-bezier(.2,.75,.25,1) infinite}"
                           % (i, f(26 + 5 * i), f(lh * final, 2), f(lh * final, 2), i, i))
            else:
                css.append("@keyframes $pc%d{to{transform:translateY(%spx)}}.$pc%d{animation:$pc%d %ss linear infinite}"
                           % (i, f(lh * 10, 2), i, i, f(2.5 + i, 2)))
        cx += cwid
    sfx = doc.text("B", cx + 6, base, "cap", size * 0.36, T["gold"])[0]
    digits = "".join(cols)
    out = ['<g filter="url(#%sg)" opacity=".45"><g clip-path="url(#%sc)" fill="%s">%s</g></g>' % (p, p, T["gold"], digits.replace(T["text"], T["gold"])),
           '<g clip-path="url(#%sc)">%s</g>' % (p, digits), sfx]
    _css(doc, "\n".join(css), p)
    out.append(cap(doc, T, "Claude Code tokens", x + w / 2, y + 22, 11, T["dim"], "middle"))
    if total:
        out.append(cap(doc, T, "measured, to %s" % as_of, x + w / 2, y + h - 10, 10, T["faint"], "middle"))
    return "".join(out)


# ----------------------------------------------------------------------------------------------
# 8. a BB chevron and a Taekwondo black-belt knot, drawn in gold
# ----------------------------------------------------------------------------------------------
def bb_tkd(doc, T, x, y, w, h):
    p = _pfx(doc, "bt")
    s = min(w / 2, h) / 100 * 0.98
    lx, rx = x + w * 0.27, x + w * 0.71
    cy = y + h * 0.48
    # the chevron: two nested Vs, point down
    chev = ["M%s %sL%s %sL%s %s" % (f(lx - 30 * s), f(cy - 20 * s + o * s), f(lx), f(cy + 6 * s + o * s), f(lx + 30 * s), f(cy - 20 * s + o * s))
            for o in (0, 14)]
    # the knot: the belt's two layers either side, the square knot, two tails falling away, a stripe near each end
    k = lambda px, py: (f(rx + px * s), f(cy + py * s))
    knot = [
        "M%s %sH%s M%s %sH%s" % (k(-44, -9)[0], k(-44, -9)[1], k(-9, -9)[0], k(-44, 1)[0], k(-44, 1)[1], k(-9, 1)[0]),
        "M%s %sH%s M%s %sH%s" % (k(9, -9)[0], k(9, -9)[1], k(44, -9)[0], k(9, 1)[0], k(9, 1)[1], k(44, 1)[0]),
        "M%s %sL%s %sL%s %sL%s %sZ" % (k(-9, -12) + k(9, -12) + k(10, 4) + k(-10, 4)),
        "M%s %sL%s %s" % (k(-9, -12) + k(10, 4)),
        "M%s %sL%s %sL%s %sL%s %s" % (k(-6, 4) + k(-20, 34) + k(-12, 37) + k(-1, 4)),
        "M%s %sL%s %sL%s %sL%s %s" % (k(6, 4) + k(22, 32) + k(30, 27) + k(1, 4)),
        "M%s %sL%s %sM%s %sL%s %s" % (k(-17.5, 27.5) + k(-10.5, 30.8) + k(19, 25.5) + k(25.6, 21.8)),
    ]
    paths = [(d, .0 + .05 * i) for i, d in enumerate(chev)] + [(d, .22 + .05 * i) for i, d in enumerate(knot)]
    g = "".join('<path d="%s" pathLength="1" class="%sd" style="animation-delay:%ss"/>' % (d, p, f(dl * 10, 2)) for d, dl in paths)
    gb = _blur(doc, p + "g", 2.4)
    out = ['<g fill="none" stroke="%s" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" opacity=".4" filter="url(#%s)">%s</g>'
           % (T["gold"], gb, g.replace('class="%sd"' % p, 'class="%sd"' % p)),
           '<g fill="none" stroke="%s" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">%s</g>' % (T["gold"], g),
           cap(doc, T, "Boys' Brigade", lx, y + h - 8, 10.5, T["dim"], "middle"),
           cap(doc, T, "Taekwondo", rx, y + h - 8, 10.5, T["dim"], "middle")]
    _css(doc, """
.$pd{stroke-dasharray:1;animation:$pd 10s cubic-bezier(.6,0,.3,1) infinite}
@keyframes $pd{0%{stroke-dashoffset:1;opacity:1}22%{stroke-dashoffset:0}90%{stroke-dashoffset:0;opacity:1}97%,100%{stroke-dashoffset:0;opacity:0}}
""", p)
    return "".join(out)
