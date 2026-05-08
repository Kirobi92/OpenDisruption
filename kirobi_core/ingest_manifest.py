"""Safe ingest manifest planning for personal-memory preparation.

The helpers in this module create a policy-gated manifest for candidate files.
Sensitive zones are represented only by path metadata and an explicit policy
decision so later ingestion stages can fail closed until Sven approves the next
step. Content is only read for files that are already allowed for autonomous
PUBLIC/WORKSPACE staging.
"""

from __future__ import annotations

import json
import hashlib
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .zones import Zone, can_write, classify, relpath_in_repo


_AUTONOMOUS_INGEST_ZONES = frozenset({Zone.PUBLIC, Zone.WORKSPACE})
_BLOCKED_WITHOUT_APPROVAL_ZONES = frozenset(
    {Zone.FAMILY_PRIVATE, Zone.QUARANTINE, Zone.SACRED}
)


@dataclass(frozen=True)
class ManifestEntry:
    """Metadata-only policy decision for one candidate file."""

    path: str
    zone: Zone
    size: int
    suffix: str
    action: str
    reason: str
    sha256: str | None = None
    mime_type: str | None = None

    def to_dict(self) -> dict[str, str | int]:
        """Return a stable JSON-serialisable representation."""
        payload: dict[str, str | int] = {
            "path": self.path,
            "zone": self.zone.value,
            "size": self.size,
            "suffix": self.suffix,
            "action": self.action,
            "reason": self.reason,
        }
        if self.sha256 is not None:
            payload["sha256"] = self.sha256
        if self.mime_type is not None:
            payload["mime_type"] = self.mime_type
        return payload


@dataclass(frozen=True)
class IngestManifest:
    """Collection of metadata-only ingest decisions."""

    root: str
    entries: tuple[ManifestEntry, ...]

    def summary(self) -> dict[str, object]:
        """Return aggregate counts for humans and automation."""
        by_zone = {zone.value: 0 for zone in Zone}
        by_action: dict[str, int] = {}
        total_bytes = 0

        for entry in self.entries:
            by_zone[entry.zone.value] += 1
            by_action[entry.action] = by_action.get(entry.action, 0) + 1
            total_bytes += entry.size

        return {
            "root": self.root,
            "total_files": len(self.entries),
            "total_bytes": total_bytes,
            "by_zone": by_zone,
            "by_action": dict(sorted(by_action.items())),
        }

    def to_dict(self) -> dict[str, object]:
        """Return the full manifest as a JSON-serialisable dictionary."""
        return {
            **self.summary(),
            "entries": [entry.to_dict() for entry in self.entries],
        }


def decide_ingest_action(zone: Zone) -> tuple[str, str]:
    """Return the safe manifest action and human-readable reason for *zone*."""
    if zone in _AUTONOMOUS_INGEST_ZONES:
        return "stage", f"{zone.value} may be staged for local ingest preparation"
    if zone == Zone.QUARANTINE:
        return "block", "QUARANTINE is untrusted and requires human review before ingest"
    if zone in _BLOCKED_WITHOUT_APPROVAL_ZONES:
        return "block", f"{zone.value} requires explicit Sven approval before ingest"
    return "block", f"{zone.value} is not recognised as an autonomous ingest zone"


def _iter_candidate_files(root: Path, candidates: Iterable[str | Path]) -> Iterable[Path]:
    for raw in candidates:
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = root / candidate
        if candidate.is_dir():
            for current, dirnames, filenames in __import__("os").walk(candidate):
                dirnames[:] = [d for d in dirnames if d not in {".git", "__pycache__"}]
                for filename in filenames:
                    yield Path(current) / filename
        else:
            yield candidate


def _zone_rank(zone: Zone) -> int:
    """Return a conservative sensitivity rank for *zone*."""
    return list(Zone).index(zone)


def _read_frontmatter_zone(path: Path) -> Zone | None:
    """Return a zone declared in Markdown frontmatter, if safely present."""
    try:
        with path.open("r", encoding="utf-8") as handle:
            first = handle.readline()
            if first.strip() != "---":
                return None
            for _ in range(50):
                line = handle.readline()
                if not line:
                    return None
                stripped = line.strip()
                if stripped == "---":
                    return None
                if stripped.lower().startswith("zone:"):
                    raw_zone = stripped.split(":", 1)[1].strip().strip('"\'')
                    try:
                        return Zone(raw_zone.upper())
                    except ValueError:
                        return None
    except (OSError, UnicodeDecodeError):
        return None
    return None


def _apply_markdown_frontmatter_zone(path: Path, path_zone: Zone) -> Zone:
    """Use Markdown frontmatter to increase, never decrease, path sensitivity."""
    if path_zone not in _AUTONOMOUS_INGEST_ZONES:
        return path_zone
    if path.suffix.lower() not in {".md", ".markdown"}:
        return path_zone

    frontmatter_zone = _read_frontmatter_zone(path)
    if frontmatter_zone is None:
        return path_zone
    if _zone_rank(frontmatter_zone) > _zone_rank(path_zone):
        return frontmatter_zone
    return path_zone


def _sha256_file(path: Path) -> str:
    """Return the SHA256 digest for an allowed staged file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(
    repo_root: str | Path,
    candidates: Iterable[str | Path],
) -> IngestManifest:
    """Build a metadata-only ingest manifest for *candidates*.

    Paths outside *repo_root* are blocked and recorded as SACRED fail-closed
    entries. Contents are opened only after a file has been classified as
    PUBLIC/WORKSPACE and the manifest action remains ``stage``.
    """
    root = Path(repo_root).resolve()
    entries: list[ManifestEntry] = []

    for candidate in _iter_candidate_files(root, candidates):
        rel = relpath_in_repo(root, candidate)
        if rel is None:
            entries.append(
                ManifestEntry(
                    path=str(candidate),
                    zone=Zone.SACRED,
                    size=0,
                    suffix=candidate.suffix.lower(),
                    action="block",
                    reason="Path is outside repository sandbox; fail closed as SACRED",
                )
            )
            continue

        zone = _apply_markdown_frontmatter_zone(candidate, classify(rel))
        action, reason = decide_ingest_action(zone)
        try:
            stat = candidate.stat()
            size = stat.st_size
        except OSError:
            size = 0
            action = "block"
            reason = "Path cannot be stat()ed safely; ingest preparation blocked"

        sha256: str | None = None
        mime_type: str | None = None
        if action == "stage":
            try:
                sha256 = _sha256_file(candidate)
                mime_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
            except OSError:
                action = "block"
                reason = "Path cannot be read safely for staged metadata; ingest preparation blocked"
                sha256 = None
                mime_type = None

        entries.append(
            ManifestEntry(
                path=rel,
                zone=zone,
                size=size,
                suffix=candidate.suffix.lower(),
                action=action,
                reason=reason,
                sha256=sha256,
                mime_type=mime_type,
            )
        )

    entries.sort(key=lambda entry: entry.path)
    return IngestManifest(root=str(root), entries=tuple(entries))


def render_manifest_json(manifest: IngestManifest) -> str:
    """Render *manifest* as deterministic UTF-8 JSON text."""
    return json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False, sort_keys=True)


def render_manifest_jsonl(manifest: IngestManifest) -> str:
    """Render manifest entries as deterministic UTF-8 JSON Lines text."""
    lines = [
        json.dumps(entry.to_dict(), ensure_ascii=False, sort_keys=True)
        for entry in manifest.entries
    ]
    return "\n".join(lines) + ("\n" if lines else "")


def render_manifest(manifest: IngestManifest, output_format: str = "json") -> str:
    """Render *manifest* as ``json`` or ``jsonl`` text."""
    if output_format == "json":
        return render_manifest_json(manifest)
    if output_format == "jsonl":
        return render_manifest_jsonl(manifest)
    raise ValueError(f"Unsupported manifest output format: {output_format}")


def write_manifest_output(
    repo_root: str | Path,
    manifest: IngestManifest,
    output: str | Path,
    *,
    output_format: str = "json",
) -> Path:
    """Write *manifest* to an allowed PUBLIC/WORKSPACE output path.

    The output path must stay inside *repo_root* and be writable under the
    repository zone policy. Protected paths fail closed before any file is
    opened or overwritten.
    """
    root = Path(repo_root).resolve()
    target = Path(output)
    if not target.is_absolute():
        target = root / target

    rel = relpath_in_repo(root, target)
    if rel is None:
        raise PermissionError("Manifest output path is outside repository sandbox")

    decision = can_write(rel)
    if not decision.allowed:
        raise PermissionError(f"Manifest output path blocked: {decision.reason}")

    parent_rel = relpath_in_repo(root, target.parent)
    if parent_rel is None:
        raise PermissionError("Manifest output parent is outside repository sandbox")
    parent_decision = can_write(parent_rel)
    if not parent_decision.allowed:
        raise PermissionError(f"Manifest output parent blocked: {parent_decision.reason}")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_manifest(manifest, output_format), encoding="utf-8")
    return target
