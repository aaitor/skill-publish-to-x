# skill-publish-to-x

A Claude Code skill that publishes an X (Twitter) thread from a Nevermined content `x.md`
to a personal X account (`@aaitor` by default) through the X API v2.

It runs as a dry run by default: it prints each post, its length (280 maximum, a link
counts as 23) and the images it would attach, and checks everything without calling X.
It posts only with `--live`.

```
SKILL.md          the skill contract Claude follows
publish_x.py      parse, check, upload images, post the thread
tests/            unit tests (X client mocked), H Company thread as a fixture
```

## Install

Clone this repo into your skills folder; the folder name is the skill name:

```bash
git clone https://github.com/aaitor/skill-publish-to-x ~/.claude/skills/publish-to-x
```

Or clone it elsewhere and symlink it: `ln -s "$PWD" ~/.claude/skills/publish-to-x`.
Then `/publish-to-x <content-folder>` is available in Claude Code.

It needs [`uv`](https://docs.astral.sh/uv/): `uv run publish_x.py` installs its one
dependency (`tweepy==4.17.0`, declared in the script header) in a cached environment.
Without `uv`, use Python 3.10+ and `pip install tweepy==4.17.0`. A dry run needs only the
standard library.

```bash
uv run publish_x.py ~/path/to/gtm/content/2026-10-28-hcompany-catalog-recall-agent --account aaitor
```

## Credentials

Live posting reads four OAuth 1.0a user-context values from the environment. Nothing
else is read, and they are never printed or written.

| Variable | X developer portal name |
|---|---|
| `X_CONSUMER_KEY` | API Key (consumer key) |
| `X_CONSUMER_KEY_SECRET` | API Key Secret (consumer secret) |
| `X_ACCESS_TOKEN_OAUTH1` | Access Token, for @aaitor |
| `X_ACCESS_TOKEN_SECRET_OAUTH1` | Access Token Secret, for @aaitor |

Other X values, such as the OAuth 2.0 `X_ACCESS_TOKEN`, `X_REFRESH_TOKEN`, `X_CLIENT_ID`
or `X_BEARER_TOKEN`, are ignored, so they can share the same file.

Keep them out of this repo in an env file (`chmod 600`, plain `NAME=value` lines), loaded
with `set -a; . <file>; set +a` so the values reach the script. Before posting, the script
checks that the credentials belong to the `--account` handle, and stops if they do not.

## X API prerequisites

1. **Developer account and app.** At [developer.x.com](https://developer.x.com), create a
   project and an app, signed in as @aaitor.
2. **Write permission.** In the app's *User authentication settings*, set *App
   permissions* to **Read and write**. Do this before generating the access token; a
   token generated earlier stays read-only and must be regenerated.
3. **Keys.** In *Keys and tokens*, generate the API Key and Secret, and the Access Token
   and Secret. When the app belongs to @aaitor, the portal issues the access token for
   @aaitor directly, with no consent screen.
   If the app belongs to another account, authorize @aaitor once with the PIN flow:
   ```python
   import tweepy
   h = tweepy.OAuth1UserHandler("<API key>", "<API secret>", callback="oob")
   print(h.get_authorization_url())          # open it signed in as @aaitor, click Authorize
   token, secret = h.get_access_token(input("PIN: "))
   ```
4. **Access tier and cost.** Since February 2026 new developer accounts use pay-per-use
   pricing; the free tier is closed to new sign-ups. Creating a post is billed per
   request, reportedly more for a post that contains a link, and each run also makes one
   account lookup and one media upload per image. The H Company thread is 4 posts (2 with
   links) and 4 images. Check current prices in the developer console and set a spending
   cap there.

Endpoints used: `GET /2/users/me`, `POST /2/media/upload` (one-shot image upload: PNG,
JPG or WEBP, 5 MB maximum, up to 4 per post) and `POST /2/tweets`. All accept OAuth 1.0a
user context.

## Tests

```bash
uv run --no-project --with pytest --with tweepy==4.17.0 pytest -q
```

The X client is mocked; one test runs the real tweepy client and OAuth 1.0a signing with
only the HTTP transport faked. No test calls X.
