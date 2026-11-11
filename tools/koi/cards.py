"""Builds the cards under the banner (assets/*-dark.svg, *-light.svg): ghost glass in the TV widgets' tokens, with the
animated motifs from motifs.py. (The folder keeps its old name; the koi pond pieces left in koilib are retired.)

    python tools/koi/cards.py

All text is outlined into paths and every animation is CSS or SMIL inside the SVG, because GitHub
strips <style> and <script> from README HTML and serves images with a no-fetch CSP.
Facts on these images come from the README draft and the CV data, nothing else.
"""
import math
import os
import random

from koilib import (Doc, THEMES, REDUCED, GLASS_PAD, cr, f, font, glass, koi, koi_defs, caustics, shadow_filter,
                    lily_pad, lotus, ripples)
import motifs
import caret

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets")


def loop_pts(cx, cy, rx, ry, n=10, jit=0.08, seed=1, reverse=False, start=0.0):
    r = random.Random(seed)
    pts = []
    for i in range(n):
        a = start + 2 * math.pi * i / n
        k = 1 + r.uniform(-jit, jit)
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    return list(reversed(pts)) if reverse else pts


def poly_len(pts, closed=True):
    L = 0
    P = pts + ([pts[0]] if closed else [])
    for a, b in zip(P, P[1:]):
        L += math.hypot(b[0] - a[0], b[1] - a[1])
    return L * 1.04


def swimmer(doc, variety, pts, speed, scale, begin_frac=0.0, wag=1.7, A1=7.0, N=10):
    sid = doc.uid("sw")
    path = cr(pts, closed=True)
    dur = poly_len(pts) / speed
    body = koi(doc, variety, T=wag, begin=-random.Random(sid).uniform(0, wag), A1=A1, N=N)
    g = ('<g id="%s"><animateMotion dur="%ss" begin="%ss" repeatCount="indefinite" rotate="auto" path="%s"/>'
         '<g transform="scale(%s)">%s</g></g>' % (sid, f(dur, 2), f(-dur * begin_frac, 2), path, f(scale, 3), body))
    return sid, g


def still_koi(doc, variety, x, y, rot, scale, phase=0.6):
    return '<g transform="translate(%s %s) rotate(%s) scale(%s)">%s</g>' % (
        f(x), f(y), f(rot), f(scale, 3), koi(doc, variety, static=True, phase=phase))


def frame_css():
    return """
.rise{animation:rise 1.2s cubic-bezier(.2,.7,.2,1) both}
@keyframes rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
.fade{animation:fade 1.4s ease-out both}
@keyframes fade{from{opacity:0}to{opacity:1}}
.pulse{transform-box:view-box;transform-origin:0 0;animation:pulse 2.6s ease-out infinite}
@keyframes pulse{0%{transform:scale(.6);opacity:.8}80%,100%{transform:scale(2.6);opacity:0}}
.flow{animation:flow 1.2s linear infinite}
@keyframes flow{to{stroke-dashoffset:-16}}
"""


def write(name, theme, doc):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "%s-%s.svg" % (name, theme))
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc.render())
    return p, os.path.getsize(p)


# ----------------------------------------------------------------------------------------------
# hero: the koi pond
# ----------------------------------------------------------------------------------------------
def hero(T):
    W, H = 1280, 460
    doc = Doc(W, H, "Ethan Soh",
              "An animated koi pond: four koi swim under lily pads and a lotus while ripples spread and light plays "
              "on the pond floor. Text: Ethan Soh. Applied AI and agent engineering, with a security edge. Year 2, "
              "Cybersecurity and Digital Forensics, Singapore Polytechnic. Seeking a 44-week internship from 12 April 2027.")
    koi_defs(doc)
    shadow_filter(doc, T, 5)
    doc.css.append(frame_css())
    doc.defs.append(
        '<radialGradient id="bg" cx=".68" cy=".42" r=".8"><stop offset="0" stop-color="%s"/><stop offset=".55" stop-color="%s"/>'
        '<stop offset="1" stop-color="%s"/></radialGradient>' % (T["bgA"], T["bgB"], T["bgC"]))
    doc.defs.append(
        '<radialGradient id="vig" cx=".6" cy=".45" r=".78"><stop offset=".55" stop-color="%s" stop-opacity="0"/>'
        '<stop offset="1" stop-color="%s" stop-opacity="%s"/></radialGradient>' % (T["bgC"], T["bgC"], ".7" if T["name"] == "dark" else ".45"))
    doc.defs.append(
        '<linearGradient id="scrim" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="%s" stop-opacity="%s"/>'
        '<stop offset=".45" stop-color="%s" stop-opacity="%s"/><stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient>'
        % (T["scrim"], f(T["scrimOp"], 2), T["scrim"], f(T["scrimOp"] * 0.72, 2), T["scrim"]))
    doc.defs.append(
        '<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset=".5" stop-color="#fff" stop-opacity="%s"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        % (".06" if T["name"] == "dark" else ".22"))
    doc.defs.append('<clipPath id="frame"><rect width="%d" height="%d" rx="22"/></clipPath>' % (W, H))

    b = doc.body
    b.append('<g clip-path="url(#frame)">')
    b.append('<rect width="%d" height="%d" fill="url(#bg)"/>' % (W, H))
    # pond floor
    r = random.Random(4)
    peb = []
    for _ in range(90):
        x, y = r.uniform(-20, W + 20), r.uniform(0, H) ** 0.85 * (H / H ** 0.85)
        peb.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" transform="rotate(%s %s %s)" fill="%s" opacity="%s"/>'
                   % (f(x), f(y), f(r.uniform(5, 24)), f(r.uniform(4, 14)), f(r.uniform(0, 180)), f(x), f(y),
                      r.choice(T["pebbles"]), f(r.uniform(0.25, 0.6), 2)))
    b.append("<g>%s</g>" % "".join(peb))
    b.append(caustics(doc, T, W, H))

    # swimmers
    pair = loop_pts(992, 232, 222, 126, n=10, jit=0.07, seed=2)
    ogon_pts = [(-220, 452), (180, 452), (470, 432), (690, 318), (860, 150), (1080, 74), (1340, 128), (1520, 330),
                (1380, 640), (600, 700), (-200, 650), (-420, 520)]
    tancho_pts = loop_pts(612, 368, 160, 60, n=8, jit=0.06, seed=9, reverse=True)
    s_tancho, g_tancho = swimmer(doc, "tancho", tancho_pts, 30, 0.82, 0.2, wag=1.5, A1=7.5)
    s_koh, g_koh = swimmer(doc, "kohaku", pair, 36, 1.12, 0.0, wag=1.8)
    s_sho, g_sho = swimmer(doc, "showa", pair, 36, 1.04, 0.5, wag=1.65)
    s_ogo, g_ogo = swimmer(doc, "ogon", ogon_pts, 46, 1.22, 0.08, wag=2.0, A1=6.5)

    b.append('<g class="motion">')
    b.append('<use href="#%s" transform="translate(8 10)" filter="url(#shd)" opacity=".7"/>' % s_tancho)
    for s in (s_koh, s_sho, s_ogo):
        b.append('<use href="#%s" transform="translate(16 20)" filter="url(#shd)"/>' % s)
    b.append(g_tancho)
    b.append('<rect width="%d" height="%d" fill="%s" opacity="%s"/>' % (W, H, T["tint"], f(T["tintOp"], 2)))
    b.append(g_koh + g_sho + g_ogo)
    b.append('</g>')
    # reduced motion: the same koi, posed
    b.append('<g class="still">')
    b.append(still_koi(doc, "tancho", 640, 392, 168, 0.82))
    b.append('<rect width="%d" height="%d" fill="%s" opacity="%s"/>' % (W, H, T["tint"], f(T["tintOp"], 2)))
    b.append(still_koi(doc, "kohaku", 905, 150, 18, 1.12))
    b.append(still_koi(doc, "showa", 1080, 318, 196, 1.04, phase=2.2))
    b.append(still_koi(doc, "ogon", 760, 220, -38, 1.22, phase=4.0))
    b.append('</g>')

    # ripples on the surface
    rp, rcss = ripples([(700, 92, 0.4), (1120, 400, 2.6), (640, 300, 4.9), (1210, 230, 6.1)],
                       "#ffffff" if T["name"] == "dark" else "#ffffff", 1.6, 74, 8.0, 0.42 if T["name"] == "dark" else 0.75)
    doc.css.append(rcss)
    b.append(rp)

    # lily pads and a lotus (drift gently)
    doc.css.append("""
.drA{animation:drA 17s ease-in-out infinite alternate;transform-box:view-box;transform-origin:0 0}
.drB{animation:drB 21s ease-in-out infinite alternate;transform-box:view-box;transform-origin:0 0}
@keyframes drA{from{transform:translate(0,0) rotate(0)}to{transform:translate(-9px,6px) rotate(-3deg)}}
@keyframes drB{from{transform:translate(0,0) rotate(0)}to{transform:translate(8px,-5px) rotate(4deg)}}
.bloom{transform-box:view-box;transform-origin:0 0;animation:bloom 7s ease-in-out infinite alternate}
@keyframes bloom{from{transform:scale(.95) rotate(0)}to{transform:scale(1.04) rotate(6deg)}}
.tw{animation:tw 5s ease-in-out infinite}
@keyframes tw{0%,100%{opacity:0}50%{opacity:.85}}
.sh{animation:sh 16s ease-in-out infinite}
@keyframes sh{0%{transform:translateX(-900px)}55%,100%{transform:translateX(1500px)}}
""")
    grads, pads = [], []
    for (cx, cy, rr, notch, seed) in [(0, 0, 64, 205, 11), (-82, 58, 40, 25, 12), (40, 92, 30, 130, 13)]:
        g_, p_ = lily_pad(T, cx, cy, rr, notch, seed)
        grads.append(g_)
        pads.append(p_)
    lg, lp = lotus(T, -12, 10, 30)
    grads.append(lg)
    b.append('<g transform="translate(1214 34)"><g class="drA">%s%s</g></g>' % ("".join(pads), lp))
    pads = []
    for (cx, cy, rr, notch, seed) in [(0, 0, 56, 300, 21), (70, -34, 30, 160, 22), (-66, 18, 34, 60, 23)]:
        g_, p_ = lily_pad(T, cx, cy, rr, notch, seed)
        grads.append(g_)
        pads.append(p_)
    b.append('<g transform="translate(820 452)"><g class="drB">%s</g></g>' % "".join(pads))
    doc.defs.extend(grads)

    # glints and the passing sheen
    r = random.Random(17)
    gl = []
    for i in range(18):
        gl.append('<ellipse cx="%s" cy="%s" rx="%s" ry="1" fill="%s" class="tw" style="animation-delay:%ss;animation-duration:%ss"/>'
                  % (f(r.uniform(560, 1260)), f(r.uniform(20, 440)), f(r.uniform(2, 5)), T["glint"], f(r.uniform(0, 6), 2),
                     f(r.uniform(4, 8), 2)))
    b.append("<g>%s</g>" % "".join(gl))
    b.append('<g class="sh"><rect x="0" y="-200" width="380" height="900" fill="url(#sheen)" transform="rotate(18)"/></g>')
    b.append('<rect width="%d" height="%d" fill="url(#vig)"/>' % (W, H))
    b.append('<rect width="780" height="%d" fill="url(#scrim)"/>' % H)

    # text
    x0 = 72
    eb, _ = doc.text("YEAR 2  ·  CYBERSECURITY & DIGITAL FORENSICS  ·  SINGAPORE POLYTECHNIC", x0, 112, "mono", 13.5,
                     T["gold"], tracking=0.12)
    nm, nmw = doc.text("Ethan Soh", x0 - 4, 232, "serif", 124, T["text"])
    t1, _ = doc.text("Applied AI and agent engineering,", x0, 286, "sans", 30, T["text"])
    t2, _ = doc.text("with a security edge.", x0, 324, "sans", 30, T["dim"])
    b.append('<g class="rise" style="animation-delay:.1s">%s</g>' % eb)
    b.append('<g class="rise" style="animation-delay:.25s">%s</g>' % nm)
    b.append('<g class="rise" style="animation-delay:.45s">%s%s</g>' % (t1, t2))
    # pills
    py = 356
    p1t = "Seeking a 44-week internship from 12 April 2027"
    w1 = font("sans").width(p1t, 15.5)
    pill1 = ('<rect x="%s" y="%s" width="%s" height="36" rx="18" fill="%s" fill-opacity=".85" stroke="%s"/>'
             '<g transform="translate(%s %s)"><circle r="4.5" fill="%s"/><circle r="4.5" fill="%s" class="pulse"/></g>'
             % (f(x0), py, f(w1 + 50), T["card"], T["chipStroke"], f(x0 + 20), py + 18, T["ok"], T["ok"]))
    pt1, _ = doc.text(p1t, x0 + 36, py + 23.5, "sans", 15.5, T["text"])
    x2 = x0 + w1 + 62
    p2t = "CCA-F  ·  ISC2 CC"
    w2 = font("mono").width(p2t, 13.5)
    pill2 = '<rect x="%s" y="%s" width="%s" height="36" rx="18" fill="%s" fill-opacity=".85" stroke="%s"/>' % (f(x2), py, f(w2 + 32), T["card"], T["chipStroke"])
    pt2, _ = doc.text(p2t, x2 + 16, py + 22.5, "mono", 13.5, T["gold"])
    b.append('<g class="rise" style="animation-delay:.65s">%s%s%s%s</g>' % (pill1, pt1, pill2, pt2))
    b.append('</g>')
    b.append('<rect x=".5" y=".5" width="%d" height="%d" rx="22" fill="none" stroke="%s" stroke-opacity=".6"/>' % (W - 1, H - 1, T["stroke"]))
    doc.css.append(REDUCED)
    return doc


# ----------------------------------------------------------------------------------------------
# typing line
# ----------------------------------------------------------------------------------------------
PHRASES = ["multi-agent orchestration", "applied AI", "AI security", "MCP agents that drive Android",
           "Claude Code harness engineering"]


def typing(T):
    W, H = 880, 56
    doc = Doc(W, H, "Focus areas", "Typed line cycling through: " + "; ".join(PHRASES) + ".")
    doc.pad = (GLASS_PAD[0], 0, GLASS_PAD[2], 0)
    size = 21
    mono = font("mono")
    cw = mono.adv(mono.glyph("a")) * size / mono.upm
    prefix = "› now focused on "
    try:
        mono.glyph("›")
    except KeyError:
        prefix = "> now focused on "
    base_y = 36
    pre, prew = doc.text(prefix, 4, base_y, "mono", size, T["dim"])
    x_text = 4 + len(prefix) * cw
    doc.body.append(pre)

    type_ms, del_ms, hold, gap = 0.058, 0.026, 2.5, 1.3   # the hold and the rest are long enough for Clawd's hops
    events = []  # (t, phrase_index, chars)
    segs = []    # (pose, start, end): R runs right, L runs left, F faces the viewer and hops
    t = 0.2
    segs.append(("F", 0.0, t))
    for i, p in enumerate(PHRASES):
        t0 = t
        for k in range(1, len(p) + 1):
            events.append((t, i, k))
            t += type_ms
        segs.append(("R", t0, t))
        segs.append(("F", t, t + hold))
        t += hold
        t1 = t
        for k in range(len(p) - 1, -1, -1):
            events.append((t, i, k))
            t += del_ms
        segs.append(("L", t1, t))
        segs.append(("F", t, t + gap))
        t += gap
    cycle = t
    caret_kt, caret_v = ["0"], [f(x_text + 2, 2)]
    clips = []
    motion = ['<g class="motion">']
    for i, p in enumerate(PHRASES):
        kt, vals = ["0"], ["0"]
        for (te, pi, k) in events:
            if pi != i:
                continue
            kt.append(f(te / cycle, 5))
            vals.append(f(k * cw + (2 if k else 0), 2))
        cid = "cl%d" % i
        clips.append('<clipPath id="%s"><rect x="%s" y="4" height="48" width="0"><animate attributeName="width" dur="%ss" '
                     'repeatCount="indefinite" calcMode="discrete" keyTimes="%s" values="%s"/></rect></clipPath>'
                     % (cid, f(x_text, 2), f(cycle, 3), ";".join(kt), ";".join(vals)))
        tx, _ = doc.text(p, x_text, base_y, "mono", size, T["text"] if i % 2 == 0 else T["accent"])
        motion.append('<g clip-path="url(#%s)">%s</g>' % (cid, tx))
    for (te, pi, k) in events:
        caret_kt.append(f(te / cycle, 5))
        caret_v.append(f(x_text + k * cw + 2, 2))
    doc.defs.extend(clips)
    # Clawd is the caret: he stands straight after the last typed letter and moves with it
    motion.append(caret.build(doc, T, cycle, caret_kt, caret_v, segs))
    motion.append("</g>")
    doc.body.append("".join(motion))
    still_text = "multi-agent orchestration · applied AI"   # two items, so Clawd fits after it
    st, stw = doc.text(still_text, x_text, base_y, "mono", size, T["text"])
    doc.body.append('<g class="still">%s%s</g>' % (st, caret.still(x_text + stw + 8)))
    doc.css.append(REDUCED)
    return doc


# ----------------------------------------------------------------------------------------------
# section headers: a title and a little stream with one koi in it
# ----------------------------------------------------------------------------------------------
def header(T, idx, title, motif, desc):
    """A section heading: the number and title, then a glass window holding that section's animated motif."""
    W, H = 880, 92
    doc = Doc(W, H, title, "Section heading: %s. %s" % (title, desc))
    doc.pad = (GLASS_PAD[0], 0, GLASS_PAD[2], 0)   # same side margins as the cards, so the edges line up
    doc.css.append(frame_css())
    ix, _ = doc.text(idx, 2, 56, "cap", 13, T["gold"], tracking=0.12)
    tt, tw = doc.text(title, 34, 60, "serif", 42, T["text"])
    doc.body.append(ix + tt)
    x1 = 34 + tw + 26
    cw = W - 2 - x1
    wy, wh = 12, 66
    doc.defs.append('<clipPath id="ch"><rect x="%s" y="%s" width="%s" height="%s" rx="18"/></clipPath>' % (f(x1), wy, f(cw), wh))
    doc.body.append(glass(doc, T, x1, wy, cw, wh, 18, sd=4))
    doc.body.append('<g clip-path="url(#ch)">%s</g>' % motif(doc, T, x1, wy, cw, wh))
    doc.css.append(REDUCED)
    return doc


def tile(T, name, title, desc, draw):
    """A small glass tile for the strip under the typing line."""
    W, H = 286, 176
    doc = Doc(W, H, title, desc)
    doc.pad = GLASS_PAD
    doc.body.append(glass(doc, T, 1, 1, W - 2, H - 2, 18))
    doc.defs.append('<clipPath id="tc"><rect x="1" y="1" width="%d" height="%d" rx="18"/></clipPath>' % (W - 2, H - 2))
    doc.body.append('<g clip-path="url(#tc)">%s</g>' % draw(doc, T, 1, 1, W - 2, H - 2))
    doc.css.append(REDUCED)
    return doc


def band(T, title, desc, draw, H):
    """A full-width glass band: the weather divider and the Concorde footer."""
    W = 880
    doc = Doc(W, H, title, desc)
    doc.pad = GLASS_PAD
    doc.body.append(glass(doc, T, 1, 1, W - 2, H - 2, 20))
    doc.defs.append('<clipPath id="bc"><rect x="1" y="1" width="%d" height="%d" rx="20"/></clipPath>' % (W - 2, H - 2))
    doc.body.append('<g clip-path="url(#bc)">%s</g>' % draw(doc, T, 1, 1, W - 2, H - 2))
    doc.css.append(REDUCED)
    return doc


# ----------------------------------------------------------------------------------------------
# cards
# ----------------------------------------------------------------------------------------------
def card_frame(doc, T, W, H):
    """The card's ghost glass (koilib.glass), with room round the drawing for its soft shadow."""
    doc.pad = GLASS_PAD
    doc.body.append(glass(doc, T, 1, 1, W - 2, H - 2, 18))
    # anything that swims keeps inside the glass, not out in the shadow's margin
    doc.defs.append('<clipPath id="cf"><rect x="1" y="1" width="%d" height="%d" rx="18"/></clipPath>' % (W - 2, H - 2))


def card_head(doc, T, W, eyebrow, title, subtitle, right1, right2):
    a, _ = doc.text(eyebrow, 32, 46, "cap", 12, T["gold"], tracking=0.12)
    b_, _ = doc.text(title, 30, 98, "serif", 50, T["text"])
    c, _ = doc.text(subtitle, 32, 128, "sans", 17, T["dim"])
    d, _ = doc.text(right1, W - 32, 72, "sans", 16, T["text"], anchor="end")
    e, _ = doc.text(right2, W - 32, 96, "sans", 16, T["dim"], anchor="end")
    doc.body.append('<g class="rise">%s%s%s</g><g class="rise" style="animation-delay:.2s">%s%s</g>' % (a, b_, c, d, e))


def node(doc, T, x, y, w, h, l1, l2, extra=""):
    s = '<rect x="%s" y="%s" width="%s" height="%s" rx="12" fill="%s" stroke="%s"/>' % (f(x), f(y), f(w), f(h), T["chip"], T["chipStroke"])
    t1, _ = doc.text(l1, x + 14, y + 27, "sansb", 15, T["text"])
    t2, _ = doc.text(l2, x + 14, y + 47, "mono", 11.5, T["dim"])
    return s + t1 + t2 + extra


def chip(doc, T, label, colour, stroke):
    w = font("mono").width(label, 11) + 22
    t, _ = doc.text(label, -w / 2 + 11, 4, "mono", 11, colour)
    return '<rect x="%s" y="-11" width="%s" height="22" rx="11" fill="%s" stroke="%s"/>%s' % (f(-w / 2), f(w), T["card"], stroke, t), w


def agentroid(T):
    W, H = 880, 330
    doc = Doc(W, H, "Agentroid",
              "Agentroid, an Android agent bridge for MCP clients. Diagram: any MCP client, the brain, calls a TypeScript MCP "
              "server, then a Rust core that puts a risk label on every action, then a deny-by-default adb gate with a device "
              "allowlist, then Android emulators. Animated requests: R0 read and R1 navigate pass through; R4 destructive is "
              "held at the gate for approval. No model API key: the calling agent is the brain. Open-source release planned.")
    doc.css.append(frame_css())
    card_frame(doc, T, W, H)
    card_head(doc, T, W, "NOW BUILDING  ·  OPEN-SOURCE RELEASE PLANNED", "Agentroid",
              "An Android agent bridge for MCP clients.", "No model API key.", "The calling agent is the brain.")
    b = doc.body
    y, h = 168, 66
    cy = y + h / 2
    nodes = [(32, 156, "Any MCP client", "the brain"), (214, 140, "MCP server", "TypeScript"),
             (380, 164, "Rust core", "risk label per action"), (570, 146, "adb gate", "deny-by-default")]
    # connectors
    conns = [(188, 214), (354, 380), (544, 570), (716, 744)]
    for x_a, x_b in conns:
        b.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="2" stroke-dasharray="3 5" class="flow"/>'
                 % (f(x_a), f(cy), f(x_b), f(cy), T["line"]))
        b.append('<path d="M%s %sl-6-4v8z" fill="%s"/>' % (f(x_b), f(cy), T["line"]))
    for i, (x, w, l1, l2) in enumerate(nodes):
        extra = ""
        if i == 3:
            # shield with tick: the allowlist
            extra = ('<g transform="translate(%s %s)"><path d="M0-9l8 3v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10v-6z" fill="none" '
                     'stroke="%s" stroke-width="1.6"/><path d="M-3.5 0.5l2.5 2.6 4.6-5" fill="none" stroke="%s" stroke-width="1.6"/></g>'
                     % (f(x + w - 22), f(y + 24), T["ok"], T["ok"]))
        b.append('<g class="rise" style="animation-delay:%ss">%s</g>' % (f(0.3 + i * 0.12, 2), node(doc, T, x, y, w, h, l1, l2, extra)))
    al, _ = doc.text("device allowlist", 570 + 2, y - 10, "mono", 11, T["ok"])
    b.append(al)
    # phones
    doc.css.append("""
.scr{animation:scr 12s linear infinite}
@keyframes scr{0%,24%{opacity:.25}27%{opacity:1}34%{opacity:.25}55%{opacity:.25}58%{opacity:1}65%,100%{opacity:.25}}
""")
    for k in range(3):
        px = 748 + k * 34
        b.append('<rect x="%s" y="%s" width="28" height="56" rx="6" fill="%s" stroke="%s" stroke-width="1.4"/>'
                 % (f(px), f(cy - 28), T["chip"], T["dim"]))
        b.append('<rect x="%s" y="%s" width="20" height="40" rx="2" fill="%s" class="scr" style="animation-delay:%ss"/>'
                 % (f(px + 4), f(cy - 21), T["ok"], f(k * 0.12, 2)))
        for j in range(3):
            b.append('<rect x="%s" y="%s" width="%s" height="2.4" rx="1" fill="%s" opacity=".55"/>'
                     % (f(px + 7), f(cy - 15 + j * 9), f(14 - j * 3), T["card"]))
    em, _ = doc.text("emulators", 748, y - 10, "mono", 11, T["dim"])
    b.append(em)
    # request track
    ty = 288
    b.append('<line x1="40" y1="%s" x2="848" y2="%s" stroke="%s" stroke-width="1"/>' % (ty, ty, T["line"]))
    gate_x = 643
    b.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1" stroke-dasharray="2 4"/>' % (gate_x, y + h, gate_x, ty - 14, T["line"]))
    b.append('<rect x="%s" y="%s" width="4" height="30" rx="2" fill="%s"/>' % (gate_x - 2, ty - 15, T["line"]))
    b.append('<rect x="%s" y="%s" width="4" height="30" rx="2" fill="%s" class="gflash"/>' % (gate_x - 2, ty - 15, T["danger"]))
    lab, _ = doc.text("held for approval", gate_x + 12, ty - 20, "mono", 11, T["danger"])
    b.append('<g class="glab">%s</g>' % lab)
    pk = []
    labels = [("R0 · read", T["ok"]), ("R1 · navigate", T["ok"]), ("R4 · destructive", T["danger"])]
    for i, (lbl, col) in enumerate(labels):
        c, w = chip(doc, T, lbl, col, col)
        pk.append('<g transform="translate(%s %s)"><g class="pk%d">%s</g></g>' % (f(40 + w / 2), ty, i, c))
    b.append('<g class="motion">%s</g>' % "".join(pk))
    st = []
    xx = 40
    for i, (lbl, col) in enumerate(labels):
        c, w = chip(doc, T, lbl, col, col)
        st.append('<g transform="translate(%s %s)">%s</g>' % (f(xx + w / 2 + (0 if i < 2 else 0)), ty + 0, c))
        xx += w + 12
    b.append('<g class="still">%s</g>' % "".join(st))
    # timings: one 12 s cycle, three requests
    w_r4 = font("mono").width(labels[2][0], 11) + 22
    stop = gate_x - 6 - 40 - w_r4  # stop with the chip's right edge at the gate
    doc.css.append("""
.pk0,.pk1,.pk2{opacity:0}
.pk0{animation:pk0 12s cubic-bezier(.45,0,.55,1) infinite}
.pk1{animation:pk1 12s cubic-bezier(.45,0,.55,1) infinite}
.pk2{animation:pk2 12s ease-in-out infinite}
@keyframes pk0{0%%{transform:translateX(0);opacity:0}3%%{opacity:1}27%%{transform:translateX(%(e)spx);opacity:1}31%%,100%%{transform:translateX(%(e)spx);opacity:0}}
@keyframes pk1{0%%,33%%{transform:translateX(0);opacity:0}36%%{opacity:1}58%%{transform:translateX(%(e)spx);opacity:1}62%%,100%%{transform:translateX(%(e)spx);opacity:0}}
@keyframes pk2{0%%,66%%{transform:translateX(0);opacity:0}69%%{opacity:1}82%%{transform:translateX(%(s)spx);opacity:1}95%%{transform:translateX(%(s)spx);opacity:1}99%%,100%%{transform:translateX(%(s)spx);opacity:0}}
.gflash,.glab{opacity:0;animation:gf 12s linear infinite}
@keyframes gf{0%%,81%%{opacity:0}83%%{opacity:1}95%%{opacity:1}98%%,100%%{opacity:0}}
""" % dict(e=f(808 - 120), s=f(stop)))
    doc.css.append(REDUCED + ".still .gflash{opacity:1}")
    return doc


def unburden(T):
    W, H = 880, 330
    doc = Doc(W, H, "Unburden Root",
              "Unburden Root, the harness I work in every day. Diagram: Claude Code sessions run as named roles "
              "(orchestrator, lane, reviewer) through a core of hooks, persistent memory and written rulings, then a PII "
              "guard that fails closed, then a router that sends work to model pools by cost and urgency. Animated: work "
              "flows through; a request carrying PII is blocked at the guard. Private; a write-up will follow.")
    doc.css.append(frame_css())
    card_frame(doc, T, W, H)
    card_head(doc, T, W, "DAILY DRIVER  ·  PRIVATE, WRITE-UP TO FOLLOW", "Unburden Root",
              "The harness I work in every day.", "Routes work across model pools", "by cost and urgency.")
    b = doc.body
    lab, _ = doc.text("sessions as named roles", 32, 160, "mono", 11, T["dim"])
    b.append(lab)
    core = (338, 228)
    for i, role in enumerate(["orchestrator", "lane", "reviewer"]):
        yy = 172 + i * 38
        b.append('<path d="M182 %sC236 %s 250 %s %s %s" fill="none" stroke="%s" stroke-width="1.6" stroke-dasharray="3 5" class="flow"/>'
                 % (f(yy + 15), f(yy + 15), f(core[1]), f(core[0] - 44), f(core[1]), T["line"]))
        t, _ = doc.text(role, 58, yy + 20, "sansb", 13.5, T["text"])
        b.append('<g class="rise" style="animation-delay:%ss"><rect x="32" y="%s" width="150" height="30" rx="15" fill="%s" stroke="%s"/>'
                 '<g transform="translate(46 %s)"><circle r="4" fill="%s"/><circle r="4" fill="%s" class="pulse" style="animation-delay:%ss"/></g>%s</g>'
                 % (f(0.25 + 0.1 * i, 2), yy, T["chip"], T["chipStroke"], yy + 15, T["ok"], T["ok"], f(i * 0.8, 2), t))
    # core ring
    b.append('<circle cx="%s" cy="%s" r="44" fill="%s" stroke="%s" stroke-width="1.5"/>' % (core[0], core[1], T["chip"], T["chipStroke"]))
    b.append('<circle cx="%s" cy="%s" r="30" fill="none" stroke="%s" stroke-dasharray="2 4"/>' % (core[0], core[1], T["line"]))
    doc.css.append(".orb{transform-box:view-box;transform-origin:0 0;animation:orb 9s linear infinite}@keyframes orb{to{transform:rotate(360deg)}}")
    b.append('<g transform="translate(%s %s)"><g class="orb"><circle cx="44" cy="0" r="4.5" fill="%s"/></g></g>' % (core[0], core[1], T["gold"]))
    ct, _ = doc.text("core", core[0], core[1] + 5, "mono", 12.5, T["text"], anchor="middle")
    b.append(ct)
    for (lbl, dx, dy, anc) in [("hooks", 0, -56, "middle"), ("memory", -40, 66, "middle"), ("rulings", 42, 66, "middle")]:
        t, _ = doc.text(lbl, core[0] + dx, core[1] + dy, "mono", 11.5, T["gold"], anchor=anc)
        b.append(t)
    # guard
    gx, gy, gw, gh = 448, 198, 118, 60
    b.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="2"/>' % (core[0] + 44, core[1], gx, core[1], T["line"]))
    t1, _ = doc.text("PII guard", gx + 14, gy + 26, "sansb", 15, T["text"])
    t2, _ = doc.text("fails closed", gx + 14, gy + 45, "mono", 11.5, T["dim"])
    b.append('<rect x="%s" y="%s" width="%s" height="%s" rx="12" fill="%s" stroke="%s"/>%s%s' % (gx, gy, gw, gh, T["chip"], T["chipStroke"], t1, t2))
    bar_x = gx + gw + 14
    b.append('<rect x="%s" y="%s" width="4" height="40" rx="2" fill="%s"/>' % (bar_x - 2, core[1] - 20, T["line"]))
    b.append('<rect x="%s" y="%s" width="4" height="40" rx="2" fill="%s" class="gflash"/>' % (bar_x - 2, core[1] - 20, T["danger"]))
    bl, _ = doc.text("blocked", bar_x + 8, core[1] - 26, "mono", 11, T["danger"])
    b.append('<g class="glab">%s</g>' % bl)
    # router
    rx_, ry_ = 626, core[1]
    b.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="2"/>' % (gx + gw, core[1], rx_ - 15, core[1], T["line"]))
    b.append('<circle cx="%s" cy="%s" r="15" fill="%s" stroke="%s" stroke-width="1.5"/>' % (rx_, ry_, T["chip"], T["gold"]))
    b.append('<path d="M%s %sh6m0 0l6-6m-6 6l6 6m-6-6h6" fill="none" stroke="%s" stroke-width="1.6" stroke-linecap="round"/>' % (rx_ - 8, ry_, T["gold"]))
    rl, _ = doc.text("cost × urgency", rx_, ry_ + 38, "mono", 11, T["dim"], anchor="middle")
    b.append(rl)
    pl, _ = doc.text("model pools", 690, 166, "mono", 11, T["dim"])
    b.append(pl)
    lanes = []
    for i, yy in enumerate([188, 228, 268]):
        b.append('<path d="M%s %sC%s %s %s %s 690 %s" fill="none" stroke="%s" stroke-width="1.6"/>'
                 % (rx_ + 15, ry_, rx_ + 40, ry_, 660, yy, yy, T["line"]))
        b.append('<rect x="690" y="%s" width="158" height="26" rx="13" fill="%s" stroke="%s"/>' % (yy - 13, T["chip"], T["chipStroke"]))
        lanes.append('<clipPath id="ln%d"><rect x="692" y="%s" width="154" height="22" rx="11"/></clipPath>' % (i, yy - 11))
        dur = [2.4, 3.6, 5.2][i]
        dots = "".join('<circle cx="690" cy="%s" r="3.2" fill="%s" class="ld" style="animation-duration:%ss;animation-delay:-%ss"/>'
                       % (yy, T["ok"] if i != 1 else T["gold"], f(dur), f(dur * j / 3, 2)) for j in range(3))
        b.append('<g clip-path="url(#ln%d)">%s</g>' % (i, dots))
    doc.defs.extend(lanes)
    doc.css.append(".ld{animation:ld 3s linear infinite}@keyframes ld{from{transform:translateX(-10px)}to{transform:translateX(170px)}}")
    # packets core -> router; one red PII packet stopped at the guard
    pk = []
    for j in range(3):
        pk.append('<circle cx="%s" cy="%s" r="4" fill="%s" class="pw" style="animation-delay:%ss"/>' % (core[0] + 46, core[1], T["ok"], f(j * 2.0, 2)))
    pii, pw = chip(doc, T, "PII", T["danger"], T["danger"])
    pk.append('<g transform="translate(%s %s)"><g class="pii">%s</g></g>' % (core[0] + 46 + pw / 2, core[1] - 26, pii))
    b.append('<g class="motion">%s</g>' % "".join(pk))
    stop = bar_x - (core[0] + 46) - pw - 4
    doc.css.append("""
.pw{opacity:0;animation:pw 6s linear infinite}
@keyframes pw{0%%{transform:translateX(0);opacity:0}4%%{opacity:1}26%%{transform:translateX(%(e)spx);opacity:1}30%%,100%%{transform:translateX(%(e)spx);opacity:0}}
.pii{opacity:0;animation:pii 12s ease-in-out infinite}
@keyframes pii{0%%,55%%{transform:translate(0,0);opacity:0}58%%{opacity:1}66%%{transform:translate(%(s)spx,26px);opacity:1}88%%{transform:translate(%(s)spx,26px);opacity:1}92%%,100%%{transform:translate(%(s)spx,26px);opacity:0}}
.gflash,.glab{opacity:0;animation:gf 12s linear infinite}
@keyframes gf{0%%,65%%{opacity:0}67%%{opacity:1}88%%{opacity:1}91%%,100%%{opacity:0}}
""" % dict(e=f(rx_ - 15 - core[0] - 46), s=f(stop)))
    doc.css.append(REDUCED)
    return doc


# ----------------------------------------------------------------------------------------------
# toolkit
# ----------------------------------------------------------------------------------------------
TOOL, DONE, ONGOING, DISTINCTION = "tool", "done", "ongoing", "distinction"
COLUMNS = [
    ("Agents and applied AI", "agents", [
        (TOOL, "Claude Code"), (TOOL, "MCP servers and clients"), (TOOL, "Multi-agent orchestration"),
        (TOOL, "Hooks, memory, written rulings"), (TOOL, "Model routing by cost and urgency"), (DONE, "AI for Impact")]),
    ("Security", "shield", [
        (DISTINCTION, "Digital Forensics and Investigation"), (DONE, "Ethical Hacking Essentials"), (DONE, "Offensive Security"),
        (DONE, "Linux Administration and Security"), (DONE, "Securing Microsoft Windows"),
        (ONGOING, "Malware Reverse Engineering"), (ONGOING, "Applied Cryptography"), (ONGOING, "Data Protection for Cyber Security")]),
    ("Build", "code", [
        (TOOL, "Rust"), (TOOL, "TypeScript"), (TOOL, "Android and adb"), (DONE, "Back-End Web Development"),
        (DONE, "Front-End Web Development"), (DONE, "Programming Methodology")]),
]


def star(r, inner=0.45):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * inner
        pts.append("%s %s" % (f(rr * math.cos(a)), f(rr * math.sin(a))))
    return "M" + "L".join(pts) + "Z"


def marker(T, kind, x, y, i):
    if kind == TOOL:
        return '<rect x="-3.6" y="-3.6" width="7.2" height="7.2" rx="1" transform="translate(%s %s) rotate(45)" fill="%s"/>' % (f(x), f(y), T["accent"])
    if kind == DONE:
        return '<circle cx="%s" cy="%s" r="4" fill="%s"/>' % (f(x), f(y), T["ok"])
    if kind == ONGOING:
        return ('<g transform="translate(%s %s)"><circle r="4.6" fill="none" stroke="%s" stroke-width="1.6" stroke-dasharray="3 2.4" class="spin"/></g>'
                % (f(x), f(y), T["ok"]))
    return '<g transform="translate(%s %s)"><path d="%s" fill="%s" class="twk"/></g>' % (f(x), f(y), star(6.4), T["gold"])


def icon(T, kind, x, y):
    c = T["gold"]
    if kind == "agents":
        d = ('<path d="M7 22L14 8L21 22Z" fill="none" stroke="%s" stroke-width="1.4" stroke-opacity=".6"/>'
             '<circle cx="7" cy="22" r="4" fill="%s"/><circle cx="21" cy="22" r="4" fill="%s"/><circle cx="14" cy="8" r="4" fill="%s"/>') % (c, T["card"], T["card"], T["card"])
        d += '<circle cx="7" cy="22" r="4" fill="none" stroke="%s" stroke-width="1.8"/><circle cx="21" cy="22" r="4" fill="none" stroke="%s" stroke-width="1.8"/><circle cx="14" cy="8" r="4" fill="none" stroke="%s" stroke-width="1.8"/>' % (c, c, c)
    elif kind == "shield":
        d = ('<path d="M14 2l10 4v8c0 6.5-4.5 11-10 13-5.5-2-10-6.5-10-13V6z" fill="none" stroke="%s" stroke-width="1.8" stroke-linejoin="round"/>'
             '<circle cx="14" cy="13" r="2.6" fill="%s"/><path d="M14 15v5" stroke="%s" stroke-width="2" stroke-linecap="round"/>') % (c, c, c)
    else:
        d = '<path d="M9 8l-6 6 6 6M19 8l6 6-6 6M16 5l-4 18" fill="none" stroke="%s" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/>' % c
    return '<g transform="translate(%s %s)">%s</g>' % (f(x), f(y), d)


def toolkit(T):
    W, H = 960, 452
    desc = []
    for title, _, items in COLUMNS:
        desc.append("%s: %s." % (title, ", ".join(
            n + {TOOL: "", DONE: " (module)", ONGOING: " (module, in progress)", DISTINCTION: " (module, Distinction)"}[k] for k, n in items)))
    doc = Doc(W, H, "Toolkit", " ".join(desc))
    doc.css.append(frame_css())
    card_frame(doc, T, W, H)
    doc.css.append("""
.spin{transform-box:view-box;transform-origin:0 0;animation:spin 6s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}
.twk{transform-box:view-box;transform-origin:0 0;animation:twk 3.2s ease-in-out infinite}@keyframes twk{0%,100%{transform:scale(1) rotate(0)}50%{transform:scale(1.25) rotate(20deg)}}
.sweep{animation:sweep 7s ease-in-out infinite}@keyframes sweep{0%{transform:translateX(-120px);opacity:0}10%{opacity:1}60%{transform:translateX(300px);opacity:0}100%{opacity:0;transform:translateX(300px)}}
""")
    doc.defs.append('<linearGradient id="sw" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="%s" stop-opacity="0"/>'
                    '<stop offset=".5" stop-color="%s"/><stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient>' % (T["gold"], T["gold"], T["gold"]))
    b = doc.body
    col_w = 304
    for ci, (title, ic, items) in enumerate(COLUMNS):
        x0 = 28 + ci * col_w
        tt, _ = doc.text(title, x0 + 40, 50, "serif", 27, T["text"])
        b.append('<g class="rise" style="animation-delay:%ss">%s%s</g>' % (f(ci * 0.15, 2), icon(T, ic, x0, 26), tt))
        b.append('<line x1="%s" y1="70" x2="%s" y2="70" stroke="%s"/>' % (f(x0), f(x0 + 272), T["line"]))
        doc.defs.append('<clipPath id="sc%d"><rect x="%s" y="68" width="272" height="4"/></clipPath>' % (ci, f(x0)))
        b.append('<g clip-path="url(#sc%d)"><g class="sweep" style="animation-delay:%ss"><rect x="%s" y="69" width="110" height="2" fill="url(#sw)"/></g></g>'
                 % (ci, f(ci * 1.1, 2), f(x0)))
        for i, (kind, name) in enumerate(items):
            yy = 104 + i * 34
            size = 15.5
            while font("sans").width(name, size) > 248 and size > 12:
                size -= 0.25
            t, _ = doc.text(name, x0 + 22, yy + 5.5, "sans", size, T["text"] if kind != DONE else T["text"], opacity=None)
            b.append('<g class="rise" style="animation-delay:%ss">%s%s</g>' % (f(0.35 + ci * 0.12 + i * 0.07, 2), marker(T, kind, x0 + 6, yy, i), t))
    # legend
    lx, ly = 28, 420
    parts = [(TOOL, "tool or practice"), (DONE, "Singapore Polytechnic module"), (ONGOING, "module in progress"), (DISTINCTION, "Distinction")]
    b.append('<line x1="28" y1="388" x2="%d" y2="388" stroke="%s"/>' % (W - 28, T["line"]))
    for kind, lbl in parts:
        b.append(marker(T, kind, lx + 6, ly - 4, 0))
        t, w = doc.text(lbl, lx + 18, ly, "mono", 11.5, T["dim"])
        b.append(t)
        lx += w + 44
    doc.css.append(REDUCED)
    return doc


# ----------------------------------------------------------------------------------------------
# track record
# ----------------------------------------------------------------------------------------------
def record(T):
    W, H = 880, 280
    doc = Doc(W, H, "Track record",
              "HTB Cyber Apocalypse CTF 2026: 30th of 6,744 teams, the top 0.45 percent. Singapore Cyber Conquest 2026: "
              "student finalist. BrainHack CDDC 2026: finalist, Explorer category.")
    doc.css.append(frame_css())
    card_frame(doc, T, W, H)
    b = doc.body
    e1, _ = doc.text("HTB CYBER APOCALYPSE CTF 2026", 32, 48, "cap", 12, T["gold"], tracking=0.12)
    n1, nw = doc.text("30th", 30, 124, "num", 84, T["accent"])
    o1, _ = doc.text("of 6,744 teams", 30 + nw + 14, 122, "sans", 20, T["text"])
    b.append('<g class="rise">%s%s%s</g>' % (e1, n1, o1))
    bx0, bx1, by = 470, 848, 98
    frac = 30 / 6744
    mx = bx0 + (bx1 - bx0) * frac
    b.append('<rect x="%s" y="%s" width="%s" height="10" rx="5" fill="%s" stroke="%s"/>' % (bx0, by - 5, bx1 - bx0, T["chip"], T["chipStroke"]))
    # one tick per 500 teams, so the scale reads as a field of teams
    ticks = "".join('<line x1="%s" y1="%s" x2="%s" y2="%s"/>' % (f(bx0 + (bx1 - bx0) * k * 500 / 6744), by - 2, f(bx0 + (bx1 - bx0) * k * 500 / 6744), by + 2)
                    for k in range(1, 14))
    b.append('<g stroke="%s" stroke-width="1">%s</g>' % (T["line"], ticks))
    l1, _ = doc.text("1", bx0, by + 26, "mono", 11, T["dim"])
    l2, _ = doc.text("6,744", bx1, by + 26, "mono", 11, T["dim"], anchor="end")
    b.append(l1 + l2)
    top, _ = doc.text("30th  ·  top 0.45%", 0, -16, "mono", 12, T["accent"])
    mk = ('<g transform="translate(%s %s)"><g class="mk"><path d="M0-9l5 9-5 9-5-9z" fill="%s"/>'
          '<circle r="5" fill="%s" class="pulse"/><g transform="translate(-4 0)">%s</g></g></g>' % (f(mx), by, T["accent"], T["accent"], top))
    b.append(mk)
    doc.css.append(".mk{animation:mk 1.8s cubic-bezier(.16,1,.3,1) .4s both}@keyframes mk{from{transform:translateX(%spx);opacity:0}to{transform:none;opacity:1}}"
                   % f(bx1 - mx))
    b.append('<line x1="32" y1="164" x2="848" y2="164" stroke="%s"/>' % T["line"])
    for i, (eyebrow, big) in enumerate([("SINGAPORE CYBER CONQUEST 2026", "Student finalist"), ("BRAINHACK CDDC 2026", "Finalist, Explorer")]):
        x0 = 32 + i * 438
        e, _ = doc.text(eyebrow, x0, 204, "cap", 12, T["gold"], tracking=0.12)
        t, _ = doc.text(big, x0 - 2, 250, "serif", 40, T["text"])
        b.append('<g class="rise" style="animation-delay:%ss">%s%s</g>' % (f(0.3 + i * 0.15, 2), e, t))
    b.append('<line x1="455" y1="186" x2="455" y2="256" stroke="%s"/>' % T["line"])
    doc.css.append(REDUCED)
    return doc


# ----------------------------------------------------------------------------------------------
# footer: a small round of the pond
# ----------------------------------------------------------------------------------------------
def footer(T):
    W, H = 880, 120
    doc = Doc(W, H, "Koi pond footer", "Two koi chase each other around a narrow pond with a lily pad.")
    koi_defs(doc)
    shadow_filter(doc, T, 3.5)
    doc.css.append(frame_css())
    doc.defs.append('<clipPath id="ff"><rect x="1" y="1" width="%d" height="%d" rx="24"/></clipPath>' % (W - 2, H - 2))
    doc.defs.append('<radialGradient id="fbg" cx=".5" cy=".5" r=".7"><stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></radialGradient>'
                    % (T["bgA"], T["bgB"]))
    b = doc.body
    b.append('<g clip-path="url(#ff)"><rect width="%d" height="%d" fill="url(#fbg)"/>' % (W, H))
    b.append(caustics(doc, T, W, H, scale=0.6))
    loop = loop_pts(440, 60, 360, 30, n=12, jit=0.05, seed=5)
    s1, g1 = swimmer(doc, "kohaku", loop, 40, 0.42, 0.0, wag=1.5, N=8)
    s2, g2 = swimmer(doc, "ogon", loop, 40, 0.44, 0.5, wag=1.7, N=8)
    b.append('<g class="motion"><use href="#%s" transform="translate(6 8)" filter="url(#shd)"/><use href="#%s" transform="translate(6 8)" filter="url(#shd)"/>%s%s</g>'
             % (s1, s2, g1, g2))
    b.append('<g class="still">%s%s</g>' % (still_koi(doc, "kohaku", 300, 40, 0, 0.42), still_koi(doc, "ogon", 560, 82, 180, 0.44)))
    rp, rcss = ripples([(180, 70, 1.0), (700, 40, 4.2)], "#ffffff", 1.2, 40, 7.5, 0.4 if T["name"] == "dark" else 0.8)
    doc.css.append(rcss)
    b.append(rp)
    doc.css.append(".drA{animation:drA 15s ease-in-out infinite alternate;transform-box:view-box;transform-origin:0 0}"
                   "@keyframes drA{to{transform:translate(-6px,4px) rotate(-5deg)}}")
    grads, pads = [], []
    for (cx, cy, rr, notch, seed) in [(0, 0, 34, 200, 41), (-44, 34, 20, 40, 42)]:
        g_, p_ = lily_pad(T, cx, cy, rr, notch, seed)
        grads.append(g_)
        pads.append(p_)
    doc.defs.extend(grads)
    b.append('<g transform="translate(842 22)"><g class="drA">%s</g></g>' % "".join(pads))
    b.append('</g><rect x="1" y="1" width="%d" height="%d" rx="24" fill="none" stroke="%s"/>' % (W - 2, H - 2, T["stroke"]))
    doc.css.append(REDUCED)
    return doc


# ----------------------------------------------------------------------------------------------
# projects: one small card per project, each its own image so the README can link each one
# ----------------------------------------------------------------------------------------------
# (slug, eyebrow, title, description, link or None, status line, koi variety)
PROJECTS = [
    ("agentroid", "ANDROID  ·  MCP  ·  RUST", "Agentroid",
     "Any MCP client drives Android emulators, with no model API key of its own: deny-by-default adb, a device "
     "allowlist and a risk label on every action.", None, "OPEN-SOURCE RELEASE COMING SOON", "kohaku"),
    ("unburden-root", "MULTI-AGENT HARNESS", "Unburden Root",
     "Claude Code sessions work as named roles with shared memory and written rules; work is routed to model "
     "pools by cost, and a PII guard fails closed.", None, "PRIVATE  ·  WRITE-UP COMING SOON", "ogon"),
    ("bb-portal", "NEXT.JS  ·  REACT  ·  SUPABASE", "BB Master Portal",
     "Awards, attendance and training-programme records for the Boys' Brigade 5th Singapore Company.", None,
     "IN DEVELOPMENT  ·  COMING SOON", "showa"),
    ("show-me-your-agents", "NUS-ISS HACKATHON 2026", "Show Me Your Agents",
     "Team Unburden, four of us: an agentic AI answer to a real business problem, with AWS and the Singapore "
     "Business Federation.", None, "WRITE-UP COMING SOON", "tancho"),
    ("tv-home-screen", "THIS PROFILE  ·  SVG  ·  PYTHON", "My TV, as a banner",
     "The banner above: my TV's home screen rebuilt as one animated SVG, 23 paintings, the name behind each "
     "subject and live Claude usage.", "https://github.com/Sohwhat6420/Sohwhat6420", "OPEN ON GITHUB", "ogon"),
    ("st2612-est", "STUDY HARNESS  ·  AGENTS", "ST2612 EST System",
     "An open-book exam harness for Securing Microsoft Windows: a knowledge base, adversarial audit agents and "
     "an answer pipeline.", "https://github.com/Sohwhat6420/ST2612-EST-System", "OPEN ON GITHUB", "kohaku"),
]


def wrap(s, key, size, width):
    out, cur = [], ""
    for w in s.split():
        t = (cur + " " + w).strip()
        if cur and font(key).width(t, size) > width:
            out.append(cur)
            cur = w
        else:
            cur = t
    return out + ([cur] if cur else [])


def project(T, i, slug, eyebrow, title, desc, link, status, variety):
    W, H = 430, 236
    doc = Doc(W, H, title, "%s. %s %s." % (title, desc, "Links to " + link if link else status.title()))
    doc.css.append(frame_css())
    card_frame(doc, T, W, H)
    b = doc.body
    e, _ = doc.text(eyebrow, 24, 38, "cap", 11, T["gold"], tracking=0.12)
    t, _ = doc.text(title, 22, 78, "serif", 34, T["text"])
    lines = "".join(doc.text(s, 24, 106 + 20 * k, "sans", 14.5, T["dim"])[0] for k, s in enumerate(wrap(desc, "sans", 14.5, W - 48)[:3]))
    b.append('<g class="rise" style="animation-delay:%ss">%s%s%s</g>' % (f(0.08 * i, 2), e, t, lines))
    # the status line: a live link nudges its arrow; a coming-soon project breathes a gold dot
    sy = H - 50
    if link:
        s, sw = doc.text(status, 24, sy + 4, "cap", 11.5, T["accent"], tracking=0.12)
        b.append(s)
        doc.css.append(".nudge{animation:nudge 1.8s cubic-bezier(.5,0,.3,1) infinite}@keyframes nudge{0%,100%{transform:none}50%{transform:translateX(5px)}}")
        b.append('<g class="nudge"><path d="M%s %sh14m-5-5 5 5-5 5" fill="none" stroke="%s" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></g>'
                 % (f(24 + sw + 10), f(sy), T["accent"]))
    else:
        b.append('<circle cx="29" cy="%s" r="4" fill="%s"/><circle cx="29" cy="%s" r="4" fill="%s" class="pulse" style="transform-origin:29px %spx;transform-box:view-box"/>'
                 % (f(sy), T["gold"], f(sy), T["gold"], f(sy)))
        s, _ = doc.text(status, 42, sy + 4, "cap", 11.5, T["dim"], tracking=0.12)
        b.append(s)
    doc.css.append(REDUCED)
    return doc


HEADERS = [
    ("01", "Now building", motifs.agent_phone,
     "In a glass window beside it, an agent's cursor taps an app on a small phone, then an R4 delete action is held at the gate for approval."),
    ("02", "Projects", motifs.f1,
     "In a glass window beside it, an F1 car runs a glowing racing line through an S-bend, trailing light."),
    ("03", "Track record", motifs.handshake,
     "In a glass window beside it, SYN, SYN-ACK and ACK packets cross between two nodes, then a flag is captured on the target."),
]


def token_total():
    """His Claude Code token total, as the TV hub measured it (the hub's /api/activity, else the last copy refresh.py
    kept in .live/activity.json). Returns (total, 'D Mon YYYY') or (None, None): the odometer then turns with no number."""
    import datetime as dt
    import json
    import urllib.request
    # TOKEN_TOTAL_OVERRIDE="63545988543|11 Nov 2026": a total counted from the session logs (deduplicated), used in place of
    # the hub's figure. The hub's /api/activity reads the plan's own meter, which counts each reply more than once.
    ov = os.environ.get("TOKEN_TOTAL_OVERRIDE")
    if ov:
        n, d = ov.split("|")
        return int(n), d.strip()
    src = None
    try:
        with urllib.request.urlopen("http://127.0.0.1:8790/api/activity", timeout=5) as r:
            src = json.load(r)
    except Exception:
        p = os.path.join(os.path.dirname(OUT), ".live", "activity.json")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as fh:
                src = json.load(fh)
    if not src or not src.get("total") or not src.get("made"):
        return None, None
    made = dt.datetime.fromisoformat(src["made"].replace("Z", "+00:00")).astimezone(dt.timezone(dt.timedelta(hours=8)))
    return int(src["total"]), "%d %s" % (made.day, made.strftime("%b %Y"))


def main():
    """The cards under the README's banner, all ghost glass in the TV widgets' tokens: the typed focus line, three
    glass tiles (helmet, token odometer, BB and Taekwondo), three section headings each with its animated motif, the
    Agentroid and Unburden Root diagrams, the track record, one card per project, the weather divider and the Concorde
    footer. The koi pond hero, toolkit and koi footer are retired."""
    total, as_of = token_total()
    print("tokens: %s (%s)" % (total, as_of or "no reading: the odometer turns with no number"))
    tok_desc = ("Odometer digits roll up to %d billion: tokens on Claude Code, as shown on its /stats screen, to %s. /stats counts each "
                "part of a reply separately; counted once per reply across Claude, Gemini and Codex it is 67.5 billion."
                % (int(total // 1e9), as_of) if total else "Odometer digits turning: my Claude Code token count.")
    report = []
    for name, T in THEMES.items():
        random.seed(1)
        report.append(write("typing", name, typing(T)))
        report.append(write("about-helmet", name, tile(T, "helmet", "Spartan",
                            "An original gold line drawing of a crested Greek helmet draws itself, then a light sweeps across it.",
                            motifs.helmet)))
        report.append(write("about-tokens", name, tile(T, "tokens", "Tokens on Claude Code", tok_desc,
                            lambda d, t, x, y, w, h: motifs.tokens(d, t, x, y, w, h, total, as_of))))
        report.append(write("about-bb-tkd", name, tile(T, "bb", "Boys' Brigade and Taekwondo",
                            "A Boys' Brigade chevron and a Taekwondo black-belt knot draw themselves in gold lines.",
                            motifs.bb_tkd)))
        for idx, title, motif, desc in HEADERS:
            report.append(write("h%s-%s" % (idx, title.lower().replace(" ", "-")), name, header(T, idx, title, motif, desc)))
        report.append(write("card-agentroid", name, agentroid(T)))
        report.append(write("card-unburden-root", name, unburden(T)))
        report.append(write("track-record", name, record(T)))
        for i, p in enumerate(PROJECTS):
            report.append(write("project-" + p[0], name, project(T, i, *p)))
        report.append(write("divider-weather", name, band(T, "Weather",
                            "My TV's live weather layer: rain streaks and drifting cloud, a lightning flash, then a golden-hour glow.",
                            motifs.weather, 110)))
        report.append(write("footer-concorde", name, band(T, "Concorde",
                            "Concorde rolls along a wet runway, rotates and climbs away, heat shimmering behind its engines.",
                            motifs.concorde, 150)))
    for p, s in report:
        print("%7.1f KB  %s" % (s / 1024, os.path.basename(p)))


if __name__ == "__main__":
    main()
