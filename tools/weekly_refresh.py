"""Weekly README tile refresh (Ethan's ruling, 12 Nov 2026: a hidden WEEKLY task, Sunday night, pushes only if a number changed).

Regenerates three tiles of github.com/Sohwhat6420/Sohwhat6420 (main):
  about-contrib-*.svg   GitHub contributions, past year (GitHub GraphQL via `gh api`, the logged-in gh account)
  about-tokens-*.svg    Claude Code /stats odometer + active days (via tools/measure_tokens.mjs from local
                        ~/.claude/stats-cache.json + recent ~/.claude/projects/**/*.jsonl tail; read-only, no model calls)
  about-projects-*.svg  "N projects published" = public, non-fork, non-archived repos on Sohwhat6420 except the profile repo (`gh api`)
Also refreshes the matching numbers in README.md (alt text and the cross-model deduplicated footnote), never adding
or altering wording, and never lowering a token or active-day figure if local logs are temporarily unavailable.

It works in a throw-away shallow clone (or an existing --clone-dir): builds the tiles, compares them with the clone's
files, and if any differ commits "Weekly refresh (automatic) ..." and pushes main (plain push, never forced).
Nothing differs -> no commit, no push.
One log line per run: ~/.claude/run/readme-weekly-refresh.log.

    python weekly_refresh.py                     # the scheduled run (own shallow clone)
    python weekly_refresh.py --clone-dir <dir>   # reuse an existing shallow clone
    python weekly_refresh.py --dry-run           # build and compare, never commit or push
    python weekly_refresh.py --tokens-only       # refresh only the token tile & README token numbers
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
NOWIN = 0x08000000 if os.name == "nt" else 0   # CREATE_NO_WINDOW
REPO = "https://github.com/Sohwhat6420/Sohwhat6420.git"
RUN = os.path.join(os.path.expanduser("~"), ".claude", "run")
LOG = os.path.join(RUN, "readme-weekly-refresh.log")
DRY = "--dry-run" in sys.argv
APPLY_ONLY = "--apply-only" in sys.argv
NO_LOG = "--no-log" in sys.argv
TOKENS_ONLY = "--tokens-only" in sys.argv


def _arg(flag):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return None


CLONE_DIR = _arg("--clone-dir")
OUT_DIR = _arg("--out-dir")


def log(msg):
    line = "%s %s" % (dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), msg)
    print(line)
    if NO_LOG:
        return
    os.makedirs(RUN, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def run(args, cwd=None, check=True, timeout=240):
    kw = {"creationflags": NOWIN} if NOWIN else {}
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout, **kw)
    if check and r.returncode:
        raise RuntimeError("%s -> %s: %s" % (" ".join(args[:3]), r.returncode, (r.stdout + r.stderr)[-300:]))
    return r


def _node_bin():
    for cand in (r"C:\Program Files\nodejs\node.exe", shutil.which("node")):
        if cand and os.path.exists(cand):
            return cand
    return "node"


def measure_tokens():
    """Run local read-only tools/measure_tokens.mjs. Returns dict or None on failure."""
    script = os.path.join(HERE, "measure_tokens.mjs")
    if not os.path.exists(script):
        return None
    try:
        r = run([_node_bin(), "--no-warnings", script], timeout=120)
        return json.loads(r.stdout)
    except Exception as e:
        log("measure_tokens warning: %s" % str(e)[:160])
        return None


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


def _existing_readme_floor(readme_text):
    """Parse existing README token numbers so a transient log issue never lowers them."""
    m_tok = re.search(r"Odometer:\s*(\d+)\s+billion tokens on Claude Code", readme_text)
    m_days = re.search(r"over\s+(\d+)\s+active days", readme_text)
    m_dedup = re.search(r"across Claude, Gemini and Codex it is\s+([0-9.]+)\s+B\.", readme_text)
    return (
        int(m_tok.group(1)) if m_tok else 0,
        int(m_days.group(1)) if m_days else 0,
        float(m_dedup.group(1)) if m_dedup else 0.0,
    )


def main():
    import koilib
    koilib.FONT_DIR = os.path.join(HERE, "fonts")
    import cards
    import motifs
    own_tmp = None
    if CLONE_DIR:
        clone = os.path.abspath(CLONE_DIR)
        out = os.path.abspath(OUT_DIR) if OUT_DIR else os.path.join(os.path.dirname(clone), "out")
        os.makedirs(out, exist_ok=True)
    else:
        own_tmp = tempfile.mkdtemp(prefix="readme-weekly-")
        clone = os.path.join(own_tmp, "repo")
        out = os.path.join(own_tmp, "out")
        run(["git", "clone", "--depth", "1", "--branch", "main", REPO, clone])
    try:
        cards.OUT = out
        rp = os.path.join(clone, "README.md")
        readme_orig = open(rp, encoding="utf-8", newline="").read()
        prev_b, prev_days, prev_dedup_b = _existing_readme_floor(readme_orig)

        notes = []
        cal = None
        if not TOKENS_ONLY:
            cal = github_cal()
            cards.CAL = cal
            notes.append("contributions %d" % cal["total"])
            for name, T in cards.THEMES.items():
                cards.write("about-contrib", name, cards.tile(T, "contrib", "GitHub contributions",
                            "My last twenty weeks of GitHub contributions filling in week by week, with my past-year total underneath.",
                            lambda d, t, x, y, w, h: motifs.contributions(d, t, x, y, w, h, cal)))

        # Measure live local token totals (Claude /stats + active days + cross-model deduplicated)
        tok_data = measure_tokens()
        tot, as_of = cards.STATS_TOKENS
        active_days = None
        since_label = "May 2026"
        dedup_b = None

        if tok_data and isinstance(tok_data.get("stats_total"), (int, float)) and tok_data["stats_total"] > 0:
            meas_tot = int(tok_data["stats_total"])
            if round(meas_tot / 1e9) >= prev_b and meas_tot >= tot:
                tot = meas_tot
                as_of = tok_data.get("stats_as_of") or as_of
            if isinstance(tok_data.get("active_days"), int) and tok_data["active_days"] >= prev_days:
                active_days = tok_data["active_days"]
                since_label = tok_data.get("since_label") or since_label
            if isinstance(tok_data.get("cross_model_dedup_total"), (int, float)) and tok_data["cross_model_dedup_total"] > 0:
                cand_dedup = round(tok_data["cross_model_dedup_total"] / 1e9, 1)
                if cand_dedup >= prev_dedup_b:
                    dedup_b = cand_dedup

        # Fallback for active_days if measure_tokens did not provide it
        if active_days is None:
            act = activity()
            if act and act.get("replies"):
                days = sorted(dt.date.fromisoformat(k) for k, v in act["replies"].items() if v > 0)
                if days and len(days) >= prev_days:
                    active_days = len(days)
                    since_label = "%s %d" % (days[0].strftime("%b"), days[0].year)
            if active_days is None and prev_days > 0:
                active_days = prev_days

        if active_days:
            notes.append("tokens %.1fB" % (tot / 1e9))
            notes.append("days %d" % active_days)
            if dedup_b is not None:
                notes.append("dedup %.1fB" % dedup_b)
            tdesc = ("Odometer digits roll up to %d billion: my Claude Code tokens as shown by its /stats screen, to %s, over %d active days since %s."
                     % (round(tot / 1e9), as_of, active_days, since_label))
            for name, T in cards.THEMES.items():
                cards.write("about-tokens", name, cards.tile(T, "tokens", "Claude Code tokens", tdesc,
                            lambda d, t, x, y, w, h: motifs.tokens(d, t, x, y, w, h, tot, as_of, "%d active days" % active_days)))
        else:
            notes.append("tokens: no local data, tile kept")

        nproj = None
        if not TOKENS_ONLY:
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
        to_copy = []
        for f in sorted(os.listdir(out)):
            if not f.endswith(".svg"):
                continue
            new = open(os.path.join(out, f), "rb").read().replace(b"\r\n", b"\n")
            old_p = os.path.join(clone, "assets", f)
            old = open(old_p, "rb").read().replace(b"\r\n", b"\n") if os.path.exists(old_p) else None
            if old != new:
                to_copy.append((os.path.join(out, f), old_p))
                changed.append(f)

        # Keep README.md numbers in step with the tiles (numbers/dates only; never alter wording)
        s2 = readme_orig
        if cal is not None:
            s2 = re.sub(r"with [0-9.]+ thousand contributions in the past year",
                        "with %.1f thousand contributions in the past year" % (cal["total"] / 1000), s2)
        if active_days:
            s2 = re.sub(
                r"Odometer: \d+ billion tokens on Claude Code as shown by its /stats screen, to [0-9A-Za-z ]+, over \d+ active days since [A-Za-z0-9 ]+\.",
                "Odometer: %d billion tokens on Claude Code as shown by its /stats screen, to %s, over %d active days since %s."
                % (round(tot / 1e9), as_of, active_days, since_label),
                s2,
            )
        if dedup_b is not None:
            s2 = re.sub(
                r"counted once per reply across Claude, Gemini and Codex it is [0-9.]+ B\.",
                "counted once per reply across Claude, Gemini and Codex it is %.1f B." % dedup_b,
                s2,
            )
        if nproj is not None:
            s2 = re.sub(r"\d+ projects (?:shipped|published): my public repositories",
                        "%d projects published: my public repositories" % nproj, s2)

        readme_changed = s2 != readme_orig
        if not changed and not readme_changed:
            log("no change (%s); nothing pushed" % ", ".join(notes))
            return 0
        if readme_changed:
            changed.append("README.md")
        if DRY:
            log("DRY RUN: would push %s (%s)" % (", ".join(changed), ", ".join(notes)))
            return 0
        for src_p, dst_p in to_copy:
            shutil.copyfile(src_p, dst_p)
        if readme_changed:
            open(rp, "w", encoding="utf-8", newline="").write(s2)
        if APPLY_ONLY:
            log("APPLIED: %s (%s)" % (", ".join(changed), ", ".join(notes)))
            return 0
        run(["git", "add", "--", "README.md", "assets"], cwd=clone)
        msg = ("Weekly refresh (automatic): tiles regenerated, %s\n\n"
               "Hidden Sunday-night task ReadmeWeeklyRefresh; pushes only when a number changed. "
               "Measured locally by tools/measure_tokens.mjs (zero model calls)." % ", ".join(notes))
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
        if own_tmp:
            shutil.rmtree(own_tmp, onerror=_rm)


if __name__ == "__main__":
    sys.exit(main())
