#!/usr/bin/env bash

set -Eeuo pipefail

usage() {
  echo "Usage: $0 [--dry-run]" >&2
}

dry_run=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      dry_run=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      exit 2
      ;;
  esac
  shift
done

if ! docker compose ps auth >/dev/null 2>&1; then
  echo "✗ Auth service is not available via docker compose" >&2
  exit 1
fi

docker compose exec -T auth python - "$dry_run" <<'PY'
import asyncio
import os
import sys

import asyncpg
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
dry_run = sys.argv[1] == "1"
username = os.getenv("KIROBI_DEFAULT_USER", "").strip()
password = os.getenv("KIROBI_DEFAULT_PASSWORD", "").strip()

if not username or not password:
    raise SystemExit("✗ KIROBI_DEFAULT_USER or KIROBI_DEFAULT_PASSWORD is empty")


async def main() -> None:
    database_url = (
        f"postgresql://{os.getenv('POSTGRES_USER', 'kirobi')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'changeme')}@"
        f"{os.getenv('POSTGRES_HOST', 'postgres')}:"
        f"{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.getenv('POSTGRES_DB', 'kirobi')}"
    )
    conn = await asyncpg.connect(database_url)
    try:
        row = await conn.fetchrow(
            "SELECT id, password_hash FROM users WHERE username = $1",
            username,
        )
        if row is None:
            raise SystemExit(f"✗ Bootstrap user '{username}' was not found")

        if pwd_context.verify(password, row["password_hash"]):
            print("✓ Bootstrap password already matches configured default")
            return

        if dry_run:
            print("→ Dry-run: bootstrap password would be reset to the configured default")
            return

        await conn.execute(
            "UPDATE users SET password_hash = $1 WHERE id = $2",
            pwd_context.hash(password),
            row["id"],
        )
        print("✓ Bootstrap password reset to configured default")
    finally:
        await conn.close()


asyncio.run(main())
PY