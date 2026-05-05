# Review-Matrix: Kirobi / Disruptive OS

**Version:** 1.0 | **Zone:** WORKSPACE

---

## Review-Anforderungen nach Inhalt und Zone

| Inhaltstyp | PUBLIC | WORKSPACE | FAMILY_PRIVATE | SACRED |
|------------|--------|-----------|---------------|--------|
| Neue Dokumente | Kein Review | kirobi-observer | Sven | Sven (persönlich) |
| Schema-Änderungen | kirobi-architect | kirobi-architect + Sven | N/A | N/A |
| Agent-Prompts | kirobi-core | kirobi-core + Sven | N/A | N/A |
| Canon-Updates | kirobi-core | kirobi-core + Sven | Sven | Sven |
| Policy-Änderungen | Sven | Sven | Sven | Sven |
| Infrastruktur | kirobi-ops | kirobi-ops + Sven | N/A | N/A |

## Review-Prozess

1. Agent erstellt Dokument mit `reviewed_by: pending`
2. kirobi-observer erkennt Review-Bedarf
3. Benachrichtigung an verantwortliche Person
4. Review abgeschlossen: `reviewed_by: [Name]`, Datum eintragen
5. Bei Ablehnung: Dokument in `quarantine/review-needed/`

## SLA für Reviews

| Priorität | Frist | Eskalation |
|-----------|-------|-----------|
| Kritisch (SACRED) | Sofort | Direkte Benachrichtigung |
| Hoch (Policy) | 24 Stunden | kirobi-observer Alert |
| Normal | 7 Tage | Wöchentliche Erinnerung |
| Niedrig | 30 Tage | Monatlicher Bericht |
