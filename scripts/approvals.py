#!/usr/bin/env python3
"""
approvals.py: remember "Allow Computer Use to use <App>?" answers, like the ChatGPT app does.

Computer Use asks for approval before EVERY action (each click, each read). The ChatGPT app
remembers your answer and replies for you; Claude Code doesn't, so you would be asked again on
every click. These two Claude Code hooks fill that gap (setup.py installs them):

    approvals.py ask      Elicitation hook: before a question is shown.
                          - the app is in your always-allow list    -> allow, no question
                          - you allowed this app in this session    -> allow, no question
                          - otherwise                               -> show the normal question
    approvals.py result   ElicitationResult hook: after you answer. If you allowed the app,
                          it is remembered until this Claude Code session ends.

Only the app question is ever answered automatically. Every other question (for example
"Allow Computer Use to record computer audio?") is always shown to you.

Always-allow list (optional): one app name per line, exactly as the question shows it, in
    ~/.claude/codex-cu/always-allow.txt

Session memory lives in your temp folder and is never sent anywhere. Standard library only.
"""

import json
import re
import sys
import tempfile
import time
from pathlib import Path

APP_QUESTION = re.compile(r'^Allow Computer Use to use "(?P<app>.+)"\?$')
ALWAYS_ALLOW = Path.home() / ".claude" / "codex-cu" / "always-allow.txt"
SESSIONS = Path(tempfile.gettempdir()) / "codex-cu-approvals"
SESSION_MAX_AGE_S = 7 * 24 * 3600


def session_file(session_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id or "unknown")
    return SESSIONS / f"{safe}.json"


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {"allowed": [], "pending": {}}


def save(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state))


def always_allowed() -> set:
    try:
        lines = ALWAYS_ALLOW.read_text().splitlines()
    except OSError:
        return set()
    return {line.strip() for line in lines if line.strip() and not line.strip().startswith("#")}


def tidy() -> None:
    """Forget sessions older than a week."""
    if not SESSIONS.is_dir():
        return
    cutoff = time.time() - SESSION_MAX_AGE_S
    for f in SESSIONS.glob("*.json"):
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink()
        except OSError:
            pass


def allow() -> None:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "Elicitation", "action": "accept", "content": {}}}))


def on_ask(event: dict) -> None:
    match = APP_QUESTION.match(event.get("message", ""))
    if not match:
        return  # not the app question: show it as usual
    app = match.group("app")
    path = session_file(event.get("session_id", ""))
    state = load(path)
    if app in always_allowed() or app in state["allowed"]:
        allow()
        return
    # Show the question; remember which app it was about, to learn from the answer.
    state["pending"][event.get("elicitation_id", "")] = app
    save(path, state)


def on_result(event: dict) -> None:
    path = session_file(event.get("session_id", ""))
    state = load(path)
    app = state["pending"].pop(event.get("elicitation_id", ""), None)
    if app and event.get("action") == "accept" and app not in state["allowed"]:
        state["allowed"].append(app)
    if app:
        save(path, state)


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0  # never block a question because of bad input
    if mode == "ask":
        tidy()
        on_ask(event)
    elif mode == "result":
        on_result(event)
    return 0


if __name__ == "__main__":
    sys.exit(main())
