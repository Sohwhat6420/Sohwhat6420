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
RINGS = [   # (icon, label, fill 0-1)
    ("flag", "0.5%", 0.995),       # HTB: top 0.5%
    ("cap", "3.77", 3.77 / 4),     # cGPA
    ("book", "5", 1.0),            # Anthropic Academy courses
    ("trophy", "136", 1.0),        # all 136 flags at Cyber Apocalypse
]
