---
zone: WORKSPACE
type: experiment-log
tags: [qdrant, vector, performance]
---

# Qdrant Optimierungs-Experimente

## EXP-VDB-001: Chunk-Size Optimierung

**Datum:** Ausstehend  
**Hypothese:** Chunk-Size von 512 Tokens mit 50-Token-Overlap ist optimal für deutsche Texte  
**Methode:** Teste 256, 512, 1024 Token-Chunks mit identischen Query-Sets  
**Metriken:** Precision@5, Recall@10, Latenz  
**Status:** geplant

## EXP-VDB-002: Hybrid-Search Evaluation

**Datum:** Ausstehend  
**Hypothese:** Hybrid-Search (Dense + Sparse) verbessert Retrieval für fachspezifische Texte  
**Status:** geplant
