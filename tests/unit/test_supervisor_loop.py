"""
Unit-Tests für den verbesserten autonomen Task-Loop des Supervisors.

Testet:
- Retry-Logik mit exponentiellem Backoff (max 3 Versuche)
- Dead-Letter nach 3 Fehlern
- Priority-Ordering (critical > high > medium > low > background)
- Heartbeat-Logging
"""

from __future__ import annotations

import asyncio
import json
import time as _time
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Minimal stubs so the module can be imported without asyncpg / httpx
# ---------------------------------------------------------------------------
import sys
import types

for _mod in ("asyncpg", "httpx"):
    if _mod not in sys.modules:
        sys.modules[_mod] = types.ModuleType(_mod)

# pydantic stub — provide a minimal BaseModel
if "pydantic" not in sys.modules:
    _pydantic = types.ModuleType("pydantic")

    class _BaseModel:
        def __init__(self, **kwargs: Any) -> None:
            for k, v in kwargs.items():
                setattr(self, k, v)

    _pydantic.BaseModel = _BaseModel  # type: ignore[attr-defined]
    sys.modules["pydantic"] = _pydantic

import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from services.orchestrator.supervisor import (  # noqa: E402
    KirobiSupervisor,
    MAX_RETRY_ATTEMPTS,
    RETRY_BACKOFF_BASE,
    SupervisorConfig,
    Task,
    TaskPriority,
    TaskStatus,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(coro):
    """Run a coroutine synchronously in a fresh event loop."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _make_task(
    name: str = "test-task",
    priority: TaskPriority = TaskPriority.MEDIUM,
    status: TaskStatus = TaskStatus.PENDING,
    retry_count: int = 0,
) -> Task:
    now = datetime.now()
    return Task(
        id=f"task_{name}",
        name=name,
        description=f"Description for {name}",
        priority=priority,
        status=status,
        created_at=now,
        updated_at=now,
        retry_count=retry_count,
        last_error=None,
        assigned_agent=None,
        completed_at=None,
        metadata={},
        dependencies=[],
    )


def _make_supervisor() -> KirobiSupervisor:
    """Return a supervisor with a mocked DB pool."""
    sup = KirobiSupervisor.__new__(KirobiSupervisor)
    sup.config = SupervisorConfig()
    sup.state = MagicMock()
    sup.task_queue: List[Task] = []
    sup.active_tasks: Dict[str, Task] = {}
    sup.shutdown_flag = False
    sup.stats = {
        "tasks_completed": 0,
        "tasks_failed": 0,
        "uptime_start": datetime.now(),
        "last_health_check": None,
    }
    sup._api_token = None

    # Mock DB pool
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=None)
    mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn.__aexit__ = AsyncMock(return_value=False)

    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(return_value=mock_conn)
    sup.db_pool = mock_pool

    return sup


# ---------------------------------------------------------------------------
# Tests: Priority Ordering
# ---------------------------------------------------------------------------

class TestPriorityOrdering:
    """process_task_queue soll Tasks nach Priorität sortieren."""

    def test_critical_before_low(self):
        sup = _make_supervisor()
        low_task = _make_task("low-task", TaskPriority.LOW)
        critical_task = _make_task("critical-task", TaskPriority.CRITICAL)
        sup.task_queue = [low_task, critical_task]

        executed: List[str] = []

        async def fake_execute(task: Task) -> None:
            executed.append(task.name)
            task.status = TaskStatus.COMPLETED
            sup.task_queue.remove(task)
            sup.stats["tasks_completed"] += 1

        sup.execute_task = fake_execute  # type: ignore[method-assign]
        _run(sup.process_task_queue())

        assert executed == ["critical-task"], f"Expected critical first, got {executed}"

    def test_priority_order_all_levels(self):
        """Alle fünf Prioritätsstufen werden korrekt sortiert."""
        sup = _make_supervisor()
        priorities = [
            TaskPriority.BACKGROUND,
            TaskPriority.LOW,
            TaskPriority.HIGH,
            TaskPriority.CRITICAL,
            TaskPriority.MEDIUM,
        ]
        tasks = [_make_task(p.value, p) for p in priorities]
        sup.task_queue = tasks[:]

        executed: List[str] = []

        async def fake_execute(task: Task) -> None:
            executed.append(task.priority.value)
            task.status = TaskStatus.COMPLETED
            sup.task_queue.remove(task)

        sup.execute_task = fake_execute  # type: ignore[method-assign]

        for _ in range(len(priorities)):
            _run(sup.process_task_queue())

        assert executed == ["critical", "high", "medium", "low", "background"], executed

    def test_same_priority_fifo(self):
        """Bei gleicher Priorität gilt FIFO (created_at ASC)."""
        sup = _make_supervisor()

        t1 = _make_task("first", TaskPriority.MEDIUM)
        _time.sleep(0.01)
        t2 = _make_task("second", TaskPriority.MEDIUM)
        sup.task_queue = [t2, t1]  # reversed insertion order

        executed: List[str] = []

        async def fake_execute(task: Task) -> None:
            executed.append(task.name)
            task.status = TaskStatus.COMPLETED
            sup.task_queue.remove(task)

        sup.execute_task = fake_execute  # type: ignore[method-assign]
        _run(sup.process_task_queue())
        _run(sup.process_task_queue())

        assert executed == ["first", "second"], executed


# ---------------------------------------------------------------------------
# Tests: Retry-Logik
# ---------------------------------------------------------------------------

class TestRetryLogic:
    """execute_task soll bei Fehler bis zu MAX_RETRY_ATTEMPTS wiederholen."""

    def test_retry_increments_count(self):
        sup = _make_supervisor()
        task = _make_task("retry-task")
        sup.task_queue = [task]

        async def failing_route(t: Task) -> Any:
            raise RuntimeError("simulated failure")

        sup.route_to_agent = failing_route  # type: ignore[method-assign]

        async def run():
            with patch("services.orchestrator.supervisor.asyncio.sleep", new_callable=AsyncMock):
                await sup.execute_task(task)

        _run(run())

        assert task.retry_count == 1
        assert task.last_error == "simulated failure"
        assert task.status == TaskStatus.PENDING  # back to pending for retry

    def test_dead_letter_after_max_retries(self):
        sup = _make_supervisor()
        task = _make_task("dead-task", retry_count=MAX_RETRY_ATTEMPTS - 1)
        sup.task_queue = [task]

        async def failing_route(t: Task) -> Any:
            raise RuntimeError("always fails")

        sup.route_to_agent = failing_route  # type: ignore[method-assign]
        sup.log_event = AsyncMock()

        _run(sup.execute_task(task))

        assert task.status == TaskStatus.DEAD_LETTER
        assert task.retry_count == MAX_RETRY_ATTEMPTS
        assert task not in sup.task_queue
        assert sup.stats["tasks_failed"] == 1
        sup.log_event.assert_called_once()

    def test_exponential_backoff_timing(self):
        """Backoff-Zeiten: attempt 1→1s, attempt 2→2s."""
        sleep_calls: List[float] = []

        async def fake_sleep(seconds: float) -> None:
            sleep_calls.append(seconds)

        sup = _make_supervisor()

        async def failing_route(t: Task) -> Any:
            raise RuntimeError("fail")

        sup.route_to_agent = failing_route  # type: ignore[method-assign]
        sup.log_event = AsyncMock()

        async def run():
            with patch("services.orchestrator.supervisor.asyncio.sleep", side_effect=fake_sleep):
                # Attempt 1 (retry_count 0→1, backoff = 1s)
                task = _make_task("backoff-task", retry_count=0)
                sup.task_queue = [task]
                await sup.execute_task(task)
                assert sleep_calls[-1] == pytest.approx(1.0)

                # Attempt 2 (retry_count 1→2, backoff = 2s)
                task.status = TaskStatus.PENDING
                sup.task_queue = [task]
                await sup.execute_task(task)
                assert sleep_calls[-1] == pytest.approx(2.0)

                # Attempt 3 (retry_count 2→3 = MAX → dead_letter, no sleep)
                task.status = TaskStatus.PENDING
                sup.task_queue = [task]
                prev_len = len(sleep_calls)
                await sup.execute_task(task)
                assert len(sleep_calls) == prev_len  # no sleep on dead-letter

        _run(run())

    def test_successful_task_no_retry(self):
        sup = _make_supervisor()
        task = _make_task("success-task")
        sup.task_queue = [task]

        async def ok_route(t: Task) -> Any:
            return {"status": "success"}

        sup.route_to_agent = ok_route  # type: ignore[method-assign]

        _run(sup.execute_task(task))

        assert task.status == TaskStatus.COMPLETED
        assert task.retry_count == 0
        assert task not in sup.task_queue
        assert sup.stats["tasks_completed"] == 1


# ---------------------------------------------------------------------------
# Tests: Heartbeat
# ---------------------------------------------------------------------------

class TestHeartbeat:
    def test_heartbeat_writes_to_log(self, tmp_path):
        sup = _make_supervisor()
        sup.stats["tasks_completed"] = 5
        sup.stats["tasks_failed"] = 1
        sup.task_queue = [_make_task("q1"), _make_task("q2")]

        log_file = tmp_path / "core-events.log"
        sup.config = MagicMock()
        sup.config.KIROBI_CORE_PATH = tmp_path

        _run(sup._write_heartbeat())

        content = log_file.read_text()
        assert "HEARTBEAT" in content
        assert "processed=5" in content
        assert "failed=1" in content
        assert "queue_depth=2" in content

    def test_heartbeat_tolerates_missing_dir(self):
        """Heartbeat darf nicht crashen wenn das Log-Verzeichnis fehlt."""
        sup = _make_supervisor()
        sup.config = MagicMock()
        sup.config.KIROBI_CORE_PATH = pathlib.Path("/nonexistent/path")

        # Should not raise
        _run(sup._write_heartbeat())


# ---------------------------------------------------------------------------
# Tests: TaskStatus.DEAD_LETTER existiert
# ---------------------------------------------------------------------------

class TestTaskStatusEnum:
    def test_dead_letter_in_enum(self):
        assert TaskStatus.DEAD_LETTER == "dead_letter"

    def test_all_statuses_present(self):
        values = {s.value for s in TaskStatus}
        assert "dead_letter" in values
        assert "failed" in values
        assert "pending" in values
        assert "completed" in values
