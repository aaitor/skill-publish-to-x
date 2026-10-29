# API usage and cost

Dry runs with `python3 scripts/publish_x.py` make no X API calls and require no tweepy package or API credits. A live run makes an account lookup, one upload request per image, and one create-post request per post in the thread.

Live publishing uses the user's X developer app and available API credits. Check the [official X pricing page](https://docs.x.com/x-api/getting-started/pricing) and [Developer Console](https://console.x.com) for current pricing, account access, and spending controls before enabling `--live`. Pricing can depend on request type and post content. This guide intentionally does not fix prices to a dated snapshot.

Recording the real Claude Code demo may consume model usage on your Claude account. The recording stops at preview/approval and does not call X or incur X posting charges.
