# Kirobi / Disruptive OS

> **Local-first, agentengesteuertes Betriebssystem & Ökosystem für Familie, Kreativität und Business**

---

## Was ist Kirobi / Disruptive OS?

Kirobi ist ein persönliches, lokal betriebenes KI-Ökosystem, das als Supervisor-Agent fungiert und alle Bereiche des Lebens von Sven Darusi koordiniert: Familie, Projekte, Business, Kreativität und Selbstentfaltung. Das System läuft vollständig on-premise auf leistungsstarker Hardware und verbindet lokale LLMs mit einem strukturierten Wissensgraphen, Workflow-Automatisierung und multimodalen Interfaces.

**Kernprinzipien:**
- 🏠 **Local-First**: Alle sensiblen Daten bleiben auf eigener Hardware
- 🤖 **Agentgesteuert**: Spezialisierte Agenten für jeden Lebensbereich
- 🔒 **Zonenbasierte Sicherheit**: 5 Sicherheitszonen (PUBLIC → SACRED)
- 🌱 **Wachsend**: Das System lernt und entwickelt sich kontinuierlich weiter
- 💡 **Integriert**: AQAL-basierter Ansatz (All Quadranten, Alle Ebenen)

---

## Schnellstart

### One-Command-Installation (empfohlen — Mensch oder Agent)

```bash
curl -fsSL https://raw.githubusercontent.com/Kirobi92/OpenDisruption/main/install.sh | bash
```

Vollständig autonom (für Coding-Agenten wie Claude, GPT, Cursor, Copilot):

```bash
curl -fsSL https://raw.githubusercontent.com/Kirobi92/OpenDisruption/main/install.sh \
  | bash -s -- --auto --yes --profile=auto
```

Der Installer erkennt OS, CPU, RAM, GPU und Agenten-Umgebung, generiert
`.env` mit zufälligen Secrets, wählt das passende Compose-Profil
(`minimal | cpu | nvidia | amd | voice-full | production | development`),
zieht alle Images, startet die Services und führt einen Healthcheck aus.
Idempotent — beliebig oft erneut ausführbar.

Details: [`AGENT-INSTALLATION.md`](AGENT-INSTALLATION.md) ·
Agenten-System-Prompt: [`AGENT-SYSTEM-PROMPT.md`](AGENT-SYSTEM-PROMPT.md) ·
Architektur: [`PROJECT-ARCHITECTURE.md`](PROJECT-ARCHITECTURE.md).

### Voraussetzungen
- Docker & Docker Compose v2+
- NVIDIA GPU mit CUDA-Support (empfohlen, optional — CPU-Fallback funktioniert)
- Mindestens 8 GB RAM (32 GB empfohlen), 20 GB freier Speicherplatz
- Linux (Ubuntu 22.04+ empfohlen) oder macOS (Apple Silicon)

### Manuelle Installation (Alternative)

```bash
git clone https://github.com/Kirobi92/OpenDisruption.git
cd OpenDisruption
cp .env.example .env
nano .env                 # Secrets anpassen
make init                 # Verzeichnisse + Image-Pull
make up                   # Services starten
make pull-models          # Ollama-Modelle herunterladen
make status               # Health prüfen
```

### Erste Schritte nach dem Start

1. **Open WebUI** unter `http://localhost:3000` aufrufen
2. **Flowise** für Workflows unter `http://localhost:3001`
3. **Qdrant Dashboard** unter `http://localhost:6333/dashboard`
4. System-Gesundheit prüfen: `make status`

### Local-First Kickstart (kein Docker nötig)

Für eine reine Python-Variante (ideal auf einem frischen Pop!_OS-Rechner
oder in CI) gibt es das Modul `kirobi_core/`:

```bash
make bootstrap         # .env anlegen + Doctor + Repo-Scan
make interview         # geführtes Onboarding (CLI, lokal)
make autonomous-once   # eine sichere Dry-Run-Iteration des Autonomy-Loops
make backlog LIMIT=5   # priorisierten Backlog ansehen
make test              # 58 Unit-Tests (stdlib only)
```

### Stack-Integration (Docker + kirobi_core)

Sobald die Docker-Services laufen (`docker compose up -d`), bindet
sich der lokale Core automatisch an sie an:

```bash
make status            # Live-Probes für Ollama / Qdrant / Postgres / API / …
make integration-test  # End-to-end Check (Tests + compose validate + Skripte)
python -m kirobi_core doctor --live   # Doctor inkl. Service-Probes
```

Der Supervisor (`services/orchestrator/supervisor.py`) erkennt
`kirobi_core` automatisch und kann seine Task-Queue aus dem Backlog
seeden — aktivieren mit `KIROBI_SEED_BACKLOG=true` in `.env`.

> **Sicherheits-Default:** alle internen Service-Ports sind via
> `KIROBI_BIND_HOST=127.0.0.1` nur auf localhost erreichbar. Der
> Reverse-Proxy unten ist die einzige Komponente, die im LAN sichtbar
> ist (Standard: `KIROBI_PROXY_BIND_HOST=0.0.0.0` auf Port 80/443).

### Family-PWA unter `kirobi.local` und im LAN

Damit Familie und Geräte sofort loslegen können, läuft Kirobi als
installierbare PWA hinter einem lokalen Caddy-Reverse-Proxy:

```bash
make pwa-icons         # PWA-Icons generieren (einmalig)
make pwa-up            # caddy + web + auth + api + postgres starten
sudo make pwa-mdns     # kirobi.local via Avahi/mDNS publizieren (einmalig)
```

Danach erreichbar unter:

| URL | Zweck |
|---|---|
| `http://kirobi.local/` | PWA aus dem Heimnetz |
| `https://kirobi.local/` | gleiche PWA mit TLS (Caddy `tls internal`) |
| `http://<LAN-IP>/` | Fallback, falls mDNS nicht verfügbar (z. B. Windows) |

Erste Anmeldung: das Auth-Service legt beim ersten Start automatisch
einen Admin-User an (Standard `sven` / Passwort aus
`KIROBI_DEFAULT_PASSWORD`). Danach sofort über die PWA ändern.

Details: siehe `DEVELOPER-RUNBOOK.md` und `infra/caddy/README.md`.

---

## Architektur-Übersicht

```
┌─────────────────────────────────────────────────────────┐
│                    KIROBI CORE                          │
│              (Supervisor Agent)                         │
├──────────┬──────────┬──────────┬──────────┬────────────┤
│ Architect│  Coder   │   Ops    │ Observer │  Hermes    │
├──────────┴──────────┴──────────┴──────────┴────────────┤
│              WISSENSSCHICHT                             │
│    Qdrant (Vektoren) + PostgreSQL (Relational)         │
├─────────────────────────────────────────────────────────┤
│              MODELLSCHICHT                              │
│    Ollama (lokal) + Cloud-APIs (optional)              │
├─────────────────────────────────────────────────────────┤
│              INFRASTRUKTUR                              │
│    Docker + Flowise + Open WebUI + Monitoring          │
└─────────────────────────────────────────────────────────┘
```

### Verzeichnisstruktur

| Verzeichnis | Zweck |
|-------------|-------|
| `kirobi-core/` | Kernidentität, Prompts, Routing, Policies |
| `sources/` | Rohdaten-Eingang (Inbox, Imports, etc.) |
| `extracts/` | Verarbeitete Extrakte aus Quellen |
| `clusters/` | Semantisch geclusterte Wissensknoten |
| `canon/` | Kanonische Masterdokumente |
| `experiences/` | Erfahrungen, Projekte, Lernpunkte |
| `analytics/` | System- und Performancemetriken |
| `integrations/` | Externe Dienst-Integrationen |
| `infra/` | Docker, Scripts, Backup, Monitoring |
| `models/` | Modell-Registry und Konfigurationen |
| `metadata/` | Schema, Policies, Agent-Registry |
| `sacred/` | Höchst vertrauliche Familie/Werte |
| `quarantine/` | Unverarbeitetes, unsicheres Material |
| `archive/` | Archivierte und superseded Inhalte |

---

## Sicherheitszonen

| Zone | Farbe | Beschreibung | Beispiele |
|------|-------|-------------|----------|
| `PUBLIC` | 🟢 Grün | Öffentlich teilbar | Blog-Posts, Open-Source-Code |
| `WORKSPACE` | 🔵 Blau | Arbeitskontext | Projekte, Tech-Docs, APIs |
| `FAMILY_PRIVATE` | 🟡 Gelb | Familiäre Inhalte | Erfahrungen, Rituale, Mediation |
| `QUARANTINE` | 🟠 Orange | Unsicher/Ungeprüft | Unbearbeitete Imports |
| `SACRED` | 🔴 Rot | Streng vertraulich | Kern-Werte, Grenzen, Trauma |

---

## Agenten-Ökosystem

| Agent | Rolle | Modell |
|-------|-------|--------|
| `kirobi-core` | Supervisor & Orchestrator | llama3.1:70b |
| `kirobi-architect` | System-Design & Planung | deepseek-r1:32b |
| `kirobi-coder` | Code-Entwicklung | qwen2.5-coder:32b |
| `kirobi-ops` | DevOps & Infrastruktur | llama3.1:8b |
| `kirobi-observer` | Monitoring & Analyse | mistral:7b |
| `hermes-extractor` | Datenextraktion & Ingestion | mistral:7b |
| `samira-heart-agent` | Familien-Mediation | llama3.1:8b |
| `sineo-creator-coach` | Kreativitäts-Coaching | llama3.1:8b |
| `research-crew` | Web-Recherche & Analyse | perplexica |
| `mediation-crew` | Konfliktlösung | llama3.1:8b |
| `creative-agent` | Kreative Inhalte | llama3.1:70b |
| `voice-agent` | Sprach-Interface | whisper + TTS |
| `installer-agent` | Setup & Onboarding | llama3.1:8b |
| `enterprise-agent` | Business & Enterprise | llama3.1:70b |

---

## Key Docs

- 📋 [Project Charter](PROJECT-CHARTER.md) - Vision & Prinzipien
- 🗺️ [Roadmap](ROADMAP.md) - Phasen & Meilensteine
- 🤝 [Contributing](CONTRIBUTING.md) - Beitragen & Mitarbeiten
- 🔒 [Security](metadata/SECURITY-CLASSIFICATION.md) - Sicherheitsklassifizierung
- 🤖 [Agent Registry](metadata/AGENTREGISTRY.md) - Alle Agenten
- 🗄️ [Model Registry](metadata/MODEL-REGISTRY.md) - Alle Modelle
- ⚙️ [System Config](metadata/SYSTEMCONFIG.md) - Systemkonfiguration

---

## Beitragen

Kirobi ist ein persönliches Projekt mit offenem Charakter. Beiträge sind willkommen:

```bash
# Fork und Branch erstellen
git checkout -b feature/mein-feature

# Änderungen committen
git commit -m "feat: beschreibe deine Änderung"

# Pull Request erstellen
```

Mehr Details: [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Lizenz

MIT License – Kirobi / Disruptive OS
© 2024 Sven Darusi (Kirobi92)

Details: [LICENSE.md](LICENSE.md)
