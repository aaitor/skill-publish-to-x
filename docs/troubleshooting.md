# Troubleshooting

| Symptom | Fix |
|---|---|
| `missing credentials: X_...` | Create `credentials.env` (see [Configuration](installation.md#configuration)), or export the variables. |
| `cannot read ~/.config/x-publisher/credentials.env` | Make the file readable by you (`chmod 600`) and save it as plain UTF-8 text. |
| `no account to post to` | Pass `--account <handle>` or set `X_ACCOUNT`. |
| `the file is written for @a, not @b` | The file's `account:` differs from the target. Rerun with `--account b` if that is intended. |
| `the X credentials are for @a, not @b` | Your access token belongs to another account. Generate one for the right account (see [Create an X app](installation.md#create-an-x-app)). |
| `401 Unauthorized` | Wrong or revoked keys. Copy them again from *Keys and tokens*. |
| `403 Forbidden` when posting | The access token is read-only. Set *Read and write*, then regenerate the Access Token and Secret. |
| An error about credits or spend | Add credits or raise your spending limit in the Developer Console. |
| `429 Too Many Requests` | Rate limited. Wait and retry; if it happened mid-thread, do not rerun (see below). |
| `post N of M failed ... already live` | Part of the thread is live. Don't rerun; delete those posts or finish the thread by hand. |
| `front matter line '...' is not 'key: value'` | The file starts with `---`, so its first block is read as front matter. If that block is a post, remove the leading `---`. |
| `post N is 291 characters` | Shorten it. Links count as 23, whatever their length. |
| `GIFs are not supported` | Convert to PNG, JPG or WEBP. |
| Cannot reach X, or `uv` cannot install tweepy | No network, or the agent's sandbox blocks it (see [Network and permissions](agent-setup.md#network-and-permissions)). |
| The agent doesn't use the skill | Check the install path for your agent (see [Install](installation.md)), restart the agent, and mention "X" or "tweet" in your request. |
