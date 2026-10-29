# Usage and post-file format

### With your agent

Ask in plain language. For example:

- "Post on X: *We just shipped dark mode. Thanks to everyone who asked for it!*"
- "Turn this blog post into a 4-post X thread with ./cover.png on the first post, and show me before posting."
- "Preview this thread for X, don't post it yet: ..."

The agent follows the workflow in [`SKILL.md`](../SKILL.md):

1. Drafts the text, using a writing-voice or style skill if you have one.
2. Runs a dry run and shows you every post, its length and its images.
3. Publishes only after you explicitly approve that text.
4. Returns the post URLs.

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

- **Front matter** is optional: lowercase `key: value` lines between the first two `---` lines. A file that starts with `---` always opens front matter, so don't put `---` before the first post. The preview shows the front matter it read. `account` is the handle the text was written for. If it differs from the account you post to, the script asks you to confirm with `--account`.
- **Posts** are separated by a line holding only `---`. A single post has no separators.
- **HTML comments** are never posted and never count toward the 280 characters.
- **Images** are declared in a comment as `post N: <path>`, relative to the file and inside its folder.

## Limitations

- Posts go to the account that owns the access token.
- **Not supported:** video, GIF, polls, quote posts, editing, deleting and scheduling.
- The length check counts emoji and CJK characters as 1; X counts them as 2.
- A thread that fails midway is not resumed. The error lists what is live, and you finish it by hand.
