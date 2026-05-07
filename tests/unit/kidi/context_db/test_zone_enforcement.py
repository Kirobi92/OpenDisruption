"""
tests/unit/kidi/context_db/test_zone_enforcement.py
Zone: WORKSPACE

Tests für den Zone-Guard — Zugriffskontrolle zwischen Zonen.
Kein Redis erforderlich.
"""

import pytest

from kidi.context_db.errors import SacredApprovalMissing, ZoneViolation
from kidi.context_db.zone_guard import (
    check_read,
    check_write,
    is_readable,
    zone_rank,
)


# ─── zone_rank ───────────────────────────────────────────────────────────────

class TestZoneRank:
    def test_reihenfolge_korrekt(self):
        assert zone_rank("PUBLIC") < zone_rank("WORKSPACE")
        assert zone_rank("WORKSPACE") < zone_rank("FAMILY_PRIVATE")
        assert zone_rank("FAMILY_PRIVATE") < zone_rank("SACRED")

    def test_quarantine_isoliert(self):
        # QUARANTINE hat sehr hohen Rang — kann nicht normal gelesen werden
        assert zone_rank("QUARANTINE") > zone_rank("SACRED")

    def test_unbekannte_zone_negativ(self):
        assert zone_rank("UNKNOWN") < 0


# ─── check_read ──────────────────────────────────────────────────────────────

class TestCheckRead:
    """
    Für jede Kombination: requester_max_zone x entry_zone.
    Regel: entry_rank <= requester_rank → erlaubt (außer SACRED/QUARANTINE)
    """

    # Erlaubte Zugriffe
    def test_public_liest_public(self):
        check_read("PUBLIC", "PUBLIC")  # kein Raise

    def test_workspace_liest_public(self):
        check_read("WORKSPACE", "PUBLIC")  # kein Raise

    def test_workspace_liest_workspace(self):
        check_read("WORKSPACE", "WORKSPACE")  # kein Raise

    def test_family_liest_workspace(self):
        check_read("FAMILY_PRIVATE", "WORKSPACE")  # kein Raise

    def test_family_liest_family(self):
        check_read("FAMILY_PRIVATE", "FAMILY_PRIVATE")  # kein Raise

    # Verweigerte Zugriffe
    def test_public_liest_workspace_rejected(self):
        with pytest.raises(ZoneViolation) as exc_info:
            check_read("PUBLIC", "WORKSPACE")
        assert "PUBLIC" in str(exc_info.value)
        assert "WORKSPACE" in str(exc_info.value)

    def test_public_liest_family_rejected(self):
        with pytest.raises(ZoneViolation):
            check_read("PUBLIC", "FAMILY_PRIVATE")

    def test_workspace_liest_family_rejected(self):
        with pytest.raises(ZoneViolation):
            check_read("WORKSPACE", "FAMILY_PRIVATE")

    def test_workspace_liest_sacred_rejected(self):
        with pytest.raises(SacredApprovalMissing):
            check_read("WORKSPACE", "SACRED")

    def test_family_liest_sacred_rejected(self):
        with pytest.raises(SacredApprovalMissing):
            check_read("FAMILY_PRIVATE", "SACRED")

    def test_sacred_liest_sacred_rejected(self):
        # SACRED erfordert immer Session-Approval — kein Zonenlevel erlaubt automatischen Zugriff
        with pytest.raises(SacredApprovalMissing):
            check_read("SACRED", "SACRED")

    def test_quarantine_immer_rejected(self):
        with pytest.raises(ZoneViolation):
            check_read("SACRED", "QUARANTINE")

    def test_unbekannte_requester_zone_rejected(self):
        with pytest.raises(ZoneViolation):
            check_read("UNKNOWN", "PUBLIC")


# ─── check_write ─────────────────────────────────────────────────────────────

class TestCheckWrite:
    def test_public_write_erlaubt(self, monkeypatch):
        monkeypatch.setenv("KIROBI_EGRESS_ALLOWED", "true")
        check_write("PUBLIC")  # kein Raise

    def test_workspace_write_erlaubt_egress_off(self, monkeypatch):
        monkeypatch.setenv("KIROBI_EGRESS_ALLOWED", "false")
        check_write("WORKSPACE")  # WORKSPACE ist nicht egress-sensitiv

    def test_family_write_blockiert_ohne_egress(self, monkeypatch):
        monkeypatch.setenv("KIROBI_EGRESS_ALLOWED", "false")
        from kidi.context_db.errors import EgressViolation
        with pytest.raises(EgressViolation):
            check_write("FAMILY_PRIVATE")

    def test_family_write_erlaubt_mit_egress(self, monkeypatch):
        monkeypatch.setenv("KIROBI_EGRESS_ALLOWED", "true")
        check_write("FAMILY_PRIVATE")  # kein Raise

    def test_sacred_write_immer_rejected(self, monkeypatch):
        monkeypatch.setenv("KIROBI_EGRESS_ALLOWED", "true")
        with pytest.raises(SacredApprovalMissing):
            check_write("SACRED")

    def test_quarantine_write_rejected(self, monkeypatch):
        monkeypatch.setenv("KIROBI_EGRESS_ALLOWED", "true")
        with pytest.raises(ZoneViolation):
            check_write("QUARANTINE")


# ─── is_readable ─────────────────────────────────────────────────────────────

class TestIsReadable:
    def test_workspace_liest_workspace_true(self):
        assert is_readable("WORKSPACE", "WORKSPACE") is True

    def test_workspace_liest_family_false(self):
        assert is_readable("WORKSPACE", "FAMILY_PRIVATE") is False

    def test_workspace_liest_sacred_false(self):
        assert is_readable("WORKSPACE", "SACRED") is False

    def test_public_liest_public_true(self):
        assert is_readable("PUBLIC", "PUBLIC") is True
