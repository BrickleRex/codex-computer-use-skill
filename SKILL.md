---
name: codex-computer-use
description: >-
  Operate apps on the user's Mac in the background (click buttons, type, read what a window
  shows) through the ChatGPT app's Computer Use, connected to Claude Code as the "codex-cu" MCP
  server. Use when the user asks Claude to use a desktop app or read something from an app's
  window that has no API, CLI or better tool (for example "use Calculator to work out…", "in
  Notes, find…", "click … in System Settings"), or asks to set up Codex / ChatGPT Computer Use
  for Claude Code. Do not use it when a command, API, file or a dedicated tool can do the job.
---

# Codex Computer Use for Claude Code

The ChatGPT desktop app includes Codex's Computer Use: a JavaScript runtime that can read and
operate Mac apps through the accessibility system, in the background. This skill connects it to
Claude Code as the MCP server `codex-cu` and explains how to drive it.

## 1. Setup check

- If the tool `mcp__codex-cu__js` is available, go to step 2.
- If not, run the setup script. Replace `<SKILL_DIR>` with this skill's base directory (Claude
  Code shows it when the skill loads; for a personal install it is
  `~/.claude/skills/codex-computer-use`):

  ```bash
  python3 "<SKILL_DIR>/scripts/setup.py"
  ```

  It finds the newest Computer Use in the ChatGPT app, registers it as `codex-cu`, checks that it
  connects, and adds two hooks that remember the user's app approvals for the session. Then tell
  the user to close and reopen Claude Code: MCP tools load at startup.
  If it stops, show the user its message; it says what is missing.

## 2. How to use `mcp__codex-cu__js`

1. **First call: one API call only.** In a new session (or after `js_reset`), the first `js` call
   must be exactly one API call, for example:

   ```javascript
   let app = await cua.getApp("Calculator");
   ```

   The result contains the full API documentation and the app's UI as a numbered accessibility
   tree. Read both before acting.
2. **Permission.** The first time an app is used in a session, the user is asked
   *Allow Computer Use to use "App"?* Once they allow it, the hooks answer the repeat questions
   for that app until the session ends. If the result says it was not approved, ask the user to
   allow it and try again. Do not work around it.
3. **Act by element number, then look again.** Use the numbers from the latest tree, batch the
   actions, and end the same call with a fresh state:

   ```javascript
   await app.click(8);          // All Clear
   await app.click(19);         // 1
   await app.getAXState();
   ```

   Other actions: `setValue(i, text)`, `typeText(text)`, `pressKey("Return")`,
   `scroll(i, "down", 1)`, `selectText(i, text)`. Variables such as `app` stay alive between calls.
4. **Numbers change.** Element numbers can shift between calls. Always take them from the newest
   tree; never reuse old ones.
5. **Check before you answer.** Confirm the result is visible in the returned state.

## 3. Rules

- Use only the `cua` API for UI actions. No AppleScript, `osascript` or System Events (the
  runtime's own rule).
- Apps work in the background; the user's front window stays in front.
- Ask the user right before risky steps: deleting things, sending messages or forms, payments,
  changing system settings, uploading files, or typing passwords or personal data. The first tool
  result includes the runtime's full confirmation policy; follow it.
- Prefer a command, API or file when one exists. Computer Use is for UI that has no other way in.

## 4. If something goes wrong

| Problem | Fix |
| --- | --- |
| No `mcp__codex-cu__js` tool | Run the setup script, then restart Claude Code. |
| "Computer Use was not approved to use …" | The user must allow the app when asked. In the VS Code extension the question is not shown yet: use Claude Code in the terminal, or add the app to `~/.claude/codex-cu/always-allow.txt` (one app name per line). |
| The user is asked on every click | The approval hooks are missing: run the setup script again, then restart Claude Code. |
| Setup: "Computer Use … was not found" | Install the ChatGPT desktop app and use Computer Use there once. |
| It worked before, now it fails after a ChatGPT update | Run the setup script again, then restart Claude Code. |
| The app cannot be read or clicked | Open the ChatGPT app and allow the macOS permissions Computer Use asks for (Accessibility, Screen Recording). |
