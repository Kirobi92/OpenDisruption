"""Five-zone security helpers used across :mod:`kirobi_core`.

The zones mirror the model documented in ``CLAUDE.md`` and
``metadata/ZONE-POLICY-MATRIX.md``:

==================  =====================================================
Zone                Folders / examples
==================  =====================================================
PUBLIC              ``canon/public``, ``extracts/public``, top-level docs
WORKSPACE           ``kirobi-core``, ``services``, ``infra``, ``config``, ``metadata``,
                    ``apps``, ``integrations``, ``prompts``, ``tests``,
                    ``kirobi_core``, ``tools``
FAMILY_PRIVATE      ``extracts/family-private``, ``experiences/family``,
                    ``canon/family``, ``clusters/family``
QUARANTINE          ``quarantine``, ``sources/inbox``
SACRED              ``sacred``
==================  =====================================================

The functions here are intentionally conservative: when a path does not
match any known zone the resolver returns :data:`Zone.SACRED` so that
callers fail closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Iterable


class Zone(str, Enum):
    """Security zones, ordered from most open to most sensitive."""

    PUBLIC = "PUBLIC"
    WORKSPACE = "WORKSPACE"
    FAMILY_PRIVATE = "FAMILY_PRIVATE"
    QUARANTINE = "QUARANTINE"
    SACRED = "SACRED"


# Order matters: longer / more specific prefixes win and are checked first.
_ZONE_PREFIXES: tuple[tuple[str, Zone], ...] = (
    ("sacred/", Zone.SACRED),
    ("quarantine/", Zone.QUARANTINE),
    ("sources/inbox/", Zone.QUARANTINE),
    ("extracts/family-private/", Zone.FAMILY_PRIVATE),
    ("experiences/family/", Zone.FAMILY_PRIVATE),
    ("canon/family/", Zone.FAMILY_PRIVATE),
    ("clusters/family/", Zone.FAMILY_PRIVATE),
    ("canon/public/", Zone.PUBLIC),
    ("extracts/public/", Zone.PUBLIC),
    ("docs/", Zone.PUBLIC),
    # Workspace folders
    ("kirobi-core/", Zone.WORKSPACE),
    ("kirobi_core/", Zone.WORKSPACE),
    ("metadata/", Zone.WORKSPACE),
    ("config/", Zone.WORKSPACE),
    ("prompts/", Zone.WORKSPACE),
    ("infra/", Zone.WORKSPACE),
    ("integrations/", Zone.WORKSPACE),
    ("models/", Zone.WORKSPACE),
    ("templates/", Zone.WORKSPACE),
    ("research/", Zone.WORKSPACE),
    ("tests/", Zone.WORKSPACE),
    ("services/", Zone.WORKSPACE),
    ("apps/", Zone.WORKSPACE),
    ("analytics/", Zone.WORKSPACE),
    ("tools/", Zone.WORKSPACE),
    ("archive/", Zone.WORKSPACE),
    ("agents/", Zone.WORKSPACE),
    ("kidi/", Zone.WORKSPACE),
    ("github/", Zone.WORKSPACE),   # .github/ after _normalize strips leading dot
    ("opencode/", Zone.WORKSPACE),  # .opencode/ after _normalize
    ("agents/", Zone.WORKSPACE),
    ("extracts/workspace/", Zone.WORKSPACE),
    ("extracts/technical/", Zone.WORKSPACE),
    ("clusters/", Zone.WORKSPACE),
    ("experiences/", Zone.WORKSPACE),
    ("canon/", Zone.WORKSPACE),
    ("extracts/", Zone.WORKSPACE),
    ("sources/", Zone.WORKSPACE),
)

# Top-level files that are explicitly safe to treat as PUBLIC.
_PUBLIC_TOP_LEVEL_FILES = frozenset(
    {
        "README.md",
        "LICENSE.md",
        "LICENSE",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CHANGELOG.md",
        "CLAUDE.md",
        "ARCHITECTURE.md",
        "ROADMAP.md",
        "PROJECT-CHARTER.md",
        "POST-CLONE-SETUP.md",
        "DEVELOPER-RUNBOOK.md",
        "QUICK-REFERENCE.md",
        "BENUTZERHANDBUCH.md",
        "ENTWICKLERDOKUMENTATION.md",
        "AUDIT-REPORT.md",
        "COMPLETION-REPORT.md",
        "IMPLEMENTATION-SUMMARY.md",
        "ULTIMATE-IMPLEMENTATION-ROADMAP.md",
        "THREAT-MODEL.md",
        ".env.example",
        ".gitignore",
        "Makefile",
        "docker-compose.yml",
        "setup-family-profiles.sh",
    }
)


def _normalize(rel_path: str | Path) -> str:
    """Return a forward-slash, lower-cased relative path string."""
    s = str(rel_path).replace("\\", "/").lstrip("./")
    return s


def classify(rel_path: str | Path) -> Zone:
    """Return the :class:`Zone` for a repository-relative path.

    The resolver fails *closed*: unknown locations are reported as
    :attr:`Zone.SACRED` to make sure callers gate every write.
    """
    norm = _normalize(rel_path)
    if not norm:
        return Zone.SACRED

    # Top-level file?
    if "/" not in norm and norm in _PUBLIC_TOP_LEVEL_FILES:
        return Zone.PUBLIC

    for prefix, zone in _ZONE_PREFIXES:
        if norm == prefix.rstrip("/") or norm.startswith(prefix):
            return zone

    # Unknown locations fail closed: see module docstring.
    return Zone.SACRED


@dataclass(frozen=True)
class WriteDecision:
    """Result of :func:`can_write`."""

    allowed: bool
    zone: Zone
    reason: str


# Zones an autonomous agent is allowed to *write* to without an explicit
# human approval. Anything else must be gated.
_AUTONOMOUS_WRITE_ALLOWLIST: frozenset[Zone] = frozenset(
    {Zone.PUBLIC, Zone.WORKSPACE}
)


def can_write(rel_path: str | Path, *, approved: bool = False) -> WriteDecision:
    """Return whether an autonomous write to *rel_path* is permitted."""
    zone = classify(rel_path)
    if zone in _AUTONOMOUS_WRITE_ALLOWLIST:
        return WriteDecision(True, zone, f"{zone.value} is on the autonomous allowlist")
    if approved:
        return WriteDecision(True, zone, f"{zone.value} write explicitly approved by human")
    return WriteDecision(False, zone, f"{zone.value} requires explicit human approval")


def filter_writable(paths: Iterable[str | Path]) -> list[str]:
    """Return only the paths that are writable without human approval."""
    out: list[str] = []
    for p in paths:
        decision = can_write(p)
        if decision.allowed:
            out.append(_normalize(p))
    return out


def is_inside_repo(repo_root: Path, candidate: Path) -> bool:
    """True if *candidate* resolves inside *repo_root*.

    Used to make sure autonomous file operations never escape the
    repository sandbox.
    """
    try:
        repo_root_resolved = repo_root.resolve()
        candidate_resolved = candidate.resolve()
    except OSError:
        return False
    try:
        candidate_resolved.relative_to(repo_root_resolved)
        return True
    except ValueError:
        return False


def relpath_in_repo(repo_root: Path, candidate: Path) -> str | None:
    """Return *candidate* as a forward-slash relative path inside the repo.

    ``None`` is returned when *candidate* is outside *repo_root*.
    """
    if not is_inside_repo(repo_root, candidate):
        return None
    rel = candidate.resolve().relative_to(repo_root.resolve())
    return str(PurePosixPath(*rel.parts))
