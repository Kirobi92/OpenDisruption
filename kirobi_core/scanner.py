"""Repository structural scan.

Walks the repository, classifies every file by zone and produces a
compact :class:`RepoScan` summary. The scan deliberately avoids
reading file contents for SACRED / FAMILY_PRIVATE zones — only metadata
(size, mtime) is recorded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .zones import Zone, classify, relpath_in_repo

# Folders that are *never* descended into — they are caches / build output
# rather than meaningful repository content.
_SKIP_DIRS = frozenset(
    {
        ".git",
        ".kirobi",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        ".venv",
        "venv",
        ".mypy_cache",
        ".ruff_cache",
        "dist",
        "build",
        ".cache",
        "postgres_data",
        "qdrant_data",
        "ollama_data",
        "openwebui_data",
        "flowise_data",
        ".next",          # Next.js Build-Artefakte — kein echter Code
        "standalone",     # Next.js standalone output
        "chunks",         # Next.js Webpack-Chunks
    }
)

# Extensions considered "code" for backlog/reporting purposes.
_CODE_EXTS = frozenset(
    {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".sh", ".yml", ".yaml"}
)
_DOC_EXTS = frozenset({".md", ".rst"})


@dataclass
class FileEntry:
    """One file recorded by the scanner."""

    path: str  # repository-relative, forward slashes
    zone: Zone
    size: int
    suffix: str

    @property
    def is_code(self) -> bool:
        return self.suffix.lower() in _CODE_EXTS

    @property
    def is_doc(self) -> bool:
        return self.suffix.lower() in _DOC_EXTS


@dataclass
class RepoScan:
    """Aggregated scan of the repository."""

    root: str
    files: list[FileEntry] = field(default_factory=list)
    by_zone: dict[Zone, int] = field(default_factory=dict)
    total_files: int = 0
    total_bytes: int = 0
    code_files: int = 0
    doc_files: int = 0

    # ----------------------------------------------------------- helpers
    def files_in_zone(self, zone: Zone) -> list[FileEntry]:
        return [f for f in self.files if f.zone == zone]

    def code_files_writable(self) -> list[FileEntry]:
        """Code files in zones where autonomous edits are allowed."""
        return [
            f
            for f in self.files
            if f.is_code and f.zone in (Zone.PUBLIC, Zone.WORKSPACE)
        ]

    def docs_writable(self) -> list[FileEntry]:
        return [
            f
            for f in self.files
            if f.is_doc and f.zone in (Zone.PUBLIC, Zone.WORKSPACE)
        ]

    def summary(self) -> dict:
        return {
            "root": self.root,
            "total_files": self.total_files,
            "total_bytes": self.total_bytes,
            "code_files": self.code_files,
            "doc_files": self.doc_files,
            "by_zone": {zone.value: self.by_zone.get(zone, 0) for zone in Zone},
        }


def _iter_files(root: Path) -> Iterable[Path]:
    for current, dirnames, filenames in __import__("os").walk(root):
        # Mutate dirnames in place to skip unwanted folders. ``.git`` is
        # in ``_SKIP_DIRS``; do not blanket-skip ``.git*`` so that
        # ``.github`` (workflows) remains visible.
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for fname in filenames:
            yield Path(current) / fname


def scan_repository(root: Path | str = ".") -> RepoScan:
    """Walk *root*, classify each file by zone and return a :class:`RepoScan`."""
    root_path = Path(root).resolve()
    scan = RepoScan(root=str(root_path))

    for full in _iter_files(root_path):
        rel = relpath_in_repo(root_path, full)
        if rel is None:
            continue
        try:
            stat = full.stat()
        except OSError:
            continue
        zone = classify(rel)
        entry = FileEntry(
            path=rel,
            zone=zone,
            size=stat.st_size,
            suffix=full.suffix,
        )
        scan.files.append(entry)
        scan.total_files += 1
        scan.total_bytes += stat.st_size
        scan.by_zone[zone] = scan.by_zone.get(zone, 0) + 1
        if entry.is_code:
            scan.code_files += 1
        if entry.is_doc:
            scan.doc_files += 1

    return scan
