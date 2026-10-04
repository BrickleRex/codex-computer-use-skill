#!/usr/bin/env python3
"""
setup.py: connect the ChatGPT app's Computer Use to Claude Code.

The ChatGPT desktop app ships Codex's Computer Use as an MCP server ("cua_repl"). Its settings
live in ~/.codex/plugins/cache/openai-bundled/unified-computer-use/<version>/.mcp.json. This
script:
  1. reads the newest version of that file and registers the same command, arguments and
     environment in Claude Code as a user-wide MCP server (default name: "codex-cu");
  2. adds two hooks to ~/.claude/settings.json (a backup is saved first) that remember the
     "Allow Computer Use to use <App>?" answer for the rest of the session (scripts/approvals.py).
     Without them, Claude Code would ask on every single click.

Run it again after the ChatGPT app updates: it replaces the old registration.

Usage:
    python3 setup.py               # register (or update) "codex-cu" and its hooks
    python3 setup.py --dry-run     # show what would change, change nothing
    python3 setup.py --uninstall   # remove the server and the hooks
    python3 setup.py --name NAME   # use another server name

Standard library only. Nothing is sent anywhere: the script runs `claude mcp` and edits your
own Claude Code settings file.
"""

import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PLUGIN_DIR = Path.home() / ".codex" / "plugins" / "cache" / "openai-bundled" / "unified-computer-use"
SERVER_KEY = "cua_repl"
SETTINGS = Path.home() / ".claude" / "settings.json"
APPROVALS = Path(__file__).resolve().parent / "approvals.py"
HOOK_EVENTS = {"Elicitation": "ask", "ElicitationResult": "result"}


def fail(message: str) -> None:
    print(f"\nSetup stopped: {message}", file=sys.stderr)
    sys.exit(1)


def version_key(name: str) -> tuple:
    """Sort '26.10.5' above '26.9.12': compare the numeric parts as numbers."""
    return tuple(int(part) if part.isdigit() else -1 for part in name.split("."))


def newest_server_config() -> tuple:
    """Return (version, server settings) from the newest installed Computer Use plugin."""
    if not PLUGIN_DIR.is_dir():
        fail(
            "Computer Use from the ChatGPT app was not found.\n"
            "Install the ChatGPT desktop app, use Codex's Computer Use in it once, then run this again."
        )
    versions = sorted(
        (folder for folder in PLUGIN_DIR.iterdir() if (folder / ".mcp.json").is_file()),
        key=lambda folder: version_key(folder.name),
    )
    if not versions:
        fail(f"No .mcp.json found in {PLUGIN_DIR}. Use Computer Use in the ChatGPT app once, then run this again.")

    newest = versions[-1]
    config = json.loads((newest / ".mcp.json").read_text())
    server = config.get("mcpServers", {}).get(SERVER_KEY)
    if not server or "command" not in server:
        fail(f'No "{SERVER_KEY}" server in {newest / ".mcp.json"}. The ChatGPT app may have changed its layout.')
    if not Path(server["command"]).exists():
        fail(f"The Computer Use program is missing: {server['command']}\nUpdate or reinstall the ChatGPT app.")
    return newest.name, server


def is_our_hook(entry: dict, name: str) -> bool:
    return entry.get("matcher") == name and any("approvals.py" in h.get("command", "") for h in entry.get("hooks", []))


def update_hooks(name: str, install: bool, dry_run: bool) -> None:
    """Add (or remove) the approval-memory hooks in ~/.claude/settings.json, keeping everything else."""
    settings = json.loads(SETTINGS.read_text()) if SETTINGS.exists() else {}
    hooks = settings.setdefault("hooks", {})
    for event, mode in HOOK_EVENTS.items():
        kept = [entry for entry in hooks.get(event, []) if not is_our_hook(entry, name)]
        if install:
            kept.append({"matcher": name, "hooks": [{"type": "command", "command": f'python3 "{APPROVALS}" {mode}'}]})
        if kept:
            hooks[event] = kept
        else:
            hooks.pop(event, None)
    if not hooks:
        settings.pop("hooks")
    if dry_run:
        verb = "add" if install else "remove"
        print(f"Would {verb} the approval-memory hooks ({', '.join(HOOK_EVENTS)}) in {SETTINGS}")
        return
    if SETTINGS.exists():
        backup = SETTINGS.with_name("settings.json.backup-codex-cu")
        backup.write_text(SETTINGS.read_text())
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(settings, indent=2) + "\n")
    print(("Added" if install else "Removed") + f" the approval-memory hooks in {SETTINGS} (backup: settings.json.backup-codex-cu).")


def main() -> int:
    parser = argparse.ArgumentParser(description="Connect the ChatGPT app's Computer Use to Claude Code.")
    parser.add_argument("--name", default="codex-cu", help='MCP server name in Claude Code (default: "codex-cu").')
    parser.add_argument("--dry-run", action="store_true", help="Show what would change; change nothing.")
    parser.add_argument("--uninstall", action="store_true", help="Remove the server and the hooks.")
    args = parser.parse_args()

    if platform.system() != "Darwin":
        fail("Computer Use from the ChatGPT app works on macOS only.")
    claude = shutil.which("claude")
    if not claude:
        fail("The `claude` command was not found. Install Claude Code first.")

    if args.uninstall:
        if args.dry_run:
            print(f'Would remove the user MCP server "{args.name}".')
        else:
            subprocess.run([claude, "mcp", "remove", args.name, "--scope", "user"], capture_output=True, text=True)
            print(f'Removed the MCP server "{args.name}".')
        update_hooks(args.name, install=False, dry_run=args.dry_run)
        if not args.dry_run:
            print("\nDone. Close Claude Code and open it again.")
        return 0

    version, server = newest_server_config()
    spec = {
        "type": "stdio",
        "command": server["command"],
        "args": server.get("args", []),
        "env": server.get("env", {}),
    }
    print(f"Found Computer Use version {version}.")

    if args.dry_run:
        print(f'Would register the user MCP server "{args.name}" with:')
        print(f"  command: {spec['command']}")
        print(f"  args:    {' '.join(spec['args'])}")
        print(f"  env:     {len(spec['env'])} variables ({', '.join(sorted(spec['env']))})")
        update_hooks(args.name, install=True, dry_run=True)
        return 0

    # Replace any earlier registration (for example, from an older ChatGPT version).
    subprocess.run([claude, "mcp", "remove", args.name, "--scope", "user"], capture_output=True, text=True)
    added = subprocess.run(
        [claude, "mcp", "add-json", args.name, json.dumps(spec), "--scope", "user"],
        capture_output=True, text=True,
    )
    if added.returncode != 0:
        fail(f"`claude mcp add-json` failed:\n{added.stderr.strip() or added.stdout.strip()}")
    print(f'Registered "{args.name}" for all your Claude Code projects.')

    # Start the server once to check that it answers.
    check = subprocess.run([claude, "mcp", "get", args.name], capture_output=True, text=True, timeout=180)
    status = next((line.strip() for line in check.stdout.splitlines() if line.strip().startswith("Status:")), "")
    print(status or "Status: unknown (run `claude mcp get codex-cu` to check)")
    if "Connected" not in status:
        fail("The server did not connect. Open the ChatGPT app once, then run this again.")

    update_hooks(args.name, install=True, dry_run=False)

    print("\nDone. Close Claude Code and open it again, so it loads the new tools.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
