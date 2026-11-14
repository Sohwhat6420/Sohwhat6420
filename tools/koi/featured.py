"""Builds the README's project cards, section headings, typed focus line and projects tile (assets/*-dark.svg,
*-light.svg), in the same ghost glass as cards.py.

    python tools/koi/featured.py

Run this, not cards.py's main(): the stat tiles and repo cards already in assets/ come from a newer build on the
laptop, and cards.main() would overwrite them (the token odometer needs the TV hub).

Every image on a card is a real product shot, kept small in tools/shots/ (2x the card's window) and embedded as a
data URI, because GitHub serves README images as <img> with a CSP that fetches nothing:
  agentroid-look.jpg, agentroid-job.jpg   the last frames of agentroid-mcp's docs/media/demo-1.gif and demo-3.gif
  council-chart-*.jpg                     human-llm-council's docs/img/held-out-{light,dark}.svg, rendered
  council-retest-*.jpg                    its build/retest page, served by its own server over its synthetic fixtures
  hk-*.jpg                                the top of headless-kit's real terminal demos (tools/*/docs/demo.svg)
  dytv-*.jpg                              designyourtv's docs/screens/*.webp (its demo, headless Chromium, 1920x1080)
  thumb-*.jpg                             the screens already on the designyourwindows, Sidemic and film-simulation cards
Every number on a card comes from that repository's public README (14 Nov 2026); the alt text says the same.
Motion is CSS only (no scripts, no SMIL needed): frames cross-fade with a slow Ken Burns drift and progress pips,
and under prefers-reduced-motion each card rests on its first frame (koilib.REDUCED).
"""
import base64
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from koilib import Doc, THEMES, REDUCED, GLASS_PAD, f, font, glass   # noqa: E402
import motifs   # noqa: E402
import cards    # noqa: E402

SHOTS = os.path.join(os.path.dirname(HERE), "shots")
_URI = {}


def uri(name):
    if name not in _URI:
        with open(os.path.join(SHOTS, name), "rb") as fh:
            _URI[name] = "data:image/jpeg;base64," + base64.b64encode(fh.read()).decode("ascii")
    return _URI[name]


def cap(doc, s, x, y, size, colour, anchor="start"):
    return doc.text(s.upper(), x, y, "cap", size, colour, tracking=0.12, anchor=anchor)


# ----------------------------------------------------------------------------------------------
# the rotation: real frames cross-fading in a window, with a Ken Burns drift, a sheen and progress pips
# ----------------------------------------------------------------------------------------------
def rotator(doc, T, x, y, w, h, frames, hold=4.6, fade=0.9, r=11, captions=None, cap_at=None, pips_at=None):
    p = doc.uid("ro")
    n = len(frames)
    C = n * hold
    pct = lambda t: f(100 * max(0.0, min(C, t)) / C, 2)
    doc.defs.append('<clipPath id="%sw"><rect x="%s" y="%s" width="%s" height="%s" rx="%s"/></clipPath>'
                    % (p, f(x), f(y), f(w), f(h), f(r)))
    doc.defs.append('<linearGradient id="%sv" x1="0" y1="0" x2="0" y2="1"><stop offset=".55" stop-color="#000" stop-opacity="0"/>'
                    '<stop offset="1" stop-color="#000" stop-opacity=".38"/></linearGradient>' % p)
    doc.defs.append('<linearGradient id="%ss" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                    '<stop offset=".5" stop-color="#fff" stop-opacity=".16"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>' % p)
    css = [".%sk{transform-box:fill-box;transform-origin:50%% 50%%;animation:%sk 18s ease-in-out infinite alternate}"
           "@keyframes %sk{from{transform:scale(1)}to{transform:scale(1.07) translate(-1.5%%,-1%%)}}" % (p, p, p),
           ".%sj{transform-box:fill-box;transform-origin:50%% 50%%;animation:%sj 18s ease-in-out infinite alternate}"
           "@keyframes %sj{from{transform:scale(1.07) translate(1.5%%,.5%%)}to{transform:scale(1)}}" % (p, p, p),
           ".%ssw{animation:%ssw 9s ease-in-out infinite}@keyframes %ssw{0%%,40%%{transform:translateX(-%spx)}75%%,100%%{transform:translateX(%spx)}}"
           % (p, p, p, f(w * 0.7), f(w * 1.4))]
    out = ['<g clip-path="url(#%sw)">' % p]
    for k, img in enumerate(frames):
        el = ('<image href="%s" x="%s" y="%s" width="%s" height="%s" preserveAspectRatio="xMidYMid slice"/>'
              % (uri(img), f(x), f(y), f(w), f(h)))
        cls = "%sf%d" % (p, k)
        out.append('<g class="%s"><g class="%s%s">%s</g></g>' % (cls, p, "k" if k % 2 == 0 else "j", el))
        if k:
            a, b = k * hold, k * hold + fade
            if k < n - 1:
                c = (k + 1) * hold + fade
                e = c + 0.05
            else:
                c, e = C - fade, C
            css.append(".%s{opacity:0;animation:%s %ss linear infinite}@keyframes %s{0%%,%s%%{opacity:0}%s%%,%s%%{opacity:1}%s%%,100%%{opacity:0}}"
                       % (cls, cls, f(C, 2), cls, pct(a), pct(b), pct(c), pct(e)))
    out.append('<rect x="%s" y="%s" width="%s" height="%s" fill="url(#%sv)"/>' % (f(x), f(y), f(w), f(h), p))
    out.append('<g class="%ssw"><rect x="%s" y="%s" width="%s" height="%s" fill="url(#%ss)"/></g>' % (p, f(x), f(y), f(w * 0.45), f(h), p))
    out.append("</g>")
    out.append('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="none" stroke="#ffffff" stroke-opacity="%s"/>'
               % (f(x + 0.5), f(y + 0.5), f(w - 1), f(h - 1), f(r), ".22" if T["name"] == "dark" else ".55"))
    if n > 1:
        # progress pips: one bar per frame, filling while its frame is on top
        px, py = pips_at or (x + w - 14 - (n * 18 - 6), y + h - 14)
        if not pips_at:
            out.append('<rect x="%s" y="%s" width="%s" height="13" rx="6.5" fill="#000" fill-opacity=".38"/>' % (f(px - 7), f(py - 5), f(n * 18 + 8)))
        track = "#ffffff" if not pips_at or T["name"] == "dark" else T["text"]
        for k in range(n):
            bx = px + k * 18
            out.append('<rect x="%s" y="%s" width="12" height="3" rx="1.5" fill="%s" fill-opacity=".3"/>' % (f(bx), f(py), track))
            cls = "%sp%d" % (p, k)
            out.append('<rect x="%s" y="%s" width="12" height="3" rx="1.5" fill="%s" class="%s"/>'
                       % (f(bx), f(py), track if not pips_at else T["accent"], cls))
            a, b = k * hold, (k + 1) * hold
            css.append(".%s{transform-box:fill-box;transform-origin:0 50%%;transform:scaleX(%s);animation:%s %ss linear infinite}"
                       "@keyframes %s{0%%,%s%%{transform:scaleX(0);opacity:1}%s%%{transform:scaleX(1);opacity:1}%s%%,100%%{transform:scaleX(1);opacity:0}}"
                       % (cls, "1" if k == 0 else "0", cls, f(C, 2), cls, pct(a), pct(b), pct(b + 0.25)))
    if captions:
        cx, cy = cap_at
        for k, s in enumerate(captions):
            t, _ = doc.text(s, cx, cy, "mono", 11.5, T["dim"])
            cls = "%sc%d" % (p, k)
            out.append('<g class="%s">%s</g>' % (cls, t))
            if k == 0:
                css.append(".%s{animation:%s %ss linear infinite}@keyframes %s{0%%,%s%%{opacity:1}%s%%,%s%%{opacity:0}100%%{opacity:1}}"
                           % (cls, cls, f(C, 2), cls, pct(hold - 0.2), pct(hold + 0.2), pct(C - fade)))
            else:
                a, b = k * hold, (k + 1) * hold if k < n - 1 else C - fade
                css.append(".%s{opacity:0;animation:%s %ss linear infinite}@keyframes %s{0%%,%s%%{opacity:0}%s%%,%s%%{opacity:1}%s%%,100%%{opacity:0}}"
                           % (cls, cls, f(C, 2), cls, pct(a), pct(a + 0.4), pct(b - 0.2), pct(b + 0.2)))
    doc.css.append("\n".join(css))
    return "".join(out)


def nudge_link(doc, T, label, x, y):
    s, sw = cap(doc, label, x, y + 4, 11.5, T["accent"])
    doc.css.append(".nudge{animation:nudge 1.8s cubic-bezier(.5,0,.3,1) infinite}@keyframes nudge{0%,100%{transform:none}50%{transform:translateX(5px)}}")
    return s + ('<g class="nudge"><path d="M%s %sh14m-5-5 5 5-5 5" fill="none" stroke="%s" stroke-width="1.8" stroke-linecap="round" '
                'stroke-linejoin="round"/></g>' % (f(x + sw + 10), f(y), T["accent"]))


def breathe_dot(doc, T, x, y):
    return ('<circle cx="%s" cy="%s" r="4" fill="%s"/><circle cx="%s" cy="%s" r="4" fill="%s" class="pulse" '
            'style="transform-origin:%spx %spx;transform-box:view-box"/>' % (f(x), f(y), T["gold"], f(x), f(y), T["gold"], f(x), f(y)))


# ----------------------------------------------------------------------------------------------
# Agentroid: the wide card that opens the section
# ----------------------------------------------------------------------------------------------
AGENTROID_ROWS = [
    ("tree", "Text, not screenshots", ["The screen comes back as a numbered UI tree,", "or just what changed since an earlier snapshot."]),
    ("steps", "Six taps, one call", ["job_start runs the steps on the daemon, with", "no model round trip between them."]),
    ("zero", "Zero tokens for the bridge", ["No model calls and no API key of its own:", "your agent is the only brain in the loop."]),
]


def row_icon(T, kind, x, y):
    c = T["gold"]
    if kind == "tree":
        d = ('<path d="M4 4h6M4 4v16M4 11h5M4 18h5" fill="none" stroke="%s" stroke-width="1.7" stroke-linecap="round"/>'
             '<rect x="11" y="8.5" width="9" height="5" rx="1.6" fill="none" stroke="%s" stroke-width="1.6"/>'
             '<rect x="11" y="15.5" width="9" height="5" rx="1.6" fill="none" stroke="%s" stroke-width="1.6"/>'
             '<rect x="12" y="1.5" width="9" height="5" rx="1.6" fill="%s" fill-opacity=".25" stroke="%s" stroke-width="1.6"/>') % (c, c, c, c, c)
    elif kind == "steps":
        d = ('<path d="M3 12h4M10 12h4M17 12h4" fill="none" stroke="%s" stroke-width="1.7" stroke-linecap="round"/>'
             '<circle cx="5" cy="12" r="2.6" fill="%s"/><circle cx="12" cy="12" r="2.6" fill="%s"/><circle cx="19" cy="12" r="2.6" fill="%s"/>'
             '<path d="M2 4.5h20" stroke="%s" stroke-width="1.7" stroke-linecap="round" stroke-dasharray="1 3.4"/>') % (c, c, c, c, c)
    else:
        d = ('<circle cx="12" cy="12" r="8.6" fill="none" stroke="%s" stroke-width="1.7"/>'
             '<path d="M6 18 18 6" stroke="%s" stroke-width="1.7" stroke-linecap="round"/>'
             '<path d="M12 7.6c2 0 3 1.9 3 4.4s-1 4.4-3 4.4-3-1.9-3-4.4 1-4.4 3-4.4z" fill="none" stroke="%s" stroke-width="1.5"/>') % (c, c, c)
    return '<g transform="translate(%s %s)">%s</g>' % (f(x), f(y), d)


def agentroid(T):
    W, H = 880, 420
    doc = Doc(W, H, "Agentroid",
              "Agentroid: an MCP server and a Rust daemon that let Claude Code look at and operate an Android phone or emulator "
              "over adb, built to spend as little of the agent's context as it can. The screen comes back as a numbered UI tree "
              "(text, not screenshots), or just what changed since an earlier snapshot; job_start runs several steps on the daemon with "
              "no model round trip between them; the bridge makes no model calls and needs no API key, so it reports 0 tokens "
              "for itself. 27 MCP tools, Apache-2.0, preview release. Beside it, two real recordings cross-fade: look then four "
              "taps on the phone's Calculator (7 × 6 = 42), and one job_start call running six steps (9 × 8 + 7 = 79). "
              "Opens github.com/Sohwhat6420/agentroid-mcp.")
    doc.css.append(cards.frame_css())
    cards.card_frame(doc, T, W, H)
    b = doc.body
    # the frames: 859 x 640 recordings, phone screen beside the tool calls
    fw, fh = 420, 313
    fx, fy = W - 24 - fw, 30
    b.append(rotator(doc, T, fx, fy, fw, fh, ["agentroid-look.jpg", "agentroid-job.jpg"], hold=5.2,
                     captions=["look, then 4 taps:  7 × 6 = 42", "1 job_start call, 6 steps:  9 × 8 + 7 = 79"],
                     cap_at=(fx + 2, fy + fh + 26), pips_at=(fx + fw - 30, fy + fh + 20)))
    e, _ = cap(doc, "MCP server  ·  Rust daemon  ·  preview", 32, 52, 11.5, T["gold"])
    t, _ = doc.text("Agentroid", 30, 104, "serif", 54, T["text"])
    s1, _ = doc.text("Claude Code drives an Android phone over MCP,", 32, 136, "sans", 16, T["text"])
    s2, _ = doc.text("and spends its context on the task, not the screen.", 32, 157, "sans", 16, T["dim"])
    b.append('<g class="rise">%s%s%s%s</g>' % (e, t, s1, s2))
    for k, (ic, head, lines) in enumerate(AGENTROID_ROWS):
        yy = 196 + k * 54
        h_, _ = doc.text(head, 66, yy + 6, "sansb", 14.5, T["text"])
        ls = "".join(doc.text(s, 66, yy + 24 + 16 * j, "sans", 12.8, T["dim"])[0] for j, s in enumerate(lines))
        b.append('<g class="rise" style="animation-delay:%ss">%s%s%s</g>' % (f(0.25 + 0.12 * k, 2), row_icon(T, ic, 32, yy - 10), h_, ls))
    # footer: the count, the licence, the link
    y0 = H - 30
    n1, nw = doc.text("27", 32, y0 + 6, "num", 30, T["text"])
    l1, _ = cap(doc, "MCP tools", 32 + nw + 8, y0 + 5, 10.5, T["dim"])
    b.append(n1 + l1)
    b.append(nudge_link(doc, T, "Open on GitHub", 178, y0))
    doc.css.append(REDUCED)
    return doc


# ----------------------------------------------------------------------------------------------
# the featured cards: a rotation of real frames, the claim, three real numbers, the link
# ----------------------------------------------------------------------------------------------
def feature(T, i, slug, eyebrow, title, desc, frames, stats, link_label, status, alt, motif=None, hold=4.6):
    W, H = 430, 440
    doc = Doc(W, H, title, alt)
    doc.css.append(cards.frame_css())
    cards.card_frame(doc, T, W, H)
    b = doc.body
    ix, iy, iw, ih = 14, 14, 402, 190
    if frames:
        b.append(rotator(doc, T, ix, iy, iw, ih, frames, hold=hold))
    else:
        k = doc.uid("mw")
        doc.defs.append('<clipPath id="%s"><rect x="%s" y="%s" width="%s" height="%s" rx="11"/></clipPath>' % (k, ix, iy, iw, ih))
        b.append('<rect x="%s" y="%s" width="%s" height="%s" rx="11" fill="%s" stroke="%s"/>' % (ix, iy, iw, ih, T["chip"], T["chipStroke"]))
        b.append('<g clip-path="url(#%s)">%s</g>' % (k, motif(doc, T, ix, iy, iw, ih)))
    e, _ = cap(doc, eyebrow, 24, 236, 11, T["gold"])
    t, _ = doc.text(title, 22, 273, "serif", 33, T["text"])
    lines = cards.wrap(desc, "sans", 14, W - 48)
    assert len(lines) <= 3, (title, lines)
    ds = "".join(doc.text(s, 24, 299 + 19 * k, "sans", 14, T["dim"])[0] for k, s in enumerate(lines))
    b.append('<g class="rise" style="animation-delay:%ss">%s%s%s</g>' % (f(0.08 * i, 2), e, t, ds))
    if stats:
        sy = 380
        b.append('<line x1="24" y1="%s" x2="%s" y2="%s" stroke="%s"/>' % (sy - 26, W - 24, sy - 26, T["line"]))
        widths = [max(font("num").width(num, 25), font("cap").layout(lab.upper(), 9.5, 0.12)[1]) for num, lab in stats]
        gap = (W - 48 - sum(widths)) / max(1, len(stats) - 1)
        assert gap >= 14, (title, gap)
        x0 = 24
        for k, (num, lab) in enumerate(stats):
            n_, _ = doc.text(num, x0, sy + 2, "num", 25, T["text"])
            l_, _ = cap(doc, lab, x0, sy + 19, 9.5, T["faint"])
            b.append('<g class="rise" style="animation-delay:%ss">%s%s</g>' % (f(0.3 + 0.1 * k, 2), n_, l_))
            x0 += widths[k] + gap
    fy = H - 26
    if link_label:
        b.append(nudge_link(doc, T, link_label, 24, fy))
    else:
        b.append(breathe_dot(doc, T, 29, fy))
        b.append(cap(doc, "Write-up coming soon", 42, fy + 4, 11.5, T["dim"])[0])
    if status:
        b.append(cap(doc, status, W - 24, fy + 4, 10.5, T["faint"], anchor="end")[0])
    doc.css.append(REDUCED)
    return doc


FEATURES = [
    ("human-llm-council", "Local models  ·  Apache-2.0", "Human LLM Council",
     "A small local model of one person's judgement, built to review what agents send and stop what that person would "
     "reject. Its benchmark scores the times I overrode the agent.",
     ["council-chart-{t}.jpg", "council-retest-{t}.jpg"],
     [("375", "held-out decisions"), ("70.6%", "bar fixed pre-training"), ("3.34 GB", "peak VRAM")],
     "Open on GitHub", "Preview  ·  not yet trained",
     "Human LLM Council: a small local model of one person's judgement that reviews what AI agents send and stops what "
     "that person would reject, scored on the decisions where the person overrode the agent. The benchmark is 375 held-out "
     "decisions; a trained model must reach 70.6% overall, a bar fixed before training; the training test peaked at 3.34 GB "
     "of VRAM on a 6 GB laptop GPU. No model is trained on real data yet (preview). Frames: the held-out results chart, then "
     "the self-consistency retest page on synthetic sample questions. Opens github.com/Sohwhat6420/human-llm-council."),
    ("headless-kit", "Node  ·  zero dependencies  ·  MIT", "headless-kit",
     "Cheap, agent-first tools that run with no browser, sign-in or window: model routing, Claude Code hooks, machine "
     "guards, research and trackers.",
     ["hk-model-router.jpg", "hk-reddit-pull.jpg", "hk-memory-gate.jpg", "hk-focus-gate.jpg"],
     [("20", "tools and hooks"), ("0", "dependencies"), ("2", "OSes in CI")],
     "Open on GitHub", "MIT",
     "headless-kit: 20 cheap, agent-first tools and Claude Code hooks (14 tools, 6 hooks) that run with no browser, sign-in "
     "or window, with zero dependencies and CI on Windows and Ubuntu: model routing, Claude Code hooks, machine guards, "
     "research and trackers. reddit-pull and detached-run are part of it. Frames: real terminal runs of model-router, "
     "reddit-pull, memory-gate and focus-gate. Opens github.com/Sohwhat6420/headless-kit."),
    ("designyourtv", "Google TV  ·  oil paintings  ·  MIT", "designyourtv",
     "Your Google TV's idle screen becomes a painted lock screen, the clock standing behind the painting, with glass "
     "widgets that never fake a number.",
     ["dytv-tv.jpg", "dytv-tv-thunderhead.jpg", "dytv-tv-dock.jpg", "dytv-setup.jpg"],
     [("10", "clock faces"), ("2", "local ONNX models"), ("1.7 s", "painting change")],
     "Open on GitHub", "MIT",
     "designyourtv: a Google TV's idle screen becomes a painted lock screen with the clock standing behind the painting, "
     "and glass widgets that never fake a number. Ten clock faces; each painting is cut into layers once by two small ONNX "
     "models run on your own computer; changing painting is a single 1.7-second move. Frames from the repo's own demo: "
     "two depth-clock paintings, the dock, and the setup page. Opens github.com/Sohwhat6420/designyourtv."),
    ("show-me-your-agents", "NUS-ISS hackathon 2026", "Show Me Your Agents",
     "Team Unburden, four of us: an agentic AI answer to a real business problem, with AWS and the Singapore Business "
     "Federation.",
     None, None,
     None, None,
     "Show Me Your Agents, the NUS-ISS hackathon 2026: Team Unburden, four of us, built an agentic AI answer to a real "
     "business problem, with AWS and the Singapore Business Federation. Write-up coming soon."),
]


# ----------------------------------------------------------------------------------------------
# also built: compact cards with a real thumbnail or an icon
# ----------------------------------------------------------------------------------------------
ICONS = {   # the TV's own widget icons (tools/tv-profile.js), 24 x 24, stroked
    "layers": '<path d="m12 3.5 8.5 4.3L12 12 3.5 7.8z"/><path d="m3.5 12 8.5 4.2 8.5-4.2M3.5 16.2l8.5 4.3 8.5-4.3"/>',
    "chevron": '<path d="m5 11 7-4.5 7 4.5M5 16.5 12 12l7 4.5"/>',
    "bulb": '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.6 10.8c.7.6 1.1 1.4 1.1 2.2v.5h5v-.5c0-.8.4-1.6 1.1-2.2A6 6 0 0 0 12 3z"/>',
}

MINIS = [
    ("unburden-root", "Multi-agent harness  ·  private", "Unburden Root",
     "The Claude Code harness I work in every day: named roles, shared memory, written rulings, a PII guard.",
     None, "layers", None),
    ("bb-5th-coy-admin-portal", "Private client project", "BB 5th Coy Administration Portal",
     "Awards, attendance and training-programme records for the Boys' Brigade 5th Singapore Company.",
     None, "chevron", None),
    ("designyourwindows", "Windows 10 + 11  ·  MIT", "designyourwindows",
     "The depth-clock look on a Windows desktop: the time sits behind your wallpaper's subject.",
     "thumb-designyourwindows.jpg", None, "https://github.com/Sohwhat6420/designyourwindows"),
    ("sidemic", "Android  ·  MIT", "Sidemic",
     "Your Android phone becomes your PC's wireless microphone, with noise removed on the phone.",
     "thumb-sidemic.jpg", None, "https://github.com/Sohwhat6420/sidemic"),
    ("film-simulations", "Python  ·  adb  ·  MIT", "Film simulations",
     "Fujifilm-style looks measured on a stock Android camera: a rig finds the nearest setting.",
     "thumb-android-film-simulations.jpg", None, "https://github.com/Sohwhat6420/android-film-simulations"),
    ("building-now", "In progress  ·  no links yet", "Building now",
     "Claude for HMOS Lite: answer your coding agent from a Huawei watch. Prompt Rambler: talk your way into a good prompt.",
     None, "bulb", None),
]


def mini(T, i, slug, eyebrow, title, desc, thumb, icon, link):
    W, H = 430, 132
    alt = "%s. %s %s" % (title, desc, ("Opens " + link.replace("https://", "") + ".") if link else eyebrow.replace("  ·  ", ", ") + ".")
    doc = Doc(W, H, title, alt)
    doc.css.append(cards.frame_css())
    cards.card_frame(doc, T, W, H)
    b = doc.body
    tx, ty, tw, th = 14, 14, 132, 104
    k = doc.uid("th")
    doc.defs.append('<clipPath id="%s"><rect x="%s" y="%s" width="%s" height="%s" rx="10"/></clipPath>' % (k, tx, ty, tw, th))
    if thumb:
        doc.css.append(".%sz{transform-box:fill-box;transform-origin:50%% 50%%;animation:%sz 14s ease-in-out infinite alternate}"
                       "@keyframes %sz{to{transform:scale(1.08)}}" % (k, k, k))
        b.append('<g clip-path="url(#%s)"><g class="%sz"><image href="%s" x="%s" y="%s" width="%s" height="%s" preserveAspectRatio="xMidYMid slice"/></g></g>'
                 % (k, k, uri(thumb), tx, ty, tw, th))
        b.append('<rect x="%s" y="%s" width="%s" height="%s" rx="10" fill="none" stroke="#ffffff" stroke-opacity="%s"/>'
                 % (tx + .5, ty + .5, tw - 1, th - 1, ".22" if T["name"] == "dark" else ".55"))
    else:
        b.append('<rect x="%s" y="%s" width="%s" height="%s" rx="10" fill="%s" stroke="%s"/>' % (tx, ty, tw, th, T["chip"], T["chipStroke"]))
        doc.css.append(".%sb{animation:%sb 5s ease-in-out infinite}@keyframes %sb{0%%,100%%{opacity:.75}50%%{opacity:1}}" % (k, k, k))
        b.append('<g class="%sb" transform="translate(%s %s) scale(1.9)" fill="none" stroke="%s" stroke-width="1.15" '
                 'stroke-linecap="round" stroke-linejoin="round">%s</g>' % (k, f(tx + tw / 2 - 22.8), f(ty + th / 2 - 22.8), T["gold"], ICONS[icon]))
    x0 = tx + tw + 16
    e, _ = cap(doc, eyebrow, x0, 38, 10, T["gold"])
    size = 25
    while font("serif").width(title, size) > W - x0 - 40 and size > 18:
        size -= 0.5
    t, _ = doc.text(title, x0 - 1, 67, "serif", size, T["text"])
    lines = cards.wrap(desc, "sans", 12.6, W - x0 - 20)
    assert len(lines) <= 3, (title, lines)
    ds = "".join(doc.text(s, x0, 88 + 16 * j, "sans", 12.6, T["dim"])[0] for j, s in enumerate(lines))
    b.append('<g class="rise" style="animation-delay:%ss">%s%s%s</g>' % (f(0.06 * i, 2), e, t, ds))
    if link:
        doc.css.append(".nudge{animation:nudge 1.8s cubic-bezier(.5,0,.3,1) infinite}@keyframes nudge{0%,100%{transform:none}50%{transform:translateX(4px)}}")
        b.append('<g class="nudge"><path d="M%s 36h14m-5-5 5 5-5 5" fill="none" stroke="%s" stroke-width="1.8" stroke-linecap="round" '
                 'stroke-linejoin="round"/></g>' % (f(W - 40), T["accent"]))
    doc.css.append(REDUCED)
    return doc


# ----------------------------------------------------------------------------------------------
# the projects tile: how many projects the page shows, open-source ones filled, private ones outlined
# ----------------------------------------------------------------------------------------------
OPEN_SOURCE = 7   # agentroid-mcp, human-llm-council, headless-kit, designyourtv, designyourwindows, sidemic, film simulations
PRIVATE = 3       # Show Me Your Agents (Team Unburden), Unburden Root, BB 5th Coy Administration Portal


def projects_tile(T):
    n = OPEN_SOURCE + PRIVATE

    def draw(doc, T, x, y, w, h):
        out = [cap(doc, "Projects", x + w / 2, y + 22, 11, T["dim"], "middle")[0]]
        out.append(doc.text(str(n), x + w / 2, y + 115, "num", 78, T["text"], anchor="middle")[0])
        pitch, g = 21, 14
        x0 = x + (w - (n * pitch - (pitch - g))) / 2
        doc.css.append(".pjq{animation:pjq 10s ease-out infinite backwards;transform-box:fill-box;transform-origin:center}"
                       "@keyframes pjq{0%,3%{opacity:0;transform:scale(.4)}12%,90%{opacity:1;transform:scale(1)}97%,100%{opacity:0;transform:scale(1)}}")
        for k in range(n):
            gx, gy = x0 + k * pitch, y + 131
            c = T["gold"]
            if k < OPEN_SOURCE:
                body = ('<rect x="%s" y="%s" width="14" height="14" rx="3.5" fill="%s" fill-opacity=".16" stroke="%s" stroke-width="1.3"/>'
                        '<rect x="%s" y="%s" width="8" height="1.5" rx=".75" fill="%s"/><rect x="%s" y="%s" width="6" height="1.5" rx=".75" fill="%s" fill-opacity=".6"/>'
                        '<rect x="%s" y="%s" width="8" height="1.5" rx=".75" fill="%s" fill-opacity=".6"/>'
                        % (f(gx), f(gy), c, c, f(gx + 3), f(gy + 3.2), c, f(gx + 3), f(gy + 6.4), c, f(gx + 3), f(gy + 9.6), c))
            else:   # private: an outlined padlock
                body = ('<rect x="%s" y="%s" width="14" height="14" rx="3.5" fill="none" stroke="%s" stroke-width="1.3" stroke-dasharray="2.4 1.8"/>'
                        '<rect x="%s" y="%s" width="6" height="4.6" rx="1" fill="%s"/><path d="M%s %sv-1.6a1.8 1.8 0 0 1 3.6 0v1.6" fill="none" stroke="%s" stroke-width="1.1"/>'
                        % (f(gx), f(gy), T["faint"], f(gx + 4), f(gy + 6.4), T["faint"], f(gx + 5.2), f(gy + 6.4), T["faint"]))
            out.append('<g class="pjq" style="animation-delay:%ss">%s</g>' % (f(0.4 + 0.14 * k, 2), body))
        out.append(cap(doc, "%d open source  ·  %d private" % (OPEN_SOURCE, PRIVATE), x + w / 2, y + h - 11, 10, T["faint"], "middle")[0])
        return "".join(out)

    return cards.tile(T, "projects", "Projects",
                      "%d projects, all shown below: %d open source on GitHub (one filled glyph each) and %d private (one outlined padlock each)."
                      % (n, OPEN_SOURCE, PRIVATE), draw)


def team(doc, T, x, y, w, h):
    """Four of us around one agent: messages flow in from each seat and back out."""
    p = doc.uid("tm")
    cx, cy = x + w / 2, y + h / 2 + 8
    seats = [(x + 62, y + 52), (x + w - 62, y + 52), (x + 62, y + h - 34), (x + w - 62, y + h - 34)]
    out = [cap(doc, "Team Unburden", x + 16, y + 26, 10.5, T["dim"])[0]]
    css = [".%sl{animation:%sl 1.4s linear infinite}@keyframes %sl{to{stroke-dashoffset:-14}}" % (p, p, p),
           ".%ss{transform-box:fill-box;transform-origin:center;animation:%ss 3.6s ease-in-out infinite}@keyframes %ss{50%%{transform:rotate(45deg) scale(.82)}}" % (p, p, p)]
    for k, (sx, sy) in enumerate(seats):
        out.append('<path d="M%s %sL%s %s" stroke="%s" stroke-width="1.4" stroke-dasharray="3 4" class="%sl" style="animation-direction:%s"/>'
                   % (f(sx), f(sy), f(cx), f(cy), T["line"], p, "normal" if k % 2 else "reverse"))
    for k, (sx, sy) in enumerate(seats):
        out.append('<circle cx="%s" cy="%s" r="15" fill="%s" stroke="%s"/>' % (f(sx), f(sy), T["card"], T["chipStroke"]))
        out.append('<g transform="translate(%s %s) scale(.9)" fill="none" stroke="%s" stroke-width="1.5" stroke-linecap="round">'
                   '<circle cx="12" cy="9" r="3.4"/><path d="M5.8 19.2c.7-3.3 3.2-5.1 6.2-5.1s5.5 1.8 6.2 5.1"/></g>' % (f(sx - 10.8), f(sy - 11), T["dim"]))
        cls = "%sd%d" % (p, k)
        dx, dy = cx - sx, cy - sy
        css.append(".%s{animation:%s 4.8s cubic-bezier(.45,0,.55,1) infinite;animation-delay:%ss;opacity:0}"
                   "@keyframes %s{0%%{transform:translate(0,0);opacity:0}8%%{opacity:1}42%%{transform:translate(%spx,%spx);opacity:1}48%%,100%%{transform:translate(%spx,%spx);opacity:0}}"
                   % (cls, cls, f(k * 1.2, 2), cls, f(dx), f(dy), f(dx), f(dy)))
        out.append('<circle cx="%s" cy="%s" r="3.4" fill="%s" class="%s"/>' % (f(sx), f(sy), T["ok"], cls))
    out.append('<circle cx="%s" cy="%s" r="26" fill="%s" stroke="%s" stroke-width="1.4"/>' % (f(cx), f(cy), T["card"], T["gold"]))
    out.append('<circle cx="%s" cy="%s" r="26" fill="none" stroke="%s" stroke-width="1.4" class="pulse" style="transform-origin:%spx %spx;transform-box:view-box;opacity:.5"/>'
               % (f(cx), f(cy), T["gold"], f(cx), f(cy)))
    out.append('<path d="M%s %sq1.8 7.2 9 9-7.2 1.8-9 9q-1.8-7.2-9-9 7.2-1.8 9-9z" fill="%s" class="%ss"/>' % (f(cx), f(cy - 9), T["gold"], p))
    out.append(cap(doc, "agent", cx, cy + 44, 10, T["gold"], "middle")[0])
    doc.css.append("\n".join(css))
    return "".join(out)


def cv_button(T):
    """The CV download pill. Outlined text, so its width is the same on every machine (the old one used system fonts and
    its second line ran past the pill on fonts wider than Segoe UI)."""
    t1, t2 = "Download CV (PDF)", "Full version  ·  2 pages  ·  for ATS or a closer read"
    w1 = font("sansb").width(t1, 17)
    w2 = font("sans").width(t2, 12)
    W, H = int(68 + max(w1, w2) + 30), 64
    doc = Doc(W, H, "Download CV (PDF)", "Button. Download Ethan Soh's full CV as a PDF, 2 pages, for ATS or a closer read.")
    doc.css.append(".arrow{animation:nudge 2.4s ease-in-out infinite}@keyframes nudge{0%,70%,100%{transform:translateY(0)}35%{transform:translateY(2.5px)}}")
    b = doc.body
    b.append('<rect x="1" y="1" width="%d" height="62" rx="31" fill="none" stroke="%s" stroke-width="2"/>' % (W - 2, T["gold"]))
    b.append('<g class="arrow" fill="none" stroke="%s" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">'
             '<path d="M36 20v19M27 31l9 9 9-9"/><path d="M26 46h20"/></g>' % T["gold"])
    b.append(doc.text(t1, 68, 29, "sansb", 17, T["text"])[0])
    b.append(doc.text(t2, 68, 47, "sans", 12, T["dim"])[0])
    doc.css.append(REDUCED)
    return doc


HEADERS = [
    ("01", "Featured", motifs.f1, "In a glass window beside it, an F1 car runs a glowing racing line through an S-bend, trailing light."),
    ("02", "Security", motifs.handshake,
     "In a glass window beside it, SYN, SYN-ACK and ACK packets cross between two nodes, then a flag is captured on the target."),
    ("03", "Also built", motifs.agent_phone,
     "In a glass window beside it, an agent's cursor taps an app on a small phone, then an R4 delete action is held at the gate."),
]


def main():
    report = []
    for name, T in THEMES.items():
        report.append(cards.write("typing", name, cards.typing(T)))
        for idx, title, motif, desc in HEADERS:
            report.append(cards.write("s%s-%s" % (idx, title.lower().replace(" ", "-")), name, cards.header(T, idx, title, motif, desc)))
        report.append(cards.write("feature-agentroid", name, agentroid(T)))
        for i, (slug, eb, title, desc, frames, stats, link, status, alt) in enumerate(FEATURES):
            fr = [s.format(t=name) for s in frames] if frames else None
            report.append(cards.write("feature-" + slug, name, feature(T, i, slug, eb, title, desc, fr, stats, link, status, alt,
                                                                    motif=team if not fr else None)))
        for i, m in enumerate(MINIS):
            report.append(cards.write("mini-" + m[0], name, mini(T, i, *m)))
        report.append(cards.write("about-projects", name, projects_tile(T)))
        report.append(cards.write("cv-download", name, cv_button(T)))
    for p, s in report:
        print("%7.1f KB  %s" % (s / 1024, os.path.basename(p)))


if __name__ == "__main__":
    main()
