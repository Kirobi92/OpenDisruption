# Ordner-Schema: clusters/

**Zone:** Gemischt | **Version:** 1.0

## Cluster-Dokument-Format

```markdown
---
cluster_id: YYYY-MM-DD_cluster-name
sources: 
  - extracts/workspace/datei1.md
  - extracts/workspace/datei2.md
created_by: kirobi-core
created_at: ISO-8601
zone: WORKSPACE
confidence: 0.0-1.0
conflict: false
tags: []
---

# Cluster: [Name]

## Synthese
[Zusammenführung der Kernaussagen]

## Quell-Konsistenz
[Wie konsistent sind die Quellen?]

## Konflikte
[Widersprüche zwischen Quellen]

## Empfehlung für Canon
[Soll dieses Cluster in canon/ aufgenommen werden?]
```
