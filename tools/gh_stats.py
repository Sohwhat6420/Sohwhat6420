"""Reads Ethan's public GitHub numbers from the GraphQL API and redraws the GitHub widget.

    python tools/gh_stats.py [login]

The token comes from GITHUB_TOKEN (the daily Action, .github/workflows/github-stats.yml) or, on a laptop, from
`gh auth token`. Only public data is read: the contribution calendar (the number his profile shows, which counts
private contributions as plain numbers, never repository names), his public non-fork repositories, their stars and
their languages by size. Writes data/github.json and assets/widget-github-{dark,light}.svg. Exits non-zero, writing
nothing, if the API fails, so a bad day never replaces good numbers.
"""
import datetime as dt
import json
import os
import subprocess
import sys
import urllib.request

import widgets

WEEKS = 40
QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
    }
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false, first: 100) {
      totalCount
      nodes { stargazerCount languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } } }
    }
  }
}
"""


def token():
    t = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if t:
        return t
    kw = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True, **kw).stdout.strip()


def fetch(login):
    req = urllib.request.Request("https://api.github.com/graphql",
                                 data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
                                 headers={"Authorization": "bearer " + token(), "User-Agent": "profile-readme-stats"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if body.get("errors") or not body.get("data", {}).get("user"):
        raise SystemExit("GraphQL error: %s" % json.dumps(body.get("errors"))[:500])
    return body["data"]["user"]


def summarise(u):
    cal = u["contributionsCollection"]["contributionCalendar"]
    weeks = []
    for w in cal["weeks"][-WEEKS:]:
        col = [None] * 7
        for d in w["contributionDays"]:
            col[(dt.date.fromisoformat(d["date"]).weekday() + 1) % 7] = d["contributionCount"]   # Sunday first
        weeks.append(col)
    repos = u["repositories"]["nodes"]
    size = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            size[e["node"]["name"]] = size.get(e["node"]["name"], 0) + e["size"]
    tot = sum(size.values()) or 1
    langs = sorted(((n, 100.0 * s / tot) for n, s in size.items()), key=lambda x: -x[1])
    return dict(asof=dt.datetime.now(dt.timezone.utc).date().isoformat(),
                contributions=cal["totalContributions"], repos=u["repositories"]["totalCount"],
                stars=sum(r["stargazerCount"] for r in repos),
                languages=[[n, round(p, 1)] for n, p in langs if p >= 1][:5], weeks=weeks)


def main():
    login = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GITHUB_REPOSITORY_OWNER", "Sohwhat6420")
    d = summarise(fetch(login))
    os.makedirs(widgets.DATA, exist_ok=True)
    with open(os.path.join(widgets.DATA, "github.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(d, fh, separators=(",", ":"))
        fh.write("\n")
    for p, s in widgets.write_widget("widget-github", widgets.github_svg, d):
        print("%7.1f KB  %s" % (s / 1024, os.path.basename(p)))
    print("contributions %d, repos %d, stars %d, languages %s" % (d["contributions"], d["repos"], d["stars"], d["languages"]))


if __name__ == "__main__":
    main()
