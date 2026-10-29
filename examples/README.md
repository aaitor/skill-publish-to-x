# Install the skill and use it with Claude Code

The README GIF shows a real Claude Code session on a black terminal background:

1. Clone the skill into the project's `.claude/skills/publish-to-x` directory.
2. Invoke `/publish-to-x` through Claude Code.
3. Review the draft and stop at the publishing approval prompt.

Claude reads the installed skill and uses the actual CLI to preview the message for @aaitor, including its character count and attachments. Its final response shows the draft, target account, and approval question. Nothing is published. Waiting time for cloning and model output is omitted from the animation; the commands and Claude's answer are recorded live.

## Try it

Install Claude Code and Python 3.10+. Previewing does not require X credentials; [app setup](../docs/installation.md) is needed only for live publishing. From your project directory:

```bash
git clone https://github.com/aaitor/skill-publish-to-x .claude/skills/publish-to-x
```

Create `message.txt` with your draft, then use Claude Code's non-interactive harness:

```bash
claude -p "/publish-to-x Preview message.txt for @aaitor. Ask before posting."
```

You can also start `claude` interactively and submit the same `/publish-to-x` request. Allow the skill's dry-run command when your harness asks. Review the exact post text and target account before authorizing publishing. In the recorded demo, the user chose to stop at this approval step.

## Reproduce the recording

Requires Python 3.10+, Git, an authenticated Claude Code installation, [VHS with ttyd and ffmpeg](https://github.com/charmbracelet/vhs#installation), and DejaVu Sans Mono or a substitute font. Recording invokes your real Claude Code account, needs model network access, and may consume model usage. The actual X CLI dry-run requires no API credentials and never calls X.

From this repository:

```bash
python3 examples/record_demo.py
```

The helper creates an isolated temporary project, installs the skill visibly through the tape, and saves the finished GIF to `assets/terminal-demo.gif`. Use `--out /tmp/demo.gif` to choose another location. The existing GIF is replaced only after recording completes.

[demo.tape](demo.tape) controls the visible commands, timing, and black background. [claude-demo.md](claude-demo.md) contains the recording instructions. [demo-post.txt](demo-post.txt) supplies the draft. The helper limits the harness to file/skill tools plus the Python dry-run command, loads only the isolated project settings, disables optional hooks, and excludes configured MCP servers. It leaves global harness settings unchanged. It does not bypass permissions. The visible `claude` command uses this session-specific configuration through a shell function; Claude Code and the skill execute normally.

Watch the finished GIF before committing it. It may contain your name, draft text, and Claude's response; do not record private content. Regenerating the recording is a manual action, never a CI step.

## Credential-free CLI example

For a separate offline exercise or CI:

```bash
python3 scripts/publish_x.py examples/post.txt --account yourhandle
python3 scripts/publish_x.py examples/thread --account yourhandle
```

These run the unmodified CLI without `--live`, using the [single post](post.txt) and [thread](thread/x.md). They need only Python 3.10+, make no X API calls, and do not mock an identity or client. The main GIF adds actual skill installation and Claude Code invocation.
