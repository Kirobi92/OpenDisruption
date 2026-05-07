"""
kidi/context_db/keys.py
Zone: WORKSPACE

Key-Schema für den ContextDB-Layer.

Format:  {zone}:{agent}:{category}:{uuid}
Beispiel: WORKSPACE:opencode:task:a1b2c3d4-...

Regeln:
- zone:     eines der 5 Zonen-Strings (PUBLIC, WORKSPACE, FAMILY_PRIVATE, SACRED, QUARANTINE)
- agent:    lowercase, nur [a-z0-9_-], max 40 Zeichen
- category: lowercase, nur [a-z0-9_-], max 40 Zeichen (z.B. "task", "memory", "event", "context")
- uuid:     UUID4 als String (wird bei make_key automatisch generiert)
"""

import re
import uuid as _uuid
from typing import NamedTuple

VALID_ZONES = frozenset({"PUBLIC", "WORKSPACE", "FAMILY_PRIVATE", "SACRED", "QUARANTINE"})

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,39}$")
_KEY_RE = re.compile(
    r"^(PUBLIC|WORKSPACE|FAMILY_PRIVATE|SACRED|QUARANTINE)"
    r":([a-z0-9][a-z0-9_-]{0,39})"
    r":([a-z0-9][a-z0-9_-]{0,39})"
    r":([0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})$"
)


class ParsedKey(NamedTuple):
    zone: str
    agent: str
    category: str
    uid: str


def make_key(zone: str, agent: str, category: str, uid: str | None = None) -> str:
    """
    Erzeuge einen validen ContextDB-Schlüssel.

    Args:
        zone:     Zonen-String (muss in VALID_ZONES sein)
        agent:    Agent-Bezeichner (lowercase, [a-z0-9_-])
        category: Kategorie (lowercase, [a-z0-9_-])
        uid:      Optional: UUID4-String; wird bei None automatisch generiert

    Returns:
        Fertig formatierter Key-String

    Raises:
        ValueError: bei ungültigen Eingaben
    """
    if zone not in VALID_ZONES:
        raise ValueError(f"Ungültige Zone '{zone}'. Erlaubt: {sorted(VALID_ZONES)}")
    if not _SLUG_RE.match(agent):
        raise ValueError(
            f"Ungültiger agent-Slug '{agent}'. Nur lowercase [a-z0-9_-], 1-40 Zeichen."
        )
    if not _SLUG_RE.match(category):
        raise ValueError(
            f"Ungültige category '{category}'. Nur lowercase [a-z0-9_-], 1-40 Zeichen."
        )
    if uid is None:
        uid = str(_uuid.uuid4())
    # Validierung des übergebenen UIDs
    try:
        parsed = _uuid.UUID(uid, version=4)
        uid = str(parsed)
    except ValueError:
        raise ValueError(f"Ungültige UUID4 '{uid}'.")
    return f"{zone}:{agent}:{category}:{uid}"


def parse_key(key: str) -> ParsedKey:
    """
    Parse einen ContextDB-Schlüssel in seine Bestandteile.

    Args:
        key: Schlüssel im Format zone:agent:category:uuid

    Returns:
        ParsedKey NamedTuple

    Raises:
        ValueError: wenn der Key nicht dem Schema entspricht
    """
    m = _KEY_RE.match(key)
    if not m:
        raise ValueError(
            f"Ungültiges Key-Format: '{key}'. "
            f"Erwartet: ZONE:agent:category:uuid4"
        )
    return ParsedKey(zone=m.group(1), agent=m.group(2), category=m.group(3), uid=m.group(4))


def is_valid_key(key: str) -> bool:
    """Gibt True zurück wenn key dem Schema entspricht, sonst False."""
    return bool(_KEY_RE.match(key))
