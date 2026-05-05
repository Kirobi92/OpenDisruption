"""Minimal task router / supervisor.

The :class:`Orchestrator` knows about the agent registry and routes a
:class:`~kirobi_core.backlog.Task` to the most appropriate agent based
on the task's ``suggested_agent`` field, then by capability. It does
**not** execute LLM calls — that lives in the agent processes
(Flowise, voice, …). Instead, it produces a structured plan that an
operator (or the autonomous loop) can act on.

Routing is deterministic and side-effect free; every decision is
logged via the optional :class:`~kirobi_core.audit.AuditLogger`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .audit import AuditLogger
from .backlog import Task
from .registry import AgentRegistry, AgentSpec
from .zones import Zone, can_write


@dataclass
class RoutingDecision:
    """Outcome of :meth:`Orchestrator.route`."""

    task_id: str
    agent: str | None
    allowed: bool
    reason: str
    zone: Zone
    plan: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "agent": self.agent,
            "allowed": self.allowed,
            "reason": self.reason,
            "zone": self.zone.value,
            "plan": list(self.plan),
        }


# Plan templates per task kind. Plans are deliberately short, concrete
# and reviewable.
_PLAN_TEMPLATES: dict[str, list[str]] = {
    "missing-readme": [
        "Read existing files in the folder.",
        "Draft a README.md with purpose, structure and usage.",
        "Run `make doctor` to verify nothing is broken.",
    ],
    "placeholder-readme": [
        "Read the placeholder file and surrounding context.",
        "Replace placeholder content with concrete documentation.",
        "Open a PR with the diff for human approval.",
    ],
    "oversized-file": [
        "Identify cohesive sub-modules inside the file.",
        "Extract them into smaller modules with tests.",
        "Run the test suite before committing.",
    ],
    "missing-tests": [
        "Pick the smallest module from the suggested paths.",
        "Add a pytest module that covers its public API.",
        "Wire the test command into `make test`.",
    ],
    "zone-misclassification": [
        "Confirm the file's intended zone with the operator.",
        "Move the file or update zone mappings accordingly.",
        "Re-run `python -m kirobi_core scan` to verify.",
    ],
    "stale-doc": [
        "Diff the document against the current codebase.",
        "Refresh outdated sections; preserve historical notes.",
        "Bump the document's `Last Updated` field.",
    ],
}


class Orchestrator:
    """Route tasks to agents using static, auditable rules."""

    def __init__(
        self,
        registry: AgentRegistry,
        *,
        audit: AuditLogger | None = None,
    ) -> None:
        self.registry = registry
        self.audit = audit

    # ---------------------------------------------------------- routing
    def _pick_agent(self, task: Task) -> AgentSpec | None:
        if task.suggested_agent and task.suggested_agent in self.registry:
            spec = self.registry.get(task.suggested_agent)
            if spec is not None:
                return spec
        # Fall back to capability search using the task kind.
        kind_to_capability = {
            "missing-readme": "architecture",
            "placeholder-readme": "architecture",
            "oversized-file": "code",
            "missing-tests": "test",
            "zone-misclassification": "architecture",
            "stale-doc": "architecture",
        }
        cap = kind_to_capability.get(task.kind)
        if cap:
            candidates = self.registry.find_by_capability(cap)
            if candidates:
                return candidates[0]
        # Final fallback: kirobi-coder if present, else any agent.
        return self.registry.get("kirobi-coder") or next(iter(self.registry), None)

    def route(self, task: Task) -> RoutingDecision:
        """Compute a routing decision for *task* (no side effects)."""
        agent = self._pick_agent(task)
        write_decision = can_write(task.paths[0]) if task.paths else can_write(".")
        if agent is None:
            decision = RoutingDecision(
                task_id=task.id,
                agent=None,
                allowed=False,
                reason="No agent available in registry.",
                zone=task.zone,
            )
        elif not agent.can_access(task.zone):
            decision = RoutingDecision(
                task_id=task.id,
                agent=agent.name,
                allowed=False,
                reason=f"Agent {agent.name!r} cannot access zone {task.zone.value}.",
                zone=task.zone,
            )
        elif not write_decision.allowed:
            decision = RoutingDecision(
                task_id=task.id,
                agent=agent.name,
                allowed=False,
                reason=(
                    f"Write to path {task.paths[0]!r} ({write_decision.zone.value}) "
                    "requires human approval."
                ) if task.paths else write_decision.reason,
                zone=task.zone,
            )
        else:
            decision = RoutingDecision(
                task_id=task.id,
                agent=agent.name,
                allowed=True,
                reason=f"Routed to {agent.name} ({agent.role}).",
                zone=task.zone,
                plan=list(_PLAN_TEMPLATES.get(task.kind, ["Investigate task and propose plan."])),
            )

        if self.audit is not None:
            self.audit.log(
                "task.routed",
                actor="kirobi-core",
                zone=task.zone.value,
                data={
                    "task_id": task.id,
                    "kind": task.kind,
                    "agent": decision.agent,
                    "allowed": decision.allowed,
                    "reason": decision.reason,
                },
            )
        return decision

    def route_all(self, tasks: Iterable[Task]) -> list[RoutingDecision]:
        return [self.route(t) for t in tasks]
