# How it works

```text
Agent reads SKILL.md → drafts a post file → runs a dry-run preview
  → asks for approval of the exact text and account
  → publishes with --live only after approval → returns post URLs
```

`scripts/publish_x.py` parses optional front matter, splits threads, maps image attachments, checks length and target-account constraints, then prints the preview. Without `--live`, it returns before creating an X client; there are no X API calls and no tweepy dependency.

In live mode, the script uses tweepy with OAuth 1.0a user credentials. It checks the credential owner's account, uploads every image first, then creates the reply chain. Failed uploads create no posts. A failure midway through a thread reports the posts already live; rerunning would risk duplicates.

The approval gate is defined in [SKILL.md](../SKILL.md). Direct CLI calls with `--live` execute immediately, so use the default dry run for previews. The [README demo](../examples/README.md) records actual skill installation and Claude Code invocation, ending at the approval prompt. Credentials stay local; there is no hosted backend.
