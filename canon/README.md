# Canon – Kanonische Masterdokumente

**Zone:** WORKSPACE (PUBLIC für öffentliche Teile, FAMILY_PRIVATE für Familie) | **Verantwortlich:** kirobi-core

## Zweck
Canon enthält die "kanonische Wahrheit" des Kirobi-Systems. Diese Dokumente repräsentieren den aktuellen, verifizierten Stand des Wissens zu jedem Bereich. Sie werden aus Clustern synthetisiert und sind die primäre Referenz für alle Agenten.

## Prinzip: Kanonizität

Ein Canon-Dokument ist:
- Die beste verfügbare Synthese zu einem Thema
- Verifiziert durch Human-Review
- Versioniert mit Änderungshistorie
- Widerspruchsfrei (Konflikte sind gelöst)

## Canon-Dokumente (Root)

| Datei | Beschreibung | Zone |
|-------|-------------|------|
| `self-model-master.md` | Kirobis Selbstmodell | WORKSPACE |
| `architecture-master.md` | System-Architektur | WORKSPACE |
| `platform-vision-master.md` | Plattform-Vision | WORKSPACE |
| `family-values-master.md` | Familienwerte | FAMILY_PRIVATE |
| `security-master.md` | Sicherheits-Masterdok. | WORKSPACE |
| `model-strategy-master.md` | Modell-Strategie | WORKSPACE |
| `api-catalog-master.md` | API-Katalog | WORKSPACE |
| `project-portfolio-master.md` | Projekt-Portfolio | WORKSPACE |
| `business-universe-master.md` | Business-Universum | WORKSPACE |

## Unterverzeichnisse

| Verzeichnis | Inhalt |
|-------------|--------|
| `architecture/` | Architektur-Entscheidungen und -Diagramme |
| `identity/` | Kirobi-Identität und -Werte |
| `policies/` | Operative Policies |
| `models/` | Modell-Strategie und -Evaluierungen |
| `family/` | Familien-Werte und -Agreements |
| `business/` | Business-Strategie und -Prozesse |
| `clients/` | Kunden-Dokumentation |
| `enterprise/` | Enterprise-Features und -Anforderungen |
| `research/` | Forschungs-Erkenntnisse |

## Update-Prozess

1. Konflikt oder neue Erkenntnisse werden in `clusters/` identifiziert
2. kirobi-core schlägt Canon-Update vor
3. Human-Review und Freigabe durch Sven
4. Update mit Versionsnummer und Datum
5. Event-Log-Eintrag
