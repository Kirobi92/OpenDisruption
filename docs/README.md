---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# docs/

Betriebsdokumentation für das OpenDisruption-System. Enthält Deployment-Anleitungen, Familien-Onboarding, Remote-Zugriff und Agent-Konzepte.

## Dateien

- `DEPLOYMENT-SUMMARY.md` — Zusammenfassung der implementierten Family-Profiles-Infrastruktur (Datenbank-Schema, Benutzer, Services)
- `FAMILY-PROFILES-SYSTEM.md` — Beschreibung des Familien-Profil-Systems mit Zonen-Berechtigungen für Sven, Samira und Sineo
- `MVP-E2E-PROOF.md` — belegter End-to-End-Nachweis für das lokale zone-aware MVP inkl. Demo- und Troubleshooting-Hinweisen
- `QUICKSTART-FAMILY.md` — Schnellstart-Anleitung für Familienmitglieder
- `REMOTE-ACCESS.md` — Anleitung für sicheren Remote-Zugriff via Tailscale inkl. Doctor/Service-Helper
- `NEXT-GENERATION-EXECUTION-PLAN.md` — kanonischer, sequenzieller Ausführungsplan für die Next-Generation-Strategie

## Unterordner

- `agent/` — Konzept-Dokumente zur Agent-Architektur: Multi-Agent-System, KeyCodi-Orchestrator, Telegram-Integration, Onboarding-Prozess, Context-Window-Management

## Hinweis

Diese Dokumente beschreiben den Betrieb und die Nutzung des Systems. Für den aktuellen Produkt-/Entwicklerzustand sind zusätzlich maßgeblich:

- `README.md` — unterstützte Oberflächen und Schnellstart
- `apps/README.md` und `apps/web/README.md` — UI-Surfaces
- `services/README.md` — aktive Backend-Services
- `tests/README.md` — aktuelle Test-Baseline
- `DEVELOPER-RUNBOOK.md` — operative Entwickler-Workflows
