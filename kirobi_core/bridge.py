"""Bridge between :mod:`kirobi_core` and the ``services/orchestrator`` supervisor.

The supervisor (``services/orchestrator/supervisor.py``) keeps its own
pydantic ``Task`` model so it can persist tasks to PostgreSQL. This
module converts between the stdlib :class:`kirobi_core.backlog.Task`
and the supervisor's pydantic model **without importing pydantic at
the package level** — the import is performed lazily so the rest of
``kirobi_core`` stays dependency-free.

Typical use:

>>> from kirobi_core.scanner import scan_repository
>>> from kirobi_core.backlog import generate_backlog
>>> from kirobi_core.bridge import iter_supervisor_tasks
>>> for sup_task in iter_supervisor_tasks(generate_backlog(scan_repository("."))):
...     await supervisor.create_task(sup_task.name, sup_task.description, ...)

The supervisor itself can stay loosely coupled via
:func:`backlog_for_supervisor`, which returns plain dicts safe to feed
into ``KirobiSupervisor.create_task``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Iterator

from .backlog import Priority, Task

# Map kirobi_core priorities to the strings the supervisor expects.
# (They happen to match today, but going through a map keeps the two
# enums independent.)
_PRIORITY_TO_SUPERVISOR: dict[Priority, str] = {
    Priority.CRITICAL: "critical",
    Priority.HIGH: "high",
    Priority.MEDIUM: "medium",
    Priority.LOW: "low",
    Priority.BACKGROUND: "background",
}


def task_to_supervisor_dict(task: Task) -> dict[str, Any]:
    """Serialise a :class:`Task` for ``KirobiSupervisor.create_task``.

    The returned dict matches the keyword arguments accepted by the
    supervisor's ``create_task`` method (``name``, ``description``,
    ``priority`` as string, ``agent`` and ``metadata``).
    """
    return {
        "name": task.title,
        "description": task.reason or task.title,
        "priority": _PRIORITY_TO_SUPERVISOR[task.priority],
        "agent": task.suggested_agent,
        "metadata": {
            "kirobi_core_task_id": task.id,
            "kind": task.kind,
            "paths": list(task.paths),
            "zone": task.zone.value,
            "source": "kirobi_core.backlog",
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
    }


def backlog_for_supervisor(tasks: Iterable[Task]) -> list[dict[str, Any]]:
    """Eagerly convert a backlog into supervisor-ready dicts."""
    return [task_to_supervisor_dict(t) for t in tasks]


def iter_supervisor_tasks(tasks: Iterable[Task]) -> Iterator[dict[str, Any]]:
    """Lazy variant of :func:`backlog_for_supervisor`."""
    for t in tasks:
        yield task_to_supervisor_dict(t)


def supervisor_dict_to_task_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Reduce a supervisor task dict / row to a kirobi_core-friendly summary.

    Useful for reporting back from the supervisor into autonomous
    reports without reintroducing a pydantic dependency.
    """
    return {
        "id": str(payload.get("id", "")),
        "name": str(payload.get("name", "")),
        "priority": str(payload.get("priority", "medium")),
        "status": str(payload.get("status", "pending")),
        "agent": payload.get("assigned_agent"),
        "kirobi_core_task_id": (payload.get("metadata") or {}).get("kirobi_core_task_id"),
    }
