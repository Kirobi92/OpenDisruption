# Kontext-Management: Kirobi Core

**Zone:** WORKSPACE | **Version:** 1.0

---

## Kontext-Fenster-Management

### Kontext-Hierarchie
1. **Sitzungs-Kontext** (aktuell, vollständig)
2. **Kurzzeit-Gedächtnis** (letzte 7 Sitzungen, Summary)
3. **Langzeit-Gedächtnis** (Qdrant, semantische Suche)
4. **Canon** (kanonische Masterdokumente, immer aktuell)

### Kontext-Lade-Reihenfolge beim Start
1. Core-Identity und Core-Policies laden
2. Letztes Session-Summary aus PostgreSQL
3. Offene Aufgaben aus `experiences/projects/`
4. Aktuelle System-Health aus `analytics/system-health.md`
5. Relevant-Kontext via Qdrant-Suche

---

## Kontext-Regeln

### Was IMMER im Kontext ist
- Kirobi-Identität (core-identity.md)
- Aktive Policies (core-policies.md)
- Aktuelle Sitzungs-Informationen
- Zone des aktuellen Gesprächspartners

### Was auf Anfrage geladen wird
- Familien-Kontext (nur wenn relevant und Zone = FAMILY_PRIVATE erlaubt)
- Projektspezifische Dokumente
- Historische Entscheidungen und Learnings

### Was NIE automatisch geladen wird
- SACRED-Inhalte (nur mit expliziter Freigabe)
- Quarantäne-Inhalte
- Veraltete archivierte Dokumente

---

## Kontext-Komprimierung

Wenn der Kontext das Fenster überschreitet:
1. Älteste, nicht-kritische Informationen zuerst entfernen
2. Zusammenfassungen statt vollständiger Texte nutzen
3. Kritische Regeln und aktive Aufgaben niemals entfernen
4. Komprimierungs-Ereignis im Event-Log dokumentieren
