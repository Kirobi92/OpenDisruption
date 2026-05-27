# OpenDisruption

**Dach-Repository für KIROBI (privat) und LUKI (Business) auf gemeinsamer Shared-Infrastruktur.**

## Struktur

| Ordner | Domäne | Zweck |
|---|---|---|
| `docs/` | OPENDISRUPTION_ROOT | Canon, Architektur-Planung, Runbooks, Security-Policies |
| `infra/` | SHARED_INFRA | Caddy, Hermes-Runtime, Qdrant, Ollama, Backup, Monitoring |
| `products/kirobi/` | KIROBI_FAMILY | Family-PWA, Telegram-Gateways, Skills, Canon |
| `products/luki/` | LUKI_BUSINESS | Knowledge-Stack, Source-Docs-Manifest, Eval, Business-Doku |
| `packages/` | OPENDISRUPTION_ROOT | Geteilte Libraries (policy-gate, ingest, retrieval) |
| `tools/` | OPENDISRUPTION_ROOT | CLI, Doctor, Vorlagen |
| `labs/` | LABS | Webshop, 3D-Druck, ComfyUI etc. (opt-in) |
| `archive/` | ARCHIVE | Eingefrorene Altlasten |

## Runtime-Daten

**Niemals im Repo.** Alle Runtime-Daten leben unter:

```
/Datenspeicher/OpenDisruption-Data/
├── shared/   (Qdrant, Ollama, Hermes, Logs, Monitoring, Caddy)
├── kirobi/   (PWA-Daten, Gateways, FAMILY_PRIVATE, FAMILY_SHARED)
├── luki/     (Source-Docs, Ingest-Staging, Audit, Evals)
├── labs/     (Webshop, ComfyUI, Open-WebUI, etc.)
├── secrets/  (chmod 600, eine .env pro Service)
├── backups/  (Restic, DB-Dumps, Qdrant-Snapshots)
└── archive/
```

## Status

- **2026-05-27:** Skelett angelegt (PHASE B).
- Detaillierte Planungsdokumente: siehe `docs/architecture-planning/` (kopiert aus `OpenDisruption_v0.1`).
- Migration in Phasen A–H gemäß `docs/architecture-planning/07_phased_implementation_plan.md`.

## Wichtige Regeln

1. Keine Secrets im Repo. Pre-Commit-Hooks (TruffleHog, gitleaks) blockieren.
2. Keine Runtime-Daten im Repo (`.gitignore` schließt `data/`, `logs/`, `*.sqlite`, `node_modules/`, `.venv/`).
3. Caddy ist einziger HTTP-Entry; alle Services binden 127.0.0.1 oder Docker-Internal.
4. Family-Private niemals Cloud, niemals LUKI-Kontext.
5. Jede schreibende Aktion: Backup → Change → Verifikation → Rollback-Punkt.

## Owner

Sven (sven@OpenDisruption)
