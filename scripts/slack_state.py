#!/usr/bin/env python3
"""Remember which Slack threads the briefing already reported (~/work/state/slack-reported.json).

  slack_state.py filter  < candidates.json   -> prints the candidates worth reporting
  slack_state.py mark    < reported.json     -> records them as reported
  slack_state.py show                        -> prints the state

Input: a JSON list of {"channel": "C0...", "ts": "<thread or message ts>", "replies": <int>}.
Other fields are passed through unchanged.

filter keeps a candidate when it was never reported ("status": "new"), or when it was
reported but has gained at least MIN_NEW_REPLIES replies since ("status": "update",
"new_replies": n). Entries older than KEEP_DAYS are dropped from the state on mark.
"""
import json
import sys
import time
from pathlib import Path

STATE = Path.home() / "work" / "state" / "slack-reported.json"
MIN_NEW_REPLIES = 3
KEEP_DAYS = 30


def load():
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def key(c):
    return f"{c['channel']}:{c['ts']}"


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "show"
    state = load()
    if cmd == "show":
        json.dump(state, sys.stdout, indent=1)
        print()
        return 0
    items = json.load(sys.stdin)
    if cmd == "filter":
        out = []
        for c in items:
            prev = state.get(key(c))
            replies = int(c.get("replies") or 0)
            if prev is None:
                out.append({**c, "status": "new"})
            elif replies - prev["replies"] >= MIN_NEW_REPLIES:
                out.append({**c, "status": "update", "new_replies": replies - prev["replies"]})
        json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
        print()
        return 0
    if cmd == "mark":
        now = time.time()
        for c in items:
            state[key(c)] = {"replies": int(c.get("replies") or 0), "reported_at": now}
        state = {k: v for k, v in state.items() if now - v["reported_at"] < KEEP_DAYS * 86400}
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(state, indent=0))
        print(f"marked {len(items)}, state has {len(state)}")
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
