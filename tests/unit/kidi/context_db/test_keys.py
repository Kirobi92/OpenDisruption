"""
tests/unit/kidi/context_db/test_keys.py
Zone: WORKSPACE

Tests für kidi/context_db/keys.py — Key-Format-Validierung.
Kein Redis erforderlich.
"""

import pytest

from kidi.context_db.keys import (
    VALID_ZONES,
    is_valid_key,
    make_key,
    parse_key,
)


# ─── make_key ────────────────────────────────────────────────────────────────

class TestMakeKey:
    def test_basis_format(self):
        key = make_key("WORKSPACE", "opencode", "task")
        parts = key.split(":")
        # Zone:agent:category:uuid → 4 Teile, aber UUID enthält selbst Bindestriche
        assert parts[0] == "WORKSPACE"
        assert parts[1] == "opencode"
        assert parts[2] == "task"
        # UUID-Teil (Rest nach drittem Colon)
        uuid_part = ":".join(parts[3:])
        assert len(uuid_part) == 36  # UUID4 hat 36 Zeichen

    def test_alle_zonen_erlaubt(self):
        for zone in VALID_ZONES:
            key = make_key(zone, "testagent", "memory")
            assert key.startswith(zone + ":")

    def test_uid_wird_uebernommen(self):
        uid = "12345678-1234-4234-8234-123456789abc"
        key = make_key("PUBLIC", "hermes", "event", uid=uid)
        assert key.endswith(uid)

    def test_ungueltige_zone_raises(self):
        with pytest.raises(ValueError, match="Ungültige Zone"):
            make_key("GEHEIM", "agent", "cat")

    def test_ungueltige_zone_leer(self):
        with pytest.raises(ValueError):
            make_key("", "agent", "cat")

    def test_ungültiger_agent_uppercase(self):
        with pytest.raises(ValueError, match="agent-Slug"):
            make_key("WORKSPACE", "OpenCode", "task")

    def test_ungültiger_agent_leerzeichen(self):
        with pytest.raises(ValueError):
            make_key("WORKSPACE", "open code", "task")

    def test_ungültige_category_sonderzeichen(self):
        with pytest.raises(ValueError, match="category"):
            make_key("WORKSPACE", "opencode", "my/task")

    def test_ungültige_uuid_raises(self):
        with pytest.raises(ValueError, match="UUID4"):
            make_key("WORKSPACE", "opencode", "task", uid="not-a-uuid")

    def test_agent_mit_bindestrich_erlaubt(self):
        key = make_key("WORKSPACE", "kirobi-core", "context")
        assert "kirobi-core" in key

    def test_agent_mit_unterstrich_erlaubt(self):
        key = make_key("WORKSPACE", "kirobi_core", "context")
        assert "kirobi_core" in key

    def test_agent_zu_lang_raises(self):
        with pytest.raises(ValueError):
            make_key("WORKSPACE", "a" * 41, "task")


# ─── parse_key ───────────────────────────────────────────────────────────────

class TestParseKey:
    def test_roundtrip(self):
        uid = "12345678-1234-4234-8234-123456789abc"
        key = make_key("WORKSPACE", "opencode", "task", uid=uid)
        parsed = parse_key(key)
        assert parsed.zone == "WORKSPACE"
        assert parsed.agent == "opencode"
        assert parsed.category == "task"
        assert parsed.uid == uid

    def test_alle_zonen_parsebar(self):
        for zone in VALID_ZONES:
            key = make_key(zone, "agent", "cat")
            parsed = parse_key(key)
            assert parsed.zone == zone

    def test_ungültiges_format_raises(self):
        with pytest.raises(ValueError, match="Key-Format"):
            parse_key("WORKSPACE:opencode:task")  # fehlende UUID

    def test_ungültiger_zone_teil_raises(self):
        with pytest.raises(ValueError):
            parse_key("GEHEIM:opencode:task:12345678-1234-4234-8234-123456789abc")

    def test_leerzeichen_raises(self):
        with pytest.raises(ValueError):
            parse_key("")

    def test_extra_colons_raises(self):
        with pytest.raises(ValueError):
            parse_key("WORKSPACE:opencode:task:extra:12345678-1234-4234-8234-123456789abc")


# ─── is_valid_key ────────────────────────────────────────────────────────────

class TestIsValidKey:
    def test_gültiger_key(self):
        key = make_key("WORKSPACE", "opencode", "task")
        assert is_valid_key(key) is True

    def test_ungültiger_key_false(self):
        assert is_valid_key("not-a-key") is False

    def test_leerer_string_false(self):
        assert is_valid_key("") is False

    def test_falsche_zone_false(self):
        assert is_valid_key("PRIVATE:opencode:task:12345678-1234-4234-8234-123456789abc") is False
