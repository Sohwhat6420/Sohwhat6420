"""Refreshes the README hero's live numbers and publishes it: the one command to schedule.

    python tools/refresh.py              # read, build, publish to the `live` branch
    python tools/refresh.py --no-push    # read and build only (writes .live/hero.svg)
    python tools/refresh.py --ci         # the daily Action: GitHub from the API, Claude numbers kept from `live`

What it reads (each falls back to the last published copy on the `live` branch, so a missing source never blanks a
card):
  usage.json     his Claude plan's 5-hour and weekly limits: the TV hub's /api/claude (http://127.0.0.1:8790), which
                 reads the plan's usage page. Kept: the two percentages, their reset times and when it was read.
  activity.json  Claude Code tokens per day: the hub's /api/activity, else the TV's data file
                 (Vault/Projects/xiaomi-tv-revamp/data/claude-activity.json). Kept: tokens per day, total, first day.
                 Counts only; no prompts, no project names.
  github.json    his public GitHub numbers (tools/gh_stats.py).
What it writes: .live/{hero.svg, usage.json, activity.json, github.json}, then, unless --no-push, one commit holding
exactly those four files on the branch `live`, which holds nothing else and shares no history with main (an ordinary
push; see publish()). The README shows https://raw.githubusercontent.com/Sohwhat6420/Sohwhat6420/live/hero.svg.
Main is never touched.
"""
import json
import os
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, ".live")
HUB = os.environ.get("TV_HUB", "http://127.0.0.1:8790")
TV_ACTIVITY = os.path.join(os.path.expanduser("~"), "Vault", "Projects", "xiaomi-tv-revamp", "data", "claude-activity.json")
BRANCH = "live"
FILES = ("hero.svg", "usage.json", "activity.json", "github.json")
NOWIN = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}

sys.path.insert(0, HERE)


def git(*args, env=None, inp=None):
    # bytes in and out: text mode on Windows would turn mktree's "\n" into "\r\n" and put a CR in every file name
    r = subprocess.run(["git", "-C", ROOT] + list(args), capture_output=True,
                       input=inp.encode("utf-8") if isinstance(inp, str) else inp, env=env, **NOWIN)
    if r.returncode:
        raise RuntimeError("git %s: %s" % (" ".join(args[:2]), r.stderr.decode("utf-8", "replace").strip()[:300]))
    return r.stdout.decode("utf-8")


def hub(path):
    with urllib.request.urlopen(HUB + path, timeout=8) as r:
        return json.load(r)


def published(name):
    """The copy of `name` on the live branch (fetched first), or None."""
    try:
        return json.loads(git("show", "origin/%s:%s" % (BRANCH, name)))
    except Exception:
        return None


def usage():
    try:
        u = hub("/api/claude")
        if u.get("session") and u.get("read_at") and not u.get("stale"):
            keep = lambda w: w and {"pct": w.get("pct"), "resets_at": w.get("resets_at")}
            return {"session": keep(u["session"]), "weekly": keep(u.get("weekly")), "read_at": u["read_at"],
                    "source": "tv-hub"}, "hub"
    except Exception:
        pass
    return published("usage.json"), "kept"


def activity():
    src = None
    try:
        src, how = hub("/api/activity"), "hub"
    except Exception:
        if os.path.exists(TV_ACTIVITY):
            with open(TV_ACTIVITY, encoding="utf-8") as fh:
                src, how = json.load(fh), "file"
    if src and src.get("tokens"):
        return {"tokens": dict(sorted(src["tokens"].items())), "total": src.get("total"), "first": src.get("first"),
                "tz": src.get("tz"), "made": src.get("made")}, how
    return published("activity.json"), "kept"


def github():
    import gh_stats
    try:
        return gh_stats.collect(os.environ.get("GITHUB_REPOSITORY_OWNER", "Sohwhat6420")), "api"
    except BaseException as e:   # gh_stats raises SystemExit on an API error
        print("github: %s" % e, file=sys.stderr)
        return published("github.json"), "kept"


def remote_tip():
    try:
        return git("rev-parse", "--verify", "--quiet", "refs/remotes/origin/%s" % BRANCH).strip() or None
    except Exception:
        return None


def publish():
    """One new commit on `live` holding the four files, on top of the branch's last commit (an ordinary push, never a
    force). Each refresh changes a few numbers in a 2.7 MB file, so git sends it as a small delta and the branch's
    history stays cheap. Main is never touched; the working tree and index are not used."""
    entries = []
    for name in FILES:
        sha = git("hash-object", "-w", os.path.join(OUT, name)).strip()
        entries.append("100644 blob %s\t%s" % (sha, name))
    tree = git("mktree", inp="\n".join(entries) + "\n").strip()
    msg = "Live banner: Claude usage, Claude Code activity, GitHub (tools/refresh.py)"
    for attempt in range(3):
        parent = remote_tip()
        if parent and git("rev-parse", parent + "^{tree}").strip() == tree:
            return parent + " (unchanged)"
        commit = git("commit-tree", tree, "-m", msg, *(["-p", parent] if parent else [])).strip()
        try:
            git("push", "origin", "%s:refs/heads/%s" % (commit, BRANCH))
            return commit
        except RuntimeError:          # the branch moved (the daily Action published meanwhile): build on its new tip
            git("fetch", "--quiet", "origin", "%s:refs/remotes/origin/%s" % (BRANCH, BRANCH))
    raise RuntimeError("could not publish to %s after 3 tries" % BRANCH)


def main():
    ci = "--ci" in sys.argv
    try:
        git("fetch", "--quiet", "origin", "%s:refs/remotes/origin/%s" % (BRANCH, BRANCH))
    except Exception:
        pass                                   # the first run: no live branch yet
    os.makedirs(OUT, exist_ok=True)
    got = {}
    if ci:
        got["usage.json"] = (published("usage.json"), "kept")
        got["activity.json"] = (published("activity.json"), "kept")
    else:
        got["usage.json"] = usage()
        got["activity.json"] = activity()
    got["github.json"] = github()
    for name, (d, how) in got.items():
        if d is None:
            print("%-14s none (the card shows that)" % name)
            p = os.path.join(OUT, name)
            if os.path.exists(p):
                os.remove(p)
            continue
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(d, fh, separators=(",", ":"))
            fh.write("\n")
        print("%-14s %s" % (name, how))
    import hero
    from svglib import write_svg
    p, s = write_svg(os.path.join(OUT, "hero.svg"), hero.build(OUT))
    print("hero.svg       %.0f KB" % (s / 1024))
    for name in FILES:                          # an empty card still needs its file in the tree
        q = os.path.join(OUT, name)
        if not os.path.exists(q):
            with open(q, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("null\n")
    if "--no-push" not in sys.argv:
        print("published      %s -> %s" % (publish()[:10], BRANCH))


if __name__ == "__main__":
    main()
