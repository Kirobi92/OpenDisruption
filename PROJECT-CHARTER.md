# Projekt-Charta: Kirobi / Disruptive OS

**Version:** 1.0
**Datum:** 2024
**Eigentümer:** Sven Darusi (Kirobi92)
**Status:** Aktiv

---

## 1. Vision

> **„Ein lebendiges, lernendes digitales Ökosystem, das Sven und seiner Familie ermöglicht, ihr volles kreatives und menschliches Potenzial zu entfalten – unterstützt durch KI, nicht ersetzt."**

Kirobi / Disruptive OS ist mehr als ein Tool – es ist ein digitaler Lebenspartner. Ein System, das Zusammenhänge erkennt, proaktiv unterstützt, Wissen strukturiert und dabei die menschliche Autonomie und Privatsphäre vollständig respektiert.

---

## 2. Mission

Das System hat drei gleichwertige Säulen:

### 2.1 Familie & Persönlichkeit
- Unterstützung familiärer Dynamiken (Sven, Samira, Sineo)
- Begleitung von Wachstum, Mediation und Ritualen
- Schutz der familiären Privatsphäre durch höchste Sicherheitszonen

### 2.2 Kreativität & Selbstentfaltung
- Förderung kreativer Projekte (Musik, Video, Design, 3D-Druck)
- Coaching und Mentoring durch spezialisierte Agenten
- Dokumentation von Lernpfaden und Fortschritten

### 2.3 Business & Unternehmen
- Unterstützung bei Geschäftsprozessen und Projekten
- Enterprise-taugliche Workflows und Automatisierung
- Wissensmanagement für Kundenprojekte

---

## 3. Kernprinzipien

### 3.1 Local-First & Privatsphäre
Alle sensiblen Daten werden ausschließlich auf eigener Hardware verarbeitet und gespeichert. Cloud-APIs werden nur für nicht-sensible Aufgaben mit expliziter Freigabe genutzt.

### 3.2 Agenten-Autonomie mit menschlicher Kontrolle
Agenten können autonom Aufgaben ausführen, aber der Mensch behält jederzeit die volle Kontrolle. Keine Aktion mit externen Auswirkungen ohne menschliche Bestätigung (Human-in-the-Loop für kritische Entscheidungen).

### 3.3 Zonenbasierte Sicherheit
Das Fünf-Zonen-Modell (PUBLIC → SACRED) sorgt für klare Trennung zwischen öffentlich zugänglichen und streng vertraulichen Informationen. Jeder Inhalt trägt eine Zonenkennung.

### 3.4 Transparenz & Nachvollziehbarkeit
Alle Agenten-Entscheidungen werden in `core-events.log` dokumentiert. Das System erklärt seine Reasoning-Schritte auf Anfrage. Fehler werden offen protokolliert und als Lernmaterial behandelt.

### 3.5 AQAL-Integration (Integraler Ansatz)
Das System berücksichtigt alle vier Quadranten der integralen Theorie:
- **Ich** (Innere Welt, Erfahrungen, Werte)
- **Wir** (Familie, Beziehungen, Kultur)
- **Es** (Systeme, Technologie, Prozesse)
- **Sie** (Gesellschaft, Business, externe Systeme)

### 3.6 Wachstum & Kontinuierliches Lernen
Das System verbessert sich durch jede Interaktion. Lernpunkte werden in `experiences/learnings/` dokumentiert und in zukünftige Entscheidungen eingespeist.

---

## 4. Stakeholder

| Rolle | Person | Beschreibung |
|-------|--------|-------------|
| **Eigentümer & Primärnutzer** | Sven Darusi | Visionsträger, Hauptnutzer, Admin |
| **Familie** | Samira | Familienkontext, Mediation, Kreativität |
| **Familie** | Sineo | Creator-Content, Jugendprojekte |
| **Technische Mitarbeiter** | Kirobi-Agenten | KI-Agenten als "digitale Mitarbeiter" |
| **Community** | Open-Source-Beitragende | Externen Beiträge zu Nicht-SACRED-Bereichen |

---

## 5. Projektumfang

### 5.1 Im Scope
- Vollständige lokale KI-Infrastruktur (Ollama, Qdrant, PostgreSQL, Flowise)
- Multi-Agent-Orchestrierung mit Kirobi als Supervisor
- Strukturiertes Wissensmanagement (5-Schichten-Modell)
- Multimodale Interfaces (Text, Sprache, Bild, Video)
- Familien-Mediation und Persönlichkeits-Coaching
- Business-Automatisierung und Enterprise-Features
- Hardware-Monitoring und Selbstwartung

### 5.2 Außerhalb des Scopes (initial)
- Öffentliche Cloud-Deployments ohne explizite Anforderung
- Drittparteien-Datenspeicherung ohne Einwilligung
- Vollautomatische Entscheidungen in SACRED-Zonen
- Öffentliche API ohne Authentifizierung

---

## 6. Erfolgskriterien

| Metrik | Ziel | Zeithorizont |
|--------|------|-------------|
| System-Uptime | > 99% | MVP |
| Agent-Response-Zeit | < 5 Sek. (7B), < 30 Sek. (70B) | MVP |
| Wissensabruf-Präzision | > 85% | Phase 2 |
| Familien-Nutzungsfrequenz | > 3x pro Woche | Phase 2 |
| Automatisierungsrate | > 60% wiederkehrender Aufgaben | Phase 3 |

---

## 7. Risiken & Maßnahmen

| Risiko | Wahrscheinlichkeit | Impact | Maßnahme |
|--------|-------------------|--------|----------|
| Hardware-Ausfall | Mittel | Hoch | Automatisches Backup, RAID |
| Datenleck SACRED | Niedrig | Kritisch | Air-Gap für SACRED-Zonen |
| Agent-Halluzination | Hoch | Mittel | Observer-Agent + Human-in-Loop |
| Modell-Veralterung | Mittel | Niedrig | Model-Registry + Update-Plan |
| Komplexitäts-Drift | Hoch | Mittel | Regelmäßige Charter-Reviews |

---

## 8. Governance

- **Quartals-Review**: Überprüfung der Vision und Roadmap
- **Monatliche Retrospektive**: Kirobi-Agenten analysieren Systemperformance
- **Wöchentliches Check-in**: Sven überprüft `analytics/system-health.md`
- **Event-Log**: Kontinuierliche Dokumentation in `kirobi-core/core-events.log`

---

*Diese Charta wird bei wesentlichen Änderungen der Vision oder des Umfangs aktualisiert.*
