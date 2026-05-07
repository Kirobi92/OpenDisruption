"""
kidi/context_db/zone_guard.py
Zone: WORKSPACE

Zonen-Hierarchie und Zugriffskontrolle für den ContextDB-Layer.

Hierarchie (aufsteigend, höhere Zahl = sensibler):
    PUBLIC(0) < WORKSPACE(1) < FAMILY_PRIVATE(2) < SACRED(3)
    QUARANTINE(Q) — isoliert, darf nie promoted werden

Regeln:
    - Ein Agent darf nur Einträge lesen, die <= seiner Maximalzone sind.
    - SACRED erfordert zusätzlich eine explizite Session-Genehmigung.
    - QUARANTINE darf nie gelesen/geschrieben werden ohne separaten Approval-Flow.
    - Egress-Guard: Schreiben von FAMILY_PRIVATE+ zu externen Services blockiert,
      wenn KIROBI_EGRESS_ALLOWED != "true".
"""

import os

from .errors import EgressViolation, SacredApprovalMissing, ZoneViolation

# Zonen-Rang: höher = sensibler
_ZONE_RANK: dict[str, int] = {
    "PUBLIC": 0,
    "WORKSPACE": 1,
    "FAMILY_PRIVATE": 2,
    "SACRED": 3,
    "QUARANTINE": 99,  # Immer isoliert
}

# Zonen, für die der Egress-Guard gilt
_EGRESS_SENSITIVE = frozenset({"FAMILY_PRIVATE", "SACRED"})


def zone_rank(zone: str) -> int:
    """Gibt den numerischen Rang einer Zone zurück."""
    return _ZONE_RANK.get(zone, -1)


def check_read(requester_max_zone: str, entry_zone: str) -> None:
    """
    Prüft ob ein Agent mit gegebener Maximalzone einen Eintrag in entry_zone lesen darf.

    Raises:
        ZoneViolation: wenn Zugriff verweigert
        SacredApprovalMissing: wenn entry_zone == SACRED (immer, da Runtime-Approval nötig)
    """
    if entry_zone == "QUARANTINE":
        raise ZoneViolation(requester_max_zone, entry_zone, operation="read")

    if entry_zone == "SACRED":
        raise SacredApprovalMissing()

    req_rank = zone_rank(requester_max_zone)
    entry_rank = zone_rank(entry_zone)

    if req_rank < 0:
        raise ZoneViolation(requester_max_zone, entry_zone, operation="read")

    if entry_rank > req_rank:
        raise ZoneViolation(requester_max_zone, entry_zone, operation="read")


def check_write(zone: str, check_egress: bool = True) -> None:
    """
    Prüft ob in eine Zone geschrieben werden darf.

    Args:
        zone:          Ziel-Zone des Eintrags
        check_egress:  Wenn True, wird KIROBI_EGRESS_ALLOWED ausgewertet

    Raises:
        EgressViolation:        wenn Egress aktiv und Zone ist sensitiv
        SacredApprovalMissing:  bei SACRED-Writes (immer blockiert ohne Approval)
    """
    if zone == "SACRED":
        raise SacredApprovalMissing()

    if zone == "QUARANTINE":
        raise ZoneViolation("PUBLIC", zone, operation="write")

    if check_egress and zone in _EGRESS_SENSITIVE:
        egress_allowed = os.environ.get("KIROBI_EGRESS_ALLOWED", "false").lower() == "true"
        if not egress_allowed:
            raise EgressViolation(zone)


def is_readable(requester_max_zone: str, entry_zone: str) -> bool:
    """Gibt True zurück wenn check_read keine Exception werfen würde."""
    try:
        check_read(requester_max_zone, entry_zone)
        return True
    except (ZoneViolation, SacredApprovalMissing):
        return False
