# CLAUDE.md

A Claude Code skill: `SKILL.md` (contract) + `publish_x.py` (script) + `tests/`.

- Test: `uv run --no-project --with pytest --with tweepy==4.17.0 pytest -q`. Lint: `ruff check --line-length 120 .`
- Tests never call X. Mock the client (`create_autospec(tweepy.Client)`) or fake the HTTP transport.
- No credentials anywhere in the repo; they come from the `X_*` environment variables only.
- Never run `--live` without the user's explicit go-ahead for that thread.
- The `x.md` format and counting rules follow nevermined-io/gtm `content/README.md` and
  `content/check.py`; keep the post split in step with them. `x_length` is deliberately
  stricter than `check.py`: a link stops before trailing punctuation, as on X.
