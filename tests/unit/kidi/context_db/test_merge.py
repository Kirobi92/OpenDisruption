"""
tests/unit/kidi/context_db/test_merge.py
Zone: WORKSPACE

Tests für die Merge-Strategie des ContextDB-Clients.
Verwendet fakeredis — kein echtes Redis erforderlich.
"""

import time

import pytest

try:
    import fakeredis
    _FAKEREDIS = True
except ImportError:
    _FAKEREDIS = False

from kidi.context_db.client import ContextDB, _deep_merge

pytestmark = pytest.mark.skipif(
    not _FAKEREDIS, reason="fakeredis nicht installiert — `pip install fakeredis`"
)


@pytest.fixture
def db():
    r = fakeredis.FakeRedis(decode_responses=True)
    return ContextDB(redis_client=r)


# ─── _deep_merge (Unit) ──────────────────────────────────────────────────────

class TestDeepMerge:
    def test_flacher_merge(self):
        base = {"a": 1, "b": 2}
        patch = {"b": 99, "c": 3}
        result = _deep_merge(base, patch)
        assert result == {"a": 1, "b": 99, "c": 3}

    def test_nested_merge(self):
        base = {"config": {"host": "localhost", "port": 6379}, "name": "redis"}
        patch = {"config": {"port": 6380, "password": "secret"}}
        result = _deep_merge(base, patch)
        assert result["config"]["host"] == "localhost"   # erhalten
        assert result["config"]["port"] == 6380          # überschrieben
        assert result["config"]["password"] == "secret"  # neu
        assert result["name"] == "redis"                 # unberührt

    def test_tiefe_verschachtelung(self):
        base = {"l1": {"l2": {"l3": "original"}}}
        patch = {"l1": {"l2": {"l3": "updated", "new": True}}}
        result = _deep_merge(base, patch)
        assert result["l1"]["l2"]["l3"] == "updated"
        assert result["l1"]["l2"]["new"] is True

    def test_patch_ueberschreibt_dict_mit_scalar(self):
        base = {"key": {"nested": "value"}}
        patch = {"key": "scalar"}
        result = _deep_merge(base, patch)
        assert result["key"] == "scalar"

    def test_leerer_patch(self):
        base = {"a": 1}
        result = _deep_merge(base, {})
        assert result == {"a": 1}

    def test_base_unveraendert(self):
        base = {"a": {"b": 1}}
        patch = {"a": {"b": 2}}
        _deep_merge(base, patch)
        # base darf nicht mutiert werden
        assert base["a"]["b"] == 1


# ─── ContextDB.merge (Integration mit FakeRedis) ─────────────────────────────

class TestContextDBMerge:
    def test_merge_dict_payload(self, db, monkeypatch):
        monkeypatch.setenv("KIROBI_EGRESS_ALLOWED", "false")
        key = db.put("WORKSPACE", "opencode", "task", {"status": "pending", "prio": 5})
        updated = db.merge(key, {"status": "running"}, requester_zone="WORKSPACE")
        assert updated["payload"]["status"] == "running"
        assert updated["payload"]["prio"] == 5  # erhalten

    def test_merge_scalar_last_write_wins(self, db, monkeypatch):
        monkeypatch.setenv("KIROBI_EGRESS_ALLOWED", "false")
        key = db.put("WORKSPACE", "opencode", "counter", 42)
        updated = db.merge(key, 100, requester_zone="WORKSPACE")
        assert updated["payload"] == 100

    def test_merge_aktualisiert_timestamp(self, db, monkeypatch):
        monkeypatch.setenv("KIROBI_EGRESS_ALLOWED", "false")
        key = db.put("WORKSPACE", "opencode", "task", {"x": 1})
        before = db.get(key, "WORKSPACE")["ts"]
        time.sleep(0.01)
        db.merge(key, {"x": 2}, requester_zone="WORKSPACE")
        after = db.get(key, "WORKSPACE")["ts"]
        assert after > before

    def test_merge_nicht_existierender_key_raises(self, db):
        fake_key = "WORKSPACE:opencode:task:12345678-1234-4234-8234-123456789abc"
        with pytest.raises(KeyError):
            db.merge(fake_key, {"x": 1}, requester_zone="WORKSPACE")

    def test_merge_zone_verletzung_raises(self, db, monkeypatch):
        monkeypatch.setenv("KIROBI_EGRESS_ALLOWED", "true")
        key = db.put("FAMILY_PRIVATE", "kirobi", "profile", {"name": "Sven"})
        from kidi.context_db.errors import ZoneViolation
        with pytest.raises(ZoneViolation):
            db.merge(key, {"name": "X"}, requester_zone="PUBLIC")


# ─── ContextDB.put + get (Basis-Roundtrip) ───────────────────────────────────

class TestContextDBPutGet:
    def test_roundtrip_workspace(self, db, monkeypatch):
        monkeypatch.setenv("KIROBI_EGRESS_ALLOWED", "false")
        key = db.put("WORKSPACE", "opencode", "context", {"mission": "Phase 1"})
        entry = db.get(key, requester_zone="WORKSPACE")
        assert entry["payload"]["mission"] == "Phase 1"
        assert entry["zone"] == "WORKSPACE"
        assert entry["agent"] == "opencode"

    def test_get_nicht_vorhanden_raises(self, db):
        fake_key = "WORKSPACE:opencode:task:12345678-1234-4234-8234-123456789abc"
        with pytest.raises(KeyError):
            db.get(fake_key, requester_zone="WORKSPACE")

    def test_delete(self, db, monkeypatch):
        monkeypatch.setenv("KIROBI_EGRESS_ALLOWED", "false")
        key = db.put("WORKSPACE", "opencode", "tmp", "data")
        assert db.delete(key) is True
        assert db.delete(key) is False

    def test_query_nach_zone(self, db, monkeypatch):
        monkeypatch.setenv("KIROBI_EGRESS_ALLOWED", "false")
        db.put("WORKSPACE", "opencode", "task", {"n": 1})
        db.put("WORKSPACE", "opencode", "task", {"n": 2})
        results = db.query("WORKSPACE", agent="opencode", category="task",
                           requester_zone="WORKSPACE")
        assert len(results) >= 2
