# Codex Computer Use for Claude Code

Let Claude Code use the apps on your Mac, in the background.

> "Use Calculator to work out 12 × 12."
> "Open Notes and find my packing list."

Claude clicks and reads the app for you while you keep working in another window.
It uses the Computer Use that comes with the ChatGPT desktop app.

## What you need

- **A Mac**
- **Claude Code** ([claude.com/claude-code](https://claude.com/claude-code)), used in the terminal
- **The ChatGPT desktop app**, with Codex's Computer Use used at least once
  (this installs it and asks macOS for the permissions it needs)

## Install (about 2 minutes)

### The easy way: let Claude Code do it

1. Open Claude Code and paste this:

   ```
   Install this skill for all my projects, then run its setup:
   npx skills add BrickleRex/codex-computer-use-skill -g -a claude-code -y
   ```

2. Close Claude Code and open it again.

### Or do it yourself in a terminal

```bash
npx skills add BrickleRex/codex-computer-use-skill -g -a claude-code -y
python3 ~/.claude/skills/codex-computer-use/scripts/setup.py
```

Then close Claude Code and open it again.

`npx` comes with Node.js. If you don't have it, install Node.js from [nodejs.org](https://nodejs.org) first.

## Use it

Ask Claude Code to do something in an app:

- "Use Calculator to work out 12 × 12."
- "In Notes, find the note called Groceries and tell me what's on it."
- "In Reminders, tell me what's on my Today list."

The first time Claude uses an app, you are asked: **Allow Computer Use to use "Calculator"?**
Choose to allow it. You won't be asked again for that app until you close Claude Code.
Claude still asks you before anything risky, like deleting or sending.

To never be asked about an app, add its name (one per line) to
`~/.claude/codex-cu/always-allow.txt`.

## If something goes wrong

| What you see | What to do |
| --- | --- |
| Claude says it has no Computer Use tool | Run the setup again (the second command above), then close and reopen Claude Code. |
| "Computer Use was not approved" | Allow the app when asked. In the VS Code extension this question doesn't appear yet: use Claude Code in the terminal, or add the app to the always-allow list above. |
| You are asked on every click | Run the setup again, then close and reopen Claude Code. |
| Setup says Computer Use was not found | Install the ChatGPT desktop app and use Computer Use in it once. |
| It stopped working after a ChatGPT update | Run the setup again, then close and reopen Claude Code. |
| The Computer Use pointer stays on screen | Run the setup again (it adds the "turn ended" hook), then close and reopen Claude Code. |

## Good to know

- This is an unofficial bridge. It is not made by OpenAI or Anthropic, and a ChatGPT update can
  change things. Running the setup again usually fixes it.
- When Claude finishes a reply, the skill tells Computer Use the turn is over (like the ChatGPT
  app does), so it can tidy up, for example its on-screen pointer.
- Nothing is sent anywhere by this skill. The setup only adds a server and a few small hooks to
  your own Claude Code settings (it saves a backup first), pointing at the ChatGPT app already
  on your Mac.
- To remove everything: `python3 ~/.claude/skills/codex-computer-use/scripts/setup.py --uninstall`

## What's inside

- `SKILL.md`: the instructions Claude follows
- `scripts/setup.py`: finds Computer Use in the ChatGPT app and connects it to Claude Code
- `scripts/approvals.py`: remembers which apps you allowed, so you aren't asked on every click

## License

MIT
