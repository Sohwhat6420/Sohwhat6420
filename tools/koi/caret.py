"""Clawd as the typing line's caret (11 Nov 2026, his call): one text line high, he stands straight after the last typed
letter and moves with it. Typing forward he scurries right; at each hold and each rest he turns to face the viewer, does a
few happy hops holding the RAM and the GPU, turns toward the way he goes next, and scurries again.

Everything is the same SMIL + CSS the rest of the typing line already uses (it renders in an <img>, so nothing is fetched
and no script runs): the sprites are base64 PNGs (tools/koi/clawd_caret_sprites.py, built by the career-2027 avatar
tools), the position is one SMIL translate in discrete steps, and each pose is a group faded in and out with CSS. A turn is
a quick squash to a third of the width at the moment the pose changes.
"""
import clawd_caret_sprites as S

BASE = 43.0          # his feet, in the typing SVG's user units (the text baseline is 36)
RUN_H = S.RUN_H / 2  # 28 high
TURN = 0.07          # seconds each side of a pose change that he squashes
HOP = 0.44           # one hop, launch to landing
APEX = 7.0           # hop height in user units


def _f(v, n=3):
    s = ("%." + str(n) + "f") % v
    return s.rstrip("0").rstrip(".") if "." in s else s


def _pct(t, cycle):
    return _f(100.0 * t / cycle, 4) + "%"


def _img(sp, x, y, extra=""):
    b64, w, h = sp
    return '<image href="data:image/png;base64,%s" x="%s" y="%s" width="%s" height="%s"%s/>' % (
        b64, _f(x, 2), _f(y, 2), _f(w / 2.0, 2), _f(h / 2.0, 2), extra)


def front(arm_cls=True):
    """The front view standing on BASE with its left edge at x=0: the mascot, the GPU held on his left, the RAM on his right."""
    mw, mh = S.MASCOT[1] / 2.0, S.MASCOT[2] / 2.0
    gw, gh = S.GPU[1] / 2.0, S.GPU[2] / 2.0
    rw, rh = S.RAM[1] / 2.0, S.RAM[2] / 2.0
    mx = gw - 3.0
    body = _img(S.MASCOT, mx, BASE - mh)
    gpu = _img(S.GPU, 0, BASE - 5 - gh, ' class="arm gp"' if arm_cls else "")
    ram = _img(S.RAM, mx + mw - 2.5, BASE - 5 - rh, ' class="arm rm"' if arm_cls else "")
    return body + gpu + ram, mx + mw - 2.5 + rw


def run_sprite(sp, cell, cls):
    """A nested svg one cell wide: the sheet slides left in 8 steps inside it."""
    b64, w, h = sp
    cw, ch = cell / 2.0, h / 2.0
    return ('<svg x="0" y="%s" width="%s" height="%s" viewBox="0 0 %d %d">%s</svg>'
            % (_f(BASE - ch, 2), _f(cw, 2), _f(ch, 2), cell, h,
               '<image class="%s" href="data:image/png;base64,%s" x="0" y="0" width="%d" height="%d"/>' % (cls, b64, w, h)))


def build(doc, T, cycle, xkt, xvals, segs):
    """segs: list of (kind, start, end) in seconds, kind R (run right), L (run left) or F (front, hopping), covering the
    whole cycle in order. Returns the <g> to append to the motion group; adds its CSS to doc.css."""
    cols = {"R": [], "L": [], "F": []}
    for kind, a, b in segs:
        cols[kind].append((a, b))
    css = []

    # which pose is showing: steps, so each keyframe holds until the next
    for kind, name in (("R", "oR"), ("L", "oL"), ("F", "oF")):
        stops, cur = [], None
        times = sorted({0.0} | {a for a, b in cols[kind]} | {b for a, b in cols[kind]})
        for t in times:
            on = any(a <= t + 1e-9 < b - 1e-9 for a, b in cols[kind])
            if on != cur:
                stops.append("%s{opacity:%d}" % (_pct(t, cycle), 1 if on else 0))
                cur = on
        css.append("@keyframes %s{%s}" % (name, "".join(stops)))
    # the turn squash: to a third of the width on both sides of each change of pose
    for kind, name in (("R", "qR"), ("L", "qL"), ("F", "qF")):
        pts = {0.0: 1.0, cycle: 1.0}
        for a, b in cols[kind]:
            if a > 1e-9:
                pts[a] = 0.3
                pts.setdefault(min(a + TURN, b), 1.0)
            if b < cycle - 1e-9:
                pts[b] = 0.3
                pts.setdefault(max(b - TURN, a), 1.0)
        stops = "".join("%s{transform:scaleX(%s)}" % (_pct(t, cycle), _f(v, 2)) for t, v in sorted(pts.items()))
        css.append("@keyframes %s{%s}" % (name, stops))

    # hops: launch squash, up, down, landing squash; the GPU and RAM lift and tilt at the top
    hop, arm_g, arm_r = [], [], []
    for a, b in cols["F"]:
        lo, hi = a + 0.12, b - 0.10
        n = int((hi - lo) / HOP)
        hop.append((a, "translateY(0) scaleY(1)", ""))
        arm_g.append((a, "translateY(0) rotate(0deg)", ""))
        arm_r.append((a, "translateY(0) rotate(0deg)", ""))
        for k in range(n):
            s = lo + k * HOP
            hop += [(s, "translateY(0) scaleY(.93)", "cubic-bezier(.2,.8,.3,1)"),
                    (s + 0.05, "translateY(0) scaleY(1.04)", "cubic-bezier(.25,.6,.4,1)"),
                    (s + HOP / 2, "translateY(-%spx) scaleY(1.04)" % _f(APEX, 1), "cubic-bezier(.6,0,.85,.45)"),
                    (s + HOP, "translateY(0) scaleY(.93)", "ease-out")]
            arm_g += [(s, "translateY(0) rotate(0deg)", "ease-out"),
                      (s + HOP / 2, "translateY(-4px) rotate(-14deg)", "ease-in"),
                      (s + HOP, "translateY(0) rotate(0deg)", "ease-out")]
            arm_r += [(s, "translateY(0) rotate(0deg)", "ease-out"),
                      (s + HOP / 2, "translateY(-4px) rotate(14deg)", "ease-in"),
                      (s + HOP, "translateY(0) rotate(0deg)", "ease-out")]
        if n:
            last = lo + n * HOP
            hop.append((last + 0.06, "translateY(0) scaleY(1)", ""))
            arm_g.append((last + 0.06, "translateY(0) rotate(0deg)", ""))
            arm_r.append((last + 0.06, "translateY(0) rotate(0deg)", ""))
        hop.append((b, "translateY(0) scaleY(1)", ""))
        arm_g.append((b, "translateY(0) rotate(0deg)", ""))
        arm_r.append((b, "translateY(0) rotate(0deg)", ""))

    def kf(name, rows):
        rows = sorted(rows, key=lambda r: r[0])
        out = []
        for t, v, tf in rows:
            out.append("%s{transform:%s%s}" % (_pct(t, cycle), v, (";animation-timing-function:" + tf) if tf else ""))
        css.append("@keyframes %s{%s}" % (name, "".join(out)))

    kf("hop", hop)
    kf("armg", arm_g)
    kf("armr", arm_r)
    c = _f(cycle, 3)
    css.append(".cl{transform-box:fill-box;transform-origin:50%% 100%%}"
               ".cR{animation:oR %ss steps(1,end) infinite,qR %ss linear infinite;opacity:0}"
               ".cL{animation:oL %ss steps(1,end) infinite,qL %ss linear infinite;opacity:0}"
               ".cF{animation:oF %ss steps(1,end) infinite,qF %ss linear infinite;opacity:0}"
               ".hp{transform-box:fill-box;transform-origin:50%% 100%%;animation:hop %ss linear infinite}"
               ".arm{transform-box:fill-box;transform-origin:50%% 50%%}"
               ".gp{animation:armg %ss linear infinite}.rm{animation:armr %ss linear infinite}"
               ".rr{animation:rr .34s steps(8) infinite}.ll{animation:ll .21s steps(8) infinite}"
               "@keyframes rr{to{transform:translateX(-%dpx)}}@keyframes ll{to{transform:translateX(-%dpx)}}"
               % (c, c, c, c, c, c, c, c, c, S.RIGHT_CELL * 8, S.LEFT_CELL * 8))
    doc.css.extend(css)

    fr, fw = front()
    right = run_sprite(S.RIGHT, S.RIGHT_CELL, "rr")
    left = run_sprite(S.LEFT, S.LEFT_CELL, "ll")
    pos = ('<animateTransform attributeName="transform" type="translate" dur="%ss" repeatCount="indefinite" '
           'calcMode="discrete" keyTimes="%s" values="%s"/>' % (c, ";".join(xkt), ";".join("%s 0" % v for v in xvals)))
    return ('<g class="clawd" aria-hidden="true">%s<g transform="translate(1 0)">'
            '<g class="cl cR">%s</g><g class="cl cL">%s</g><g class="cl cF"><g class="hp">%s</g></g></g></g>'
            % (pos, right, left, fr))


def still(x):
    """The reduced-motion picture: Clawd standing after the line, facing the viewer, GPU and RAM at his sides."""
    fr, fw = front(arm_cls=False)
    return '<g transform="translate(%s 0)">%s</g>' % (_f(x, 2), fr)
