# AI Briefing: DAM starter kit

A personal AI briefing, posted to Slack every morning. The agent reads AI feeds and the Slack channels you choose, ranks everything by your interests, and posts two blocks: **📰 News** from the feeds and **🏢 Community** from Slack, at most 10 entries each. You tune it by replying in the thread.

> ⚠️ For the Community block the agent reads Slack **as you**, but never writes there. Don't share it, and bind it only to a private channel with nobody but you in it.

## What you need

- Access to a DAM host and an account on it.
- The **DAM Slack app** installed in your Slack workspace. If it is missing, the Slack login fails. Ask your DAM administrator or the workspace admins to install it.
- About 15 minutes. You do **not** need the `dam` CLI; everything works in the web app. CLI commands are listed as an alternative.

## Setup

### 1. Connect your Slack account (optional)

Needed only for the Community block. Without it, you get News from the feeds only.

- **Web app:** Settings → Connections → **Add connection** → Connection catalog → **Apps** tab → **New** on the **Slack Account** card. Sign in, and pick the workspace in the top-right corner of Slack's login dialog.
- **CLI:**
  ```bash
  dam connection connect slack --name slack-account
  ```

To watch channels in more than one workspace, add one Slack Account connection per workspace. The agent detects each one on its own.

### 2. Create a private channel for the briefing

1. In Slack, create a **private** channel, e.g. `#my-ai-briefing`. Don't add anyone else.
2. Invite the **DAM** app to the channel (channel details → Integrations → Add apps, or mention `@DAM` and accept the invite prompt).
3. Run `/dam login` once in the channel so DAM knows your Slack account.

### 3. Create the agent from the kit

- **Web app:**
  1. Home → **Browse starter kits** → **Import from link**.
  2. Paste the link of this repository (the repo itself, not a branch or folder) and click **Open kit**.
  3. The dialog shows what the kit sets up: the network rules for the feeds and the schedule `morning-briefing`. Give the agent a name (e.g. `ai-briefing`), grant your Slack Account connection, and create it.
- **CLI:**
  ```bash
  dam kit show <repo-url>          # what the kit sets up and needs
  dam agent create ai-briefing --kit <repo-url> --connection slack-account
  ```

The harness must be **Claude Code** (the kit allows nothing else).

### 4. Bind the channel

- **Web app:** open the agent → **Channels** → Slack card → **Add Slack channel** → pick your private channel. Leave **ambient mode off**.
- **In Slack:** in the channel, run `/dam bind` and pick the agent.
- **CLI:**
  ```bash
  dam channel slack connect ai-briefing --channel-id <channel-id> --no-ambient
  ```

### 5. Onboarding (first session)

Open the agent's chat in the web app. The first session walks you through setup with a checklist:

1. installs the write block for your Slack connection(s)
2. confirms your Slack profile and sets the briefing language to the one you write in
3. **Interests:** shows starter topics and asks what to keep, add or exclude
4. **Feeds:** shows the default feeds and tests them. For a new feed it proposes a network rule for you to approve.
5. **Channels:** asks which Slack channels to watch and resolves them by name
6. **Schedule:** asks for time, days and time zone (default: weekdays 09:00 Europe/Berlin)
7. posts a **test briefing** and asks what to change

The schedule stays on hold until onboarding is complete, so nothing is posted before you are happy with it. Your settings land in `~/work/` on the agent. Nothing personal goes into this repository.

## Usage

The briefing arrives as a new thread in your channel at the time you chose. Reply in the thread, in free form:

| You write | The agent |
|---|---|
| "3 was great", "less like 7" | records a rule in `feedback.md` and scores accordingly next time |
| "more on embeddings", "no robotics" | updates the topics in `interests.md` |
| "new feed: https://…" | adds it to `sources.md` and proposes a network rule |
| "add channel #xy" | resolves the channel and adds it to `slack-channels.md` |
| "briefing at 8 instead", "also on Saturdays" | replaces the schedule |
| "briefing in English, please" | changes the briefing language |
| "test briefing" | builds one now from the last 24 hours, without marking anything as seen |

Replies come in the language you write in. The scheduled briefing uses the configured language.

## Default feeds

AlphaSignal, Import AI, Phil Schmid, Hugging Face Trending Papers. Their hosts are allowed in `kit.yaml`. You can remove any of them during onboarding or later.

## Adding a workspace later

1. Add another Slack Account connection (step 1) and grant it to the agent (agent → Connections, or `dam connection grant ai-briefing --connection <name>`).
2. Restart the agent.
3. On its next session, the agent reports the new workspace and asks whether to add it. Then ask it to watch channels there.

## Updates

Agents don't update on their own. When this repository has a newer version, the owner decides:

```bash
dam kit changes <agent>   # what the new version brings (commits and CHANGELOG.md)
dam kit update <agent>    # take it: the agent applies it in a session of its own
dam kit skip <agent>      # skip this version; the next one is offered again
```

During the update the agent replaces only the definition files. Everything under `~/work/` (your settings and history) stays as it is. If a version needs a new setting, the agent asks you for it. See [`CHANGELOG.md`](CHANGELOG.md) for what changed in each version.

## Troubleshooting

| Symptom | Fix |
|---|---|
| No briefing in the morning | Onboarding is not complete (the schedule is on hold), or the schedule time differs. Ask the agent "when is my briefing scheduled?" |
| "⚠️ <feed> was unreachable" | The feed is down, or its host has no network rule. Ask the agent to check it. |
| Community block always empty | No Slack connection, no watched channels, or nothing new in 7 days. |
| A Slack login expired | Run `dam connection reauth <name>` or reconnect it in Settings → Connections. |

## Layout

| File | Purpose |
|---|---|
| `kit.yaml` | Kit manifest: connections, network rules, schedule `morning-briefing` |
| `VERSION`, `CHANGELOG.md` | Installed version and what changed in each version |
| `AGENTS.md` | Operating manual: procedure, format, feedback, hard rules |
| `ONBOARDING.md` | Setup on first run |
| `templates/` | Starting values for `interests.md`, `sources.md`, `slack-channels.md`, `feedback.md` |
| `scripts/fetch_feeds.py` | Fetches new feed entries (RSS, Atom, HF Papers) |
| `scripts/slack_state.py` | Remembers which Slack threads were reported |
| `scripts/install.py`, `slack-guard.sh`, `slack-tools.txt` | Slack write block, for every connected workspace |

Everything you configure lives on the agent under `~/work/` and is never versioned.
