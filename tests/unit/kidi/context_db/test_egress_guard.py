"""
tests/unit/kidi/context_db/test_egress_guard.py
Zone: WORKSPACE

Tests für den Egress-Guard — schützt vor versehentlichem Export sensibler Daten.
Verwendet fakeredis — kein echtes Redis erforderlich.
"""

import os

import pytest

try:
    import fakeredis
    _FAKEREDIS = True
except ImportError:
    _FAKEREDIS = False

from kidi.context_db.client import ContextDB
from kidi.context_db.errors import EgressViolation, SacredApprovalMissing

pytestmark = pytest.mark.skipif(
    not _FAKEREDIS, reason="fakeredis nicht installiert — `pip install fakeredis`"
)


@pytest.fixture
def db():
    r = fakeredis.FakeRedis(decode_responses=True)
    return ContextDB(redis_client=r)


# ─── Egress-Blockierung ──────────────────────────────────────────────────────

class TestEgressGuard:
    def test_family_private_blockiert_ohne_egress(self, db, monkeypatch):
        """FAMILY_PRIVATE-Daten dürfen nicht geschrieben werden wenn EGRESS=false."""
        monkeypatch.setenv("KIROBI_EGRESS_ALLOWED", "false")
        with pytest.raises(EgressViolation) as exc_info:
            db.put("FAMILY_PRIVATE", "kirobi", "profile", {"name": "Samira"})
        assert "FAMILY_PRIVATE" in str(exc_info.value)
        assert "KIROBI_EGRESS_ALLOWED" in str(exc_info.value)

    def test_family_private_erlaubt_mit_egress(self, db, monkeypatch):
        """Mit EGRESS=true darf FAMILY_PRIVATE geschrieben werden."""
        monkeypatch.setenv("KIROBI_EGRESS_ALLOWED", "true")
        key = db.put("FAMILY_PRIVATE", "kirobi", "profile", {"name": "Samira"})
        assert "FAMILY_PRIVATE" in key

    def test_sacred_immer_blockiert_egal_egress(self, db, monkeypatch):
        """SACRED erfordert Session-Approval — niemals durch EGRESS-Flag entsperrbar."""
        monkeypatch.setenv("KIROBI_EGRESS_ALLOWED", "true")
        with pytest.raises(SacredApprovalMissing):
            db.put("SACRED", "kirobi", "secret", {"data": "sensitiv"})

    def test_sacred_blockiert_auch_ohne_egress(self, db, monkeypatch):
        monkeypatch.setenv("KIROBI_EGRESS_ALLOWED", "false")
        with pytest.raises(SacredApprovalMissing):
            db.put("SACRED", "kirobi", "secret", {"data": "sensitiv"})

    def test_workspace_nicht_blockiert_ohne_egress(self, db, monkeypatch):
        """WORKSPACE ist nicht egress-sensitiv — immer erlaubt."""
        monkeypatch.setenv("KIROBI_EGRESS_ALLOWED", "false")
        key = db.put("WORKSPACE", "opencode", "task", {"title": "Test"})
        assert "WORKSPACE" in key

    def test_public_nicht_blockiert_ohne_egress(self, db, monkeypatch):
        """PUBLIC ist nicht sensitiv."""
        monkeypatch.setenv("KIROBI_EGRESS_ALLOWED", "false")
        key = db.put("PUBLIC", "opencode", "event", {"msg": "hello"})
        assert "PUBLIC" in key

    def test_egress_default_ist_false(self, db, monkeypatch):
        """Wenn KIROBI_EGRESS_ALLOWED nicht gesetzt → Default ist false → FAMILY_PRIVATE blockiert."""
        monkeypatch.delenv("KIROBI_EGRESS_ALLOWED", raising=False)
        with pytest.raises(EgressViolation):
            db.put("FAMILY_PRIVATE", "kirobi", "data", {"x": 1})

    def test_egress_case_insensitive(self, db, monkeypatch):
        """KIROBI_EGRESS_ALLOWED=True (groß) soll auch als true gewertet werden."""
        monkeypatch.setenv("KIROBI_EGRESS_ALLOWED", "True")
        # Kein Raise erwartet
        key = db.put("FAMILY_PRIVATE", "kirobi", "profile", {"name": "Sineo"})
        assert "FAMILY_PRIVATE" in key

    def test_quarantine_immer_blockiert(self, db, monkeypatch):
        """QUARANTINE darf niemals beschrieben werden."""
        monkeypatch.setenv("KIROBI_EGRESS_ALLOWED", "true")
        from kidi.context_db.errors import ZoneViolation
        with pytest.raises(ZoneViolation):
            db.put("QUARANTINE", "kirobi", "inbox", {"raw": "untrusted"})


# ─── Egress-Fehlermeldungen ───────────────────────────────────────────────────

class TestEgressErrorMessages:
    def test_egress_violation_enthält_zone(self):
        err = EgressViolation("FAMILY_PRIVATE")
        assert "FAMILY_PRIVATE" in str(err)
        assert "KIROBI_EGRESS_ALLOWED" in str(err)

    def test_sacred_approval_missing_message(self):
        err = SacredApprovalMissing()
        assert "SACRED" in str(err)
        assert "Sven" in str(err)
