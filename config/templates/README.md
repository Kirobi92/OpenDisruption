# Configuration Templates

Re-usable, opinionated, agent-friendly templates that the installer (and
agents) drop into the right place at install time. Every template is safe
to overwrite — no host-specific values live here.

| Subdir | Used by |
|--------|---------|
| `compose/` | `install.sh` (writes `docker-compose.override.yml`) |
| `env/`     | `install.sh`, `infra/scripts/validate-env.sh` |
| `caddy/`   | `infra/caddy/` (production override) |
| `nginx/`   | optional — when Caddy is replaced by Nginx |

Naming convention: one file per profile, named `profile-<NAME>.<ext>`.

Available profiles (matches `install.sh --profile=`):

- `minimal` — Ollama + Postgres + Qdrant only
- `cpu` — full stack on CPU
- `nvidia` — full stack with NVIDIA GPU passthrough
- `amd` — full stack with ROCm passthrough
- `voice-full` — adds Whisper + Piper
- `production` — Caddy + restart policies + monitoring
- `development` — bind on `0.0.0.0`, hot-reload mounts
