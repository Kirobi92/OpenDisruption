# 04 — Target Architecture

**Datum:** 2026-05-26 · **Status:** Vorschlag (Mode 2 — Planung), keine Umsetzung.

## 1. Architekturprinzipien (verbindlich)

1. OpenDisruption = Dach; KIROBI und LUKI = getrennte Produktbereiche; Shared Infra strikt getrennt von Produkten.
2. Code (Repo) ≠ Runtime-Daten ≠ Secrets — drei physisch getrennte Trees.
3. Caddy ist einziger HTTP-Entry. Interne Dienste binden `127.0.0.1` oder Docker-Internal-Netz.
4. Ollama, Qdrant, Hindsight, Datenbanken nie direkt im LAN.
5. systemd startet ausschließlich Compose-Stacks oder klar dokumentierte Wrapper.
6. Keine manuell gestarteten Dauerprozesse.
7. Jede Komponente hat: Owner, Zweck, Start/Stop, Logs, Backup-Policy, Healthcheck, Domäne.
8. LUKI-MVP startet klein: nur Knowledge.
9. KIROBI bleibt privat (Family-Zone). FAMILY_PRIVATE niemals in Cloud, niemals in LUKI-Kontext.
10. Labs sind nicht produktkritisch und werden separat gestartet/gestoppt.
11. Jede produktive Änderung: Backup → Change → Verifikation → Rollback-Möglichkeit.
12. Secrets niemals im Repo, niemals in Audit-/Logfiles im Klartext.

## 2. Ziel-Domänenmodell

```
OpenDisruption (Dach)
├── KIROBI_FAMILY        (privat, lokal, Familie)
├── LUKI_BUSINESS        (Business, Nutzeisen/eNVenta, mittelständische Kunden)
├── SHARED_INFRA         (Caddy, Hermes-Runtime, Qdrant, Ollama, DBs, Backup, Monitoring)
├── LABS                 (Webshop, 3D-Druck, ComfyUI, Open-WebUI, Avatar, Marketing-Experimente)
└── ARCHIVE              (Altlasten, eingefrorene Versionen)
```

## 3. Ziel-Repository-Struktur (Monorepo, empfohlen)

```
OpenDisruption/                          # Git-Repo-Wurzel
├── README.md                            # Dachprojekt-Übersicht
├── AGENTS.md                            # Top-Level Agentenregeln
├── docs/
│   ├── canon/                           # Sven/Familien-Canon, Zonen, Policies
│   ├── architecture-planning/           # diese Audit-/Plan-Dateien
│   ├── runbooks/                        # Start/Stop, Backup, Restore, Incident
│   └── security/                        # Zonen-/Cloud-Modell, Secret-Policy
├── infra/                               # SHARED_INFRA
│   ├── caddy/                           # Caddyfile + compose
│   ├── hermes-runtime/                  # Hermes-Agent Source (Runtime ausgelagert)
│   ├── qdrant/                          # compose + collections-config
│   ├── ollama/                          # compose + Modell-Manifest (Modelle separat)
│   ├── postgres/                        # falls benötigt
│   ├── monitoring/                      # Loki/Promtail/Uptime
│   ├── backup/                          # Restic-Configs (Secrets extern)
│   └── secrets-skeleton/                # .env.template + Beschreibung (keine echten Werte)
├── products/
│   ├── kirobi/                          # KIROBI_FAMILY
│   │   ├── README.md
│   │   ├── apps/
│   │   │   ├── pwa/                     # SvelteKit (ehem. kirobi-pwa)
│   │   │   └── avatar/                  # falls beibehalten (sonst → labs/)
│   │   ├── gateways/
│   │   │   ├── telegram-sven/           # systemd-unit + config
│   │   │   └── telegram-samira/
│   │   ├── skills/                      # KIROBI-eigene Hermes-Skills (YAML)
│   │   ├── canon/                       # KIROBI-Persönlichkeiten, Zonen-Bindungen
│   │   └── compose.kirobi.yml           # KIROBI-Stack
│   └── luki/                            # LUKI_BUSINESS
│       ├── README.md
│       ├── source-docs/                 # Nutzeisen IST-Prozesse, eNVenta Hilfe (read-only)
│       ├── knowledge/                   # Ingest, Chunking, Indexierung
│       ├── retrieval/                   # Antwort-Service mit Quellenpflicht
│       ├── audit/                       # Audit-Log-Schema + Logs (Runtime extern)
│       ├── evals/                       # 50 Testfragen + Bericht
│       ├── runbooks/                    # LUKI-Spezial-Runbooks
│       └── compose.luki.yml             # LUKI-Stack
├── packages/                            # shared libraries (Python/JS)
│   ├── policy-gate/                     # Zonen-/Cloud-Policy (aus opendisruption_policy_gate.py)
│   ├── ingest/                          # gemeinsame Doku-Ingest-Lib
│   └── retrieval/                       # gemeinsame Retrieval-Lib
├── tools/                               # CLI/Operator-Tools
│   ├── opendisruption-cli/              # ehem. opendisruption_tools.py
│   ├── doctor/                          # opendisruption_doctor.py
│   └── templates/                       # _Muster-Benutzerstruktur, Vorlagen
├── labs/                                # nicht produktkritisch
│   ├── webshop/                         # WP + MySQL (Compose, Secrets extern)
│   ├── 3d-druck/                        # Pipeline, Status-Page
│   ├── inventory/                       # Homebox, Part-DB
│   ├── comfyui/                         # nur Compose, Modelle extern
│   ├── open-webui/                      # Compose, Datenvolume extern
│   ├── flowise/                         # Compose, Datenvolume extern
│   ├── hindsight/                       # Compose, Datenvolume extern
│   ├── mission-control/                 # Compose
│   └── ionos-integration/               # falls aktiv
├── archive/                             # eingefrorene Altlasten, leseweise
│   ├── audits-pre-2026-05/              # alte Audits, evtl. mit Secret-Quarantäne-Hinweis
│   ├── opendisruption-v0.1-snapshot/    # Snapshot vor Migration
│   └── home-migration-tree/             # /Datenspeicher/home-migration/OpenDisruption
├── .gitignore                           # streng: secrets, runtime, volumes, modules
├── .pre-commit-config.yaml              # TruffleHog/GitGuardian + black/eslint
└── .github/ oder .forgejo/              # CI: dependency scan, secret scan, tests
```

## 4. Ziel-Runtime-Datenstruktur (außerhalb Repo)

```
/Datenspeicher/OpenDisruption-Data/
├── shared/
│   ├── ollama/models/                   # LLM-Modelle
│   ├── qdrant/                          # Vektor-DB-Volume
│   │   ├── collections/
│   │   │   ├── kirobi_public/
│   │   │   ├── kirobi_family_shared/
│   │   │   └── luki_knowledge_v1/
│   │   └── snapshots/
│   ├── postgres/                        # falls benötigt
│   ├── caddy/{data,config}/
│   ├── hermes/                          # ~/.hermes Inhalt
│   ├── logs/                            # zentrale Logs (Loki Volume)
│   └── monitoring/
├── kirobi/
│   ├── pwa/                             # PWA-Datenvolume
│   ├── gateway-sven/
│   ├── gateway-samira/
│   ├── private/                         # FAMILY_PRIVATE-Inhalte (Sven/Samira/Sineo)
│   └── shared/                          # FAMILY_SHARED
├── luki/
│   ├── source-docs/                     # Quelldokumente (read-only Master)
│   ├── ingest-staging/                  # extract → cleanup → chunk
│   ├── audit/                           # Anfragen-Audit (append-only)
│   └── evals/                           # Eval-Outputs
├── labs/
│   ├── webshop/{mysql,wordpress}/
│   ├── comfyui/{models,outputs}/
│   ├── open-webui/{data}/
│   ├── flowise/{data,logs}/
│   ├── hindsight/{pg0-data}/
│   └── 3d-druck/{pipeline-state}/
├── secrets/                             # chmod 600, eine Datei pro Service
│   ├── webshop.env
│   ├── 3d-druck-pipeline.env
│   ├── hermes.env
│   ├── restic.env                       # backup-passphrase
│   ├── telegram-bots.env
│   └── README.md (kein echtes Geheimnis)
├── backups/
│   ├── restic-repo/                     # Restic encrypted
│   ├── db-dumps/                        # tägliche Dumps
│   └── pre-migration/                   # Snapshot-Vor-Migration
└── archive/
    ├── qdrant-legacy/                   # 10 GB aus services/qdrant
    └── opendisruption-v0.1-2026-05-26/  # vollständiger Tar
```

## 5. Ziel-Netzwerkmodell

| Zugang | Mechanismus | Routen |
|---|---|---|
| Loopback (Host) | `127.0.0.1:*` | direkte CLI-Tools, Debug |
| Interne Docker-Netze | `internal: true` + nur Caddy hat Bridge-Anschluss | DB ↔ App, App ↔ Qdrant |
| LAN/Tailscale (Familie) | Caddy bindet **nur** an Tailscale-IP **oder** an `127.0.0.1` + Tailscale-`serve` | `/kirobi`, `/avatar` |
| Öffentlich | nichts initial; falls nötig: separater Reverse-Proxy mit HTTPS+Auth in eigenem Compose | – |

**Regel:** Kein Service bindet `0.0.0.0:*` außer Caddy (und der nur an gewollten Interfaces).

## 6. Ziel-Compose-Modell

- **Per Produkt + Shared-Stack-Splits:**
  - `infra/compose.shared.yml` — Caddy, Qdrant, Ollama, Postgres, Monitoring
  - `products/kirobi/compose.kirobi.yml` — KIROBI-PWA, Telegram-Gateways, KIROBI-Skills
  - `products/luki/compose.luki.yml` — LUKI Knowledge Ingest + Retrieval + Audit
  - `labs/<lab>/compose.<lab>.yml` — opt-in
- **`docker compose --project-directory <dir> -p <project>`** trennt Stacks.
- Jeder Stack:
  - liest Secrets aus `/Datenspeicher/OpenDisruption-Data/secrets/<service>.env` (`env_file:`).
  - mountet Volumes nach `/Datenspeicher/OpenDisruption-Data/<domain>/<service>`.
  - hat `healthcheck:` und `restart: unless-stopped`.
  - pinnt Image-Tags (kein `:latest`).

## 7. Ziel-Secrets-Modell

1. **Speicherort:** ausschließlich `/Datenspeicher/OpenDisruption-Data/secrets/` (chmod 600, owner `sven`).
2. **Repo:** nur `*.env.template` mit leeren Werten + Beschreibung.
3. **Pre-Commit-Hook:** TruffleHog / GitGuardian blockiert High-Entropy-Strings.
4. **Rotation-Schedule:** Telegram-Bots quartalsweise, DB-Passwörter halbjährlich, Restic-Repo-PW jährlich, sofort nach jedem Leak.
5. **Audit-Doku:** Secrets in Markdown nur als `SECRET_FOUND(type=…, file=…, line=…, value=MASKED)`.

## 8. Ziel-Backup-Modell

| Schicht | Tool | Frequenz | Ziel |
|---|---|---|---|
| Datei-Snapshot OpenDisruption-Data | Restic | täglich | externes Repo (USB/zweite Platte) |
| DB-Dumps (MySQL/Postgres) | nativ + `pg_dump`/`mysqldump` | täglich | `…/backups/db-dumps/` (mit Rotation 7/4/12) |
| Qdrant-Snapshot | Qdrant-Snapshot-API | täglich | `…/backups/qdrant/` |
| Restore-Test | scripted | wöchentlich automatisch + monatlich manuell | Sandkasten-Verzeichnis |
| Air-Gap-Kopie | manuell | monatlich | zweite USB-Platte |

## 9. Ziel-Monitoring-Modell

- **Logs:** Loki + Promtail (gesammelt unter `/Datenspeicher/OpenDisruption-Data/shared/monitoring/loki/`)
- **Metriken (minimal):** node-exporter + container-stats; Grafana hinter Caddy mit Auth
- **Uptime-Check:** Uptime-Kuma als Single-Pane für alle Stacks (KIROBI, LUKI, Shared, Labs)
- **Alerts:** Telegram-Channel „od-alerts" — getrennt von User-Bots; nur Sven

## 10. Ziel-Deployment-Modell

- systemd-Wrapper pro Stack: `od-shared.service`, `od-kirobi.service`, `od-luki.service`, `od-lab-<x>.service`.
- Jede Unit ruft `docker compose -f <stack> up --remove-orphans` mit `ExecStop=docker compose -f <stack> down`.
- Updates: `git pull` → `docker compose pull` → `up -d` + Healthcheck-Verifikation. Rollback: `git checkout <prev>` + `up -d`.
- Kein Code wird live im Container editiert.

## 11. Ziel-Logging-Modell

- jeder Service loggt nach stdout/stderr → Container-Log → Promtail → Loki
- keine sensiblen Inhalte im Loglevel INFO (Body, Prompts, User-Messages werden auf DEBUG geschaltet und in Produktion deaktiviert)
- LUKI-Audit-Log ist **separates** Append-Only-JSONL pro Anfrage (Frage, Quellen-IDs, Antwort-Hash, Zeit, User-Hash) — kein Klartext-Antworten

## 12. Ziel-Testmodell

- **Unit-Tests** (Python/JS) pro Package
- **Integrationstests:** Compose-Up im CI gegen Smoke-Suite (kein echtes Ollama, sondern Mock)
- **LUKI-Eval:** 50 Testfragen mit erwarteten Quellen-IDs (Goldset) → automatisch pro PR
- **Security-Scan:** Trivy auf Images, TruffleHog auf Diff, Dependabot/Renovate

## 13. Monorepo vs. Multi-Repo

**Empfehlung: Monorepo** mit klarer Workspace-Trennung (`products/*`, `infra/*`, `labs/*`).

**Trade-offs:**

| Aspekt | Monorepo (Empfehlung) | Multi-Repo |
|---|---|---|
| Konsistente Tools/Standards | ✅ einfach | ⚠️ aufwendig |
| Atomische Cross-Changes | ✅ in einem PR | ❌ koordinieren |
| Sichtbarkeit für Solo-Owner | ✅ ein Tree | ❌ viele Trees |
| Repo-Größe | ⚠️ wächst | ✅ klein |
| CI-Komplexität | ⚠️ Filter nötig | ✅ je Repo |
| Separation für externe Mitarbeiter/Kunden (LUKI-Pilot) | ⚠️ schwieriger | ✅ pro Kunde |

**Mitigation für Monorepo-Nachteile:** `paths-filter` in CI; nach 6 Monaten Re-Evaluation, ob LUKI in eigenes Repo soll, sobald externer Kunde mit-developt.

## 14. Offene Entscheidungen (für Nutzer)

- E1: Monorepo bestätigen oder Multi-Repo bevorzugen?
- E2: Backup-Ziel-Hardware (USB-SSD vs. NAS vs. Remote-Restic-Server)?
- E3: Tailscale für Familienzugang als Pflicht oder optional?
- E4: Wer ist berechtigt für Notfall-Restic-Restore (nur Sven)?
- E5: Soll `kirobi-avatar` (FastAPI/React/Android) als KIROBI-App oder als Lab geführt werden?
