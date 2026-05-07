from kirobi_core.registry import AgentRegistry, parse_registry


SAMPLE = """
# Some preface

## 1. kirobi-core

**Rolle:** Supervisor
**Modell:** llama3.1:70b
**Zone-Zugriff:** Alle Zonen

## 2. kirobi-coder

**Rolle:** Coder
**Modell:** qwen2.5-coder:32b
**Zone-Zugriff:** PUBLIC, WORKSPACE
"""


def test_parse_registry_extracts_all_agents():
    specs = parse_registry(SAMPLE)
    names = [s.name for s in specs]
    assert names == ["kirobi-core", "kirobi-coder"]


def test_parse_registry_assigns_zones_and_capabilities():
    specs = {s.name: s for s in parse_registry(SAMPLE)}
    assert specs["kirobi-core"].model.startswith("llama3.1")
    # All zones expanded
    assert len(specs["kirobi-core"].zones) == 5
    # capability inferred from name
    assert "code" in specs["kirobi-coder"].capabilities


def test_registry_load_falls_back_when_file_missing(tmp_path):
    reg = AgentRegistry.load(tmp_path / "does-not-exist.md")
    assert "kirobi-core" in reg
    assert reg.get("kirobi-coder") is not None


def test_registry_find_by_capability():
    reg = AgentRegistry(parse_registry(SAMPLE))
    coders = reg.find_by_capability("code")
    assert any(a.name == "kirobi-coder" for a in coders)


def test_parse_registry_handles_all_zones_except_sacred():
    specs = parse_registry(
        """## 1. kirobi-observer
**Rolle:** Observer
**Modell:** mistral:7b
**Zone-Zugriff:** Lesen aller Zonen (außer SACRED)
"""
    )
    zones = {zone.value for zone in specs[0].zones}
    assert "SACRED" not in zones
    assert {"PUBLIC", "WORKSPACE", "FAMILY_PRIVATE", "QUARANTINE"}.issubset(zones)
