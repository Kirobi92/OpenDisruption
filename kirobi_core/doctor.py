"""``make doctor`` — environment health check.

Runs a sequence of inexpensive, read-only probes and reports a pass /
warn / fail status. Designed to be the *first* thing a user runs after
cloning, before any Docker stack is started.
"""

from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

# The status field uses a small set of strings so callers can colour
# them or filter on them without importing an enum.
PASS = "pass"
WARN = "warn"
FAIL = "fail"


@dataclass
class CheckResult:
    name: str
    status: str  # PASS / WARN / FAIL
    detail: str = ""

    def to_line(self) -> str:
        symbol = {"pass": "✓", "warn": "⚠", "fail": "✗"}.get(self.status, "?")
        return f"  {symbol} [{self.status.upper():4}] {self.name}: {self.detail}"


Check = Callable[[Path], CheckResult]


def check_python_version(_root: Path) -> CheckResult:
    major, minor = sys.version_info[:2]
    detail = f"Python {major}.{minor}.{sys.version_info.micro}"
    if (major, minor) < (3, 10):
        return CheckResult("python-version", FAIL, detail + " (>= 3.10 required)")
    return CheckResult("python-version", PASS, detail)


def check_env_example(root: Path) -> CheckResult:
    p = root / ".env.example"
    if not p.is_file():
        return CheckResult("env-example", FAIL, ".env.example missing")
    return CheckResult("env-example", PASS, str(p.relative_to(root)))


def check_env_file(root: Path) -> CheckResult:
    p = root / ".env"
    if not p.is_file():
        return CheckResult("env-file", WARN, ".env not found — run `make init` to create it")
    # Refuse to read content; just confirm it exists.
    return CheckResult("env-file", PASS, ".env present")


def check_makefile(root: Path) -> CheckResult:
    p = root / "Makefile"
    if not p.is_file():
        return CheckResult("makefile", FAIL, "Makefile missing")
    return CheckResult("makefile", PASS, "Makefile present")


def check_docker(_root: Path) -> CheckResult:
    if shutil.which("docker") is None:
        return CheckResult("docker", WARN, "docker not found in PATH (optional for dry-run)")
    return CheckResult("docker", PASS, "docker available")


def check_docker_compose(root: Path) -> CheckResult:
    p = root / "docker-compose.yml"
    if not p.is_file():
        return CheckResult("docker-compose", FAIL, "docker-compose.yml missing")
    return CheckResult("docker-compose", PASS, "docker-compose.yml present")


def check_agent_registry(root: Path) -> CheckResult:
    p = root / "metadata" / "AGENTREGISTRY.md"
    if not p.is_file():
        return CheckResult("agent-registry", WARN, "metadata/AGENTREGISTRY.md missing — fallback registry will be used")
    return CheckResult("agent-registry", PASS, "metadata/AGENTREGISTRY.md present")


def check_kirobi_core_dir(root: Path) -> CheckResult:
    p = root / "kirobi-core"
    if not p.is_dir():
        return CheckResult("kirobi-core-dir", WARN, "kirobi-core/ folder missing")
    return CheckResult("kirobi-core-dir", PASS, "kirobi-core/ present")


def check_no_committed_secrets(root: Path) -> CheckResult:
    """Quick scan for files that look like committed secrets."""
    suspicious = []
    for pattern in ("*.key", "*.pem", "*.p12", "*.pfx"):
        suspicious.extend(root.rglob(pattern))
    # Only count those tracked outside of common ignore dirs.
    suspicious = [
        s
        for s in suspicious
        if ".git" not in s.parts
        and "node_modules" not in s.parts
        and "venv" not in s.parts
    ]
    if suspicious:
        return CheckResult(
            "secrets-scan",
            WARN,
            f"Found {len(suspicious)} candidate secret file(s); review before committing",
        )
    return CheckResult("secrets-scan", PASS, "no obvious key/cert files found")


def check_writable_reports_dir(root: Path) -> CheckResult:
    p = root / ".kirobi" / "reports"
    try:
        p.mkdir(parents=True, exist_ok=True)
        return CheckResult("reports-dir", PASS, str(p.relative_to(root)))
    except OSError as e:
        return CheckResult("reports-dir", FAIL, f"cannot create reports dir: {e}")


DEFAULT_CHECKS: tuple[Check, ...] = (
    check_python_version,
    check_env_example,
    check_env_file,
    check_makefile,
    check_docker_compose,
    check_docker,
    check_agent_registry,
    check_kirobi_core_dir,
    check_writable_reports_dir,
    check_no_committed_secrets,
)


def run_doctor(root: Path | str = ".", checks: tuple[Check, ...] = DEFAULT_CHECKS) -> list[CheckResult]:
    """Run all *checks* and return their results."""
    root_path = Path(root)
    results: list[CheckResult] = []
    for check in checks:
        try:
            results.append(check(root_path))
        except Exception as exc:  # noqa: BLE001 — doctor must never raise
            results.append(CheckResult(check.__name__, FAIL, f"check raised: {exc!r}"))
    return results


def summarize(results: list[CheckResult]) -> tuple[int, int, int]:
    """Return ``(passes, warnings, failures)``."""
    p = sum(1 for r in results if r.status == PASS)
    w = sum(1 for r in results if r.status == WARN)
    f = sum(1 for r in results if r.status == FAIL)
    return p, w, f


def render(results: list[CheckResult]) -> str:
    """Pretty-print results for the CLI."""
    lines = ["Kirobi Doctor — Health Check", "=" * 30]
    for r in results:
        lines.append(r.to_line())
    p, w, f = summarize(results)
    lines.append("")
    lines.append(f"Summary: {p} pass · {w} warn · {f} fail")
    return os.linesep.join(lines)
