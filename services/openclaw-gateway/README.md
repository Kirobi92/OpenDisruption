# openclaw-gateway — Wrapper für openclaw/openclaw

**Zone:** PUBLIC + WORKSPACE · **Profile:** `external-agents` · **Upstream:** [`openclaw/openclaw`](https://github.com/openclaw/openclaw)

Multi-Channel-Messaging-Bridge zusätzlich zum bestehenden `telegram` Service.

## Zonen-Boundary (HART)

OpenClaw darf nur PUBLIC und WORKSPACE Egress transportieren. FAMILY_PRIVATE
und SACRED Pfade werden dem Container **nicht** gemountet.

## Build & Start

```bash
git submodule update --init --recursive external/openclaw
make external-up
```

## Konfiguration

- Volumes: `openclaw_config_data` (~/.openclaw), `openclaw_workspace_data`
- Gateway-Token: `OPENCLAW_GATEWAY_TOKEN` in `.env` (auto-generiert wenn leer)
- Onboarding interaktiv:
  ```bash
  docker compose --profile external-agents exec openclaw-gateway \
    node dist/index.js onboard
  ```

## Sicherheits-Defaults

- Bind: `127.0.0.1:18789/18790`, Caddy via `/openclaw/*` hinter `@not_edge_private`
- `cap_drop: [NET_RAW, NET_ADMIN]` + `no-new-privileges`
- Sandbox-Isolation deaktiviert (würde docker.sock-Mount erfordern)
