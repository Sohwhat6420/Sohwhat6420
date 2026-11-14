"""The CV facts the hero's cards show. Every line comes from the CV build (Vault: Projects/career-2027/cv/build,
cv_data.py and build_master.py, 6 Nov 2026), which traces each one to evidence/LEDGER.md. No phone, email or location.
"""
import datetime as dt

TAGLINE = "Applied AI · AI security"           # where the TV prints the date

INTERNSHIP_FROM = dt.date(2027, 4, 12)         # cv_data.SEEKING: 44 weeks from 12 Apr 2027 (to 11 Feb 2028)
INTERNSHIP = "Year 3 internship, 44 weeks"
INTERNSHIP_LINE = "From Mon 12 Apr 2027"

# (chip, main, detail)
CERTIFIED = [
    ("CCA-F", "Claude Architect", "Sep 2026"),         # Claude Certified Architect – Foundations, Anthropic, to Sep 2027
    ("CC", "ISC2 Cybersecurity", "Jan 2026"),          # ISC2 Certified in Cybersecurity, to Jan 2029
    ("5", "Anthropic Academy", "courses"),             # Claude 101, Claude Code 101, Claude Platform 101, Cowork, AI Fluency
]
LEADERSHIP = [
    ("BB", "Senior Cadet Lt", "Drill Instructor"),     # Senior Cadet Lieutenant (Primer), BB 5th Company; Drill Instructor
    ("BB", "Founder's Award", "2024"),                  # the highest award in the BB Senior Programme, Jun 2024
    ("SEED", "Senior Exco", "CS club"),                 # SEED (Computer Science Club), Senior Executive Committee, 2026
]
DIPLOMA = ("cGPA 3.77", "2 Distinctions")              # Digital Forensics and Investigation; Personal Branding
CTF = [
    ("30th", "Hack The Box", "of 6,744"),              # Cyber Apocalypse CTF 2026, top 0.5%
    ("T20", "Cyber Conquest", "finalist"),             # Singapore Cyber Conquest 2026, student finalist (top 20)
    ("FINAL", "BrainHack CDDC", "finalist"),           # DSTA BrainHack 2026, CDDC, Explorer
]
HACKATHONS = [
    ("QF", "PolyFinTech100", "quarterfinal"),          # API Hackathon 2026, ESG & AI track
    ("2026", "NUS-ISS · NAISC", "agents, Workato"),    # Show Me Your Agents 2026; National AI Student Challenge 2026
]
EVENTS = "Attended DEF CON SG · Black Hat Asia · SICW x GovWare"
PROJECTS = [   # (icon, name, one line, tag); the README's featured cards say the same (14 Nov 2026)
    ("phone", "Agentroid", "Android for MCP agents, lean on context", "PREVIEW"),
    ("people", "Human LLM Council", "A local model of one person's judgement", "PREVIEW"),
    ("layers", "headless-kit", "20 tools and hooks for AI agents", "MIT"),
    ("tv", "designyourtv", "A painted lock screen for Google TV", "MIT"),
]
COMP_RINGS = [   # (icon, ring label, caption, fill 0-1) on the TV's battery rings
    ("flag", "30th", "HTB", 1 - 30 / 6744),   # of 6,744 teams: top 0.5%
    ("trophy", "T20", "Conquest", 1.0),
    ("target", "Final", "BrainHack", 1.0),
    ("bulb", "QF", "FinTech100", 1.0),
]
RINGS = [   # (icon, label, fill 0-1)
    ("flag", "0.5%", 0.995),       # HTB: top 0.5%
    ("cap", "3.77", 3.77 / 4),     # cGPA
    ("book", "5", 1.0),            # Anthropic Academy courses
    ("trophy", "136", 1.0),        # all 136 flags at Cyber Apocalypse
]


def profile(gh, act):
    """What tools/tv-profile.js writes into the TV's widget cards (capture_tv.mjs hands it over as JSON)."""
    tok = (act or {}).get("tokens") or {}
    recent = [v for k, v in sorted(tok.items())[-7:]]
    return {
        "internship": {"from": INTERNSHIP_FROM.isoformat(), "title": "Year 3 internship", "line": "From Mon 12 Apr 2027",
                       "detail": "44 weeks · applied AI", "runup_days": 365},
        "certified": [
            {"icon": "claude", "main": "Claude Architect", "detail": "Certified · Anthropic · 2026", "tag": "CCA-F", "acc": True},
            {"icon": "shield", "main": "ISC2 Cybersecurity", "detail": "Certified in Cybersecurity", "tag": "CC", "acc": True},
            {"icon": "book", "main": "Anthropic Academy", "detail": "5 courses · 2026", "tag": "5"},
        ],
        "leadership": [
            {"icon": "chevron", "main": "BB Senior Cadet Lt", "detail": "", "tag": ""},
            {"icon": "medal", "main": "Founder's Award 2024", "detail": "", "tag": ""},
            {"icon": "cap", "main": "cGPA 3.77", "detail": "", "tag": ""},
        ],
        "rings": [{"icon": i, "label": l, "caption": c, "fill": f} for i, l, c, f in COMP_RINGS],
        "comp_foot": "<b>Hack The Box</b> Cyber Apocalypse: <b>30th of 6,744</b> · 136/136 flags",
        "projects": [{"icon": i, "name": n, "desc": d, "tag": t, "acc": t == "LIVE"} for i, n, d, t in PROJECTS],
        "projects_meta": "github.com/Sohwhat6420",
        "github": {k: (gh or {}).get(k) for k in ("contributions", "repos", "days")},
        "activity": {"total": (act or {}).get("total"), "recent_per_day": (sum(recent) / len(recent)) if recent else 0},
    }
