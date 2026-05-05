# Embedding- und Chunking-Schema: Kirobi / Disruptive OS

**Version:** 1.0 | **Zone:** WORKSPACE

---

## Embedding-Modelle

### Standard-Konfiguration
```yaml
default_embedding:
  model: nomic-embed-text
  dimensions: 768
  language: de+en
  
quality_embedding:
  model: bge-m3
  dimensions: 1024
  language: multilingual (100+)
  
cloud_embedding:  # Nur PUBLIC
  model: text-embedding-3-small
  dimensions: 1536
  provider: openai
```

---

## Chunking-Regeln

### Markdown-Dokumente
```yaml
markdown:
  strategy: recursive_character
  chunk_size: 1000
  chunk_overlap: 200
  separators: ["\n## ", "\n### ", "\n\n", "\n", " "]
  min_chunk_size: 100
```

### Fließtext (Prosa)
```yaml
prose:
  strategy: semantic
  chunk_size: 800
  chunk_overlap: 150
  preserve_sentences: true
```

### Code-Dateien
```yaml
code:
  strategy: syntax_aware
  chunk_by: function_or_class
  max_chunk_size: 2000
  include_docstrings: true
  language_detection: auto
```

### Strukturierte Daten (JSON, YAML, CSV)
```yaml
structured:
  strategy: record_based
  max_records_per_chunk: 10
  include_schema: true
```

### PDFs und Dokumente
```yaml
documents:
  strategy: page_based
  overlap_pages: 1
  extract_tables: true
  ocr_fallback: true
  ocr_model: tesseract_de
```

---

## Metadaten-Schema für Chunks

Jeder Chunk in Qdrant enthält folgende Payload-Felder:

```json
{
  "source_file": "pfad/zur/quelldatei.md",
  "source_type": "markdown|pdf|code|audio|image",
  "zone": "PUBLIC|WORKSPACE|FAMILY_PRIVATE|QUARANTINE|SACRED",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "language": "de|en|mixed",
  "chunk_index": 0,
  "total_chunks": 5,
  "tags": ["tag1", "tag2"],
  "aqal_quadrant": "I|WE|IT|ITS",
  "agent_source": "hermes-extractor",
  "reviewed": false,
  "version": "1.0"
}
```

---

## Collections-Übersicht (Qdrant)

| Collection | Embedding-Modell | Dimensionen | Zone |
|-----------|-----------------|------------|------|
| `kirobi_public` | nomic-embed-text | 768 | PUBLIC |
| `kirobi_workspace` | bge-m3 | 1024 | WORKSPACE |
| `kirobi_family` | bge-m3 | 1024 | FAMILY_PRIVATE |
| `kirobi_canon` | bge-m3 | 1024 | WORKSPACE |
| `kirobi_experiences` | bge-m3 | 1024 | WORKSPACE/FAMILY |
| `kirobi_code` | nomic-embed-text | 768 | WORKSPACE |
| `kirobi_sacred` | bge-m3 (encrypted) | 1024 | SACRED |
