---
name: publish-to-x
description: Use when the user asks to publish, post or tweet on their own X (Twitter) account, a single post or a thread, with or without images, or to preview a post or thread before publishing it.
---

# Publish to X

Publishes a post or a thread to the user's **own X account** through the X API v2: images first (`POST /2/media/upload`), then each post as a reply to the previous one (`POST /2/tweets`), signed with the user's OAuth 1.0a credentials. A dry run needs only the Python standard library; `--live` needs `tweepy`, which `uv run` installs from the script header.

`<skill-dir>` is the directory that contains this `SKILL.md`.

```bash
X="uv run <skill-dir>/scripts/publish_x.py"   # or python3, with tweepy installed
$X <folder|file>                     # dry run: every post, its length and its images; publishes nothing
$X <folder|file> --account <handle>  # handle to post to (default: X_ACCOUNT, else the file's account:)
$X <folder|file> --live              # publish
```

## The post file

A folder holding `x.md`, or any text file:

```markdown
---
account: theirhandle
---

<!-- post 1: assets/chart.png (the chart). post 2: assets/demo.png (the demo) -->

1/ First post. A link counts as 23 characters: https://example.com

---

2/ Second post, published as a reply to the first.
```

- Front matter is optional. `account` is the handle the text was written for.
- Posts are separated by a line holding only `---`; a single post has none. Each post is at most 280 characters, a link counting as 23.
- HTML comments are never posted or counted. Declare images in one as `post N: <path>`, relative to the file and inside its folder: PNG, JPG or WEBP, 5 MB and 4 per post at most.

## Workflow

1. **Draft:** if the user has a writing-voice or style skill, draft with it. Otherwise keep their wording. Write the file to a temporary folder and copy any image into `assets/` beside it. If an image pasted into the chat comes with a local path, copy that file; if not, ask for the file.
2. **Preview:** run the dry run and show the user every post, its length and its images. Fix what it reports (a post over 280, a missing image) and preview again. On "the file is written for @a, not @b", ask which account to use, and pass `--account` only after the user confirms.
3. **Approval gate:** publish only after the user explicitly approves *this exact text* for *this account* in the conversation. If the text changes after approval, preview and ask again.
4. **Publish:** rerun with `--live`. It checks that the credentials belong to the target account, uploads every image, then posts. Give the user the post URLs it prints.
5. **Failure:** if it fails before the first post, nothing is live. If it fails mid-thread, the error lists the posts already live: never rerun it, since that posts the thread twice. Ask the user whether to delete those posts or finish by hand.

Setup errors:

- `missing credentials: ...`: the one-time setup is not done. Walk the user through `<skill-dir>/README.md`, sections "Create an X app" and "Configuration". Never ask the user to paste a key or token into the chat.
- `no account to post to`: pass `--account <handle>` or have the user set `X_ACCOUNT`.
- `the X credentials are for @a, not @b`: the keys belong to another account. Stop and tell the user.
- `401 Unauthorized`: wrong or revoked keys. `403 Forbidden` on posting: the access token is read-only (README, Troubleshooting).
- Cannot reach X or install `tweepy`: the sandbox blocks the network. Request approval to run with network access.

## Notes

- **Cost:** X bills each request (pay-per-use credits). A post with a link costs much more than one without. Check prices in the README.
- **Threads:** number posts (`1/`, `2/`) if the user wants; the script does not add numbering.
- **Length:** X weighs emoji and CJK characters as 2; the counter counts them as 1, so keep a margin when a post uses them.
- **Not supported:** video, GIF, polls, quote posts, editing, deleting and scheduling. For scheduled runs, publish only text the user approved word for word.
