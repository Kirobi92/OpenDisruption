# Clusters – Semantisch geclusterte Wissensknoten

**Zone:** Gemischt | **Verantwortlich:** kirobi-core

## Zweck
Semantisch zusammengeführte Wissenscluster aus den Extrakten. Hier werden verwandte Informationen aus verschiedenen Quellen zu kohärenten Wissenseinheiten zusammengefasst.

## Unterschied zu Extracts

| Ebene | Inhalt | Quelle |
|-------|--------|--------|
| `sources/` | Rohdaten | Original-Dateien |
| `extracts/` | Strukturierte Extrakte | Eine Quelle je Datei |
| `clusters/` | Semantische Cluster | Mehrere Quellen zusammengeführt |
| `canon/` | Kanonische Wahrheit | Beste Synthese aller Cluster |

## Cluster-Typen

| Verzeichnis | Beschreibung |
|-------------|-------------|
| `public/` | Öffentliche Wissenscluster |
| `workspace/` | Arbeits-Wissenscluster |
| `family-private/` | Familien-Wissenscluster |
| `themes/` | Thematische Cluster (AQAL-basiert) |
| `projects/` | Projekt-Cluster |
| `models/` | Modell- und Technologie-Cluster |
| `patterns/` | Erkannte Muster (kirobi-observer) |
| `conflicts/` | Widersprüchliche Informationen |
| `opportunities/` | Erkannte Chancen |
| `strategy/` | Strategische Cluster |
