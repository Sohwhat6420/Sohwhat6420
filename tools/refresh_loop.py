"""Run refresh.py every 45 minutes, hidden. Started by detached-run.mjs as "gh-banner-refresh"; stop it with
node "C:/Users/ethan/.claude/scripts/detached-run.mjs" stop gh-banner-refresh
"""
import os
import subprocess
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "..", ".live", "refresh-loop.log")
EVERY = 45 * 60

os.makedirs(os.path.dirname(LOG), exist_ok=True)
while True:
    started = datetime.now().isoformat(timespec="seconds")
    try:
        r = subprocess.run([sys.executable, "-B", os.path.join(HERE, "refresh.py")], cwd=os.path.dirname(HERE),
                           capture_output=True, text=True, timeout=900,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        line = f"{started} exit {r.returncode} {(r.stdout or r.stderr).strip().splitlines()[-1:] }"
    except Exception as e:  # keep looping; one bad refresh must not stop the next
        line = f"{started} error {e!r}"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    time.sleep(EVERY)
