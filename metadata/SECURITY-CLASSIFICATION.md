# Sicherheitsklassifizierungs-Leitfaden: Kirobi / Disruptive OS

**Version:** 1.0 | **Zone:** WORKSPACE

---

## Klassifizierungs-Übersicht

Das Fünf-Zonen-Modell klassifiziert alle Inhalte nach Vertrauen und Sensitivität.

## Zone 1: PUBLIC

**Beschreibung:** Inhalte, die öffentlich geteilt werden können.

**Beispiele:**
- Blog-Posts und öffentliche Artikel
- Open-Source-Code
- Öffentliche Projektbeschreibungen
- Allgemeine Tutorials und How-Tos
- Forschungs-Zusammenfassungen ohne persönliche Daten

**Verboten in PUBLIC:**
- Persönliche Daten (Namen, Adressen, etc.)
- Geschäftsgeheimnisse
- Passwörter oder Zugangsdaten

## Zone 2: WORKSPACE

**Beschreibung:** Arbeitskontext – intern, aber nicht hochsensibel.

**Beispiele:**
- Technische Dokumentation
- Projekt-Pläne und Roadmaps
- Agent-Konfigurationen
- API-Dokumentation
- Business-Analysen (ohne Kundendaten)

**Schutzmaßnahmen:**
- Kein öffentliches Teilen ohne Prüfung
- Cloud-Sync nur mit expliziter Bestätigung

## Zone 3: FAMILY_PRIVATE

**Beschreibung:** Familiäre Inhalte – vertraulich, nur im Familienkreis.

**Beispiele:**
- Familien-Erfahrungen und -Erinnerungen
- Mediation-Protokolle und Grenzen
- Familien-Rituale und Traditionen
- Persönliche Wachstums-Notizen

**Schutzmaßnahmen:**
- Kein Cloud-Sync unter keinen Umständen
- Kein Zugriff durch Business-Agenten
- Alle Zugriffe werden geloggt

## Zone 4: QUARANTINE

**Beschreibung:** Ungeprüfte oder potenziell problematische Inhalte.

**Prozess:**
- Keine Einbettung in Qdrant bis Freigabe
- Regelmäßige Review-Zyklen (alle 30 Tage)
- Nach Review: Hochstufen oder löschen

## Zone 5: SACRED

**Beschreibung:** Höchste Vertraulichkeit – nur direkter Zugriff von Sven.

**Beispiele:**
- Kern-Werte und tiefste Überzeugungen
- Trauma-Verarbeitung und Therapie-Notizen
- Grenzen und persönliche Schutzregeln
- Handoff-Dokumente für Notfälle

**Schutzmaßnahmen:**
- Verschlüsselte Speicherung
- Kein Agent-Zugriff ohne explizite Freigabe
- Air-Gap-Option (offline möglich)
- Physische Sicherung des Zugriffsschlüssels

---

## Klassifizierungs-Entscheidungsbaum

```
Ist der Inhalt öffentlich teilbar?
  → Ja: PUBLIC
  → Nein:
    Ist es Arbeit/Technik ohne persönliche Bezüge?
      → Ja: WORKSPACE
      → Nein:
        Ist es familiär/persönlich aber nicht existenziell?
          → Ja: FAMILY_PRIVATE
          → Nein:
            Ist es ungeprüft/unsicher?
              → Ja: QUARANTINE
              → Nein: SACRED
```
