---
name: publish-to-x
description: Use when asked to publish, post or tweet an X (Twitter) thread from a Nevermined content `x.md` (gtm repo, `content/<date>-<slug>/x.md`) to Aitor's personal X account (@aaitor), or to preview/check such a thread before posting. Dry run by default; posts live only with `--live` after Aitor's explicit go-ahead. Invoke as `/publish-to-x <content-folder|x.md> [--account <handle>] [--live]`.
---

# Publish to X

Post a thread from a content `x.md` to a personal X account through the X API v2:
images first (`POST /2/media/upload`), then each post as a reply to the previous one
(`POST /2/tweets`). The script is `publish_x.py` in this skill's folder.

## Input

`/publish-to-x <path> [--account <handle>] [--live]`

- `<path>`: a content folder (its `x.md` is used) or a specific `x.md` / `x-<name>.md`.
  Given only a slug, find `content/*-<slug>/` in the gtm checkout.
- `--account`: the handle to post to, without `@`. Default `aaitor`. Required when the
  file's `account:` names another handle (gtm files usually say `nevermined_ai`).
- `--live`: post for real. Without it nothing is sent to X.

The `x.md` format (authority: gtm `content/README.md`): front matter with `account` and
`status`; posts separated by a line holding only `---`; each post at most 280 characters,
a link counting as 23. HTML comments are never posted or counted. Images are declared in a
comment, e.g. `<!-- post 1: assets/a.png (...). post 2: assets/b.png (...) -->`, and live
in the `assets/` folder beside the file.

## Steps

1. **Dry run.** `uv run <this-skill-dir>/publish_x.py <path> [--account <handle>]`
   (stdlib only, so `python3 -I <this-skill-dir>/publish_x.py ...` also works). It prints
   each post with its length and images, and exits 1 with every problem found.
2. **Problems.** Report them; never edit the `x.md` (content changes go through the gtm
   PR process). On "x.md is written for @nevermined_ai, not @aaitor", ask whether this
   thread should go to @aaitor; pass `--account aaitor` only after a yes.
3. **Go-ahead.** Show Aitor the dry-run output and ask: "Post this thread live to
   @<account>?" Wait for an explicit yes for this thread. A yes for one thread, or for an
   earlier run, does not carry over.
4. **Live.** Re-run the same command with `--live`. It needs `X_API_KEY`, `X_API_SECRET`,
   `X_ACCESS_TOKEN` and `X_ACCESS_TOKEN_SECRET` in the environment (see `README.md`). It
   checks the credentials belong to `--account`, uploads all images, then posts. Report
   the post URLs it prints.
5. **Failure.** If it fails before any post, nothing is live: fix and re-run after
   asking. If it fails mid-thread, the error lists the posts already live. Do not re-run:
   that would post the thread twice. Ask Aitor whether to delete them or finish by hand.

## Hard rules

- Never pass `--live` without Aitor's explicit go-ahead for that thread.
- Credentials come from the environment only. Never print, log, write or commit them.
- Never post to an account other than the one Aitor named.
