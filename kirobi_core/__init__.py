"""Kirobi Core — local-first agentic meta-orchestrator (Python package).

This package provides a runnable, dependency-light core for the Kirobi /
Disruptive OS repository. It deliberately uses only the Python standard
library so a fresh clone can run ``python -m kirobi_core`` without any
``pip install`` step.

Public submodules:

* :mod:`kirobi_core.config`        — local profile / config storage
* :mod:`kirobi_core.zones`         — five-zone security model helpers
* :mod:`kirobi_core.audit`         — append-only event logger
* :mod:`kirobi_core.registry`      — agent registry loader
* :mod:`kirobi_core.scanner`       — repository structural scan
* :mod:`kirobi_core.ingest_manifest` — safe metadata-only ingest planning
* :mod:`kirobi_core.backlog`       — task backlog generator
* :mod:`kirobi_core.orchestrator`  — minimal task router / supervisor
* :mod:`kirobi_core.keycodi`       — KeyCodi coding mission planner
* :mod:`kirobi_core.interview`     — guided onboarding interview
* :mod:`kirobi_core.autonomous`    — safe autonomous development loop
* :mod:`kirobi_core.doctor`        — environment health check
* :mod:`kirobi_core.cli`           — ``python -m kirobi_core`` entry point
"""

from __future__ import annotations

__version__ = "0.1.0"
__all__ = ["__version__"]
