from kirobi_core.backlog import Priority, Task
from kirobi_core.orchestrator import Orchestrator
from kirobi_core.registry import AgentRegistry, parse_registry
from kirobi_core.zones import Zone


SAMPLE = """
## 1. kirobi-core

**Rolle:** Supervisor
**Modell:** llama3.1:70b
**Zone-Zugriff:** Alle Zonen

## 2. kirobi-coder

**Rolle:** Coder
**Modell:** qwen2.5-coder:32b
**Zone-Zugriff:** PUBLIC, WORKSPACE
"""


def _registry() -> AgentRegistry:
    return AgentRegistry(parse_registry(SAMPLE))


def test_route_assigns_suggested_agent_when_present():
    orch = Orchestrator(_registry())
    task = Task(
        id="t1",
        kind="missing-tests",
        title="Add tests",
        priority=Priority.HIGH,
        paths=["kirobi_core/cli.py"],
        suggested_agent="kirobi-coder",
        zone=Zone.WORKSPACE,
    )
    decision = orch.route(task)
    assert decision.agent == "kirobi-coder"
    assert decision.allowed is True
    assert decision.plan, "expected a non-empty plan"


def test_route_blocks_sacred_zone():
    orch = Orchestrator(_registry())
    task = Task(
        id="t2",
        kind="oversized-file",
        title="Refactor",
        priority=Priority.MEDIUM,
        paths=["sacred/secret.md"],
        suggested_agent="kirobi-coder",
        zone=Zone.SACRED,
    )
    decision = orch.route(task)
    assert decision.allowed is False
    assert "sacred" in decision.reason.lower() or "approval" in decision.reason.lower()


def test_route_falls_back_when_suggested_agent_missing():
    orch = Orchestrator(_registry())
    task = Task(
        id="t3",
        kind="missing-readme",
        title="Add README",
        priority=Priority.LOW,
        paths=["services/foo/"],
        suggested_agent="does-not-exist",
        zone=Zone.WORKSPACE,
    )
    decision = orch.route(task)
    # Fallback should still pick *some* agent in the registry.
    assert decision.agent in {"kirobi-core", "kirobi-coder"}
