"""Command-line entry point: ``python -m kirobi_core <subcommand>``.

Sub-commands:

==================  ============================================
``doctor``          Run environment health checks.
``scan``            Scan the repo and print a JSON summary.
``backlog``         Generate the backlog and print it as JSON.
``interview``       Run the guided interview and save a profile.
``autonomous-once`` Run one autonomous iteration (dry-run by default).
``autonomous-loop`` Repeat ``autonomous-once`` on a schedule.
``version``         Print the package version.
==================  ============================================

All sub-commands use only the standard library and refuse to perform
destructive actions outside of WORKSPACE / PUBLIC zones.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from . import __version__
from .audit import AuditLogger
from .autonomous import run_loop, run_once
from .backlog import generate_backlog, prioritize
from .config import ConfigStore
from .doctor import render, run_doctor, summarize
from .interview import run_and_save
from .registry import AgentRegistry
from .scanner import scan_repository


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root (default: current directory).",
    )


def _cmd_version(_args: argparse.Namespace) -> int:
    print(f"kirobi_core {__version__}")
    return 0


def _cmd_doctor(args: argparse.Namespace) -> int:
    results = run_doctor(args.repo_root)
    print(render(results))
    _, _, failures = summarize(results)
    return 0 if failures == 0 else 2


def _cmd_scan(args: argparse.Namespace) -> int:
    scan = scan_repository(args.repo_root)
    print(json.dumps(scan.summary(), indent=2, ensure_ascii=False))
    return 0


def _cmd_backlog(args: argparse.Namespace) -> int:
    scan = scan_repository(args.repo_root)
    tasks = prioritize(generate_backlog(scan), limit=args.limit)
    payload = [t.to_dict() for t in tasks]
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def _cmd_interview(args: argparse.Namespace) -> int:
    store = ConfigStore(args.repo_root)
    path = run_and_save(store, profile_name=args.profile)
    print(f"Profile saved at: {path}")
    return 0


def _cmd_registry(args: argparse.Namespace) -> int:
    reg = AgentRegistry.load(Path(args.repo_root) / "metadata" / "AGENTREGISTRY.md")
    print(
        json.dumps(
            [
                {
                    "name": a.name,
                    "role": a.role,
                    "model": a.model,
                    "zones": [z.value for z in a.zones],
                    "capabilities": list(a.capabilities),
                }
                for a in reg
            ],
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def _cmd_autonomous_once(args: argparse.Namespace) -> int:
    audit = AuditLogger(Path(args.repo_root) / "kirobi-core" / "core-events.log")
    report = run_once(
        args.repo_root,
        dry_run=not args.execute,
        limit=args.limit,
        audit=audit,
        write_report=not args.no_report,
    )
    print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    return 0


def _cmd_autonomous_loop(args: argparse.Namespace) -> int:
    audit = AuditLogger(Path(args.repo_root) / "kirobi-core" / "core-events.log")
    reports = run_loop(
        args.repo_root,
        interval_seconds=args.interval,
        quiet_hours=args.quiet_hours,
        iterations=args.iterations,
        dry_run=not args.execute,
        limit=args.limit,
        audit=audit,
    )
    print(f"Completed {len(reports)} iteration(s).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m kirobi_core",
        description="Local-first Kirobi orchestration & autonomy CLI.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("version", help="Print the package version.")
    p.set_defaults(func=_cmd_version)

    p = sub.add_parser("doctor", help="Run environment health checks.")
    _add_common(p)
    p.set_defaults(func=_cmd_doctor)

    p = sub.add_parser("scan", help="Scan the repository.")
    _add_common(p)
    p.set_defaults(func=_cmd_scan)

    p = sub.add_parser("backlog", help="Generate the autonomous backlog.")
    _add_common(p)
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=_cmd_backlog)

    p = sub.add_parser("registry", help="Print the agent registry.")
    _add_common(p)
    p.set_defaults(func=_cmd_registry)

    p = sub.add_parser("interview", help="Run the guided interview.")
    _add_common(p)
    p.add_argument("--profile", default="default")
    p.set_defaults(func=_cmd_interview)

    p = sub.add_parser("autonomous-once", help="Run one autonomous iteration.")
    _add_common(p)
    p.add_argument("--limit", type=int, default=10)
    p.add_argument(
        "--execute",
        action="store_true",
        help="Disable dry-run (still gated by zone safety).",
    )
    p.add_argument("--no-report", action="store_true", help="Skip writing the JSON report.")
    p.set_defaults(func=_cmd_autonomous_once)

    p = sub.add_parser("autonomous-loop", help="Run the autonomous loop.")
    _add_common(p)
    p.add_argument("--interval", type=int, default=900, help="Seconds between iterations.")
    p.add_argument("--iterations", type=int, default=None, help="Stop after N iterations.")
    p.add_argument("--quiet-hours", default="", help='Quiet hours, e.g. "22:00-07:00".')
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--execute", action="store_true")
    p.set_defaults(func=_cmd_autonomous_loop)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
