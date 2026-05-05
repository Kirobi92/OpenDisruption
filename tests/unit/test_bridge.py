"""Tests for kirobi_core.bridge — backlog ↔ supervisor adapter."""
from __future__ import annotations

from kirobi_core.backlog import Priority, Task
from kirobi_core.bridge import (
    backlog_for_supervisor,
    iter_supervisor_tasks,
    supervisor_dict_to_task_summary,
    task_to_supervisor_dict,
)
from kirobi_core.zones import Zone


def _sample(priority: Priority = Priority.HIGH) -> Task:
    return Task(
        id="t-1",
        kind="missing-readme",
        title="Add README to services/api",
        reason="No README.md exists",
        priority=priority,
        paths=("services/api",),
        zone=Zone.WORKSPACE,
        suggested_agent="kirobi-architect",
    )


def test_task_to_supervisor_dict_has_expected_shape():
    payload = task_to_supervisor_dict(_sample())
    assert payload["name"] == "Add README to services/api"
    assert payload["priority"] == "high"
    assert payload["agent"] == "kirobi-architect"
    md = payload["metadata"]
    assert md["kirobi_core_task_id"] == "t-1"
    assert md["kind"] == "missing-readme"
    assert md["paths"] == ["services/api"]
    assert md["zone"] == "WORKSPACE"
    assert md["source"] == "kirobi_core.backlog"
    assert "created_at" in md


def test_priority_mapping_is_total():
    for prio in Priority:
        payload = task_to_supervisor_dict(_sample(priority=prio))
        assert payload["priority"] in {"critical", "high", "medium", "low", "background"}


def test_backlog_for_supervisor_eager_and_lazy_match():
    tasks = [_sample(), _sample()]
    assert backlog_for_supervisor(tasks) == list(iter_supervisor_tasks(tasks))


def test_supervisor_dict_to_task_summary_round_trip():
    payload = task_to_supervisor_dict(_sample())
    sup_row = {
        "id": "sup-42",
        "name": payload["name"],
        "priority": payload["priority"],
        "status": "pending",
        "assigned_agent": payload["agent"],
        "metadata": payload["metadata"],
    }
    summary = supervisor_dict_to_task_summary(sup_row)
    assert summary["id"] == "sup-42"
    assert summary["kirobi_core_task_id"] == "t-1"
    assert summary["agent"] == "kirobi-architect"
