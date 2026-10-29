# Contributing

Use [Issues](https://github.com/aaitor/skill-publish-to-x/issues) for reproducible bugs and proposals. Discuss large changes first. Preserve Python 3.10+ support, the dry-run default, and the skill's exact-text/account approval gate.

1. Fork, clone, and create a focused branch.
2. Keep implementation, documentation, and examples consistent.
3. Install development dependencies in a virtual environment: `python3 -m pip install -r requirements-dev.txt`.
4. Run `python3 -m pytest -q scripts`, `ruff check --line-length 120 .`, and `python3 scripts/check.py`.
5. Open a pull request describing the problem, resulting behavior, and verification.

Tests mock the X client and signing transport; no test calls X. Do not use a real account or `--live` in CI. Do not include credentials, tokens, private drafts, or raw API logs in issues or recordings. Contributions use the repository's MIT license. Follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md); report vulnerabilities through [SECURITY.md](SECURITY.md).
