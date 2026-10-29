# Launched inside an isolated project by: python3 examples/record_demo.py
# Real Claude Code + real project skill. Stops before publishing approval.
Source theme.tape
Output demo.gif
Set Width 1280
Set Height 640
Set FontSize 20
Set BorderRadius 0
Set TypingSpeed 25ms
Set Theme { "name": "Aitor Black", "background": "#000000", "foreground": "#F4F7FB", "black": "#000000", "red": "#F28B82", "green": "#89E5CC", "yellow": "#F6D78B", "blue": "#9CAEC4", "magenta": "#C2ACEE", "cyan": "#89E5CC", "white": "#F4F7FB", "brightBlack": "#6A7D94", "brightRed": "#F28B82", "brightGreen": "#89E5CC", "brightYellow": "#F6D78B", "brightBlue": "#9CAEC4", "brightMagenta": "#C2ACEE", "brightCyan": "#89E5CC", "brightWhite": "#FFFFFF", "cursor": "#89E5CC", "selection": "#37516A" }
Hide
Type "export PS1='$ '; set -o pipefail; source demo-shell.sh; clear"
Enter
Sleep 500ms
Show
Type "git clone https://github.com/aaitor/skill-publish-to-x .claude/skills/publish-to-x"
Sleep 500ms
Hide
Enter
Wait+Screen@30s /done./
Show
Sleep 3s
Type "clear"
Enter
Type 'claude -p "/publish-to-x Preview message.txt for @aaitor. Ask before posting."'
Sleep 1s
Hide
Enter
Wait+Screen@180s /Publish this exact message to @aaitor/
Show
Sleep 8s
