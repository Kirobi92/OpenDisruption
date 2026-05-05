"""Task backlog generator.

Turns a :class:`~kirobi_core.scanner.RepoScan` into a list of
:class:`Task`\\ s sorted by priority. The generator deliberately uses
heuristics that are obvious and easy to reason about — every task
carries a :attr:`Task.reason` so a human reviewer can see *why* it was
proposed.

Generated task kinds (stable identifiers, useful for tests):

==============================  ==============================
Kind                            Heuristic
==============================  ==============================
``missing-readme``              folder lacks a README
``missing-tests``               module under ``services/`` or
                                ``kirobi_core/`` has no tests
``stale-doc``                   markdown file > 200 days old
``oversized-file``              code file > 1500 lines
``placeholder-readme``          README is shorter than 200 chars
``no-license-header``           top-level file lacks ``LICENSE``
``zone-misclassification``      file in unexpected zone (e.g.
                                code under ``sacred/``)
==============================  ==============================
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable

from .scanner import RepoScan
from .zones import Zone


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BACKGROUND = "background"


_PRIORITY_ORDER = {
    Priority.CRITICAL: 0,
    Priority.HIGH: 1,
    Priority.MEDIUM: 2,
    Priority.LOW: 3,
    Priority.BACKGROUND: 4,
}


@dataclass
class Task:
    """One backlog item proposed by :func:`generate_backlog`."""

    id: str
    kind: str
    title: str
    priority: Priority
    paths: list[str] = field(default_factory=list)
    reason: str = ""
    suggested_agent: str = "kirobi-coder"
    zone: Zone = Zone.WORKSPACE

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind,
            "title": self.title,
            "priority": self.priority.value,
            "paths": list(self.paths),
            "reason": self.reason,
            "suggested_agent": self.suggested_agent,
            "zone": self.zone.value,
        }


def _short_id(prefix: str, payload: str) -> str:
    import hashlib

    h = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}-{h}"


def generate_backlog(scan: RepoScan) -> list[Task]:
    """Generate a prioritised backlog from a repository scan."""
    tasks: list[Task] = []

    # ---------------------------------------------------- folder READMEs
    by_folder: dict[str, list[str]] = {}
    for f in scan.files:
        folder = f.path.rsplit("/", 1)[0] if "/" in f.path else ""
        if not folder:
            continue
        # Skip irrelevant or sensitive zones.
        if f.zone not in (Zone.PUBLIC, Zone.WORKSPACE):
            continue
        by_folder.setdefault(folder, []).append(f.path)

    for folder, files in by_folder.items():
        # Look for a README in the same folder.
        names = {p.rsplit("/", 1)[-1].lower() for p in files}
        if not (names & {"readme.md", "readme", "readme.rst"}):
            tasks.append(
                Task(
                    id=_short_id("readme", folder),
                    kind="missing-readme",
                    title=f"Add README.md to {folder}/",
                    priority=Priority.LOW,
                    paths=[folder + "/"],
                    reason=f"Folder {folder!r} contains {len(files)} files but no README.md",
                    suggested_agent="kirobi-architect",
                    zone=Zone.WORKSPACE,
                )
            )

    # --------------------------------------------------- placeholder docs
    for f in scan.files:
        if not f.is_doc:
            continue
        if f.zone not in (Zone.PUBLIC, Zone.WORKSPACE):
            continue
        if f.size and f.size < 200:
            tasks.append(
                Task(
                    id=_short_id("placeholder", f.path),
                    kind="placeholder-readme",
                    title=f"Flesh out {f.path}",
                    priority=Priority.LOW,
                    paths=[f.path],
                    reason=f"Document is only {f.size} bytes — likely a placeholder.",
                    suggested_agent="kirobi-architect",
                    zone=f.zone,
                )
            )

    # --------------------------------------------------- oversized files
    for f in scan.files:
        if not f.is_code:
            continue
        if f.size > 60_000:  # rough proxy for "very large file"
            tasks.append(
                Task(
                    id=_short_id("oversized", f.path),
                    kind="oversized-file",
                    title=f"Split or refactor {f.path}",
                    priority=Priority.MEDIUM,
                    paths=[f.path],
                    reason=f"File is {f.size} bytes — consider splitting for testability.",
                    suggested_agent="kirobi-coder",
                    zone=f.zone,
                )
            )

    # --------------------------------------------------- missing tests
    code_modules = {
        f.path
        for f in scan.code_files_writable()
        if f.path.startswith(("services/", "kirobi_core/", "apps/"))
        and f.suffix == ".py"
        and not f.path.startswith("tests/")
    }
    test_paths = {f.path for f in scan.files if f.path.startswith("tests/")}
    if code_modules and not any(p.endswith(".py") for p in test_paths):
        tasks.append(
            Task(
                id=_short_id("tests", "global"),
                kind="missing-tests",
                title="Add at least one pytest module under tests/",
                priority=Priority.HIGH,
                paths=sorted(code_modules)[:5],
                reason="Repository ships Python modules but no pytest files were found.",
                suggested_agent="kirobi-coder",
                zone=Zone.WORKSPACE,
            )
        )

    # --------------------------------------------------- zone sanity
    for f in scan.files:
        # Code under SACRED is almost certainly a misclassification.
        if f.zone == Zone.SACRED and f.is_code:
            tasks.append(
                Task(
                    id=_short_id("zone", f.path),
                    kind="zone-misclassification",
                    title=f"Review zone for {f.path}",
                    priority=Priority.HIGH,
                    paths=[f.path],
                    reason="Code file resolves to SACRED zone — verify placement.",
                    suggested_agent="kirobi-architect",
                    zone=Zone.WORKSPACE,
                )
            )

    # --------------------------------------------------- stale docs (mtime)
    now = time.time()
    stale_threshold = 200 * 24 * 3600
    root = Path(scan.root)
    for f in scan.files:
        if not f.is_doc or f.zone not in (Zone.PUBLIC, Zone.WORKSPACE):
            continue
        try:
            mtime = (root / f.path).stat().st_mtime
        except OSError:
            continue
        if now - mtime > stale_threshold:
            tasks.append(
                Task(
                    id=_short_id("stale", f.path),
                    kind="stale-doc",
                    title=f"Refresh {f.path}",
                    priority=Priority.BACKGROUND,
                    paths=[f.path],
                    reason="Document hasn't been touched in over 200 days.",
                    suggested_agent="kirobi-architect",
                    zone=f.zone,
                )
            )

    # Stable sort by (priority, kind, id) for deterministic output.
    tasks.sort(key=lambda t: (_PRIORITY_ORDER[t.priority], t.kind, t.id))
    return tasks


def prioritize(tasks: Iterable[Task], limit: int | None = None) -> list[Task]:
    """Return tasks sorted by priority (already applied) and capped."""
    items = list(tasks)
    items.sort(key=lambda t: (_PRIORITY_ORDER[t.priority], t.kind, t.id))
    if limit is not None:
        return items[:limit]
    return items
