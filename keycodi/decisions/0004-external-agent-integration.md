---
zone: WORKSPACE
created_by: keycodi
created_at: 2026-05-09
reviewed_by: pending
version: 1.0
---

# ADR 0004 — External Agent Integration: hermes-runtime + openclaw-gateway + aionui-cockpit

**Datum:** 2026-05-09
**Status:** accepted (Phasen-Override durch Sven)
**Phase:** 4.5 (parallele Spur, eigener Track)
**Sven-Sign-off:** im Konversations-Auftrag erteilt ("LETS GOOOO")

---

## Kontext

Sven hat drei externe Open-Source-Projekte zur Integration ins lokale Ökosystem
benannt. Alle drei laufen ausschließlich gegen lokale Modelle (Ollama).

| Projekt | Upstream | Sprache | Docker | Ollama nativ |
|---|---|---|---|---|
| `hermes-agent` | `NousResearch/hermes-agent` | Python + Node | ✅ offiziell | ✅ via `custom`-Provider |
| `openclaw` | `openclaw/openclaw` | TypeScript/Node | ✅ offiziell | ✅ via `host.docker.internal` oder Service-DNS |
| `AionUi` | `iOfficeAI/AionUi` | Electron + React | ❌ keine Unterstützung | ✅ via Custom-Plattform |

Reihenfolge-Bruch: Roadmap-Phase 4 (KIDI/KEYBRODI) ist noch nicht abgeschlossen.
Sven hat Phasen-Override erteilt, weil die drei Tools keine harten Abhängigkeiten
zur KIDI-Synthese haben und unabhängig parallel laufen können.

## Entscheidung

### Skill- und Aufgabenverteilung

| Tool → Agent | Rolle im Ökosystem | Zonen (in/out) |
|---|---|---|
| `hermes-runtime` | Skill-Hub mit Ollama-Backend, MCP-Server, lokales Dashboard, Reasoning-Frontend | WORKSPACE / WORKSPACE |
| `openclaw-gateway` | Multi-Channel-Messaging-Bridge (Signal, WhatsApp, Discord, iMessage etc.) als parallele Schiene zum bestehenden `telegram` Service | PUBLIC + WORKSPACE / PUBLIC + WORKSPACE (hartes FAMILY_PRIVATE/SACRED-Egress-Verbot) |
| `aionui-cockpit` | Browser-Cockpit auf Sven's Host für CLI-Agents (Claude Code, Codex, Hermes, OpenClaw etc.) | WORKSPACE Admin (LAN-only, JWT) |

### Architektur-Entscheidungen

1. **Source-Beschaffung:** Git-Submodules unter `external/` mit konkreten Refs.
   Vorteile: reproducible Pin, Audit-Trail welcher Commit läuft, offline-Build
   nach einmaligem Klonen.
2. **Compose-Profile:** Neues Profile `external-agents` (default off). Verhindert
   Auto-Start und macht den Track explizit aktivierbar.
3. **AionUi:** Kein Compose-Service. Headless via Xvfb ist fragil und
   `server`-Mode verliert 10 kritische Bridges (File/Cron/MCP/Shell/etc.).
   Stattdessen `infra/scripts/install-aionui.sh` mit `--dry-run` als Default —
   installiert das offizielle `.deb` auf dem Host.
4. **Networking:** Beide Container hängen am bestehenden `kirobi-net`. Ollama
   via Service-DNS `http://ollama:11434/v1`. Hermes bricht damit das offizielle
   `network_mode: host`-Default; das ist gewünscht, damit Service-DNS funktioniert.
5. **Port-Bindings:** Wie alle anderen Services an `KIROBI_BIND_HOST` (default
   `127.0.0.1`). Caddy ist der einzige Edge.
6. **Caddy-Routes:** `/hermes/*` und `/openclaw/*` hinter `@not_edge_private`
   Gate (LAN/Tailscale only) — gleiche Schutzklasse wie Flowise/Qdrant/OpenWebUI.
7. **Storage:** Named Docker-Volumes (`hermes_data`, `openclaw_config_data`,
   `openclaw_workspace_data`). Keine Bind-Mounts ins Repo.
8. **Auth:** Hermes API-Server ist per Default off (offizielles Sicherheits-
   Default). OpenClaw-Gateway-Token wird beim ersten Start auto-generiert.

### Zonen-Boundary für openclaw-gateway

OpenClaw kann WhatsApp/iMessage/etc. erreichen. Genauso wie unser bestehender
`telegram`-Service ist der zulässige Egress-Inhalt **hart auf PUBLIC und
WORKSPACE begrenzt**. FAMILY_PRIVATE und SACRED dürfen den Container niemals
verlassen. Das wird operativ durch die fehlende Anbindung an die FAMILY_PRIVATE
Pfade durchgesetzt — der Container bekommt diese Pfade nicht gemountet.

## Konsequenzen

### Positiv
- Lokales Skill-Hub-Frontend (Hermes) macht alle Ollama-Modelle nutzbar mit
  reichem Tool-Use, ohne Cloud-Egress.
- OpenClaw verschafft uns 20+ Messaging-Bridges, ohne unseren `telegram`
  Service ablösen zu müssen.
- AionUi bringt ein Cockpit über mehrere CLI-Agents — vereinfacht Sven's
  Workflow als Operator.
- Phase 4.5 läuft parallel und blockiert Phase 4 nicht.

### Negativ / Risiken
- Hermes v0.13.0 ist EARLY ACTIVE — Pin und Update-Disziplin nötig.
- OpenClaw + Hermes haben theoretisch Egress-Pfade — dokumentations- und
  netzwerk-policy-pflichtig.
- AionUi-Installer arbeitet auf Host-Ebene — nicht containerisiert, daher
  weniger isoliert als der Rest.
- Build-Zeit von Hermes (Playwright + uv + npm) ist hoch (10+ min beim
  ersten Mal).

### Migrations- / Update-Pfad
- `git submodule update --remote external/hermes-agent` für Updates.
- Bei Breaking Changes: `git -C external/hermes-agent checkout vX.Y.Z` und
  Compose neu bauen.
- AionUi: `infra/scripts/install-aionui.sh --upgrade`.

## Routing-Tabelle (Vorbereitung für KEYBRODI Phase 4)

Sobald `kidi/keybrodi/routing_table.py` entsteht, gehören diese Einträge dazu:

```python
{
    "skill_hub_request":     "hermes-runtime",       # WORKSPACE only
    "messaging_bridge":      "openclaw-gateway",     # PUBLIC + WORKSPACE only
    "cli_agent_cockpit":     "aionui-cockpit",       # host-side, no routing target
}
```

## Referenzen

- `external/hermes-agent/Dockerfile` (Build), `external/hermes-agent/cli-config.yaml.example`
- `external/openclaw/Dockerfile`, `external/openclaw/docker-compose.yml`
- `services/hermes-runtime/`, `services/openclaw-gateway/`
- `infra/scripts/install-aionui.sh`
- `metadata/AGENTREGISTRY.md` Sektionen 21–23
- `metadata/ZONE-POLICY-MATRIX.md` (Zeilen für hermes-runtime, openclaw-gateway, aionui-cockpit)
- `docs/agent/EXTERNAL-AGENT-INTEGRATION.md`
- `keycodi/ROADMAP.md` Phase 4.5
