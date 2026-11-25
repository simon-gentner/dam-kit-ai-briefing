# Watched Slack channels

The agent reads only these channels (as the owner, read-only). `server` is the Slack MCP server from `CONFIG.md → ## workspaces` through which the channel is reachable.

Format: `- #<channel-name> | <channel ID> | <server> | <permalink_base> | <why / topic> | since YYYY-MM-DD`

`permalink_base` is the workspace domain of the channel's permalinks, e.g. `https://example.slack.com`. On Enterprise Grid it can differ per channel.

