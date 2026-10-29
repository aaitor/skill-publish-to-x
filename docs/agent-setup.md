# Install with your agent

Clone the repository into your agent's skills directory. Keep the full folder together: `SKILL.md` uses the bundled CLI and setup documentation.

| Agent | Personal skills | Project skills |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/publish-to-x` | `.claude/skills/publish-to-x` |
| Codex | `~/.agents/skills/publish-to-x` | `.agents/skills/publish-to-x` |

```bash
git clone https://github.com/aaitor/skill-publish-to-x .claude/skills/publish-to-x
```

Create a post file, then ask Claude Code to preview it:

```text
/publish-to-x Preview message.txt for @yourhandle. Ask before posting.
```

The skill shows each post, its length, images, and target account before requesting approval. Approval must cover the exact text and account; installing the skill does not authorize posting.

## Network and permissions

A Python dry run makes no X API requests and does not require tweepy or API credentials. Live posting requires network access to X and configured OAuth credentials. `uv run` may also need network access to install tweepy. Agent sandbox and command-permission settings vary; allow the access needed for the task in your harness. See [installation](installation.md) and [troubleshooting](troubleshooting.md).
