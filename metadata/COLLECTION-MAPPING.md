# Qdrant-Collection-Mapping: Kirobi / Disruptive OS

**Version:** 1.1 | **Zone:** WORKSPACE

---

## Collection-Übersicht

Kanonische Quelle im Code: `kirobi_core/qdrant_collections.py`. Init-Script,
Embedding-Service und Retrieval-Service müssen diese Namen verwenden, damit
abgeleitete Qdrant-Indizes rebuildfähig bleiben.

| Collection | Zone | Embedding-Modell | Dimensionen | Quell-Verzeichnisse |
|-----------|------|-----------------|------------|-------------------|
| `kirobi_public` | PUBLIC | nomic-embed-text | 768 | extracts/public/, research/ |
| `kirobi_workspace` | WORKSPACE | nomic-embed-text | 768 | extracts/workspace/, metadata/, technische Docs |
| `kirobi_code` | WORKSPACE | nomic-embed-text | 768 | services/, apps/, infra/, kirobi_core/ |
| `kirobi_canon` | WORKSPACE | nomic-embed-text | 768 | canon/ ohne Family-/Sacred-Inhalte |
| `kirobi_experiences` | WORKSPACE | nomic-embed-text | 768 | experiences/projects/, experiences/learnings/ |
| `kirobi_research` | WORKSPACE | nomic-embed-text | 768 | research/, freigegebene Web-Recherche |
| `kirobi_conversations` | WORKSPACE | nomic-embed-text | 768 | zonierte Konversations-Indizes |
| `kirobi_metadata` | WORKSPACE | nomic-embed-text | 768 | metadata/, Taxonomien, Registry-Auszüge |
| `kirobi_family` | FAMILY_PRIVATE | nomic-embed-text (lokal) | 768 | experiences/family/, canon/family/ |
| `kirobi_sacred` | SACRED | nomic-embed-text (lokal, verschlüsselt) | 768 | sacred/ nur mit expliziter Sven-Freigabe |

## Zone-zu-Collection-Regeln

| Zone | Retrieval-Collections | Schreib-Default |
|------|-----------------------|-----------------|
| PUBLIC | `kirobi_public` | `kirobi_public` |
| WORKSPACE | `kirobi_workspace`, `kirobi_code`, `kirobi_canon`, `kirobi_experiences`, `kirobi_research`, `kirobi_conversations`, `kirobi_metadata` | `kirobi_workspace` |
| FAMILY_PRIVATE | `kirobi_family` (lokal, berechtigungsgeprüft) | `kirobi_family` |
| QUARANTINE | keine Retrieval-Collection | kein Embedding ohne Review |
| SACRED | keine Standard-Retrieval-Collection | kein Standard-Flow; nur lokaler Sonderpfad mit Sven-Freigabe |

## Payload-Schema (Standard)

```json
{
  "id": "uuid-v4",
  "source_path": "relativer/pfad/zur/datei.md",
  "zone": "WORKSPACE",
  "tags": ["technik", "projekte"],
  "aqal_quadrant": "IT",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "agent_source": "hermes-extractor",
  "language": "de",
  "chunk_index": 0,
  "total_chunks": 5,
  "reviewed": false,
  "version": "1.0"
}
```

## Suchstrategien

### Semantic Search (Standard)
- Nutze `query_vectors` mit Embedding des Suchbegriffs
- Score-Threshold: 0.7 für relevante Treffer

### Hybrid Search (Empfohlen für Canon)
- Kombiniere Vektor-Suche mit Keyword-Filter
- Nutze Payload-Filter für Zone und Tags

### Filtered Search
- Zone-Filter: `{"key": "zone", "match": {"value": "WORKSPACE"}}`
- Tag-Filter: `{"key": "tags", "match": {"any": ["projekte", "technik"]}}`
