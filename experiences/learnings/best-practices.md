---
zone: WORKSPACE
type: best-practices
version: 1.0
---

# Best Practices: Kirobi / Disruptive OS

## Wissens-Ingestion

1. **Immer Frontmatter**: Jedes Dokument braucht Frontmatter mit Zone und Tags
2. **Quellen vermerken**: Originale Quelle immer dokumentieren
3. **Zone konservativ wählen**: Im Zweifel restriktivere Zone wählen
4. **Batch-Ingestion**: Große Mengen in Batches von max. 50 Dokumenten

## Agenten-Prompts

1. **Klare Rollenbeschreibung**: Wer bin ich? Was darf ich? Was nicht?
2. **Negative Beispiele**: Was soll der Agent NICHT tun?
3. **Ausgabe-Format**: Klares Format für strukturierte Outputs
4. **Eskalations-Pfad**: Was tut der Agent wenn er nicht weiterkommt?

## Sicherheit

1. **Secrets nie hardcoden**: Immer Umgebungsvariablen
2. **Zone-Check vor jeder Aktion**: Zone-Policy-Matrix konsultieren
3. **Human-in-the-Loop**: Lieber zu oft als zu selten
4. **Regelmäßige Backups**: Täglich für wichtige Daten

## Performance

1. **Modell-Auswahl**: Kleinstes Modell das die Aufgabe löst
2. **Kontext-Management**: Nicht mehr als nötig im Kontext halten
3. **Batch-Embeddings**: Embeddings in Batches verarbeiten
