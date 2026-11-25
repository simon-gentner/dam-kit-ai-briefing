# Onboarding: first run

Sets up a new ai-briefing agent, **once per agent**. Every step is safe to repeat and never overwrites an existing file under `~/work`.

Skip if `~/.ai-briefing-onboarded` exists. Then only [`AGENTS.md`](AGENTS.md) applies, unless the owner wants to **add a workspace** (below).

Talk to the owner in the language they write in.

**Ask through the harness.** Every question with fixed answers (yes/no, a choice, a pick from a list) goes through the harness's question tool, `AskUserQuestion` on Claude Code: the web chat shows it as clickable options, with "Other" for free text. Put your suggestion first and mark it "(Recommended)". The tool takes up to 4 questions per call and 2–4 options per question; for longer lists, see the paging rule where a step needs it. Ask open questions (names, topics, URLs) as plain text. If the tool is unavailable or fails (e.g. in a Slack thread), ask the same thing as plain text with a numbered list.

**Checklist first:** call `set_onboarding_checklist` with these steps and tick each one with `complete_onboarding_step`:

1. `guard`: Write block installed
2. `owner`: Owner and language confirmed
3. `interests`: Interests defined
4. `sources`: Feeds defined
5. `channels`: Slack channels defined (optional)
6. `schedule`: Time and days defined
7. `test`: Test briefing posted

The agent's schedules stay on hold until step 9 completes onboarding.

## 1. Write block (`guard`)

```bash
python3 ~/scripts/install.py
```

The output lists `slack_servers`, the Slack connections of this agent. If the list is empty, no Slack connection is granted. Without one there is only the News block. Offer **Add a workspace** (below); the owner may also skip Slack.

**Are all workspaces connected?** Each Slack connection covers exactly **one** workspace. A channel in a workspace without its own connection is invisible to this agent, and searching for it ends in "not found". So, when the list is not empty, name the connected servers and ask with `AskUserQuestion`: *"Are all Slack workspaces you want me to cover connected?"*

- **"Yes, that's all" (Recommended):** continue.
- **"I need to add one":** walk through **Add a workspace** (below). A new connection reaches the agent only after a restart, so stop onboarding here and tell the owner: *after the restart, come back to this chat and write "continue".* Then start again at step 1; every step is safe to repeat.
- **"I'm not sure":** explain how to tell: in Slack, the workspace switcher shows every workspace they are in, and a message link of a channel shows its workspace in the domain (`https://<workspace>.slack.com/archives/…`). A channel that later cannot be found is the typical sign of a missing connection.

If the script reports "Not the Claude Code harness", tell the owner clearly that the Slack write tools are **not** blocked, and recommend Claude Code.

Say once, in plain words: *This agent reads Slack as you. Never share it, and bind it only to a private channel with only you in it.*

## 2. Owner and workspaces (`owner`)

- `slack_read_user_profile` **without** `user_id` on the first Slack server: that is the owner. Show the name and have it confirmed.
- For every Slack server: one search with `slack_search_public_and_private` (`query: "a"`, `limit: 1`), and take the `permalink_base` from the permalink. Suggest a workspace name.
- `language`: the language the owner writes in during this onboarding. Mention that replies always follow the language of their message and that only the scheduled briefing uses `language`.
- Ask for the title of the Community block (suggestion: "🏢 <workspace name> Community", or just "🏢 Community", in `language`).

## 3. Create the working files

```bash
mkdir -p ~/work/briefings ~/work/state
for f in interests sources feedback slack-channels; do
  [ -f ~/work/$f.md ] || cp ~/templates/$f.md ~/work/$f.md
done
```

## 4. Interests (`interests`)

Show the topics from `~/work/interests.md` and ask: *What of this interests you, what is missing, what do you never want to see?* Turn the answer into topics with a priority (high, medium, low) and exclusions, with the owner's own words in the "examples" column.

## 5. Feeds (`sources`)

Show the feeds from `~/work/sources.md` and ask which stay and which to add (RSS, Atom or the HF Daily Papers API). For every new host, propose a rule with `egress_proposal`. Then check:

```bash
python3 ~/scripts/fetch_feeds.py --dry-run --since-hours 48 | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['per_source'], d['errors'])"
```

Show the owner every source with an error: either the network rule is missing or the feed is broken.

## 6. Slack channels (`channels`, optional)

Ask: *Which Slack channels should I watch for the Community block?* Find each name per [`AGENTS.md`](AGENTS.md) → "Finding a channel by name" (every server, then the owner's channel list with all pages), take its `permalink_base`, and add it to `~/work/slack-channels.md`. Report every name you could not find, with the servers you searched. If the owner says such a channel is in another workspace, guide them through **Add a workspace** (below) and add the channel after the restart. An empty list is fine; then the Community block is left out.

## 7. Write `~/work/CONFIG.md`

Exactly in this shape (values are examples):

```markdown
# Configuration: ai-briefing

- owner_name: Jane Doe
- owner_slack_user_id: U0123ABCD
- language: German
- community_title: 🏢 Example Corp Community
- briefing_time: 09:00
- days: MO,TU,WE,TH,FR
- timezone: Europe/Berlin
- channel_id: C0123ABCD

## workspaces

| server | workspace | permalink_base |
| --- | --- | --- |
| slack-account | Example Corp | https://example.enterprise.slack.com |
```

## 8. Schedule and channel (`schedule`)

Ask for the time, days and time zone (suggestion: weekdays 09:00, Europe/Berlin). The kit creates the schedule `morning-briefing` with this default. Check it with `mcp__platform-outbound__list_schedules`. If the wish differs, create a new one with `create_schedule` (same name and task text, `rrule: FREQ=WEEKLY;BYDAY=<days>;BYHOUR=<HH>;BYMINUTE=<MM>`, `timezone`, `sessionMode: fresh`), then delete the old one. Never use an in-process cron.

Check the bound channel with `mcp__platform-outbound__describe_channel` (`channel: "slack"`) and its members with `slack_list_channel_members`. No channel bound: ask the owner to create a private channel, invite the DAM bot and bind it (`/dam bind` in the channel, or agent → Channels → Add Slack channel in the web app, or `dam channel slack connect <agent> --channel-id <ID> --no-ambient`). Other members: warn and continue only when the channel is private.

## 9. Test briefing and finish (`test`)

Create a **test briefing** per [`AGENTS.md`](AGENTS.md) (`--since-hours 24`, mark nothing) and post it into the channel. Ask the owner what to change and apply it.

```bash
date -u +%Y-%m-%dT%H:%M:%SZ > ~/.ai-briefing-onboarded
```

Then call `mark_onboarding_complete` and summarize briefly:

1. the `CONFIG.md`
2. when the briefing arrives
3. feedback goes as a reply in the thread ("3 was great", "more on X", "new feed: …", "add channel #y")
4. never share this agent

## Add a workspace (any time)

Guide the owner through these steps, with this agent's name filled in for `<agent>`:

1. **Find the workspace:** in Slack, open a channel of that workspace and copy a message link; the domain is the workspace (`https://<workspace>.slack.com/…`).
2. **Create the connection:**
   - Web app: Settings → Connections → **Add connection** → Apps → **Slack Account** → **New**. In Slack's login dialog, pick that workspace in the top-right corner.
   - CLI: `dam connection connect slack --name slack-<workspace>`, and pick the workspace in the login dialog.
3. **Grant it to this agent:** in the web app under the agent's connections, or `dam connection grant <agent> --connection slack-<workspace>`.
4. **Restart the agent:** in the web app, or `dam agent restart <agent>`.

If Slack's login dialog does not offer the workspace, the DAM Slack app is not installed there; only that workspace's admins can add it.

After the restart, the SessionStart hook reports the new server. Run the "workspaces" part of step 2 for it, add the row to `## workspaces` and confirm it in one sentence. Ask whether to look up any channels there again that were not found before. The hook installs the write block for the new server itself.
