# Metadata – Governance & Systemwissen

## Zweck
Dieses Verzeichnis enthält alle Governance-Dokumente, Schemas, Policies und Registry-Dateien für Kirobi / Disruptive OS. Es ist das "Nervensystem" des Systems – hier werden die Regeln definiert, nach denen alle anderen Teile funktionieren.

## Inhalt

| Datei | Beschreibung |
|-------|-------------|
| `SYSTEMCONFIG.md` | Systemweite Konfigurationsparameter |
| `EMBEDDINGSCHEMA.md` | Embedding- und Chunking-Regeln für Qdrant |
| `FOLDERMANIFEST.md` | Vollständiges Verzeichnis-Manifest mit Zonen |
| `AGENTREGISTRY.md` | Alle 14 Agenten mit Rollen und Berechtigungen |
| `BOOT-SEQUENCE.md` | System-Boot-Sequenz |
| `MODEL-REGISTRY.md` | Alle verfügbaren Modelle (lokal und Cloud) |
| `ZONE-POLICY-MATRIX.md` | Zonenbasierte Zugriffsrechte |
| `REVIEW-MATRIX.md` | Review-Anforderungen nach Inhalt und Zone |
| `RETENTION-POLICY.md` | Datenaufbewahrungs-Policies |
| `BACKUP-POLICY.md` | Backup-Strategie und -Zeitplan |
| `SECURITY-CLASSIFICATION.md` | Sicherheitsklassifizierungs-Leitfaden |
| `EVENT-TAXONOMY.md` | Event-Typen und -Taxonomie |
| `TAG-TAXONOMY.md` | Tag-System |
| `AQAL-TAXONOMY.md` | Integrale Theorie-Taxonomie |
| `COLLECTION-MAPPING.md` | Qdrant-Collection-Mapping |
| `API-CATALOG-SCHEMA.md` | API-Katalog-Schema |
| `TEMPLATE-LIBRARY.md` | Template-Bibliothek-Index |

## Zugriffsrechte / Zonen
- **Zone:** WORKSPACE (für strukturelle Teile), SACRED (für ZONE-POLICY-MATRIX)
- **Lesen:** Alle Agenten
- **Schreiben:** Nur `kirobi-core`, `kirobi-architect` mit Human-Review
- **Löschen:** Nie ohne explizite Freigabe

## Verantwortliche Agenten
- **Primär:** `kirobi-architect` (Schema-Design und -Pflege)
- **Review:** `kirobi-core` (Supervisor-Freigabe)
- **Monitoring:** `kirobi-observer` (Konsistenz-Prüfungen)

## Aktualisierungs-Policy
- Schemas und Policies werden versioniert (semantische Versionierung)
- Änderungen erfordern einen Kommentar mit Datum und Grund
- Breaking Changes erfordern Migration-Guides
