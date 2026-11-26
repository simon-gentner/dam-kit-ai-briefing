#!/usr/bin/env python3
"""Remember which Slack threads the briefing already reported (~/work/state/slack-reported.json).

  slack_state.py filter < candidates.json   -> prints the candidates worth reporting and
                                               keeps them as the pending set
  slack_state.py mark                       -> records the pending set as reported
  slack_state.py show                       -> prints the state

Input for filter: a JSON list of {"channel": "C0...", "ts": "<thread or message ts>",
"replies": <int>}. Keep it to these three: the agent already has the text from reading
the channel. Other fields are passed through unchanged.

`channel` must be the channel ID (C…, G… or D…), never the name: the state is keyed by
ID, so a name would never match again. filter refuses the whole input otherwise.

filter keeps a candidate when it was never reported ("status": "new"), or when it was
reported but has gained at least MIN_NEW_REPLIES replies since ("status": "update",
"new_replies": n). It stores exactly these as the pending set.

mark takes no input: it records the pending set from the last filter run, so nothing
can be marked without being filtered first. A pending set older than PENDING_MAX_HOURS
is refused. Entries older than KEEP_DAYS are dropped from the state on mark.

State written before 0.3.4 may be keyed by channel name; it is converted to IDs on the
next run, using ~/work/slack-channels.md. Names it cannot map are dropped (and listed).
"""
import json
import re
import sys
import time
from pathlib import Path

WORK = Path.home() / "work"
STATE = WORK / "state" / "slack-reported.json"
PENDING = WORK / "state" / "slack-pending.json"
CHANNELS = WORK / "slack-channels.md"
MIN_NEW_REPLIES = 3
KEEP_DAYS = 30
PENDING_MAX_HOURS = 6
CHANNEL_ID = re.compile(r"^[CGD][A-Z0-9]{6,}$")
TS = re.compile(r"^\d+\.\d+$")


def fail(msg):
    print(f"slack_state.py: {msg}", file=sys.stderr)
    sys.exit(2)


def name_to_id():
    """Map '#name' and 'name' to the channel ID from slack-channels.md."""
    mapping = {}
    if CHANNELS.exists():
        for line in CHANNELS.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\s*-\s*#?([\w.-]+)\s*\|\s*([CGD][A-Z0-9]{6,})\s*\|", line)
            if m:
                mapping[m.group(1).lower()] = m.group(2)
    return mapping


def load():
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    if all(CHANNEL_ID.match(k.split(":", 1)[0]) for k in state):
        return state
    mapping, converted, dropped = name_to_id(), {}, []
    for k, v in state.items():
        ch, _, ts = k.partition(":")
        cid = ch if CHANNEL_ID.match(ch) else mapping.get(ch.lstrip("#").lower())
        if cid:
            converted[f"{cid}:{ts}"] = v
        else:
            dropped.append(ch)
    print(f"slack_state.py: converted state from channel names to IDs ({len(converted)} kept"
          + (f", dropped unknown channels: {sorted(set(dropped))}" if dropped else "") + ")",
          file=sys.stderr)
    save(converted)
    return converted


def save(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=0))


def key(c):
    return f"{c['channel']}:{c['ts']}"


def validate(items):
    if not isinstance(items, list):
        fail("input must be a JSON list of candidates")
    bad = []
    for i, c in enumerate(items):
        ch, ts = str(c.get("channel", "")), str(c.get("ts", ""))
        if not CHANNEL_ID.match(ch) or not TS.match(ts):
            bad.append(f"#{i}: channel={ch!r} ts={ts!r}")
    if bad:
        fail("every candidate needs the channel ID (e.g. C01ABCDEF, not the name) and the "
             "message ts (e.g. 1795553477.459459). Fix these and run filter again:\n  "
             + "\n  ".join(bad[:20]))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "show"
    if cmd == "show":
        json.dump(load(), sys.stdout, indent=1)
        print()
        return 0
    if cmd == "filter":
        items = json.load(sys.stdin)
        validate(items)
        state = load()
        out = []
        for c in items:
            prev = state.get(key(c))
            replies = int(c.get("replies") or 0)
            if prev is None:
                out.append({**c, "status": "new"})
            elif replies - prev["replies"] >= MIN_NEW_REPLIES:
                out.append({**c, "status": "update", "new_replies": replies - prev["replies"]})
        PENDING.parent.mkdir(parents=True, exist_ok=True)
        PENDING.write_text(json.dumps({"created_at": time.time(), "items": out}))
        json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
        print()
        print(f"slack_state.py: {len(out)} of {len(items)} candidates kept; run `mark` after posting",
              file=sys.stderr)
        return 0
    if cmd == "mark":
        # Any input on stdin is ignored on purpose: mark records the pending set only.
        if not PENDING.exists():
            fail("nothing to mark: run `filter < candidates.json` first. Skipping filter would "
                 "report the same threads again tomorrow.")
        pending = json.loads(PENDING.read_text())
        age_h = (time.time() - pending["created_at"]) / 3600
        if age_h > PENDING_MAX_HOURS:
            fail(f"the pending set is {age_h:.0f} hours old: run `filter` again for this briefing.")
        state, now = load(), time.time()
        for c in pending["items"]:
            state[key(c)] = {"replies": int(c.get("replies") or 0), "reported_at": now}
        state = {k: v for k, v in state.items() if now - v["reported_at"] < KEEP_DAYS * 86400}
        save(state)
        PENDING.unlink()
        print(f"marked {len(pending['items'])}, state has {len(state)}")
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
