# 00 — Execution Protocol

**Datum:** 2026-05-26
**Auditor-Rolle:** Senior CTO / Principal Architect / Security Reviewer / Migration Lead
**Modus:** MODE 1 — ANALYSE (read-only, keine produktiven Änderungen)

## 1. Bestätigter Arbeitsmodus

- Mode 1 (Analyse) und Mode 2 (Planung) werden in diesem Lauf vollständig ausgeführt.
- Mode 3 (Umsetzung) startet ausschließlich nach expliziter Freigabe `FREIGABE PHASE A`.
- Während Mode 1/2 dürfen ausschließlich Dateien unter `docs/architecture-planning/` geschrieben werden.

## 2. Erkannte Projektwurzel

- **Aktive Wurzel:** `/Datenspeicher/OpenDisruption_v0.1/` — VERIFIED via `ls -la`.
- 24 Top-Level-Einträge, gemischte deutsch/englische Ordnernamen, teilweise Leerzeichen in Pfaden.
- Root-Mischbesitz: `data/` ist `root:root`, alles andere `sven:sven`. VERIFIED.

## 3. Erkannte Git-Situation

- **Kein Git-Repository** an der Wurzel (`git rev-parse --show-toplevel` → fatal). VERIFIED.
- Es existiert ein versteckter `.hermes/`-Ordner aber keine `.git/`.
- **Konsequenz:** Es gibt keine Branch-Rollback-Option. Jede Migration benötigt einen externen `rsync`-/`tar`-Snapshot, der vor Phase A angelegt wird (vom Nutzer freigegeben).

## 4. Parallele Codebase (Klärung erledigt)

- `/home/sven/OpenDisruption` ist Symlink auf `/Datenspeicher/home-migration/OpenDisruption/`. VERIFIED.
- Dieser Tree enthält eigene Struktur (agents, apps, kidi, kirobi-core, kirobi_core [doppelt!], quarantine, frontend, infra, external) — vermutlich ein älterer Migrationsstand.
- **Entscheidung (vom Nutzer freigegeben):** dieser Tree gilt **nicht** als produktiver Wahrheits-Stand. Wird in Phase 1 nur summarisch erwähnt, Empfehlung-Default: ARCHIVE oder DELETE_LATER nach Inhaltsverifikation.

## 5. Erkannte Hauptbereiche (Top-Level v0.1)

| Bereich | Pfad | Erste Klassifikation |
|---|---|---|
| Agenten-/KI-Laufzeit | `hermes-agent/`, `Orchestrierung-und-Agenten/` | SHARED_INFRA + KIROBI |
| KIROBI-Frontend | `kirobi-pwa/` | KIROBI_FAMILY |
| Services-Mix | `services/` | Gemischt: SHARED_INFRA + LUKI-Kandidaten + LABS |
| Benutzerbereich | `Benutzer-Ordner/` | KIROBI_FAMILY (privat) |
| Datenbereich | `Geteilte-Wissensbasis/`, `Systembetrieb-und-Indizes/`, `Integrationen-und-Importe/` | gemischt; Runtime-Daten gehören außerhalb Repo |
| Konfiguration | `Systemkonfiguration/`, `.hermes/`, `.omo/`, `.opencode/` | SHARED_INFRA |
| Unternehmen / Nutzeisen | `Unternehmensstruktur/`, `Nutzeisen Prozessanalyse/` | LUKI_BUSINESS-Kandidaten |
| Backups (im Repo!) | `Backups-und-Exporte/`, `.backup.env` | Risk: Runtime+Secrets im Repo |
| Vorlagen / Research / temp | `_Vorlagen/`, `Research/`, `temp/` | LABS oder ARCHIVE |
| Audits / Docs | `KIROBI_OS_AUDIT.md`, `AGENTS.md`, `AGENT-ACTIVITY-LOG.md`, `SYSTEM_MAP.md`, `README.md`, `MASTERPLAN-24H-AUTONOMIE.md` | OPENDISRUPTION_ROOT (Doku) |
| HTML-Dashboard | `opendisruption-data-dash.html` | ARCHIVE oder LABS |
| Capacitor-Reste | `package.json`, `node_modules/`, `capacitor.config.json` | LABS/Build-Artefakt — gehört nicht ins Repo |

## 6. Bestehende Audit-/Plan-Dokumente (vorab gelesen)

| Datei | Inhalt | Brauchbarkeit als Input |
|---|---|---|
| `README.md` | Familien-KI-System-Vision, Zonen-Modell (PUBLIC/FAMILY_SHARED/FAMILY_PRIVATE/SINEO_SAFE), Hermes als Orchestrator | **WERTVOLL** — definiert das KIROBI-Sicherheitsmodell. Übernehmen. |
| `SYSTEM_MAP.md` | Agenten-Topologie, Datenflüsse, Dienste-Übersicht (Ollama, Qdrant, Kirobi-Gateway) | **WERTVOLL** — Ist-Topologie. Übernehmen. |
| `AGENTS.md` | Workspace-Realität, Verifizierte Befehle, Privacy-Hinweise, App-spezifische Tests | **WERTVOLL** — operative Wahrheit. Übernehmen. |
| `AGENT-ACTIVITY-LOG.md` | Chronologisches Agenten-Tagebuch | **GEFAHR** — enthält Klartext-Credentials (Tokens, Passwörter). Wird in Phase 2 als CRITICAL-Befund eingestuft. Inhalte nur als Hinweis nutzen, **niemals zitieren**. |
| `MASTERPLAN-24H-AUTONOMIE.md` | Service-Status, Cron-Schedule, MCP-Liste, Business-Ziele 3D-Druck | Operativer Snapshot vom 2026-05-18. Service-Tabelle als ASSUMPTION übernehmen, gegen aktuelle Compose-Dateien verifizieren. |
| `KIROBI_OS_AUDIT.md` (68 KB, 1840 Zeilen lt. AGENTS.md) | Vorhandener CTO-Audit | Als Input lesen, kritisch gegenprüfen, Secret-Audit separat |

**Entscheidung:** Alt-Audits dienen als Input für Phase 1, werden aber gegen die aktuelle Datei-/Compose-Realität verifiziert. Drift wird explizit markiert.

## 7. Bestätigte Scope-Entscheidungen

1. Produktiver Tree: nur `/Datenspeicher/OpenDisruption_v0.1`.
2. Vor Phase A externer Snapshot Pflicht: `/Datenspeicher/Backups/OpenDisruption-pre-migration-2026-05-26/` via `rsync -aAX --numeric-ids` mit Größen-/Datei-Anzahl-Verifikation.
3. Alt-Audits werden gelesen, kritisch gegengeprüft, Drift dokumentiert.

## 8. Was ich ändern darf (in diesem Lauf)

- Nur Dateien unterhalb `docs/architecture-planning/`.
- Verzeichnis wurde angelegt: `mkdir -p` erfolgte als einzige nicht-lesende Aktion.

## 9. Was ich nicht ändern darf

- Keine Produktivdateien (Compose, Caddyfile, .env, Skills, Skripte, Backups, Volumes, Datenbanken, systemd-Units).
- Keine Services starten/stoppen, keine Container, keine Dependencies installieren, keine Secrets rotieren, keine Refactorings.
- Keine Git-Operationen (es gibt kein Git).
- Keine Inhalte aus Audit-Dateien mit Klartext-Secrets zitieren.

## 10. Wie ich fortfahre

1. Phase 1 — drei parallele Explore-Agents (Services/Compose, Benutzerbereich/Daten, Konfig/Skills).
2. Phase 2 — Security-Audit als separater Lauf, **alle Funde maskiert**.
3. Phasen 3–9 ableiten aus 1+2 und in Markdown-Dateien schreiben.
4. Abschluss-Zusammenfassung im Chat + Freigabe-Frage für Phase A.

## 11. Evidenzlabels

| Label | Bedeutung |
|---|---|
| VERIFIED | Direkt in Datei/Befehl/Compose gesehen. |
| INFERRED | Aus mehreren verifizierten Befunden logisch abgeleitet. |
| ASSUMPTION | Plausible Annahme, noch nicht bewiesen. |
| UNKNOWN | Aus aktueller Codebase nicht prüfbar. |

Alle nachfolgenden Dokumente verwenden diese Labels pro Aussage.
