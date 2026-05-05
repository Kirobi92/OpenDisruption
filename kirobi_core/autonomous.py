"""Safe autonomous development loop.

The loop deliberately defaults to **dry-run**: it produces a planned
report (scan → backlog → routing decisions → next-step) but never
modifies repository files unless explicitly opted-in *and* a write
callback is supplied. This satisfies the safety requirements from
``CLAUDE.md`` and the user's brief.

Two entry points are provided:

``run_once``
    A single iteration of ``repo_scan → backlog → prioritize → route →
    report``. Returns a structured :class:`AutonomousReport` and
    optionally writes it to disk under ``.kirobi/reports/``.

``run_loop``
    Repeats ``run_once`` every ``interval_seconds`` while honouring
    quiet hours. Designed for foreground use under ``make
    autonomous-loop`` — exits cleanly on ``KeyboardInterrupt``.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, time as dtime, timezone
from pathlib import Path
from typing import Callable, Iterable

from .audit import AuditLogger
from .backlog import Task, generate_backlog, prioritize
from .orchestrator import Orchestrator, RoutingDecision
from .registry import AgentRegistry
from .scanner import RepoScan, scan_repository
from .zones import can_write, classify, is_inside_repo

DEFAULT_REPORTS_DIR = Path(".kirobi/reports")


@dataclass
class AutonomousReport:
    """One iteration of the autonomous loop."""

    started_at: str
    finished_at: str
    dry_run: bool
    scan_summary: dict
    tasks: list[dict] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    blocked: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "dry_run": self.dry_run,
            "scan": self.scan_summary,
            "tasks": list(self.tasks),
            "decisions": list(self.decisions),
            "next_steps": list(self.next_steps),
            "blocked": list(self.blocked),
        }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_quiet_hours(spec: str) -> tuple[dtime, dtime] | None:
    """Parse ``"HH:MM-HH:MM"`` into a (start, end) tuple."""
    if not spec or "-" not in spec:
        return None
    try:
        start_s, end_s = spec.split("-", 1)
        start = dtime.fromisoformat(start_s.strip())
        end = dtime.fromisoformat(end_s.strip())
        return start, end
    except (ValueError, AttributeError):
        return None


def in_quiet_hours(now: datetime, spec: str) -> bool:
    """Return True if *now* falls inside the quiet-hours window."""
    parsed = _parse_quiet_hours(spec)
    if parsed is None:
        return False
    start, end = parsed
    current = now.time()
    if start <= end:
        return start <= current < end
    # Wrap around midnight, e.g. 22:00-07:00.
    return current >= start or current < end


def write_path_safety(repo_root: Path, target: Path) -> tuple[bool, str]:
    """Verify that *target* may be written to in autonomous mode."""
    if not is_inside_repo(repo_root, target):
        return False, "target outside repository"
    rel = target.resolve().relative_to(repo_root.resolve())
    decision = can_write(str(rel).replace("\\", "/"))
    return decision.allowed, decision.reason


def run_once(
    repo_root: Path | str = ".",
    *,
    dry_run: bool = True,
    limit: int = 10,
    audit: AuditLogger | None = None,
    write_report: bool = True,
    reports_dir: Path | str = DEFAULT_REPORTS_DIR,
    registry: AgentRegistry | None = None,
) -> AutonomousReport:
    """Execute one iteration of the autonomous loop."""
    started = _now_iso()
    root = Path(repo_root)
    audit = audit or AuditLogger(Path(repo_root) / "kirobi-core" / "core-events.log")

    audit.log("autonomous.iteration.start", data={"dry_run": dry_run, "limit": limit})

    scan = scan_repository(root)
    tasks = prioritize(generate_backlog(scan), limit=limit)
    registry = registry or AgentRegistry.load(root / "metadata" / "AGENTREGISTRY.md")
    orchestrator = Orchestrator(registry, audit=audit)
    decisions = orchestrator.route_all(tasks)

    blocked = [d.to_dict() for d in decisions if not d.allowed]
    next_steps = _derive_next_steps(tasks, decisions)

    report = AutonomousReport(
        started_at=started,
        finished_at=_now_iso(),
        dry_run=dry_run,
        scan_summary=scan.summary(),
        tasks=[t.to_dict() for t in tasks],
        decisions=[d.to_dict() for d in decisions],
        next_steps=next_steps,
        blocked=blocked,
    )

    if write_report:
        out_dir = Path(reports_dir)
        if not out_dir.is_absolute():
            out_dir = root / out_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = out_dir / f"autonomous-{ts}.json"
        out_path.write_text(
            json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        audit.log(
            "autonomous.report.written",
            data={"path": str(out_path.relative_to(root)) if is_inside_repo(root, out_path) else str(out_path)},
        )

    audit.log(
        "autonomous.iteration.end",
        data={
            "dry_run": dry_run,
            "tasks": len(tasks),
            "blocked": len(blocked),
        },
    )
    return report


def _derive_next_steps(
    tasks: Iterable[Task], decisions: Iterable[RoutingDecision]
) -> list[str]:
    by_id = {d.task_id: d for d in decisions}
    steps: list[str] = []
    for task in tasks:
        d = by_id.get(task.id)
        if d is None or not d.allowed:
            continue
        steps.append(
            f"[{task.priority.value}] {task.title} → {d.agent}"
            + (f" (paths: {', '.join(task.paths[:2])})" if task.paths else "")
        )
        if len(steps) >= 5:
            break
    return steps


def run_loop(
    repo_root: Path | str = ".",
    *,
    interval_seconds: int = 900,
    quiet_hours: str = "",
    iterations: int | None = None,
    dry_run: bool = True,
    limit: int = 10,
    audit: AuditLogger | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    now_fn: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    on_iteration: Callable[[AutonomousReport], None] | None = None,
) -> list[AutonomousReport]:
    """Run :func:`run_once` repeatedly while respecting quiet hours.

    Parameters
    ----------
    iterations:
        ``None`` means "run forever" (until ``KeyboardInterrupt``).
        Tests pass a small integer to bound the loop.
    sleep_fn / now_fn:
        Hooks for deterministic testing.
    """
    audit = audit or AuditLogger(Path(repo_root) / "kirobi-core" / "core-events.log")
    reports: list[AutonomousReport] = []
    counter = 0
    try:
        while iterations is None or counter < iterations:
            now = now_fn()
            if quiet_hours and in_quiet_hours(now, quiet_hours):
                audit.log("autonomous.quiet_hours.skip", data={"now": now.isoformat()})
            else:
                report = run_once(
                    repo_root,
                    dry_run=dry_run,
                    limit=limit,
                    audit=audit,
                )
                reports.append(report)
                if on_iteration is not None:
                    on_iteration(report)
            counter += 1
            if iterations is not None and counter >= iterations:
                break
            sleep_fn(interval_seconds)
    except KeyboardInterrupt:
        audit.log("autonomous.loop.interrupted", data={"iterations": counter})
    return reports


__all__ = [
    "AutonomousReport",
    "DEFAULT_REPORTS_DIR",
    "in_quiet_hours",
    "run_loop",
    "run_once",
    "write_path_safety",
]


# Backwards-friendly re-exports
def scan_only(repo_root: Path | str = ".") -> RepoScan:
    """Convenience helper: just return a :class:`RepoScan`."""
    return scan_repository(repo_root)
