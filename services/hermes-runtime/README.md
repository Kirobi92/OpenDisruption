# hermes-runtime — Wrapper für NousResearch/hermes-agent

**Zone:** WORKSPACE · **Profile:** `external-agents` · **Upstream:** [`NousResearch/hermes-agent`](https://github.com/NousResearch/hermes-agent)

Lokales Skill-Hub + Reasoning-Frontend mit Ollama-Backend.

## Build & Start

```bash
git submodule update --init --recursive external/hermes-agent
make external-up        # baut + startet hermes-runtime und openclaw-gateway
```

## Konfiguration

- Wrapper-Config: `services/hermes-runtime/config/cli-config.yaml`
- Container-Daten: Docker-Volume `hermes_data`
- Modell-Default: `HERMES_DEFAULT_MODEL` in `.env` (z. B. `llama3.1:8b`)

## Sicherheits-Defaults

- Bind: `127.0.0.1:9119` (localhost), Caddy via `/hermes/*` hinter `@not_edge_private`
- Hermes API-Server bleibt off (Default) — niemals ohne `API_SERVER_KEY` exponieren
- Egress nur Ollama im internen Compose-Netz
- Bekommt **keinen** FAMILY_PRIVATE/SACRED-Pfad gemountet
