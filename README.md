<p align="center">
  <img src="https://raw.githubusercontent.com/aaitor/assets/4f776361dcd3ff797af71aab3f85c09a805303ef/banners/skill-publish-to-x.svg" alt="Publish to X — draft, preview, and publish posts and threads" width="100%">
</p>

<h1 align="center">Publish to X</h1>
<p align="center">Draft, preview, and publish posts and threads.</p>
<p align="center">
  <a href="#quick-start">Quick start</a> ·
  <a href="docs/installation.md">Setup</a> ·
  <a href="docs/usage.md">Usage</a> ·
  <a href="#contributing-and-support">Contribute</a>
</p>
<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-89E5CC?style=flat-square&amp;labelColor=101827" alt="MIT license"></a>
  <a href="https://github.com/aaitor/skill-publish-to-x/actions/workflows/quality.yml"><img src="https://github.com/aaitor/skill-publish-to-x/actions/workflows/quality.yml/badge.svg" alt="Offline tests, lint, and documentation checks"></a>
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square" alt="Python 3.10 or later">
</p>

An [Agent Skill](https://agentskills.io) for publishing posts and threads, with images, to **your own X (Twitter) account** through the official [X API v2](https://docs.x.com/x-api/introduction). Tested with Claude Code; other Agent Skills clients can use the same `SKILL.md`. Live publishing uses tweepy; dry runs use only Python's standard library.

## Demo

![Install the skill and preview an X post with real Claude Code](assets/terminal-demo.gif)

A real recording: install the skill, invoke `/publish-to-x` in Claude Code, and review the draft, target account, and approval prompt. It uses the actual CLI dry-run, which makes no X API calls. Nothing is posted. The [recording guide](examples/README.md) includes the source, black-background preset, and reproduction command.

## Quick start

**Prerequisites:** Python 3.10+ and Git. Preview a post before configuring any API credentials:

```bash
git clone https://github.com/aaitor/skill-publish-to-x.git
cd skill-publish-to-x
python3 scripts/publish_x.py examples/post.txt --account yourhandle
```

Expected output: the target handle, post text, character count, images (`none`), and `Dry run: nothing posted`. No X API requests or tweepy installation are needed.

To use the skill from Claude Code, clone it into a project's skills directory:

```bash
git clone https://github.com/aaitor/skill-publish-to-x .claude/skills/publish-to-x
```

Create `message.txt`, then ask:

```text
/publish-to-x Preview message.txt for @yourhandle. Ask before posting.
```

For actual publishing, complete [app and credential setup](docs/installation.md), install tweepy through `uv run` or a virtual environment, then approve the exact text and target account. Direct CLI calls with `--live` publish immediately; omitting that flag is the default dry run. See [API usage and cost](docs/cost.md) before enabling live mode.

## Features

- **Posts and threads:** each subsequent post replies to the previous one.
- **Images:** up to four PNG/JPG/WEBP images per post; all images upload before the first post.
- **Preview and approval:** inspect every post, character count, attachment, and target account before approving.
- **Account guard:** live mode verifies that the credentials belong to the target account.
- **Failure reporting:** failed uploads post nothing; partial threads report what is already live.
- **Lightweight CLI:** standard-library dry run, one runtime dependency for live publishing.

Posts are limited to 280 characters; links count as 23. The local counter treats emoji/CJK as one character while X weighs them as two, so leave room for those characters. Video, GIF, polls, quote posts, editing, deleting, and scheduling are not supported. See [usage and limitations](docs/usage.md).

## Examples

Preview a two-post thread using the same CLI:

```bash
python3 scripts/publish_x.py examples/thread --account yourhandle
```

With an agent:

```text
Turn this release note into a two-post X thread for @yourhandle.
Show me every post and its length before asking to publish.
```

See [examples/](examples/README.md) for the real harness demo and runnable post/thread files. The [post-file reference](docs/usage.md#the-post-file) explains front matter, thread separators, and image comments.

## Configuration

Keep credentials in `~/.config/x-publisher/credentials.env` or environment variables. The CLI reads settings itself; do not paste keys or tokens into agent chat.

| Setting | Purpose |
| --- | --- |
| `X_CONSUMER_KEY`, `X_CONSUMER_KEY_SECRET` | Your app's API key and secret |
| `X_ACCESS_TOKEN_OAUTH1`, `X_ACCESS_TOKEN_SECRET_OAUTH1` | OAuth 1.0a user access token and secret |
| `X_ACCOUNT` | Optional default target handle; `--account` takes priority |

Dry runs do not require API credentials. See [configuration](docs/installation.md#configuration) for setup and file permissions, and [security and privacy](docs/security-and-privacy.md) for storage, account checks, and revocation.

## How it works

The agent reads [SKILL.md](SKILL.md), writes a post file, previews it through the CLI, and asks for approval. Only `--live` creates an X client: it verifies the account, uploads images, and posts the reply chain. Read the [architecture guide](docs/architecture.md) for failure handling and approval boundaries.

## Documentation

- [Installation, X app setup, and configuration](docs/installation.md)
- [Agent setup and network permissions](docs/agent-setup.md)
- [Usage, post-file format, and limitations](docs/usage.md)
- [API usage and cost](docs/cost.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Security and privacy](docs/security-and-privacy.md)
- [Banner generation and social preview](docs/branding.md)

## Contributing and support

Use [Issues](https://github.com/aaitor/skill-publish-to-x/issues) for questions, bugs, and ideas. Read [CONTRIBUTING.md](CONTRIBUTING.md) and the [code of conduct](CODE_OF_CONDUCT.md). Report vulnerabilities privately through [SECURITY.md](SECURITY.md).

Tests and CI use mocked clients and do not call X. See the contribution guide for test and lint commands, and [CHANGELOG.md](CHANGELOG.md) for changes.

## License

[MIT](LICENSE). Embedded banner fonts retain their [SIL OFL 1.1 notices](assets/font-notices/NOTICE.md). This project is not affiliated with or endorsed by X Corp., Anthropic, or OpenAI.

---

Built by [Aitor Argomaniz](https://github.com/aaitor) · [LinkedIn](https://www.linkedin.com/in/aitorargomaniz) · [More open source](https://github.com/aaitor?tab=repositories)
