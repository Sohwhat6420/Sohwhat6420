"""Shared helpers for the profile SVGs: outlined text, smooth paths, the koi and the pond.

Everything is drawn as vector paths so the SVGs need no fonts or network at render time
(GitHub serves README images with a strict CSP, so nothing may be fetched from inside them).
Fonts: Instrument Serif, Instrument Sans and JetBrains Mono, all SIL OFL 1.1 (see tools/fonts).
"""
import math
import os
import random

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")


# ----------------------------------------------------------------------------------------------
# numbers and paths
# ----------------------------------------------------------------------------------------------
def f(v, nd=1):
    s = ("%." + str(nd) + "f") % v
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if s in ("-0", ""):
        s = "0"
    return s


def pts_str(*pp):
    out = " ".join(f(c) for p in pp for c in p)
    return out.replace(" -", "-")


def cr(pts, closed=True):
    """Catmull-Rom spline through pts as cubic Beziers. Same command structure for same len(pts)."""
    n = len(pts)
    P = list(pts)
    if not closed:
        P = [P[0]] + P + [P[-1]]
        segs = range(1, n)
        out = "M" + pts_str(P[1])
        for i in segs:
            p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
            c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
            c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
            out += "C" + pts_str(c1, c2, p2)
        return out
    out = "M" + pts_str(P[0])
    for i in range(n):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % n], P[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        out += "C" + pts_str(c1, c2, p2)
    return out + "Z"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# ----------------------------------------------------------------------------------------------
# fonts: outlined glyphs shared through <defs>, laid out with GPOS pair kerning
# ----------------------------------------------------------------------------------------------
class Font:
    def __init__(self, key, filename):
        self.key = key
        self.tt = TTFont(os.path.join(FONT_DIR, filename))
        self.gs = self.tt.getGlyphSet()
        self.cmap = self.tt.getBestCmap()
        self.upm = self.tt["head"].unitsPerEm
        self.hmtx = self.tt["hmtx"]
        self._paths = {}
        self._pair = {}
        self._class = []
        self._load_kern()
        self.ids = {}

    def _load_kern(self):
        if "GPOS" not in self.tt:
            return
        gpos = self.tt["GPOS"].table
        idx = set()
        for fr in gpos.FeatureList.FeatureRecord:
            if fr.FeatureTag == "kern":
                idx.update(fr.Feature.LookupListIndex)
        for li in sorted(idx):
            lk = gpos.LookupList.Lookup[li]
            for st in lk.SubTable:
                if lk.LookupType == 9:
                    st = st.ExtSubTable
                if getattr(st, "LookupType", 2) != 2:
                    continue
                cov = st.Coverage.glyphs
                if st.Format == 1:
                    for g1, ps in zip(cov, st.PairSet):
                        for rec in ps.PairValueRecord:
                            v = getattr(rec.Value1, "XAdvance", 0) if rec.Value1 else 0
                            self._pair.setdefault((g1, rec.SecondGlyph), v or 0)
                elif st.Format == 2:
                    self._class.append((set(cov), st.ClassDef1.classDefs, st.ClassDef2.classDefs, st.Class1Record))

    def kern(self, a, b):
        if (a, b) in self._pair:
            return self._pair[(a, b)]
        for cov, cd1, cd2, recs in self._class:
            if a in cov:
                c1 = cd1.get(a, 0)
                c2 = cd2.get(b, 0)
                v = recs[c1].Class2Record[c2].Value1
                return (getattr(v, "XAdvance", 0) or 0) if v else 0
        return 0

    def glyph(self, ch):
        g = self.cmap.get(ord(ch))
        if g is None:
            raise KeyError("glyph missing for %r in %s" % (ch, self.key))
        return g

    def adv(self, g):
        return self.hmtx[g][0]

    def path(self, g):
        if g not in self._paths:
            pen = SVGPathPen(self.gs, ntos=lambda v: f(v, 0))
            self.gs[g].draw(pen)
            self._paths[g] = pen.getCommands()
        return self._paths[g]

    def layout(self, s, size, tracking=0.0):
        """Return [(glyph, x_in_font_units)], width_px. tracking is in em."""
        gl = [self.glyph(c) for c in s]
        tr = tracking * self.upm
        xs, cur = [], 0.0
        for i, g in enumerate(gl):
            xs.append(cur)
            cur += self.adv(g) + tr
            if i + 1 < len(gl):
                cur += self.kern(g, gl[i + 1])
        width = (cur - tr) * size / self.upm if gl else 0
        return list(zip(gl, xs)), width

    def width(self, s, size, tracking=0.0):
        return self.layout(s, size, tracking)[1]


FONTS = {}


def font(key):
    files = {
        "serif": "InstrumentSerif-Regular.ttf",
        "sans": "InstrumentSans-Regular.ttf",
        "sansb": "InstrumentSans-Bold.ttf",
        "mono": "JetBrainsMono-Regular.ttf",
        "monob": "JetBrainsMono-Bold.ttf",
    }
    if key not in FONTS:
        FONTS[key] = Font(key, files[key])
    return FONTS[key]


class Doc:
    """Collects defs (glyphs, gradients, patterns) and the CSS for one SVG."""

    def __init__(self, w, h, title, desc=""):
        self.w, self.h = w, h
        self.title, self.desc = title, desc
        self.defs = []
        self.glyphs = {}
        self.css = []
        self.body = []
        self._n = 0

    def uid(self, p="i"):
        self._n += 1
        return "%s%d" % (p, self._n)

    def gid(self, fnt, g):
        k = (fnt.key, g)
        if k not in self.glyphs:
            self.glyphs[k] = "%s%d" % (fnt.key[0] + fnt.key[-1], len(self.glyphs))
        return self.glyphs[k]

    def text(self, s, x, y, key, size, fill, tracking=0.0, anchor="start", cls=None, opacity=None, extra=""):
        fnt = font(key)
        gl, width = fnt.layout(s, size, tracking)
        if anchor == "end":
            x -= width
        elif anchor == "middle":
            x -= width / 2
        sc = size / fnt.upm
        uses = []
        for g, gx in gl:
            if not fnt.path(g):
                continue
            uses.append('<use href="#%s" x="%s"/>' % (self.gid(fnt, g), f(gx, 0)))
        attrs = ' fill="%s"' % fill
        if cls:
            attrs += ' class="%s"' % cls
        if opacity is not None:
            attrs += ' opacity="%s"' % f(opacity, 2)
        inner = '<g transform="translate(%s %s) scale(%s %s)">%s</g>' % (f(x, 2), f(y, 2), f(sc, 5), f(-sc, 5), "".join(uses))
        return '<g%s%s>%s</g>' % (attrs, extra, inner), width

    def render(self):
        glyph_defs = []
        for (key, g), gid in self.glyphs.items():
            glyph_defs.append('<path id="%s" d="%s"/>' % (gid, font(key).path(g)))
        css = "\n".join(self.css)
        out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" aria-labelledby="t d">'
               % (self.w, self.h, self.w, self.h),
               '<title id="t">%s</title><desc id="d">%s</desc>' % (esc(self.title), esc(self.desc)),
               "<style><![CDATA[\n%s\n]]></style>" % css,
               "<defs>%s%s</defs>" % ("".join(glyph_defs), "".join(self.defs)),
               "".join(self.body),
               "</svg>"]
        return "\n".join(out)


REDUCED = """
@media (prefers-reduced-motion: reduce){
  *{animation:none!important}
  .motion{display:none}
  .still{display:inline!important}
}
.still{display:none}
"""

# ----------------------------------------------------------------------------------------------
# themes
# ----------------------------------------------------------------------------------------------
THEMES = {
    "dark": dict(
        name="dark",
        bgA="#0f3b45", bgB="#0a2730", bgC="#04121a",
        pebbles=["#0b2c35", "#124049", "#08222a", "#0e343d"],
        caustic="#a8efe0", cau1=0.085, cau2=0.06,
        tint="#0a2a33", tintOp=0.42,
        text="#f4ecdc", dim="#a3c1bd", faint="#5f8a8a", gold="#dcb25e", accent="#f07a45", danger="#ff7a6b",
        ok="#7fd1b0",
        padEdge="#285f40", padMid="#3e8957", padVein="#86c896", padRim="#5aa36e",
        lotusA="#fbe7e1", lotusB="#ec9fa5", lotusC="#f2c94c",
        shadow=(0.01, 0.05, 0.07, 0.55),
        scrim="#051820", scrimOp=0.88,
        glint="#ffffff",
        card="#0a222b", cardHi="#0d2b35", stroke="#1d4a55", chip="#0f313b", chipStroke="#285c67",
        line="#2a5b66",
    ),
    "light": dict(
        name="light",
        bgA="#dcefe9", bgB="#b4d9d1", bgC="#86b9b2",
        pebbles=["#a6d0c8", "#c3e2db", "#93c2ba", "#b2d6ce"],
        caustic="#ffffff", cau1=0.28, cau2=0.18,
        tint="#b9dcd4", tintOp=0.3,
        text="#0b2530", dim="#33575d", faint="#6a8e90", gold="#8a6416", accent="#bf4d1b", danger="#c2362b",
        ok="#1f7a5a",
        padEdge="#3c8550", padMid="#5ea866", padVein="#b4e3b4", padRim="#83c98b",
        lotusA="#fff4f0", lotusB="#e98f99", lotusC="#e0b43a",
        shadow=(0.03, 0.16, 0.18, 0.5),
        scrim="#e6f3ef", scrimOp=0.9,
        glint="#ffffff",
        card="#f3f9f6", cardHi="#e9f4f0", stroke="#c2dbd4", chip="#e4f1ec", chipStroke="#b3d1c9",
        line="#a9cbc3",
    ),
}

# ----------------------------------------------------------------------------------------------
# the koi
# ----------------------------------------------------------------------------------------------
SLIM = 0.8  # body width relative to the first sketch: koi seen from above are long and slim
PROFILE = [(52, 0), (51, 3.2), (49, 6.4), (46, 9.2), (41, 12.2), (34, 14.8), (25, 16.6), (15, 17.4), (5, 17),
           (-5, 15.6), (-15, 13.4), (-25, 10.6), (-33, 8), (-40, 6), (-45, 4.8), (-48, 4.3)]


def hw(x):
    for (x0, w0), (x1, w1) in zip(PROFILE, PROFILE[1:]):
        if x1 <= x <= x0:
            t = (x0 - x) / (x0 - x1)
            return (w0 + (w1 - w0) * t) * SLIM
    return 0 if x > 52 else 4.3 * SLIM


BODY = [(52, 0)] + [(x, hw(x)) for x, _ in PROFILE[1:]] + [(x, -hw(x)) for x, _ in reversed(PROFILE[1:])]
TAIL = [(-44, 3.8), (-56, 9), (-70, 15.5), (-85, 22), (-96, 21.5), (-92, 13), (-85, 5), (-80, 0),
        (-85, -5), (-92, -13), (-96, -21.5), (-85, -22), (-70, -15.5), (-56, -9), (-44, -3.8)]
TAIL_RAYS = [[(-47, 2.8), (-61, 9), (-77, 15.5), (-93, 20.5)], [(-47, 1.4), (-61, 5.5), (-75, 9), (-90, 12.5)],
             [(-47, 0.4), (-61, 1.6), (-72, 2.6), (-83, 3.8)], [(-47, -0.4), (-61, -1.6), (-72, -2.6), (-83, -3.8)],
             [(-47, -1.4), (-61, -5.5), (-75, -9), (-90, -12.5)], [(-47, -2.8), (-61, -9), (-77, -15.5), (-93, -20.5)]]
DORSAL = [(10, 0), (2, 1.2), (-10, 1.9), (-22, 1.8), (-32, 1), (-38, 0), (-32, -1), (-22, -1.8), (-10, -1.9), (2, -1.2)]
PELVIC = [(-8, 9.4), (-14, 15.5), (-22, 19.5), (-26.5, 17.5), (-22, 10.8)]
SPINE = [(46, 0)] + [(x, hw(x) * 0.3) for x in (42, 34, 24, 12, 0, -12, -24, -34)] + [(-40, 0)] + \
        [(x, -hw(x) * 0.3) for x in (-34, -24, -12, 0, 12, 24, 34, 42)]
PECTORAL = [(2, -1), (-1, 7), (-9, 16), (-18, 21), (-24.5, 18.5), (-19, 9.5), (-8, 2)]
PEC_RAYS = [[(0, 0), (-6, 9), (-15, 17)], [(0, 0), (-10, 7), (-21, 15)]]


def eye(cx, cy):
    return [(cx + 2.3 * math.cos(a), cy + 1.7 * math.sin(a)) for a in [i * math.pi / 4 for i in range(8)]]


def blob(cx, cy, rx, ry, rot=0.0, n=12, jit=0.2, seed=1):
    r = random.Random(seed)
    out = []
    ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    for i in range(n):
        a = 2 * math.pi * i / n
        k = 1 + r.uniform(-jit, jit)
        px, py = rx * k * math.cos(a), ry * k * math.sin(a)
        out.append((cx + px * ca - py * sa, (cy + px * sa + py * ca) * SLIM))
    return out


VARIETIES = {
    "kohaku": dict(base="#f6f0e6", fin="#f6efe4", finOp=0.62, pecBase="#f6efe4", hi=0.15, scale="scl",
                   patches=[("#e2492a", [blob(35, 1, 10.5, 9.5, 0, seed=3), blob(6, -2, 17, 16, 20, seed=5, jit=.24),
                                         blob(-22, 6, 11, 13, -10, seed=8)])]),
    "showa": dict(base="#f3eee6", fin="#f1ebe1", finOp=0.6, pecBase="#16181c", hi=0.13, scale="scl",
                  patches=[("#de4326", [blob(31, -3, 11, 10, 10, seed=11), blob(-3, 7, 15, 14, -15, seed=12, jit=.25)]),
                           ("#16181c", [blob(12, -13, 10, 6, 35, seed=21, jit=.3), blob(-18, -4, 7, 13, 10, seed=22, jit=.3),
                                        blob(42, 9, 6, 5, 0, seed=23), blob(-35, 6, 5, 7, 0, seed=24),
                                        blob(22, 12, 5, 4, 0, seed=25)])]),
    "ogon": dict(base="url(#ogonG)", fin="#f2c45e", finOp=0.58, pecBase="#f2c45e", hi=0.3, scale="sclG", patches=[]),
    "tancho": dict(base="#f7f2ea", fin="#f5efe6", finOp=0.6, pecBase="#f5efe6", hi=0.15, scale="scl",
                   patches=[("#d93a25", [blob(36, 0, 7.5, 7.5, 0, n=14, jit=.06, seed=31)])]),
}

K_WAVE = 2 * math.pi / 165


def make_bend(A1, A0=0.45):
    def spine(x, ph):
        env = A0 + A1 * max(0.0, (22 - x) / 70) ** 1.5
        return env * math.sin(ph - K_WAVE * (52 - x))

    def bend(p, ph):
        x, y = p
        s = spine(x, ph)
        ds = (spine(x + 0.5, ph) - spine(x - 0.5, ph))
        n = math.hypot(ds, 1)
        return (x + y * (-ds / n), s + y * (1 / n))

    return bend


def koi_defs(doc):
    """Shared gradients and scale patterns for every koi in a doc (call once)."""
    doc.defs.append(
        '<pattern id="scl" width="5" height="5" patternUnits="userSpaceOnUse">'
        '<path d="M5 0A3 3 0 0 0 5 5M2.5-2.5A3 3 0 0 0 2.5 2.5M2.5 2.5A3 3 0 0 0 2.5 7.5" fill="none" stroke="#3a2a20" '
        'stroke-opacity=".17" stroke-width=".6"/></pattern>'
        '<pattern id="sclG" width="5" height="5" patternUnits="userSpaceOnUse">'
        '<path d="M5 0A3 3 0 0 0 5 5M2.5-2.5A3 3 0 0 0 2.5 2.5M2.5 2.5A3 3 0 0 0 2.5 7.5" fill="none" stroke="#fff6d8" '
        'stroke-opacity=".5" stroke-width=".7"/></pattern>'
        '<linearGradient id="ogonG" gradientUnits="userSpaceOnUse" x1="0" y1="-18" x2="0" y2="18">'
        '<stop offset="0" stop-color="#cf9530"/><stop offset=".5" stop-color="#ffe394"/><stop offset="1" stop-color="#cf9530"/></linearGradient>'
    )
    for v, d in VARIETIES.items():
        doc.defs.append(
            '<linearGradient id="tf-%s" gradientUnits="userSpaceOnUse" x1="-44" y1="0" x2="-96" y2="0">'
            '<stop offset="0" stop-color="%s" stop-opacity="%s"/><stop offset="1" stop-color="%s" stop-opacity=".18"/></linearGradient>'
            % (v, d["fin"], f(d["finOp"] + 0.2, 2), d["fin"]))
        doc.defs.append(
            '<linearGradient id="pf-%s" x1="1" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="%s" stop-opacity=".95"/><stop offset=".45" stop-color="%s" stop-opacity="%s"/>'
            '<stop offset="1" stop-color="%s" stop-opacity=".2"/></linearGradient>'
            % (v, d["pecBase"], d["fin"], f(d["finOp"], 2), d["fin"]))
    doc.css.append("""
.flap{animation:flap 1.9s ease-in-out infinite alternate;transform-box:view-box;transform-origin:0 0}
@keyframes flap{from{transform:rotate(-12deg)}to{transform:rotate(14deg)}}
""")


def koi(doc, variety, T=1.7, begin=0.0, A1=7.0, N=10, static=False, phase=0.0):
    """One koi in local coords, nose at +x. Returns an SVG group string."""
    d = VARIETIES[variety]
    fid = doc.uid("k")
    bend = make_bend(A1)
    phases = [phase] if static else [2 * math.pi * i / N for i in range(N)]

    def morph(pts, closed=True, attrs=""):
        frames = [cr([bend(p, ph) for p in pts], closed) for ph in phases]
        if static:
            return '<path d="%s"%s/>' % (frames[0], attrs)
        vals = ";".join(frames + [frames[0]])
        return '<path d="%s"%s><animate attributeName="d" dur="%ss" begin="%ss" repeatCount="indefinite" values="%s"/></path>' % (
            frames[0], attrs, f(T, 2), f(begin, 2), vals)

    def morph_multi(lines, attrs):
        frames = []
        for ph in phases:
            frames.append("".join(cr([bend(p, ph) for p in ln], closed=False) for ln in lines))
        if static:
            return '<path d="%s"%s/>' % (frames[0], attrs)
        return '<path d="%s"%s><animate attributeName="d" dur="%ss" begin="%ss" repeatCount="indefinite" values="%s"/></path>' % (
            frames[0], attrs, f(T, 2), f(begin, 2), ";".join(frames + [frames[0]]))

    body_id = fid + "b"
    doc.defs.append(morph(BODY, attrs=' id="%s"' % body_id))
    doc.defs.append('<clipPath id="%sc"><use href="#%s"/></clipPath>' % (fid, body_id))

    delay = "-%ss" % f(random.Random(fid).uniform(0, 1.8), 2)
    out = ['<g>']
    # pectoral fins (rigid, flapping) under the body
    pec = cr(PECTORAL)
    rays = "".join(cr(r, closed=False) for r in PEC_RAYS)
    for sy in (1, -1):
        out.append('<g transform="translate(25 %s) scale(1 %d)"><g class="flap" style="animation-delay:%s">'
                   '<path d="%s" fill="url(#pf-%s)"/><path d="%s" fill="none" stroke="#fff" stroke-opacity=".32" stroke-width=".5"/></g></g>'
                   % (f(11.2 * sy), sy, delay, pec, variety, rays))
    # tail and pelvic fins
    out.append(morph(TAIL, attrs=' fill="url(#tf-%s)"' % variety))
    out.append(morph_multi(TAIL_RAYS, ' fill="none" stroke="#fff" stroke-opacity=".38" stroke-width=".55"'))
    out.append(morph(PELVIC, attrs=' fill="url(#tf-%s)" opacity=".9"' % variety))
    out.append(morph([(x, -y) for x, y in PELVIC], attrs=' fill="url(#tf-%s)" opacity=".9"' % variety))
    # body, clipped detail
    out.append('<g clip-path="url(#%sc)">' % fid)
    out.append('<use href="#%s" fill="%s"/>' % (body_id, d["base"]))
    for colour, blobs in d["patches"]:
        for b in blobs:
            out.append(morph(b, attrs=' fill="%s"' % colour))
    out.append('<rect x="-60" y="-30" width="120" height="60" fill="url(#%s)"/>' % d["scale"])
    out.append(morph(SPINE, attrs=' fill="#fff" opacity="%s"' % f(d["hi"], 2)))
    out.append('<use href="#%s" fill="none" stroke="#0a1c22" stroke-opacity=".24" stroke-width="6"/>' % body_id)
    out.append('<use href="#%s" fill="none" stroke="#0a1c22" stroke-opacity=".09" stroke-width="12"/>' % body_id)
    out.append('</g>')
    out.append(morph(DORSAL, attrs=' fill="%s" opacity=".5"' % ("#8a5a14" if variety == "ogon" else "#c9bfae")))
    out.append(morph(eye(39.5, 6.9), attrs=' fill="#1a1410"'))
    out.append(morph(eye(39.5, -6.9), attrs=' fill="#1a1410"'))
    out.append('</g>')
    return "".join(out)


# ----------------------------------------------------------------------------------------------
# pond pieces
# ----------------------------------------------------------------------------------------------
def caustic_tile(size, n, seed, inset=(2.2, 4.2)):
    from scipy.spatial import Voronoi
    r = random.Random(seed)
    base = [(r.uniform(0, size), r.uniform(0, size)) for _ in range(n)]
    allp = [(x + dx * size, y + dy * size) for dx in (-1, 0, 1) for dy in (-1, 0, 1) for x, y in base]
    vor = Voronoi(allp)
    d = "M0 0H%sV%sH0Z" % (f(size), f(size))
    for i in range(len(allp)):
        reg = vor.regions[vor.point_region[i]]
        if not reg or -1 in reg:
            continue
        poly = [tuple(vor.vertices[j]) for j in reg]
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        if max(xs) < -2 or min(xs) > size + 2 or max(ys) < -2 or min(ys) > size + 2:
            continue
        cx, cy = allp[i]
        ins = r.uniform(*inset)
        ring = []
        m = len(poly)
        for k in range(m):
            a, b = poly[k], poly[(k + 1) % m]
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            for p, extra in ((a, 2.2), (mid, 1.0)):
                dx, dy = p[0] - cx, p[1] - cy
                dist = math.hypot(dx, dy) or 1
                kk = max(0.1, 1 - (ins * extra) / dist)
                ring.append((cx + dx * kk, cy + dy * kk))
        d += cr(ring)
    return d


def caustics(doc, T, w, h, scale=1.0, op_mul=1.0, cls_prefix="cz"):
    s1, s2 = 260 * scale, 190 * scale
    doc.defs.append('<pattern id="cau1" width="%s" height="%s" patternUnits="userSpaceOnUse"><path d="%s" fill="%s" fill-rule="evenodd"/></pattern>'
                    % (f(s1), f(s1), caustic_tile(s1, 15, 7), T["caustic"]))
    ang = 24
    doc.defs.append('<pattern id="cau2" width="%s" height="%s" patternUnits="userSpaceOnUse" patternTransform="rotate(%d)"><path d="%s" fill="%s" fill-rule="evenodd"/></pattern>'
                    % (f(s2), f(s2), ang, caustic_tile(s2, 11, 19, (1.6, 3.2)), T["caustic"]))
    vx, vy = s2 * math.cos(math.radians(ang)), s2 * math.sin(math.radians(ang))
    doc.css.append("""
.%(p)s1{animation:%(p)sa 70s linear infinite}
.%(p)s2{animation:%(p)sb 52s linear infinite}
.%(p)sp{animation:%(p)sq 9s ease-in-out infinite alternate}
@keyframes %(p)sa{to{transform:translate(%(a)spx,%(a)spx)}}
@keyframes %(p)sb{to{transform:translate(%(bx)spx,%(by)spx)}}
@keyframes %(p)sq{from{opacity:.55}to{opacity:1}}
""" % dict(p=cls_prefix, a=f(-s1), bx=f(vx), by=f(vy)))
    pad = 2 * max(s1, s2)
    return ('<g class="%sp"><g class="%s1"><rect x="%s" y="%s" width="%s" height="%s" fill="url(#cau1)" opacity="%s"/></g>'
            '<g class="%s2"><rect x="%s" y="%s" width="%s" height="%s" fill="url(#cau2)" opacity="%s"/></g></g>'
            % (cls_prefix, cls_prefix, f(-pad), f(-pad), f(w + 2 * pad), f(h + 2 * pad), f(T["cau1"] * op_mul, 3),
               cls_prefix, f(-pad), f(-pad), f(w + 2 * pad), f(h + 2 * pad), f(T["cau2"] * op_mul, 3)))


def shadow_filter(doc, T, sd=5):
    r, g, b, a = T["shadow"]
    doc.defs.append('<filter id="shd" x="-30%%" y="-30%%" width="160%%" height="160%%"><feColorMatrix type="matrix" '
                    'values="0 0 0 0 %s 0 0 0 0 %s 0 0 0 0 %s 0 0 0 %s 0"/><feGaussianBlur stdDeviation="%s"/></filter>'
                    % (f(r, 2), f(g, 2), f(b, 2), f(a, 2), f(sd)))


def lily_pad(T, cx, cy, r, notch, seed, rot_cls=None):
    rr = random.Random(seed)
    a0 = math.radians(notch)
    gap = math.radians(9)
    pts = []
    steps = 28
    for i in range(steps + 1):
        a = a0 + gap + (2 * math.pi - 2 * gap) * i / steps
        k = 1 + rr.uniform(-0.018, 0.018)
        pts.append((cx + r * k * math.cos(a), cy + r * k * math.sin(a)))
    # centre, out to the notch edge, round the smooth rim, back to the centre
    edge = cr(pts, closed=False)
    d = "M" + pts_str((cx, cy)) + "L" + edge[1:] + "Z"
    veins = ""
    for i in range(9):
        a = a0 + math.radians(22) + (2 * math.pi - math.radians(44)) * i / 8
        veins += "M%sL%s" % (pts_str((cx, cy)), pts_str((cx + r * 0.9 * math.cos(a), cy + r * 0.9 * math.sin(a))))
    gid = "pg%d" % seed
    grad = ('<radialGradient id="%s" cx="%s" cy="%s" r="%s" gradientUnits="userSpaceOnUse">'
            '<stop offset="0" stop-color="%s"/><stop offset=".75" stop-color="%s"/><stop offset="1" stop-color="%s"/></radialGradient>'
            % (gid, f(cx - r * 0.25), f(cy - r * 0.25), f(r * 1.2), T["padMid"], T["padMid"], T["padEdge"]))
    shadow = '<path d="%s" fill="#021015" opacity="%s" transform="translate(7 9)"/>' % (d, ".32" if T["name"] == "dark" else ".16")
    pad = ('<path d="%s" fill="url(#%s)" stroke="%s" stroke-width="1.6"/>'
           '<path d="%s" stroke="%s" stroke-opacity=".35" stroke-width="1.1" fill="none"/>'
           % (d, gid, T["padRim"], veins, T["padVein"]))
    return grad, shadow + pad


def lotus(T, cx, cy, r):
    petals = []
    for ring, (n, rl, rw, off, col) in enumerate([(9, r, r * 0.34, 0, T["lotusB"]), (7, r * 0.78, r * 0.3, 20, T["lotusA"]),
                                                    (5, r * 0.5, r * 0.24, 8, T["lotusA"])]):
        for i in range(n):
            a = 360 * i / n + off
            petals.append('<ellipse cx="%s" cy="0" rx="%s" ry="%s" transform="rotate(%s)" fill="%s" stroke="%s" stroke-opacity=".35" stroke-width=".7"/>'
                          % (f(rl * 0.5), f(rl * 0.5), f(rw), f(a), "url(#lotusG)" if ring == 0 else col, T["lotusB"]))
    grad = ('<radialGradient id="lotusG" cx=".1" cy=".5" r=".9"><stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></radialGradient>'
            % (T["lotusA"], T["lotusB"]))
    centre = '<circle r="%s" fill="%s"/><circle r="%s" fill="#fff" opacity=".35"/>' % (f(r * 0.18), T["lotusC"], f(r * 0.08))
    return grad, '<g transform="translate(%s %s)"><g class="bloom">%s%s</g></g>' % (f(cx), f(cy), "".join(petals), centre)


def ripples(points, colour, stroke=1.6, r=70, base_dur=7.0, op=0.55):
    out = []
    for i, (x, y, dl) in enumerate(points):
        for j in range(3):
            out.append('<g transform="translate(%s %s)"><circle class="rip" r="%s" fill="none" stroke="%s" stroke-width="%s" '
                       'style="animation-duration:%ss;animation-delay:%ss"/></g>'
                       % (f(x), f(y), f(r * (1 - 0.18 * j)), colour, f(stroke), f(base_dur), f(dl + j * 0.55)))
    css = """
.rip{opacity:0;transform-box:view-box;transform-origin:0 0;animation:rip 7s cubic-bezier(.2,.6,.3,1) infinite}
@keyframes rip{0%%{transform:scale(.04);opacity:0}8%%{opacity:%s}70%%{opacity:0}100%%{transform:scale(1);opacity:0}}
""" % f(op, 2)
    return "".join(out), css


def closed_path(pts):
    return cr(pts, closed=True)
