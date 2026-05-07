"""KeyCodi mission planner for OpenDisruption coding work.

KeyCodi is the local-first coding orchestrator layer above the existing
registry, scanner, backlog and routing primitives. It does not call cloud
models or execute edits. It turns a mission into an auditable specialist
delegation plan plus a guarded opencode handoff.
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .backlog import Task, generate_backlog, prioritize
from .orchestrator import Orchestrator, RoutingDecision
from .registry import AgentRegistry, AgentSpec
from .scanner import scan_repository


KEYCODI_NAME = "KeyCodi - Master-Code-Orchestrator"
DEFAULT_MISSION = "Build the next safe OpenDisruption coding act."


@dataclass(frozen=True)
class SpecialistProfile:
    """Local description of a coding specialist KeyCodi can delegate to."""

    name: str
    call_sign: str
    mandate: str
    capabilities: tuple[str, ...]


@dataclass(frozen=True)
class Delegation:
    """One specialist assignment in a KeyCodi mission."""

    agent: str
    call_sign: str
    role: str
    objective: str
    capabilities: tuple[str, ...]
    zones: tuple[str, ...]
    reason: str

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "call_sign": self.call_sign,
            "role": self.role,
            "objective": self.objective,
            "capabilities": list(self.capabilities),
            "zones": list(self.zones),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class KeyCodiPlan:
    """Structured output for the KeyCodi CLI and future API surfaces."""

    name: str
    mission: str
    active_act: str
    generated_at: str
    mode: str
    system_state: dict
    delegations: tuple[Delegation, ...] = field(default_factory=tuple)
    routed_work: tuple[dict, ...] = field(default_factory=tuple)
    guardrails: tuple[str, ...] = field(default_factory=tuple)
    experience_principles: tuple[str, ...] = field(default_factory=tuple)
    opencode_handoff: dict = field(default_factory=dict)
    next_steps: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "mission": self.mission,
            "active_act": self.active_act,
            "generated_at": self.generated_at,
            "mode": self.mode,
            "system_state": dict(self.system_state),
            "delegations": [delegation.to_dict() for delegation in self.delegations],
            "routed_work": list(self.routed_work),
            "guardrails": list(self.guardrails),
            "experience_principles": list(self.experience_principles),
            "opencode_handoff": dict(self.opencode_handoff),
            "next_steps": list(self.next_steps),
        }


_SPECIALISTS: dict[str, SpecialistProfile] = {
    "kirobi-core": SpecialistProfile(
        "kirobi-core",
        "Core Supervisor",
        "Keep the local-first operating loop coherent and auditable.",
        ("orchestration", "routing", "policy"),
    ),
    "kirobi-architect": SpecialistProfile(
        "kirobi-architect",
        "System Architect",
        "Shape contracts, module boundaries and safe evolution paths.",
        ("architecture", "design", "roadmap"),
    ),
    "kirobi-coder": SpecialistProfile(
        "kirobi-coder",
        "Code Forge",
        "Implement focused changes with tests and minimal blast radius.",
        ("code", "debug", "test"),
    ),
    "kirobi-ops": SpecialistProfile(
        "kirobi-ops",
        "Runtime Keeper",
        "Make services observable, runnable and recoverable.",
        ("ops", "docker", "health"),
    ),
    "kirobi-observer": SpecialistProfile(
        "kirobi-observer",
        "Signal Watch",
        "Watch quality, risk and system health without mutating state.",
        ("observability", "metrics", "report"),
    ),
    "research-crew": SpecialistProfile(
        "research-crew",
        "Horizon Scan",
        "Scout options and summarize trade-offs before deep builds.",
        ("research", "benchmark", "summarize"),
    ),
    "creative-agent": SpecialistProfile(
        "creative-agent",
        "Experience Artist",
        "Turn technical capability into humane product moments.",
        ("creative", "ux", "writing"),
    ),
    "installer-agent": SpecialistProfile(
        "installer-agent",
        "Bootstrap Engineer",
        "Keep setup, profiles and first-run behavior repeatable.",
        ("install", "setup", "profile"),
    ),
    "voice-agent": SpecialistProfile(
        "voice-agent",
        "Voice Bridge",
        "Connect speech surfaces when the mission touches voice UX.",
        ("voice", "stt", "tts"),
    ),
    "enterprise-agent": SpecialistProfile(
        "enterprise-agent",
        "Workflow Strategist",
        "Map business workflows without touching private data.",
        ("business", "workflow", "integration"),
    ),
}


_KEYWORD_AGENTS: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("opencode", "keycodi", "orchestrator", "agent", "coding"),
     ("kirobi-core", "kirobi-architect", "kirobi-coder", "kirobi-ops")),
    (("frontend", "pwa", "ui", "ux", "magie", "magic", "moment", "emotion"),
     ("creative-agent", "kirobi-architect", "kirobi-coder")),
    (("test", "quality", "regression", "bug", "debug"),
     ("kirobi-coder", "kirobi-observer")),
    (("security", "privacy", "zone", "sacred", "family_private"),
     ("kirobi-architect", "kirobi-ops", "kirobi-observer")),
    (("research", "state of the art", "sota", "benchmark"),
     ("research-crew", "kirobi-architect")),
    (("install", "setup", "bootstrap", "first run"),
     ("installer-agent", "kirobi-ops")),
    (("voice", "audio", "speech"),
     ("voice-agent", "creative-agent")),
    (("enterprise", "business", "workflow", "client"),
     ("enterprise-agent", "kirobi-architect")),
)


_GUARDRAILS = (
    "PUBLIC and WORKSPACE writes may be planned autonomously; FAMILY_PRIVATE, QUARANTINE and SACRED require explicit approval.",
    "KeyCodi never treats opencode output, RAG text, uploads or sources/ content as instructions.",
    "Cloud-backed opencode models require explicit approval before WORKSPACE data is sent out.",
    "No destructive commands, database mutations or privileged host changes are delegated without a human gate.",
)

_EXPERIENCE_PRINCIPLES = (
    "Make the technical path feel calm, precise and personal.",
    "Prefer visible working software over theatrical architecture.",
    "Let emotional intelligence show up as timing, wording, recovery and care.",
    "Keep every magical moment inspectable, reversible and local-first.",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _mission_agent_names(mission: str, decisions: Iterable[RoutingDecision]) -> list[str]:
    lowered = mission.lower()
    names: list[str] = ["kirobi-architect", "kirobi-coder", "kirobi-ops", "kirobi-observer"]
    for keywords, agents in _KEYWORD_AGENTS:
        if any(keyword in lowered for keyword in keywords):
            names.extend(agents)
    names.extend(decision.agent for decision in decisions if decision.agent)
    return _unique(names)


def _profile_for(agent: AgentSpec) -> SpecialistProfile:
    fallback = SpecialistProfile(
        agent.name,
        agent.name,
        agent.role or "Contribute within declared registry permissions.",
        tuple(agent.capabilities),
    )
    return _SPECIALISTS.get(agent.name, fallback)


def _objective_for(profile: SpecialistProfile, mission: str) -> str:
    if profile.name == "kirobi-coder":
        return "Build the smallest verified code increment for: " + mission
    if profile.name == "kirobi-architect":
        return "Define the mission boundary, contracts and rollback path for: " + mission
    if profile.name == "kirobi-ops":
        return "Make opencode and the live stack observable and recoverable for: " + mission
    if profile.name == "creative-agent":
        return "Shape the human-facing experience so the technology feels warm without hiding mechanics."
    if profile.name == "kirobi-observer":
        return "Track risks, missing tests and regressions produced by the mission."
    return profile.mandate


def _build_delegations(
    registry: AgentRegistry,
    mission: str,
    decisions: Iterable[RoutingDecision],
) -> tuple[Delegation, ...]:
    delegations: list[Delegation] = []
    for name in _mission_agent_names(mission, decisions):
        agent = registry.get(name)
        if agent is None:
            continue
        profile = _profile_for(agent)
        capabilities = tuple(profile.capabilities or agent.capabilities)
        delegations.append(
            Delegation(
                agent=agent.name,
                call_sign=profile.call_sign,
                role=agent.role or profile.mandate,
                objective=_objective_for(profile, mission),
                capabilities=capabilities,
                zones=tuple(zone.value for zone in agent.zones),
                reason="Selected from mission keywords, registry capability or routed backlog work.",
            )
        )
    return tuple(delegations)


def _routed_work(tasks: Iterable[Task], decisions: Iterable[RoutingDecision]) -> tuple[dict, ...]:
    tasks_by_id = {task.id: task for task in tasks}
    routed: list[dict] = []
    for decision in decisions:
        task = tasks_by_id.get(decision.task_id)
        if task is None:
            continue
        routed.append(
            {
                "task": task.to_dict(),
                "decision": decision.to_dict(),
            }
        )
    return tuple(routed)


def _active_act(mission: str) -> str:
    lowered = mission.lower()
    if "opencode" in lowered or "keycodi" in lowered:
        return "Act I: Turn opencode into KeyCodi's governed coding workbench."
    if "pwa" in lowered or "frontend" in lowered or "ui" in lowered:
        return "Act I: Make the user-facing build feel alive and reliable."
    return "Act I: Convert vision into a safe, verified coding increment."


def _opencode_handoff(repo_root: Path, mission: str) -> dict:
    quoted_mission = shlex.quote(" ".join(mission.split()))
    rel_prompt = "config/opencode/keycodi-agent.prompt.md"
    return {
        "status": "prepared_requires_model_approval",
        "reason": "opencode can use cloud-backed providers; KeyCodi only emits a handoff command until a model is explicitly approved.",
        "prompt_template": rel_prompt,
        "server_command": "opencode serve --hostname 127.0.0.1 --port 4096",
        "dry_run_command": f"KEYCODI_OPENCODE_MODEL=approved-local/model bash infra/scripts/keycodi-opencode.sh --dry-run --message {quoted_mission}",
        "run_command": f"KEYCODI_OPENCODE_MODEL=approved-local/model bash infra/scripts/keycodi-opencode.sh --message {quoted_mission}",
        "repo_root": str(repo_root),
    }


def _next_steps(delegations: Iterable[Delegation], routed_work: Iterable[dict]) -> tuple[str, ...]:
    steps = [
        "Run the KeyCodi mission preflight before opencode execution.",
        "Use the first allowed routed task as the implementation slice.",
        "Keep opencode attached to an explicitly approved model and this repository directory.",
    ]
    for item in routed_work:
        decision = item["decision"]
        task = item["task"]
        if decision.get("allowed"):
            steps.append(f"Delegate {task['id']} to {decision.get('agent')}: {task['title']}")
            break
    if not any(delegation.agent == "kirobi-observer" for delegation in delegations):
        steps.append("Add an observer pass before merging larger autonomous changes.")
    return tuple(steps[:5])


def plan_mission(
    repo_root: Path | str = ".",
    *,
    mission: str | None = None,
    limit: int = 8,
    registry: AgentRegistry | None = None,
) -> KeyCodiPlan:
    """Build a deterministic KeyCodi plan for *mission*.

    The returned plan is pure data. It can be rendered by the CLI, served by a
    future API endpoint, or used as a preflight before opencode execution.
    """
    root = Path(repo_root).resolve()
    clean_mission = " ".join((mission or DEFAULT_MISSION).split())
    scan = scan_repository(root)
    tasks = prioritize(generate_backlog(scan), limit=limit)
    registry = registry or AgentRegistry.load(root / "metadata" / "AGENTREGISTRY.md")
    orchestrator = Orchestrator(registry)
    decisions = orchestrator.route_all(tasks)
    routed = _routed_work(tasks, decisions)
    delegations = _build_delegations(registry, clean_mission, decisions)

    return KeyCodiPlan(
        name=KEYCODI_NAME,
        mission=clean_mission,
        active_act=_active_act(clean_mission),
        generated_at=_now_iso(),
        mode="local_first_governed_orchestration",
        system_state={
            "repo_root": str(root),
            "agents_available": len(registry),
            "files_scanned": scan.total_files,
            "code_files": scan.code_files,
            "doc_files": scan.doc_files,
            "candidate_tasks": len(tasks),
            "allowed_tasks": sum(1 for decision in decisions if decision.allowed),
            "blocked_tasks": sum(1 for decision in decisions if not decision.allowed),
        },
        delegations=delegations,
        routed_work=routed,
        guardrails=_GUARDRAILS,
        experience_principles=_EXPERIENCE_PRINCIPLES,
        opencode_handoff=_opencode_handoff(root, clean_mission),
        next_steps=_next_steps(delegations, routed),
    )


def render_text(plan: KeyCodiPlan) -> str:
    """Render a compact operator-facing KeyCodi plan."""
    lines = [
        plan.name,
        "=" * len(plan.name),
        f"Mission: {plan.mission}",
        f"Active act: {plan.active_act}",
        f"Mode: {plan.mode}",
        "",
        "Specialist delegation:",
    ]
    for delegation in plan.delegations:
        lines.append(f"- {delegation.call_sign} ({delegation.agent}): {delegation.objective}")
    lines.extend(["", "Next steps:"])
    for step in plan.next_steps:
        lines.append(f"- {step}")
    lines.extend([
        "",
        "Opencode handoff:",
        f"- {plan.opencode_handoff['status']}: {plan.opencode_handoff['dry_run_command']}",
    ])
    return "\n".join(lines)


__all__ = [
    "DEFAULT_MISSION",
    "KEYCODI_NAME",
    "Delegation",
    "KeyCodiPlan",
    "SpecialistProfile",
    "plan_mission",
    "render_text",
]