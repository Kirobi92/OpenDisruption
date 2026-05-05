# Qdrant-Collection-Mapping: Kirobi / Disruptive OS

**Version:** 1.0 | **Zone:** WORKSPACE

---

## Collection-Übersicht

| Collection | Zone | Embedding-Modell | Dimensionen | Quell-Verzeichnisse |
|-----------|------|-----------------|------------|-------------------|
| `kirobi_public` | PUBLIC | nomic-embed-text | 768 | extracts/public/, research/ |
| `kirobi_workspace` | WORKSPACE | bge-m3 | 1024 | extracts/workspace/, canon/, metadata/ |
| `kirobi_family` | FAMILY_PRIVATE | bge-m3 | 1024 | experiences/family/, canon/family/ |
| `kirobi_experiences` | WORKSPACE | bge-m3 | 1024 | experiences/projects/, experiences/learnings/ |
| `kirobi_code` | WORKSPACE | nomic-embed-text | 768 | services/, apps/, infra/ |
| `kirobi_canon` | WORKSPACE | bge-m3 | 1024 | canon/ (alle) |
| `kirobi_sacred` | SACRED | bge-m3 (enc) | 1024 | sacred/ |

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
