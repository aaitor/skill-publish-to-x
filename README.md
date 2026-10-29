# Publish to X: an Agent Skill

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Dependencies: tweepy](https://img.shields.io/badge/dependencies-tweepy-brightgreen)
[![Agent Skills](https://img.shields.io/badge/format-Agent%20Skills-purple)](https://agentskills.io)

An [Agent Skill](https://agentskills.io) that lets your AI agent write and publish posts and threads, with images, on **your own X (Twitter) account**, using the official [X API v2](https://docs.x.com/x-api/introduction).

It works with any agent that supports the open `SKILL.md` format. It has been tested with **Claude Code**.

```text
You:    Write an X thread about our v2 release and post it with ./chart.png on the first post
Agent:  [drafts the thread, shows a dry-run preview: 3 posts, 241/198/122 chars, chart.png on post 1] Post it as is?
You:    yes
Agent:  Posted: https://x.com/you/status/1849...
```

## Features

- **Single posts and threads.** Each post is published as a reply to the previous one.
- **Images:** up to 4 per post (PNG, JPG or WEBP), uploaded before anything is posted.
- **Length check as X counts it:** 280 characters per post, every link counted as 23.
- **Dry-run preview and an approval gate:** the agent shows you every post and publishes only after you approve it.
- **Account guard:** before posting, the script checks that your credentials belong to the account you asked for.
- **Safe failures:** a failed image upload posts nothing. A failure mid-thread lists the posts already live, so nothing is posted twice.
- **One dependency** ([tweepy](https://www.tweepy.org)) for publishing; the dry run uses only the standard library.

## How it works

```text
agent ──> scripts/publish_x.py ──> X API v2 (/2/users/me, /2/media/upload, /2/tweets)
               │
               ├── x.md (or any text file)   your post or thread, images declared in a comment
               └── ~/.config/x-publisher/
                     credentials.env         your X app keys and access token (you create this)
```

You create your own X developer app once and generate an access token for your account. The agent reads `SKILL.md`, writes the post to a file, previews it with a dry run and publishes it after you approve. Because the logic lives in a plain CLI, you can also use it without an agent.

## Requirements

- Python 3.10 or later, and [`uv`](https://docs.astral.sh/uv/) (recommended: `uv run` installs `tweepy` from the script header). Without `uv`, run `pip install tweepy==4.17.0` and use `python3`. Tested on Linux.
- An X account and an [X developer account](https://console.x.com) with credits. The X API is pay-per-use (see [Cost](#cost)).
- An agent that supports [Agent Skills](https://agentskills.io), such as Claude Code or OpenAI Codex. This is optional if you only use the CLI.

## 1. Install

Clone the repository into your agent's skills directory:

| Agent | Personal (all projects) | One project only |
|---|---|---|
| Claude Code | `~/.claude/skills/publish-to-x` | `<project>/.claude/skills/publish-to-x` |
| OpenAI Codex | `~/.agents/skills/publish-to-x` | `<project>/.agents/skills/publish-to-x` |
| Other agents | Your tool's skills directory (see its docs and the [client list](https://agentskills.io/clients)) | |

```bash
# Example: Claude Code
git clone https://github.com/aaitor/skill-publish-to-x.git ~/.claude/skills/publish-to-x

# Using more than one agent? Clone once and symlink, for example for Codex:
ln -s ~/.claude/skills/publish-to-x ~/.agents/skills/publish-to-x
```

In the rest of this README, `<skill-dir>` means the directory you cloned into. To update later, run `git -C <skill-dir> pull`.

## 2. Create an X app

1. Sign in to the [X Developer Console](https://console.x.com) **with the account you want to post from**, and add credits ([pricing](https://docs.x.com/x-api/getting-started/pricing)). You can set a maximum spend per billing cycle.
2. Create an app. In its **User authentication settings**, set *App permissions* to **Read and write**. The form also asks for a callback URL and a website; any valid URL works for this skill, which does not use the callback.
3. In **Keys and tokens**, generate:
   - the **API Key and Secret** (also called consumer key and secret);
   - the **Access Token and Secret**. Generate these **after** setting Read and write: a token generated earlier stays read-only.

The access token belongs to the account that owns the app. To post from a different account, authorize it once with the PIN flow and use the token it returns:

```python
import tweepy
h = tweepy.OAuth1UserHandler("<API key>", "<API key secret>", callback="oob")
print(h.get_authorization_url())          # open it signed in as the other account, click Authorize
token, secret = h.get_access_token(input("PIN: "))
```

## 3. Configuration

Store the credentials in `~/.config/x-publisher/credentials.env`, readable only by you:

```bash
mkdir -p -m 700 ~/.config/x-publisher
touch ~/.config/x-publisher/credentials.env
chmod 600 ~/.config/x-publisher/credentials.env
"${EDITOR:-nano}" ~/.config/x-publisher/credentials.env
```

```bash
X_CONSUMER_KEY=your-api-key
X_CONSUMER_KEY_SECRET=your-api-key-secret
X_ACCESS_TOKEN_OAUTH1=your-access-token
X_ACCESS_TOKEN_SECRET_OAUTH1=your-access-token-secret
X_ACCOUNT=yourhandle
```

The file uses plain `KEY=VALUE` lines, optionally prefixed with `export`. Comments and quotes are fine, and lines that don't start with `X_` are ignored, so the file can be shared with other tools. If you already keep these values in another env file, symlink it to this path. Environment variables with the same names take precedence over the file. The script warns if the file is readable by other users.

| Setting | Default | Purpose |
|---|---|---|
| `X_CONSUMER_KEY`, `X_CONSUMER_KEY_SECRET` | none | Your app's API Key and Secret |
| `X_ACCESS_TOKEN_OAUTH1`, `X_ACCESS_TOKEN_SECRET_OAUTH1` | none | Your OAuth 1.0a Access Token and Secret. The `_OAUTH1` suffix keeps them apart from an OAuth 2.0 `X_ACCESS_TOKEN`, which this skill never uses. |
| `X_ACCOUNT` | none | Handle to post to when `--account` is not given. Without it, the file's `account:` is used. |

Never paste these values into the agent chat.

## Usage

### With your agent

Ask in plain language. For example:

- "Post on X: *We just shipped dark mode. Thanks to everyone who asked for it!*"
- "Turn this blog post into a 4-post X thread with ./cover.png on the first post, and show me before posting."
- "Preview this thread for X, don't post it yet: ..."

The agent follows the workflow in [`SKILL.md`](SKILL.md):

1. Drafts the text, using a writing-voice or style skill if you have one.
2. Runs a dry run and shows you every post, its length and its images.
3. Publishes only after you explicitly approve that text.
4. Returns the post URLs.

### Network access in Codex

Codex runs commands in a sandbox with no network access by default, so `uv` cannot install `tweepy` and the script cannot reach X. Approve running the command outside the sandbox when Codex asks, or enable network access:

```bash
codex --sandbox workspace-write -c sandbox_workspace_write.network_access=true
```

Claude Code needs no extra setup. It asks for permission before running commands, according to your permission settings.

### Command line

```bash
X="uv run <skill-dir>/scripts/publish_x.py"

$X post.txt                          # dry run of a single post
$X my-thread/                        # dry run of my-thread/x.md
$X my-thread/ --account yourhandle --live
```

| Option | Description |
|---|---|
| `path` | A folder holding `x.md`, or any text file. |
| `--account HANDLE` | Account to post to. Default: `X_ACCOUNT`, else the file's `account:`. Required when the file names another account. |
| `--live` | Publish. Without it, nothing is sent to X. |

### The post file

```markdown
---
account: yourhandle
---

<!-- post 1: assets/chart.png (the chart). post 2: assets/demo.png, assets/team.png -->

1/ We shipped v2 today. Release notes: https://example.com/v2

---

2/ Thanks to everyone who tested the beta.
```

- **Front matter** is optional: lowercase `key: value` lines between the first two `---` lines. A file that starts with `---` followed by ordinary text has no front matter, so its first post is kept. `account` is the handle the text was written for. If it differs from the account you post to, the script asks you to confirm with `--account`.
- **Posts** are separated by a line holding only `---`. A single post has no separators.
- **HTML comments** are never posted and never count toward the 280 characters.
- **Images** are declared in a comment as `post N: <path>`, relative to the file and inside its folder.

## Cost

The X API is pay-per-use: you buy credits in the [Developer Console](https://console.x.com) and each request is deducted. As of October 2026, X's [pricing page](https://docs.x.com/x-api/getting-started/pricing) lists creating a post at **$0.015**, or **$0.200** when the post contains a URL, and a user lookup at $0.010. Each live run makes one account lookup, one upload per image and one request per post.

## Security and privacy

- **Local credentials:** keys and tokens stay on your machine, in the credentials file or your environment. The script never prints or writes them, and error messages name a missing setting, never its value.
- **Approval:** the skill instructs the agent never to publish without your explicit approval of the exact text.
- **Account check:** before posting, the script confirms that the credentials belong to the target account.
- **Network:** requests go only to the X API, through tweepy.
- **Revoking access:** OAuth 1.0a access tokens do not expire. Regenerate or revoke them in the app's *Keys and tokens*, or remove the app under *Settings → Security and account access → Apps and sessions → Connected apps* on X.

Use it in line with X's [Developer Agreement and Policy](https://developer.x.com/en/developer-terms) and [automation rules](https://help.x.com/en/rules-and-policies/x-automation). Don't use it for spam or mass posting.

## Limitations

- Posts go to the account that owns the access token.
- **Not supported:** video, GIF, polls, quote posts, editing, deleting and scheduling.
- The length check counts emoji and CJK characters as 1; X counts them as 2.
- A thread that fails midway is not resumed. The error lists what is live, and you finish it by hand.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `missing credentials: X_...` | Create `credentials.env` (see [Configuration](#3-configuration)), or export the variables. |
| `no account to post to` | Pass `--account <handle>` or set `X_ACCOUNT`. |
| `the file is written for @a, not @b` | The file's `account:` differs from the target. Rerun with `--account b` if that is intended. |
| `the X credentials are for @a, not @b` | Your access token belongs to another account. Generate one for the right account (see [Create an X app](#2-create-an-x-app)). |
| `401 Unauthorized` | Wrong or revoked keys. Copy them again from *Keys and tokens*. |
| `403 Forbidden` when posting | The access token is read-only. Set *Read and write*, then regenerate the Access Token and Secret. |
| An error about credits or spend | Add credits or raise your spending limit in the Developer Console. |
| `429 Too Many Requests` | Rate limited. Wait and retry; if it happened mid-thread, do not rerun (see below). |
| `post N of M failed ... already live` | Part of the thread is live. Don't rerun; delete those posts or finish the thread by hand. |
| `post N is 291 characters` | Shorten it. Links count as 23, whatever their length. |
| `GIFs are not supported` | Convert to PNG, JPG or WEBP. |
| Cannot reach X, or `uv` cannot install tweepy | No network, or the agent's sandbox blocks it (see [Network access in Codex](#network-access-in-codex)). |
| The agent doesn't use the skill | Check the install path for your agent (see [Install](#1-install)), restart the agent, and mention "X" or "tweet" in your request. |

## Development

```text
SKILL.md                  instructions the agent loads (Agent Skills format)
scripts/publish_x.py      CLI: parse, check, upload images, post the thread
scripts/test_publish_x.py tests (X client mocked; one runs real tweepy signing with the network faked)
```

Run the tests with `uv run --no-project --with pytest --with tweepy==4.17.0 pytest -q scripts` and lint with `ruff check --line-length 120 .`. No test calls X. Issues and pull requests are welcome.

## License

[MIT](LICENSE). This project is not affiliated with or endorsed by X Corp., Anthropic or OpenAI.
