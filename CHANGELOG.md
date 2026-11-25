# Changelog

All notable changes to this kit. The version in `VERSION` is the one installed on an agent.
`dam kit changes <agent>` shows what an update brings; `dam kit update <agent>` takes it.

## 0.3.2 (2026-11-25)

- Onboarding now checks that every Slack workspace the owner wants covered has its own connection, and guides through adding one (web app or CLI, grant, restart, then continue onboarding). A channel in an unconnected workspace was reported as not found before.
- "Add a workspace" is a step-by-step guide, including how to find a channel's workspace and what to do when Slack's login does not offer it.

## 0.3.1 (2026-11-25)

- Fix: channels named during onboarding or in chat ("add channel #x") are now looked up on every connected workspace, and in the owner's own channel list with all pages when the name search finds nothing. Private channels and channels in a second workspace (e.g. `channel_not_found` on the first one) were reported as missing before.
- `slack-channels.md` stores a `permalink_base` per channel, because on Enterprise Grid one connection spans several workspace domains. **On update:** add the column to every existing line, taken from the permalink of one message in that channel.

## 0.3.0 (2026-11-25)

- Kit updates: the agent now applies a `dam kit update` itself. It takes the new definition files as they are, leaves `~/work/` untouched, re-runs `install.py` and reports what changed.
- Added `VERSION` and this changelog.

## 0.2.0 (2026-11-25)

- Onboarding asks fixed-answer questions through the harness (`AskUserQuestion`), with a numbered-list fallback.

## 0.1.0 (2026-11-25)

- First version: morning AI briefing in Slack with a News block from feeds and a Community block from Slack channels, tuned by replies in the thread.
- Default feeds: AlphaSignal, Import AI, Phil Schmid, Hugging Face Trending Papers.
- Write block for all Slack connections, detected at runtime from `~/.mcp.json`.
