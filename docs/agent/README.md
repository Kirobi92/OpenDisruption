# `docs/agent/` — Agent Documentation Hub

> Everything an autonomous coding agent needs to install, operate, extend
> and recover OpenDisruption / Kirobi OS. **Start here, then go deep.**

---

## Read in this order

| # | File | Purpose | When |
|---|------|---------|------|
| 1 | [`/AGENT-SYSTEM-PROMPT.md`](../../AGENT-SYSTEM-PROMPT.md) | Drop-in system prompt | Before any action |
| 2 | [`/AGENT-INSTALLATION.md`](../../AGENT-INSTALLATION.md)   | One-command install | First run |
| 3 | [`/PROJECT-ARCHITECTURE.md`](../../PROJECT-ARCHITECTURE.md) | 10-min mental model | Once |
| 4 | [`/AGENT-DECISION-MATRIX.md`](../../AGENT-DECISION-MATRIX.md) | Act / Ask / Refuse rules | Every decision |
| 5 | [`/AGENT-RECOVERY.md`](../../AGENT-RECOVERY.md) | What to do when things break | On failure |
| 6 | [`/CLAUDE.md`](../../CLAUDE.md) | Full operating constitution | Reference |
| 7 | [`/metadata/ZONE-POLICY-MATRIX.md`](../../metadata/ZONE-POLICY-MATRIX.md) | Zone authoritative reference | When classifying |

---

## The one command

```bash
curl -fsSL https://raw.githubusercontent.com/Kirobi92/OpenDisruption/main/install.sh \
  | bash -s -- --auto --yes --profile=auto
```

Behind the scenes:

```
install.sh
 ├─ detect-system.sh   → hardware/OS facts (.kirobi/install.json)
 ├─ agent-detect.sh    → who is running me?
 ├─ validate-env.sh    → after .env generation
 ├─ pull-models.sh     → Ollama model pre-fetch (skippable)
 ├─ healthcheck.sh     → final verification
 └─ summary            → next steps
```

---

## Tool inventory (`infra/scripts/`)

| Script | What it does | Common flags |
|--------|--------------|--------------|
| `bootstrap.sh`        | legacy local bootstrap (kept for compatibility) | `full|backup|check` |
| `detect-system.sh`    | hardware + OS detection | `--json`, `--shell`, `--quiet` |
| `detect-gpu.sh`       | GPU-only quick check | – |
| `agent-detect.sh`     | which agent runtime is running this? | `--json` |
| `validate-env.sh`     | check `.env` completeness, secrets, perms | `--fix`, `--quiet` |
| `init-folders.sh`     | create the zone folder layout | – |
| `init-family-profiles.sh` | seed default family profiles | – |
| `reset-default-password.sh` | resync bootstrap auth password to current `.env` default | `--dry-run` |
| `setup-mdns.sh`       | publish `kirobi.local` on the LAN | – |
| `pull-models.sh`      | pre-fetch Ollama models | – |
| `build-pwa-icons.py`  | regenerate PWA icons | – |
| `healthcheck.sh`      | one-shot health probe (exit code = truth) | – |
| `backup.sh`           | snapshot zones + DB + Qdrant | `--dry-run`, `--no-db`, `--no-vectors`, `--out=PATH` |
| `update.sh`           | safe rolling update | `--dry-run`, `--no-backup`, `--branch=NAME` |

All scripts:

- support `--help`,
- exit non-zero on any failure (`set -Eeuo pipefail`),
- are idempotent and ShellCheck-clean,
- log to stderr, real output to stdout (machine-friendly).

---

## Configuration templates (`config/templates/`)

| Template | Picks it up |
|----------|-------------|
| `compose/profile-{minimal,cpu,nvidia,amd,voice-full,production,development}.yml` | `install.sh --profile=…` writes it as `docker-compose.override.yml` |
| `env/env.minimal` | starting point for tiny boxes |
| `caddy/Caddyfile.production` | drop into `infra/caddy/` for public deploys |
| `nginx/nginx.kirobi.conf` | when corp policy requires Nginx instead of Caddy |

---

## Cheat sheet

```bash
# bootstrap (humans)
curl -fsSL https://raw.githubusercontent.com/Kirobi92/OpenDisruption/main/install.sh | bash

# bootstrap (agents, fully autonomous)
curl -fsSL https://raw.githubusercontent.com/Kirobi92/OpenDisruption/main/install.sh \
  | bash -s -- --auto --yes --profile=auto

# inspect
bash infra/scripts/detect-system.sh --json | jq
cat .kirobi/install.json | jq
make status

# operate
make up        # start
make down      # stop
make logs      # follow
make doctor    # local diagnostics

# safety
bash infra/scripts/validate-env.sh
bash infra/scripts/backup.sh
bash infra/scripts/update.sh --dry-run

# repair
bash install.sh --no-clone --auto    # re-bootstrap config (idempotent)
bash install.sh --uninstall          # remove containers (data preserved)
```

---

## Authoring conventions for new agent docs

When you add a file under `docs/agent/`:

1. Use lowercase-kebab filenames (`how-to-add-a-service.md`).
2. Start with a `> Audience:` line so other agents can route requests fast.
3. Include a **Decision matrix excerpt** if the topic involves zone changes.
4. Include a **Recovery note** if the topic involves destructive ops.
5. Link back here from the table at the top of this file.

---

## Additional docs

| File | Purpose |
|------|---------|
| [`opencode-role.md`](./opencode-role.md) | define the safe role of the compose-adjacent `kirobi-opencode` UI |
| [`keycodi-orchestrator.md`](./keycodi-orchestrator.md) | operate KeyCodi, the repo-owned coding mission orchestrator |
