# Security and privacy

- **Local credentials:** keys and tokens stay on your machine, in the credentials file or your environment. The script never prints or writes them, and error messages name a missing setting, never its value.
- **Approval:** the skill instructs the agent never to publish without your explicit approval of the exact text.
- **Account check:** before posting, the script confirms that the credentials belong to the target account.
- **Network:** requests go only to the X API, through tweepy.
- **Revoking access:** OAuth 1.0a access tokens do not expire. Regenerate or revoke them in the app's *Keys and tokens*, or remove the app under *Settings → Security and account access → Apps and sessions → Connected apps* on X.

Use it in line with X's [Developer Agreement and Policy](https://developer.x.com/en/developer-terms) and [automation rules](https://help.x.com/en/rules-and-policies/x-automation). Don't use it for spam or mass posting.

For responsible disclosure, use [SECURITY.md](../SECURITY.md).
