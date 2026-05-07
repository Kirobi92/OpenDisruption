"""
kidi/context_db/errors.py
Zone: WORKSPACE

Fehlerhierarchie für den ContextDB-Layer.
Alle Fehler erben von ContextDBError damit Upstream-Code einen einzigen except-Block nutzen kann.
"""


class ContextDBError(Exception):
    """Basis-Fehler für alle ContextDB-Operationen."""


class ZoneViolation(ContextDBError):
    """
    Raised wenn ein Agent versucht, Daten einer höheren Zone zu lesen oder zu schreiben
    als sein deklariertes Zonen-Maximum erlaubt.

    Beispiel: WORKSPACE-Agent versucht SACRED-Eintrag zu lesen.
    """

    def __init__(self, requester_zone: str, entry_zone: str, operation: str = "read"):
        self.requester_zone = requester_zone
        self.entry_zone = entry_zone
        self.operation = operation
        super().__init__(
            f"ZoneViolation: {operation} verweigert — "
            f"Anfragender darf maximal '{requester_zone}' verarbeiten, "
            f"Eintrag ist '{entry_zone}'"
        )


class EgressViolation(ContextDBError):
    """
    Raised wenn ein Schreibversuch Daten mit Zone >= FAMILY_PRIVATE enthält
    und KIROBI_EGRESS_ALLOWED=false gesetzt ist (Default).
    Schützt vor versehentlichem Export sensibler Daten zu externen Services.
    """

    def __init__(self, zone: str):
        self.zone = zone
        super().__init__(
            f"EgressViolation: Schreiben von '{zone}'-Daten blockiert "
            f"(KIROBI_EGRESS_ALLOWED=false). "
            f"Explizit auf 'true' setzen um externe Weitergabe zu erlauben."
        )


class KeyValueMismatch(ContextDBError):
    """
    Raised wenn der Zone-Teil eines Keys nicht mit dem zone-Feld im Value übereinstimmt.
    Verhindert inkonsistente Einträge im Store.
    """

    def __init__(self, key_zone: str, value_zone: str):
        super().__init__(
            f"KeyValueMismatch: Key kodiert Zone '{key_zone}', "
            f"Value enthält Zone '{value_zone}'"
        )


class SacredApprovalMissing(ContextDBError):
    """
    Raised wenn versucht wird, SACRED-Daten ohne explizite Session-Genehmigung
    zu lesen oder zu schreiben (CLAUDE.md-Guardrail).
    """

    def __init__(self):
        super().__init__(
            "SacredApprovalMissing: Zugriff auf SACRED-Zone erfordert "
            "explizite Sven-Genehmigung in dieser Session."
        )


class ConnectionError(ContextDBError):
    """Redis-Verbindung nicht verfügbar."""

    def __init__(self, url: str, cause: Exception):
        super().__init__(f"ContextDB nicht erreichbar ({url}): {cause}")
