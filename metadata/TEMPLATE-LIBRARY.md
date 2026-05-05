# Template-Bibliothek-Index: Kirobi / Disruptive OS

**Version:** 1.0 | **Zone:** WORKSPACE

---

## Verfügbare Templates

| Template | Datei | Verwendung | Zone |
|---------|-------|-----------|------|
| Ordner-Schema | templates/folder-schema-template.md | Neue Verzeichnisse dokumentieren | WORKSPACE |
| Erfahrungs-Bericht | templates/experience-template.md | Erfahrungen und Ereignisse | alle |
| Projekt-Dokumentation | templates/project-template.md | Neue Projekte initiieren | WORKSPACE |
| Lernpunkt | templates/learning-template.md | Learnings dokumentieren | WORKSPACE |
| Analytics-Report | templates/analytics-template.md | Berichte erstellen | WORKSPACE |
| Canon-Dokument | templates/canon-template.md | Masterdokumente | WORKSPACE |
| Integration-Doku | templates/integration-template.md | Neue Integrationen | WORKSPACE |
| API-Record | templates/api-record-template.md | API im Katalog | WORKSPACE |
| Incident-Report | templates/incident-template.md | Vorfälle dokumentieren | WORKSPACE |

## Template-Verwendungsregeln

1. Templates immer aus `templates/` kopieren, nie direkt editieren
2. Alle Pflichtfelder (mit `REQUIRED` markiert) ausfüllen
3. Zone korrekt setzen bevor das Dokument gespeichert wird
4. `created_by` und `created_at` im Frontmatter setzen
5. Template-Version angeben um Updates nachvollziehen zu können

## Template-Versionen

Wenn ein Template aktualisiert wird:
- Version im Template-Header hochsetzen
- CHANGELOG.md aktualisieren
- Bestehende Dokumente müssen nicht migriert werden
- Neue Dokumente nutzen immer die neueste Template-Version
