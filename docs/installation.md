# Installation and configuration

Python 3.10+ is required. Dry runs use the standard library; live publishing requires `tweepy==4.17.0`. Use `uv run` to resolve the script dependency, or install tweepy in a virtual environment and run with Python. The project has been tested on Linux.

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

In this guide, `<skill-dir>` means the directory you cloned into. To update later, run `git -C <skill-dir> pull`.

## Create an X app

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

## Configuration

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
