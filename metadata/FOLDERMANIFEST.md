# Verzeichnis-Manifest: Kirobi / Disruptive OS

**Version:** 1.0 | **Zone:** WORKSPACE

Vollständige Liste aller Verzeichnisse mit Zonen, Zweck und verantwortlichen Agenten.

---

## Manifest

| Verzeichnis | Zone | Zweck | Agent |
|-------------|------|-------|-------|
| `metadata/` | WORKSPACE | Governance, Schemas, Policies | kirobi-architect |
| `kirobi-core/` | WORKSPACE | Kernidentität, Prompts, Routing | kirobi-core |
| `kirobi-core/core-prompts/` | WORKSPACE | Agent-System-Prompts | kirobi-core |
| `kirobi-core/schemas/` | WORKSPACE | Daten-Schemas | kirobi-architect |
| `sources/` | QUARANTINE→versch. | Rohdaten-Eingang | hermes-extractor |
| `sources/inbox/` | QUARANTINE | Unverarbeitete Eingänge | hermes-extractor |
| `sources/imports/` | QUARANTINE | Importierte Dateien | hermes-extractor |
| `sources/chats/` | WORKSPACE | Chat-Exports | hermes-extractor |
| `sources/apis/` | WORKSPACE | API-Responses | hermes-extractor |
| `sources/web-research/` | PUBLIC | Web-Recherche-Ergebnisse | research-crew |
| `sources/docs/` | WORKSPACE | Dokumente zum Verarbeiten | hermes-extractor |
| `sources/media/` | WORKSPACE | Medien-Dateien | hermes-extractor |
| `sources/audio/` | WORKSPACE | Audio-Dateien | voice-agent |
| `sources/video/` | WORKSPACE | Video-Dateien | hermes-extractor |
| `sources/images/` | WORKSPACE | Bild-Dateien | hermes-extractor |
| `sources/spreadsheets/` | WORKSPACE | Tabellen und Daten | hermes-extractor |
| `sources/models-3d/` | WORKSPACE | 3D-Modell-Dateien | hermes-extractor |
| `extracts/` | versch. | Verarbeitete Extrakte | hermes-extractor |
| `extracts/public/` | PUBLIC | Öffentliche Extrakte | hermes-extractor |
| `extracts/workspace/` | WORKSPACE | Arbeits-Extrakte | hermes-extractor |
| `extracts/family-private/` | FAMILY_PRIVATE | Familien-Extrakte | hermes-extractor |
| `extracts/research/` | PUBLIC/WORKSPACE | Recherche-Extrakte | research-crew |
| `extracts/business/` | WORKSPACE | Business-Extrakte | enterprise-agent |
| `extracts/technical/` | WORKSPACE | Tech-Extrakte | kirobi-coder |
| `extracts/media/` | WORKSPACE | Medien-Transkripte | hermes-extractor |
| `extracts/audio/` | WORKSPACE | Audio-Transkripte | voice-agent |
| `extracts/visual/` | WORKSPACE | Bild-Analysen | hermes-extractor |
| `extracts/structured/` | WORKSPACE | Strukturierte Daten | hermes-extractor |
| `clusters/` | versch. | Semantische Cluster | kirobi-core |
| `clusters/public/` | PUBLIC | Öffentliche Cluster | kirobi-core |
| `clusters/workspace/` | WORKSPACE | Arbeits-Cluster | kirobi-core |
| `clusters/family-private/` | FAMILY_PRIVATE | Familien-Cluster | samira-heart |
| `clusters/themes/` | WORKSPACE | Thematische Cluster | kirobi-observer |
| `clusters/projects/` | WORKSPACE | Projekt-Cluster | kirobi-architect |
| `clusters/models/` | WORKSPACE | Modell-Cluster | kirobi-architect |
| `clusters/patterns/` | WORKSPACE | Muster-Cluster | kirobi-observer |
| `clusters/conflicts/` | WORKSPACE | Konflikt-Cluster | kirobi-observer |
| `clusters/opportunities/` | WORKSPACE | Opportunitäten | kirobi-observer |
| `clusters/strategy/` | WORKSPACE | Strategie-Cluster | kirobi-architect |
| `canon/` | WORKSPACE | Kanonische Masterdokumente | kirobi-core |
| `canon/architecture/` | WORKSPACE | Architektur-Docs | kirobi-architect |
| `canon/identity/` | WORKSPACE | Identitäts-Docs | kirobi-core |
| `canon/policies/` | WORKSPACE | Policy-Docs | kirobi-core |
| `canon/models/` | WORKSPACE | Modell-Strategie | kirobi-architect |
| `canon/family/` | FAMILY_PRIVATE | Familien-Werte | samira-heart |
| `canon/business/` | WORKSPACE | Business-Docs | enterprise-agent |
| `canon/clients/` | WORKSPACE | Client-Docs | enterprise-agent |
| `canon/enterprise/` | WORKSPACE | Enterprise-Docs | enterprise-agent |
| `canon/research/` | PUBLIC | Forschungs-Docs | research-crew |
| `experiences/` | versch. | Erfahrungen & Lernpunkte | alle Agenten |
| `experiences/family/` | FAMILY_PRIVATE | Familien-Erfahrungen | samira-heart |
| `experiences/projects/` | WORKSPACE | Projekt-Erfahrungen | kirobi-core |
| `experiences/learnings/` | WORKSPACE | Lernpunkte | kirobi-observer |
| `experiences/experiments/` | WORKSPACE | Experimente | kirobi-coder |
| `experiences/knowledge/` | WORKSPACE | Wissensartikel | kirobi-core |
| `analytics/` | WORKSPACE | Metriken & Analysen | kirobi-observer |
| `integrations/` | WORKSPACE | Integrations-Docs | kirobi-ops |
| `apps/` | WORKSPACE | App-Code | kirobi-coder |
| `services/` | WORKSPACE | Service-Code | kirobi-coder |
| `infra/` | WORKSPACE | Infrastruktur | kirobi-ops |
| `models/` | WORKSPACE | Modell-Configs | kirobi-architect |
| `prompts/` | WORKSPACE | Prompt-Bibliothek | kirobi-core |
| `templates/` | PUBLIC | Dokument-Templates | kirobi-architect |
| `research/` | PUBLIC | Recherche-Sammlung | research-crew |
| `tests/` | WORKSPACE | Test-Suite | kirobi-coder |
| `quarantine/` | QUARANTINE | Quarantäne-Zone | hermes-extractor |
| `sacred/` | SACRED | Höchst-vertraulich | Nur Sven |
| `archive/` | WORKSPACE | Archiv | kirobi-core |
