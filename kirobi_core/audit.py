"""Append-only audit logger for autonomous actions.

Writes JSON-Lines events to ``kirobi-core/core-events.log``. The runtime
log is intentionally ignored by Git so append-only audit evidence can
accumulate locally without keeping the worktree permanently dirty. The
logger never records secrets or full SACRED file contents — callers
should pass only short summaries via the ``data`` argument.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_LOG_PATH = Path("kirobi-core/core-events.log")

# Keys that, if present in ``data``, will be redacted before writing.
_SECRET_KEY_HINTS = (
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "privatekey",
    "credential",
    "auth",
    "passphrase",
)


def _redact(value: Any) -> Any:
    """Recursively redact obviously secret values."""
    if isinstance(value, dict):
        return {
            k: ("***REDACTED***" if any(h in k.lower() for h in _SECRET_KEY_HINTS) else _redact(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_redact(v) for v in value]
    if isinstance(value, tuple):
        return [_redact(v) for v in value]
    return value


class AuditLogger:
    """Tiny append-only JSON-Lines logger.

    Each ``log()`` call appends one line containing a UTC timestamp,
    actor, action, optional zone and a redacted ``data`` payload.
    """

    def __init__(self, log_path: Path | str = DEFAULT_LOG_PATH) -> None:
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        action: str,
        *,
        actor: str = "kirobi-core",
        zone: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Append an event and return the event dict that was written."""
        event: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "actor": actor,
            "action": action,
        }
        if zone is not None:
            event["zone"] = zone
        if data:
            event["data"] = _redact(data)
        line = json.dumps(event, ensure_ascii=False, sort_keys=True)
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(line + os.linesep)
        return event
