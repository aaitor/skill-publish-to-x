#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["tweepy==4.17.0"]
# ///
"""Publish a post or a thread, with images, to your own X account via the X API v2.

Dry run by default: prints each post, its X length and its images, and checks the
280-character limit (a link counts as 23), the image mapping and the target account,
without calling X. --live uploads the images (POST /2/media/upload), then posts the
thread as a reply chain (POST /2/tweets), signed with your OAuth 1.0a user credentials
from ~/.config/x-publisher/credentials.env or the environment.

Run: `uv run scripts/publish_x.py <folder|file> [--account <handle>] [--live]`.
"""
from __future__ import annotations

import argparse
import base64
import os
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    import tweepy

CREDENTIALS_FILE = Path.home() / ".config" / "x-publisher" / "credentials.env"
X_MAX = 280
X_URL_LEN = 23  # X counts every link as 23 characters
MAX_IMAGES = 4
MAX_IMAGE_BYTES = 5 * 1024 * 1024
# OAuth 1.0a only; the _OAUTH1 suffix keeps them apart from an OAuth 2.0 X_ACCESS_TOKEN.
ENV_VARS = ("X_CONSUMER_KEY", "X_CONSUMER_KEY_SECRET", "X_ACCESS_TOKEN_OAUTH1", "X_ACCESS_TOKEN_SECRET_OAUTH1")

COMMENT = re.compile(r"<!--(.*?)-->", re.S)
SEPARATOR = re.compile(r"(?m)^---\s*$")
# A link ends before trailing punctuation, which X counts as text: "(https://a.io)." is 23 + 3.
URL = re.compile(r"""https?://\S*[^\s.,;:!?)\]}'"]""")
POST_REF = re.compile(r"\bpost\s+(\d+)", re.I)
IMAGE = re.compile(r"[\w./-]+\.(?:png|jpe?g|gif|webp)\b", re.I)
HANDLE = re.compile(r"[A-Za-z0-9_]{1,15}")
# A YAML-style "key: value" line: lowercase key, colon then a space or the end (never "https://").
# ponytail: a one-line post like "note: shipped" right after a leading --- still reads as front matter.
META_LINE = re.compile(r"\s*[a-z_][a-z0-9_]*\s*:(?:\s|$)")

Images = dict[int, tuple[str, ...]]


def x_length(text: str) -> int:
    # ponytail: plain len, links as 23; X weighs emoji/CJK as 2,
    # switch to twitter-text weighting if a thread ever uses them.
    return len(URL.sub("x" * X_URL_LEN, text))


def _comment_images(comment: str) -> Images:
    """'post 1: assets/a.png (...). post 2: assets/b.png' -> {1: (a,), 2: (b,)}."""
    before, *refs = POST_REF.split(comment)  # before, n1, text1, n2, text2, ...
    if orphan := IMAGE.findall(before):
        raise ValueError(f"image {orphan[0]} in a comment is not tied to a post (write 'post N: {orphan[0]}')")
    found: Images = {}
    for n, text in zip(refs[::2], refs[1::2]):
        if paths := tuple(IMAGE.findall(text)):
            found[int(n)] = found.get(int(n), ()) + paths
    return found


def _front_matter_end(lines: list[str]) -> int | None:
    """Index of the --- closing a leading `key: value` block, or None when the file has no front matter."""
    if lines[0].strip() != "---":
        return None
    end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    head = [line for line in lines[1:end] if line.strip() and not line.lstrip().startswith("#")]
    if not head or not META_LINE.match(head[0]):
        return None  # a leading --- divider, not front matter
    if end is None:
        raise ValueError("front matter is not closed: add a --- line after it, or remove the leading --- if it is a post")
    return end if all(META_LINE.match(line) for line in head) else None


def parse(text: str) -> tuple[dict[str, str], tuple[str, ...], Images]:
    """File text -> (front matter, posts, {post number: image paths}). Front matter is optional."""
    lines = text.split("\n")
    end = _front_matter_end(lines)
    head, body = ([], text) if end is None else (lines[1:end], "\n".join(lines[end + 1:]))
    meta = {
        key.strip(): val.strip().strip("\"'")
        for key, sep, val in (line.partition(":") for line in head)
        if sep
    }
    images: Images = {}
    for comment in COMMENT.findall(body):
        for n, paths in _comment_images(comment).items():
            images[n] = tuple(dict.fromkeys(images.get(n, ()) + paths))  # each image once per post
    # Comments are guidance, never posted, so they never count toward 280.
    posts = tuple(p.strip() for p in SEPARATOR.split(COMMENT.sub("", body)) if p.strip())
    return meta, posts, images


def _image_errors(folder: Path, paths: tuple[str, ...]) -> list[str]:
    root = folder.resolve()
    errors = []
    for rel in paths:
        path = (folder / rel).resolve()
        if not path.is_relative_to(root):
            errors.append(f"{rel} is outside {folder}")
        elif path.suffix.lower() == ".gif":
            # ponytail: animated GIFs need media_category tweet_gif; add when a thread needs one
            errors.append(f"{rel}: GIFs are not supported; use PNG, JPG or WEBP")
        elif not path.is_file():
            errors.append(f"{rel} is not a file")
        elif path.stat().st_size > MAX_IMAGE_BYTES:
            errors.append(f"{rel} is over 5 MB; X allows 5 MB per image")
    return errors


def check(folder: Path, meta: Mapping[str, str], posts: tuple[str, ...], images: Images,
          account: str, explicit: bool) -> list[str]:
    """Every reason not to post this thread to @account; empty means ready."""
    if not HANDLE.fullmatch(account):
        return [f"@{account} is not a valid X handle"]
    errors = []
    written_for = meta.get("account", "").lstrip("@")
    if written_for and written_for.lower() != account.lower() and not explicit:
        errors.append(f"the file is written for @{written_for}, not @{account}; pass --account {account} to confirm")
    if not posts:
        errors.append("no post text")
    for n, post in enumerate(posts, 1):
        if (size := x_length(post)) > X_MAX:
            errors.append(f"post {n} is {size} characters; X allows {X_MAX}")
    for n, paths in sorted(images.items()):
        if not 1 <= n <= len(posts):
            errors.append(f"{', '.join(paths)} is for post {n}; the thread has {len(posts)} posts")
        if len(paths) > MAX_IMAGES:
            errors.append(f"post {n} has {len(paths)} images; X allows {MAX_IMAGES}")
        errors += _image_errors(folder, paths)
    return errors


def _url(account: str, post_id: str) -> str:
    return f"https://x.com/{account}/status/{post_id}"


def _upload(client: tweepy.Client, path: Path) -> str:
    # tweepy 4.17 wraps only the v1.1 media/upload, which X sunset in June 2025, so call
    # the v2 endpoint through tweepy's OAuth 1.0a-signed request.
    body = {"media": base64.b64encode(path.read_bytes()).decode(), "media_category": "tweet_image"}
    return client.request("POST", "/2/media/upload", json=body, user_auth=True).json()["data"]["id"]


def publish(client: tweepy.Client, folder: Path, posts: tuple[str, ...], images: Images,
            account: str) -> list[str]:
    """Upload every image first, then post the thread as a reply chain. Returns the post ids."""
    try:
        media = {n: [_upload(client, folder / rel) for rel in paths] for n, paths in sorted(images.items())}
    except Exception as e:
        raise RuntimeError(f"image upload failed, nothing was posted: {e}") from e
    ids: list[str] = []
    for n, text in enumerate(posts, 1):
        try:
            response = client.create_tweet(
                text=text, media_ids=media.get(n), in_reply_to_tweet_id=ids[-1] if ids else None, user_auth=True
            )
            post_id = response.data["id"]
        except Exception as e:
            live = "\n".join(f"  {_url(account, i)}" for i in ids) or "  none"
            raise RuntimeError(
                f"post {n} of {len(posts)} failed: {e!r}\nalready live:\n{live}\n"
                f"check https://x.com/{account} for post {n} itself before doing anything else"
            ) from e
        ids = [*ids, post_id]
        print(f"posted {n}/{len(posts)}: {_url(account, ids[-1])}")
    return ids


def _env_value(val: str) -> str:
    """A value as a shell would read it: quoted text kept whole, else a trailing ' # comment' dropped."""
    quote = val[:1]
    if quote in ("'", '"') and quote in val[1:]:
        return val[1:val.index(quote, 1)]
    return re.sub(r"\s+#.*", "", val)


def load_settings(path: Path = CREDENTIALS_FILE, environ: Mapping[str, str] = os.environ) -> dict[str, str]:
    """X_* settings from KEY=VALUE lines in the credentials file; non-empty environment variables win."""
    found = {}
    if path.is_file():
        if os.name == "posix" and path.stat().st_mode & 0o077:
            print(f"Warning: {path} is readable by other users, run: chmod 600 {path}", file=sys.stderr)
        for line in path.read_text(encoding="utf-8").splitlines():
            key, sep, val = line.strip().removeprefix("export ").partition("=")
            if sep and key.strip().startswith("X_"):
                found[key.strip()] = _env_value(val.strip())
    return {**found, **{k: v for k, v in environ.items() if k.startswith("X_") and v}}


def make_client(settings: Mapping[str, str]) -> tweepy.Client:
    """A tweepy client signed with the OAuth 1.0a user credentials in the settings."""
    if missing := [name for name in ENV_VARS if not settings.get(name)]:
        raise ValueError(f"missing credentials: {', '.join(missing)} (see README.md, Configuration)")
    import tweepy  # only --live needs it; a dry run is stdlib-only

    key, secret, token, token_secret = (settings[name] for name in ENV_VARS)
    return tweepy.Client(consumer_key=key, consumer_secret=secret, access_token=token, access_token_secret=token_secret)


def _show(file: Path, meta: Mapping[str, str], posts: tuple[str, ...], images: Images, account: str) -> None:
    print(f"{file} -> @{account}")
    for n, post in enumerate(posts, 1):
        attach = ", ".join(images.get(n, ())) or "none"
        print(f"\npost {n}/{len(posts)} · {x_length(post)}/{X_MAX} chars · images: {attach}\n{post}")


def _fail(message: str) -> int:
    sys.stdout.flush()  # keep the error after the plan when both streams are piped
    print(f"\nERROR: {message}", file=sys.stderr)
    return 1


def main(argv: list[str], settings: Mapping[str, str] | None = None,
         client_factory: Callable[[], tweepy.Client] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="publish_x", description="Publish a post or thread to your X account.")
    ap.add_argument("path", type=Path, help="a folder holding x.md, or any post file")
    ap.add_argument("--account", help="X handle to post to (default: X_ACCOUNT, else the file's account:); "
                                      "required when the file is written for another account")
    ap.add_argument("--live", action="store_true", help="post for real; without it nothing is sent to X")
    args = ap.parse_args(argv)
    settings = load_settings() if settings is None else settings
    file = args.path / "x.md" if args.path.is_dir() else args.path

    try:
        meta, posts, images = parse(file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return _fail(f"{file}: {e}")
    flag = (args.account or "").lstrip("@")  # an empty --account confirms nothing
    account = (flag or settings.get("X_ACCOUNT") or meta.get("account") or "").lstrip("@")
    if not account:
        return _fail("no account to post to: pass --account <handle> or set X_ACCOUNT (see README.md)")
    _show(file, meta, posts, images, account)
    if errors := check(file.parent, meta, posts, images, account, bool(flag)):
        return _fail("\n".join(errors))
    if not args.live:
        print(f"\nDry run: nothing posted. Re-run with --live to post this thread to @{account}.")
        return 0

    try:
        client = client_factory() if client_factory else make_client(settings)
        me = client.get_me(user_auth=True).data.username
    except Exception as e:
        return _fail(f"{e}\nnothing was posted")
    if me.lower() != account.lower():
        return _fail(f"the X credentials are for @{me}, not @{account}; nothing was posted")
    try:
        publish(client, file.parent, posts, images, account)
    except RuntimeError as e:  # publish says what is already live
        return _fail(str(e))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
