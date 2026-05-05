"""Agent registry loader.

Reads ``metadata/AGENTREGISTRY.md`` and extracts the list of declared
agents together with their roles, models and zone access.

This is a *best-effort* parser tailored to the existing markdown
format (``## N. agent-name`` headings followed by ``**Rolle:** …``
and ``**Modell:** …`` lines). When the file is missing or unreadable a
small built-in default registry is returned so the orchestrator can
still operate.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .zones import Zone

DEFAULT_REGISTRY_PATH = Path("metadata/AGENTREGISTRY.md")

_HEADING_RE = re.compile(r"^##\s+\d+\.\s+([a-z0-9][a-z0-9-_]*)", re.IGNORECASE)
_FIELD_RE = re.compile(r"\*\*(Rolle|Modell|Zone-Zugriff)\:\*\*\s*(.+)", re.IGNORECASE)


# Capability hints derived from agent names. Keeps the parser simple
# while still letting the orchestrator route by capability.
_NAME_TO_CAPABILITIES: dict[str, tuple[str, ...]] = {
    "kirobi-core": ("orchestration", "routing", "supervision"),
    "kirobi-architect": ("planning", "architecture", "design", "roadmap"),
    "kirobi-coder": ("code", "refactor", "test", "debug"),
    "kirobi-ops": ("ops", "deploy", "infra", "monitoring", "backup"),
    "kirobi-observer": ("observability", "metrics", "report"),
    "hermes-extractor": ("ingest", "extract", "classify"),
    "samira-heart": ("family", "mediation", "care"),
    "sineo-creator": ("creative", "child", "story"),
    "research-crew": ("research", "summarize"),
    "creative-agent": ("creative", "writing", "image"),
    "voice-agent": ("voice", "stt", "tts"),
    "installer-agent": ("install", "setup"),
    "enterprise-agent": ("business", "client"),
    "claude-code": ("code", "review"),
}


@dataclass(frozen=True)
class AgentSpec:
    """Static description of an agent loaded from the registry."""

    name: str
    role: str = ""
    model: str = ""
    zones: tuple[Zone, ...] = field(default_factory=tuple)
    capabilities: tuple[str, ...] = field(default_factory=tuple)

    def can_access(self, zone: Zone) -> bool:
        if not self.zones:
            return zone in (Zone.PUBLIC, Zone.WORKSPACE)
        return zone in self.zones


def _parse_zones(raw: str) -> tuple[Zone, ...]:
    raw_upper = raw.upper()
    if "ALLE ZONEN" in raw_upper or "ALL ZONES" in raw_upper:
        return tuple(Zone)
    found: list[Zone] = []
    for zone in Zone:
        if zone.value in raw_upper:
            found.append(zone)
    return tuple(found) or (Zone.PUBLIC, Zone.WORKSPACE)


def parse_registry(text: str) -> list[AgentSpec]:
    """Parse the markdown text of ``AGENTREGISTRY.md`` into specs."""
    specs: list[AgentSpec] = []
    current: dict[str, str] = {}

    def flush() -> None:
        if not current.get("name"):
            return
        name = current["name"]
        zones = _parse_zones(current.get("zones", ""))
        spec = AgentSpec(
            name=name,
            role=current.get("role", ""),
            model=current.get("model", ""),
            zones=zones,
            capabilities=_NAME_TO_CAPABILITIES.get(name, ()),
        )
        specs.append(spec)

    for line in text.splitlines():
        m = _HEADING_RE.match(line.strip())
        if m:
            flush()
            current = {"name": m.group(1).lower()}
            continue
        f = _FIELD_RE.search(line)
        if f and current:
            key = f.group(1).lower()
            value = f.group(2).strip()
            if key.startswith("rolle"):
                current["role"] = value
            elif key.startswith("modell"):
                current["model"] = value
            elif key.startswith("zone"):
                current["zones"] = value
    flush()
    return specs


_FALLBACK_AGENTS: tuple[AgentSpec, ...] = (
    AgentSpec("kirobi-core", role="Supervisor", model="llama3.1:70b",
              zones=tuple(Zone), capabilities=_NAME_TO_CAPABILITIES["kirobi-core"]),
    AgentSpec("kirobi-architect", role="Architecture",
              zones=(Zone.PUBLIC, Zone.WORKSPACE),
              capabilities=_NAME_TO_CAPABILITIES["kirobi-architect"]),
    AgentSpec("kirobi-coder", role="Coding",
              zones=(Zone.PUBLIC, Zone.WORKSPACE),
              capabilities=_NAME_TO_CAPABILITIES["kirobi-coder"]),
    AgentSpec("kirobi-ops", role="DevOps",
              zones=(Zone.PUBLIC, Zone.WORKSPACE),
              capabilities=_NAME_TO_CAPABILITIES["kirobi-ops"]),
    AgentSpec("kirobi-observer", role="Observability",
              zones=tuple(Zone),
              capabilities=_NAME_TO_CAPABILITIES["kirobi-observer"]),
)


class AgentRegistry:
    """In-memory agent registry."""

    def __init__(self, agents: Iterable[AgentSpec]) -> None:
        self._agents: dict[str, AgentSpec] = {a.name: a for a in agents}

    @classmethod
    def load(cls, path: Path | str = DEFAULT_REGISTRY_PATH) -> "AgentRegistry":
        p = Path(path)
        if p.is_file():
            try:
                text = p.read_text(encoding="utf-8")
                parsed = parse_registry(text)
                if parsed:
                    return cls(parsed)
            except OSError:
                pass
        return cls(_FALLBACK_AGENTS)

    def __len__(self) -> int:
        return len(self._agents)

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and name in self._agents

    def __iter__(self):
        return iter(self._agents.values())

    def get(self, name: str) -> AgentSpec | None:
        return self._agents.get(name)

    def names(self) -> list[str]:
        return sorted(self._agents.keys())

    def find_by_capability(self, capability: str) -> list[AgentSpec]:
        cap = capability.lower()
        return [a for a in self._agents.values() if cap in a.capabilities]
