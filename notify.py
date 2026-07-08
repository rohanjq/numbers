"""Pushover notifications — 'you are not in control, this is life-changing'."""
from __future__ import annotations

from config import Settings


def send(s: Settings, message: str, title: str = "Numbers",
         priority: int = 0) -> tuple[bool, str]:
    """Send a Pushover notification. No-op (returns False) if not configured."""
    if not s.pushover_token or not s.pushover_user:
        return False, "Pushover not configured (set PUSHOVER_TOKEN / PUSHOVER_USER)."
    try:
        import requests
        resp = requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": s.pushover_token,
                "user": s.pushover_user,
                "title": title,
                "message": message,
                "priority": priority,
            },
            timeout=10,
        )
        ok = resp.status_code == 200
        return ok, ("sent" if ok else f"pushover error {resp.status_code}: {resp.text}")
    except Exception as exc:  # noqa: BLE001
        return False, f"pushover exception: {exc}"
