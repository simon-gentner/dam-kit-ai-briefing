# Changelog

All notable changes to this kit. The version in `VERSION` is the one installed on an agent.
`dam kit changes <agent>` shows what an update brings; `dam kit update <agent>` takes it.

## 0.3.0 (2026-11-25)

- Kit updates: the agent now applies a `dam kit update` itself. It takes the new definition files as they are, leaves `~/work/` untouched, re-runs `install.py` and reports what changed.
- Added `VERSION` and this changelog.

## 0.2.0 (2026-11-25)

- Onboarding asks fixed-answer questions through the harness (`AskUserQuestion`), with a numbered-list fallback.

## 0.1.0 (2026-11-25)

- First version: morning AI briefing in Slack with a News block from feeds and a Community block from Slack channels, tuned by replies in the thread.
- Default feeds: AlphaSignal, Import AI, Phil Schmid, Hugging Face Trending Papers.
- Write block for all Slack connections, detected at runtime from `~/.mcp.json`.
