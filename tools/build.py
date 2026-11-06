"""Rebuilds everything this README shows.

    python tools/build.py             # the cards under the banner (assets/), then a local banner (.live/hero.svg)

The cards are static and committed to main (tools/koi/cards.py). The banner carries live numbers, so it is not
committed to main: tools/refresh.py builds it and publishes it to the `live` branch (run that to update the page).
Regenerating the plates from the TV's approved set: tools/plates.py; re-measuring the TV's clock: tools/measure_tv.mjs.
"""
import os
import runpy
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

runpy.run_path(os.path.join(HERE, "koi", "cards.py"), run_name="__main__")
kw = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
sys.exit(subprocess.run([sys.executable, os.path.join(HERE, "refresh.py"), "--no-push"], **kw).returncode)
