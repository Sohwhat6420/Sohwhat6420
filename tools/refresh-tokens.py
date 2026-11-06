"""Redraws the token widget from Claude Code's own count on this laptop and pushes only that widget.

    python tools/refresh-tokens.py            rebuild, commit and push the three token files
    python tools/refresh-tokens.py --no-push  rebuild only

Source: ~/.claude/stats-cache.json, the cache behind Claude Code's /stats (modelUsage: input, output, cache-write and
cache-read tokens for every model; dailyModelTokens: the same per day). Counts only: nothing about any session's
content is read or published. The data lives on the laptop, which is why this can't be a GitHub Action.
Only data/tokens.json and assets/widget-tokens-{dark,light}.svg are staged; anything else in the tree is left alone.
"""
import json
import os
import subprocess
import sys

import widgets
from svglib import ROOT

STATS = os.path.join(os.path.expanduser("~"), ".claude", "stats-cache.json")
FILES = ["data/tokens.json", "assets/widget-tokens-dark.svg", "assets/widget-tokens-light.svg"]
KINDS = ("inputTokens", "outputTokens", "cacheCreationInputTokens", "cacheReadInputTokens")


def git(*args, check=True):
    kw = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    r = subprocess.run(["git", "-C", ROOT] + list(args), capture_output=True, text=True, **kw)
    if check and r.returncode:
        raise SystemExit("git %s failed: %s" % (" ".join(args), (r.stderr or r.stdout).strip()))
    return r


def read_stats(path=STATS):
    with open(path, encoding="utf-8") as fh:
        s = json.load(fh)
    total = sum(int(u.get(k, 0)) for u in s["modelUsage"].values() for k in KINDS)
    daily = {d["date"]: int(sum(d["tokensByModel"].values())) for d in s.get("dailyModelTokens", [])}
    first = (s.get("firstSessionDate") or min(daily))[:10]
    return dict(total=total, first=first, asof=s.get("lastComputedDate") or max(daily),
                sessions=s.get("totalSessions"), messages=s.get("totalMessages"), daily=daily,
                source="Claude Code /stats (~/.claude/stats-cache.json): input + output + cache writes + cache reads, all models")


def main():
    d = read_stats()
    with open(os.path.join(widgets.DATA, "tokens.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(d, fh, separators=(",", ":"))
        fh.write("\n")
    for p, s in widgets.write_widget("widget-tokens", widgets.tokens_svg, d):
        print("%7.1f KB  %s" % (s / 1024, os.path.basename(p)))
    print("total %s tokens, %s to %s" % ("{:,}".format(d["total"]), d["first"], d["asof"]))
    if "--no-push" in sys.argv:
        return
    git("add", "--", *FILES)
    if not git("diff", "--cached", "--quiet", "--", *FILES, check=False).returncode:
        print("no change; nothing pushed")
        return
    git("commit", "-m", "Token widget: %s tokens to %s" % (widgets.short(d["total"]), d["asof"]), "--", *FILES)
    if git("push", "origin", "HEAD:main", check=False).returncode:
        git("pull", "--rebase", "origin", "main")       # the daily Action may have pushed the GitHub widget meanwhile
        git("push", "origin", "HEAD:main")
    print("pushed")


if __name__ == "__main__":
    main()
