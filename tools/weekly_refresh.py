"""Weekly README tile refresh (Ethan's ruling, 12 Nov 2026: a hidden WEEKLY task, Sunday night, pushes only if a number changed).

Regenerates three tiles of github.com/Sohwhat6420/Sohwhat6420 (main), changed 12 Nov 2026 (three single cards):
  about-contrib-*.svg   GitHub contributions, past year (GitHub GraphQL via `gh api`, the logged-in gh account)
  about-tokens-*.svg    only its "N active days" line (the TV hub's /api/activity, else .live/activity.json)
  about-projects-*.svg  "N projects shipped" = public, non-fork, non-archived repos on Sohwhat6420 except the profile repo (`gh api`)
The odometer figure itself (117 B) is NOT refreshed: it says "as shown on /stats" and is typed from /stats by hand
(cards.STATS_TOKENS); the hub's own total is a different measure (55 B against 117 B), so regenerating it would change the claim.

It works in a throw-away shallow clone: builds the two tiles, compares them with the clone's files, and if any differ commits
"Weekly refresh (automatic) ..." and pushes main (plain push, never forced). Nothing differs -> no commit, no push.
One log line per run: ~/.claude/run/readme-weekly-refresh.log.

    python weekly_refresh.py            # the scheduled run
    python weekly_refresh.py --dry-run  # build and compare, never commit or push
"""
import datetime as dt
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "koi"))
NOWIN = 0x08000000   # CREATE_NO_WINDOW
REPO = "https://github.com/Sohwhat6420/Sohwhat6420.git"
RUN = os.path.join(os.path.expanduser("~"), ".claude", "run")
LOG = os.path.join(RUN, "readme-weekly-refresh.log")
DRY = "--dry-run" in sys.argv


def log(msg):
    line = "%s %s" % (dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), msg)
    print(line)
    os.makedirs(RUN, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def run(args, cwd=None, check=True):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, creationflags=NOWIN, timeout=240)
    if check and r.returncode:
        raise RuntimeError("%s -> %s: %s" % (" ".join(args[:3]), r.returncode, (r.stdout + r.stderr)[-300:]))
    return r


def github_cal():
    q = ("{ viewer { contributionsCollection { totalCommitContributions contributionCalendar { totalContributions "
         "weeks { contributionDays { contributionCount } } } } } }")
    r = run(["gh", "api", "graphql", "-f", "query=" + q])
    cc = json.loads(r.stdout)["data"]["viewer"]["contributionsCollection"]
    cal = cc["contributionCalendar"]
    weeks = [[d["contributionCount"] for d in w["contributionDays"]] for w in cal["weeks"]]
    weeks = [w + [0] * (7 - len(w)) for w in weeks]
    return {"total": cal["totalContributions"], "commits": cc["totalCommitContributions"], "weeks": weeks,
            "to": dt.date.today().isoformat()}


def activity():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8790/api/activity", timeout=5) as r:
            return json.load(r)
    except Exception:
        p = os.path.join(ROOT, ".live", "activity.json")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as fh:
                return json.load(fh)
    return None


def _rm(f, p, e):
    os.chmod(p, stat.S_IWRITE)
    f(p)


def main():
    import koilib
    koilib.FONT_DIR = os.path.join(HERE, "fonts")
    import cards
    import motifs
    tmp = tempfile.mkdtemp(prefix="readme-weekly-")
    try:
        clone = os.path.join(tmp, "repo")
        run(["git", "clone", "--depth", "1", "--branch", "main", REPO, clone])
        out = os.path.join(tmp, "out")
        cards.OUT = out
        cal = github_cal()
        act = activity()
        cards.CAL = cal
        notes = ["contributions %d" % cal["total"]]
        for name, T in cards.THEMES.items():
            cards.write("about-contrib", name, cards.tile(T, "contrib", "GitHub contributions",
                        "My last twenty weeks of GitHub contributions filling in week by week, with my past-year total underneath.",
                        lambda d, t, x, y, w, h: motifs.contributions(d, t, x, y, w, h, cal)))
        stat_days = None
        if act and act.get("replies"):
            days = sorted(dt.date.fromisoformat(k) for k, v in act["replies"].items() if v > 0)
            if days:
                stat_days = (str(len(days)), "days", "Claude Code", "since %s %d" % (days[0].strftime("%b"), days[0].year))
                notes.append("days %d" % len(days))
                # the tokens tile: the odometer figure stays the hand-typed /stats value; only its "N active days" line moves
                tot, as_of = cards.STATS_TOKENS
                tdesc = ("Odometer digits roll up to %d billion: my Claude Code tokens as shown by its /stats screen, to %s, over %s active days since %s."
                         % (round(tot / 1e9), as_of, stat_days[0], stat_days[3].replace("since ", "")))
                for name, T in cards.THEMES.items():
                    cards.write("about-tokens", name, cards.tile(T, "tokens", "Claude Code tokens", tdesc,
                                lambda d, t, x, y, w, h: motifs.tokens(d, t, x, y, w, h, tot, as_of, "%s active days" % stat_days[0])))
        else:
            notes.append("days: no activity log, tokens tile kept")
        try:
            nproj = cards.project_count()
            notes.append("projects %d" % nproj)
            for name, T in cards.THEMES.items():
                cards.write("about-projects", name, cards.tile(T, "projects", "Projects published",
                            "%d projects published: my public repositories on GitHub, one small repo glyph for each." % nproj,
                            lambda d, t, x, y, w, h: motifs.projects(d, t, x, y, w, h, nproj)))
        except Exception as e:
            nproj = None
            notes.append("projects: %s, tile kept" % str(e)[:60])
        changed = []
        for f in sorted(os.listdir(out)):
            new = open(os.path.join(out, f), "rb").read().replace(b"\r\n", b"\n")
            old_p = os.path.join(clone, "assets", f)
            old = open(old_p, "rb").read().replace(b"\r\n", b"\n") if os.path.exists(old_p) else None
            if old != new:
                shutil.copyfile(os.path.join(out, f), old_p)
                changed.append(f)
        if not changed:
            log("no change (%s); nothing pushed" % ", ".join(notes))
            return 0
        # keep the README's alt text in step with the numbers
        rp = os.path.join(clone, "README.md")
        s = open(rp, encoding="utf-8", newline="").read()
        s2 = re.sub(r"with [0-9.]+ thousand contributions in the past year", "with %.1f thousand contributions in the past year" % (cal["total"] / 1000), s)
        if stat_days:
            s2 = re.sub(r"over \d+ active days since [A-Za-z0-9 ]+\.", "over %s active days %s." % (stat_days[0], stat_days[3]), s2)
        if nproj is not None:
            s2 = re.sub(r"\d+ projects (?:shipped|published): my public repositories", "%d projects published: my public repositories" % nproj, s2)
        if s2 != s:
            open(rp, "w", encoding="utf-8", newline="").write(s2)
        if DRY:
            log("DRY RUN: would push %s (%s)" % (", ".join(changed), ", ".join(notes)))
            return 0
        run(["git", "add", "--", "README.md", "assets"], cwd=clone)
        msg = ("Weekly refresh (automatic): tiles regenerated, %s\n\nHidden Sunday-night task ReadmeWeeklyRefresh; pushes only when a number changed. "
               "The Claude Code tokens tile is not touched (typed from /stats by hand).\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>" % ", ".join(notes))
        run(["git", "-c", "user.name=Ethan", "-c", "user.email=Sohwhat6420@users.noreply.github.com", "commit", "-q", "-m", msg], cwd=clone)
        r = run(["git", "push", "origin", "HEAD:main"], cwd=clone, check=False)
        if r.returncode:
            run(["git", "pull", "--rebase", "origin", "main"], cwd=clone)
            run(["git", "push", "origin", "HEAD:main"], cwd=clone)
        sha = run(["git", "log", "-1", "--format=%h"], cwd=clone).stdout.strip()
        log("pushed %s: %s (%s)" % (sha, ", ".join(changed), ", ".join(notes)))
        return 0
    except Exception as e:
        log("FAILED: %s" % e)
        return 1
    finally:
        shutil.rmtree(tmp, onerror=_rm)


if __name__ == "__main__":
    sys.exit(main())
