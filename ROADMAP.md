# Roadmap: Kirobi / Disruptive OS

**Stand:** 2024 | **Eigentümer:** Sven Darusi

---

## Übersicht

```
Phase 1 (MVP)     Phase 2 (Expand)     Phase 3 (Enterprise)
━━━━━━━━━━━━━     ━━━━━━━━━━━━━━━━     ━━━━━━━━━━━━━━━━━━━
Jetzt → Q1/25     Q2/25 → Q4/25        2026+
Infrastruktur     Intelligenz           Skalierung
```

---

## Phase 1: MVP (Jetzt)

**Ziel:** Laufende Basis-Infrastruktur mit Kern-Agenten und grundlegender Wissensorganisation

### 1.1 Infrastruktur
- [x] Verzeichnisstruktur und Governance-Dokumente
- [x] Docker-Compose mit Ollama, Open WebUI, Qdrant, PostgreSQL, Flowise
- [ ] Makefile mit allen Management-Targets
- [ ] `infra/scripts/bootstrap.sh` – vollständiger Setup-Flow
- [ ] GPU-optimiertes Ollama-Setup
- [ ] Basis-Monitoring mit Healthchecks

### 1.2 Kirobi Core
- [ ] Supervisor-Prompt finalisieren
- [ ] Routing-Logik implementieren (Modell-Selektion nach Aufgabentyp)
- [ ] Event-Logging aktivieren
- [ ] Basis-Policies dokumentieren
- [ ] Fallback-Strategien definieren

### 1.3 Wissens-Ingestion
- [ ] `sources/inbox/` → `extracts/` Pipeline mit Hermes-Extractor
- [ ] Qdrant-Collections anlegen (gemäß COLLECTION-MAPPING.md)
- [ ] Embedding-Schema implementieren (BGE-M3 / nomic-embed-text)
- [ ] Erste 100 Dokumente ingesten

### 1.4 Erste Agenten
- [ ] `kirobi-core` als Flowise-Flow
- [ ] `hermes-extractor` für Inbox-Verarbeitung
- [ ] `kirobi-observer` für System-Monitoring
- [ ] `kirobi-ops` für Infrastruktur-Aufgaben

### 1.5 Interfaces
- [ ] Open WebUI konfiguriert und personalisiert
- [ ] System-Prompts für alle Agenten geladen
- [ ] Basis-Flowise-Workflows

**Meilenstein MVP:** System läuft stabil, erste Dokumente sind abrufbar, Kirobi antwortet als Supervisor

---

## Phase 2: Expand (Q2–Q4 2025)

**Ziel:** Vollständiges Agenten-Ökosystem, intelligente Workflows, Familien-Integration

### 2.1 Vollständiges Agenten-Ökosystem
- [ ] `kirobi-architect` – Planungs- und Design-Agent
- [ ] `kirobi-coder` – Code-Entwicklung mit Qwen/DeepSeek
- [ ] `samira-heart-agent` – Familien-Mediation und Herzensthemen
- [ ] `sineo-creator-coach` – YouTube/Creator-Coaching
- [ ] `research-crew` – Web-Recherche mit Perplexica
- [ ] `mediation-crew` – Multi-Agent-Konfliktlösung
- [ ] `creative-agent` – Kreative Inhalte und Brainstorming

### 2.2 Multimodale Erweiterungen
- [ ] Voice-Agent mit Whisper (STT) und TTS
- [ ] Bild-Analyse mit LLaVA / Moondream
- [ ] Stable Diffusion für Bildgenerierung
- [ ] Basis-Video-Processing

### 2.3 Familien-Features
- [ ] Familien-Mediation-Dashboard
- [ ] Sineo Creator Coach Flow
- [ ] Familien-Kalender und Rituale-Tracking
- [ ] SACRED-Zone vollständig abgesichert

### 2.4 Intelligentes Wissensmanagement
- [ ] Automatisches Clustering (`extracts/` → `clusters/`)
- [ ] Canon-Update-Flows (Konflikt-Erkennung)
- [ ] `kirobi-observer` analysiert Muster proaktiv
- [ ] Knowledge Graph Visualisierung

### 2.5 Business-Integration
- [ ] Enventa/ERP-Connector
- [ ] M365-Integration (Outlook, Teams, SharePoint)
- [ ] Projekt-Portfolio-Tracking
- [ ] Client-Briefing-Automatisierung

### 2.6 Analytics & Monitoring
- [ ] Langfuse für LLM-Tracing
- [ ] OpenObserve für System-Monitoring
- [ ] KPI-Dashboards in Grafana
- [ ] Wöchentliche automatisierte Reports

**Meilenstein Phase 2:** Alle 14 Agenten aktiv, Familien nutzen System täglich, Business-Workflows automatisiert

---

## Phase 3: Enterprise (2026+)

**Ziel:** Skalierung, Enterprise-Readiness, Community-Aufbau

### 3.1 Enterprise-Features
- [ ] Multi-User-Support mit RBAC
- [ ] SSO-Integration (Microsoft Entra ID)
- [ ] Audit-Logging und Compliance
- [ ] Enterprise-grade Backup & Recovery
- [ ] SLA-Monitoring

### 3.2 Mobile & Voice
- [ ] Android Voice Client (Rhasspy / OpenHome)
- [ ] Mobile App (React Native oder Flutter)
- [ ] Smart Speaker Integration
- [ ] Wearable-Anbindung

### 3.3 Erweiterte KI-Capabilities
- [ ] Fine-Tuning eigener Modelle auf Kirobi-Daten
- [ ] Digital Twin von Sven (Persönlichkeitsmodell)
- [ ] Proaktive Lebens-Empfehlungen (AQAL-basiert)
- [ ] Langzeit-Gedächtnis und Kohärenz über Jahre

### 3.4 Community & Open Source
- [ ] Disruptive OS als Open-Source-Framework veröffentlichen
- [ ] Plugin-System für Community-Agenten
- [ ] Installer-Wizard für andere Familien/Unternehmen
- [ ] Dokumentations-Website

### 3.5 3D-Druck Bar OS
- [ ] Inventar-Management mit KI-Unterstützung
- [ ] Kundenbestellungs-Automatisierung
- [ ] Qualitätskontrolle mit Vision-AI
- [ ] Lieferanten-Integration

**Meilenstein Phase 3:** Kirobi/Disruptive OS als eigenständiges Produkt für andere Familien und KMUs

---

## Technologische Abhängigkeiten

| Technologie | Phase | Priorität |
|-------------|-------|-----------|
| Ollama + llama3.1:70b | 1 | Kritisch |
| Qdrant | 1 | Kritisch |
| PostgreSQL | 1 | Kritisch |
| Flowise | 1 | Hoch |
| Open WebUI | 1 | Hoch |
| Whisper STT | 2 | Mittel |
| Langfuse | 2 | Mittel |
| Perplexica | 2 | Mittel |
| Stable Diffusion | 2 | Niedrig |
| Rhasspy/OpenHome | 3 | Niedrig |

---

*Roadmap wird monatlich durch `kirobi-observer` reviewed und bei Bedarf angepasst.*
