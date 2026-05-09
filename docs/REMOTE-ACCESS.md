# Remote Access — LAN + Tailscale Web UI

**Zone:** WORKSPACE
**Status:** Phase 0 decision recorded; runtime routes configured at the Caddy edge
**Last Updated:** 2026-05-07

---

## Decision

Sven requested comfortable access from the local network and from anywhere via Tailscale. The safest stable option is:

> **Expose exactly one edge: Caddy on port 80/443. Keep every backend service bound to `127.0.0.1` by default. Use Tailscale private networking, not Tailscale Funnel, for remote access.**

This keeps PostgreSQL, Qdrant, Ollama, Flowise, Open WebUI, auth and API off the public internet while still making the user-facing Web UI reachable from LAN and Tailnet devices.

---

## Access model

| Layer | Bind / Access | Purpose |
|---|---:|---|
| `caddy` | `${KIROBI_PROXY_BIND_HOST:-0.0.0.0}:80/443` | The only LAN/Tailscale entry point |
| `web` | `${KIROBI_BIND_HOST:-127.0.0.1}:${WEB_PORT:-3002}` | Local debug only; canonical access through Caddy |
| `auth`, `api`, `voice` | `${KIROBI_BIND_HOST:-127.0.0.1}:...` | API backends behind Caddy |
| `open-webui`, `flowise`, `qdrant` | `${KIROBI_BIND_HOST:-127.0.0.1}:...` | Admin/workbench UIs reached through Caddy paths |
| `postgres`, `ollama` | `${KIROBI_BIND_HOST:-127.0.0.1}:...` | Never exposed through Caddy as raw admin ports |

Tailscale clients use the same Caddy routes via the host's Tailscale IP or MagicDNS name. No port-forwarding on the router is required.

---

## URLs

Start the central Web UI:

```bash
make webui-up
```

Then open one of:

```text
http://kirobi.local/status
https://kirobi.local/status
http://<LAN-IP>/status
http://<tailscale-magicdns>/status
http://<tailscale-ip>/status
```

`make webui-url` prints the detected URLs. `make tailscale-url` prints the status URL, `make tailscale-doctor` checks whether this host is cleanly joined to the Tailnet, and `make tailscale-services` prints the useful OpenDisruption surfaces behind the Caddy edge.

---

## Central routes

| Route | Backend | Guard |
|---|---|---|
| `/` / `/chat` / `/status` | `web:3000` | PWA login / JWT |
| `/search` / `/upload` / `/settings` | `web:3000` | MVP knowledge and account flows |
| `/dashboard/` / `/dashboard/tasks` / `/dashboard/services` | `dashboard:3003` | Operator/admin surfaces |
| `/api/auth/*` | `auth:8000` | Auth service |
| `/api/*` | `api:8000` | JWT for protected endpoints |
| `/voice/*` | `voice-processing:8001` | Edge-only route |
| `/open-webui/` | `open-webui:8080` | LAN/Tailscale only + Open WebUI login |
| `/flowise/` | `flowise:3000` | LAN/Tailscale only + Flowise credentials |
| `/qdrant/dashboard` | `qdrant:6333` | LAN/Tailscale only; diagnostic use |

Caddy rejects admin/workbench routes for clients outside private LAN ranges and Tailscale `100.64.0.0/10`.

---

## Tailscale setup (host-level, not committed secrets)

On the host that runs Docker:

```bash
make tailscale-doctor
make tailscale-connect
# danach bewusst anwenden:
sudo --preserve-env=TAILSCALE_AUTH_KEY,TAILSCALE_HOSTNAME,TAILSCALE_SSH,TAILSCALE_ACCEPT_DNS,TAILSCALE_ADVERTISE_TAGS \
  bash infra/scripts/tailscale-connect.sh --apply
# optional, if available in your plan:
sudo tailscale set --auto-update
make tailscale-services
```

The helper reads a fresh `TAILSCALE_AUTH_KEY` only from the local `.env`. Never commit that value and never paste a live key into repository files.

Recommended Tailnet settings:

- Enable MagicDNS.
- Do **not** enable Funnel for OpenDisruption.
- Restrict device access via Tailscale ACLs to Sven/family devices.
- Prefer Tailscale SSH over opening SSH on the LAN.
- Keep `KIROBI_BIND_HOST=127.0.0.1`; only Caddy should remain reachable over the Tailnet.

---

## Environment knobs

`.env.example` now documents:

```env
KIROBI_ACCESS_MODE=lan-tailscale
KIROBI_TAILSCALE_HOST=
KIROBI_BIND_HOST=127.0.0.1
KIROBI_PROXY_BIND_HOST=0.0.0.0
TAILSCALE_AUTH_KEY=
TAILSCALE_HOSTNAME=
TAILSCALE_SSH=true
TAILSCALE_ACCEPT_DNS=false
KIROBI_TELEGRAM_WEB_BASE_URL=
```

Keep `KIROBI_BIND_HOST=127.0.0.1` for the safest default. Only Caddy should be reachable from LAN/Tailscale.
For Telegram URL buttons, set `KIROBI_TELEGRAM_WEB_BASE_URL` explicitly to the MagicDNS URL you actually want to open from mobile devices.

---

## Security notes

- Do not expose ports `11434`, `6333`, `5432`, `3001`, `3000`, `8002`, `8003`, `8001` directly on the router.
- Do not use Tailscale Funnel for FAMILY_PRIVATE/SACRED workflows.
- Use strong first-run values for `JWT_SECRET_KEY`, `OPENWEBUI_SECRET_KEY`, `FLOWISE_PASSWORD`, `POSTGRES_PASSWORD`.
- `KIROBI_PUBLIC_ORIGINS` may remain empty: auth/api now allow localhost, `.local`, RFC1918 LAN IPs and Tailscale `100.64.0.0/10` by safe regex instead of wildcard CORS.
- Treat `/open-webui/`, `/flowise/` and `/qdrant/dashboard` as admin/workbench routes: reachable over Tailscale, but not for public sharing.

---

## External Agent Track (Phase 4.5)

Wenn Profile `external-agents` aktiv ist (`make external-up`), gelten die gleichen Regeln:

- **Hermes Dashboard:** `https://kirobi.local/hermes/` — gated durch `@not_edge_private`. Zugriff nur aus LAN (RFC1918) oder Tailscale (`100.64.0.0/10`).
- **OpenClaw Gateway:** `https://kirobi.local/openclaw/` — gleiche Schutzklasse.
- **AionUi Cockpit:** läuft host-seitig auf `127.0.0.1:25808`. **Nicht** über Caddy exponiert. Zugriff nur via SSH-Tunnel oder lokaler Browser auf dem Host:
  ```bash
  ssh -L 25808:127.0.0.1:25808 sven@kirobi.local
  ```

Der Caddy-Matcher `@not_edge_private` lebt in `infra/caddy/Caddyfile`. Wenn ein neues Tailscale-CIDR oder Cloud-VPN dazukommt, hier ergänzen — und nur dort.
