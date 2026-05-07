"""
kidi/__main__.py
Zone: WORKSPACE

Entry-Point für `python3 -m kidi`.
Parst CLI-Argumente und startet den gewünschten Subcommand.

Verwendung:
    python3 -m kidi serve [--port PORT]
"""

import argparse
import sys


def main() -> None:
    """Haupt-Entry-Point für das kidi-Paket."""
    parser = argparse.ArgumentParser(
        prog="kidi",
        description="KeyCodi Context-DB MCP-Server",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: serve
    serve_parser = subparsers.add_parser(
        "serve",
        help="Startet den MCP-Server (stdio-Transport)",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=7700,
        help="Port (wird ignoriert, stdio-only; für Kompatibilität mit opencode.json)",
    )

    args = parser.parse_args()

    if args.command == "serve":
        from .serve import run_server
        run_server(port=args.port)
    else:
        print(f"Unbekannter Befehl: {args.command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
