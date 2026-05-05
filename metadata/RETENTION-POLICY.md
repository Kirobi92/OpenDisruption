# Datenaufbewahrungs-Policy: Kirobi / Disruptive OS

**Version:** 1.0 | **Zone:** WORKSPACE

---

## Aufbewahrungsfristen nach Zonen und Inhaltstypen

| Kategorie | Zone | Aufbewahrung | Grund |
|-----------|------|-------------|-------|
| Event-Logs | WORKSPACE | 2 Jahre | Debugging, Nachvollziehbarkeit |
| Fehler-Logs | WORKSPACE | 1 Jahr | Fehleranalyse |
| Agenten-Outputs | WORKSPACE | 6 Monate (roh) | Qualitätssicherung |
| Canon-Dokumente | WORKSPACE | Dauerhaft | Wissensbasis |
| Familien-Erfahrungen | FAMILY_PRIVATE | Dauerhaft | Familiengedächtnis |
| Sacred-Dokumente | SACRED | Dauerhaft | Kernidentität |
| Quarantäne-Einträge | QUARANTINE | 90 Tage | Dann: freigeben oder löschen |
| Roh-Importe | sources/ | 30 Tage nach Verarbeitung | Speicherplatz |
| Backups | archive/ | 30 Tage täglich, 1 Jahr monatlich | Recovery |
| Chat-Exports | sources/chats/ | 6 Monate | Kontext |
| Analytics | analytics/ | 1 Jahr detailliert, 5 Jahre aggregiert | Trends |

## Lösch-Prozess

1. Automatisches Flaggen durch kirobi-observer bei Ablauf
2. kirobi-core bestätigt Lösch-Vorschlag
3. Sven-Freigabe bei FAMILY_PRIVATE und SACRED
4. Löschen mit Audit-Log-Eintrag
5. Backup-Prüfung vor Löschung von Canon-Inhalten

## DSGVO-Compliance

- Personenbezogene Daten werden nur in FAMILY_PRIVATE und SACRED gespeichert
- Kein Sharing mit Dritten ohne explizite Zustimmung
- Alle externen APIs erhalten ausschließlich anonymisierte oder PUBLIC-Daten
- Recht auf Löschung: Sven kann jederzeit Löschung aller Daten verlangen
