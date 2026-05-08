---
zone: WORKSPACE
created_by: keycodi
created_at: 2026-05-08
reviewed_by: pending
version: "1.0"
---

# Personal-Memory Demo-Daten

Dieser Ordner beschreibt synthetische Demo-Datenbereiche für den späteren
persönlichen Speicher in OpenDisruption.

Er enthält **keine echten privaten Inhalte**. Er dient als sicherer Startpunkt,
um Manifest-Erzeugung, Ingestion, Retrieval, Review-Gates und Insight-Jobs zu
testen, bevor Sven echte Daten einliest.

## Aktive synthetische Demo-Bereiche

| Bereich | Pfad | Zone | Zweck |
|---|---|---|---|
| Public Demo | `extracts/public/demo/` | PUBLIC | öffentlich teilbare Beispielinhalte |
| Workspace Demo | `extracts/workspace/demo/` | WORKSPACE | technische Projekt- und Systemnotizen |
| Insight Seeds | `research/personal-ai/demo-insight-seeds.md` | WORKSPACE | synthetische Erkenntnis-Rohdaten |

## Gesperrte spätere Bereiche

Diese Bereiche werden hier nur beschrieben. Sie werden nicht autonom befüllt:

- FAMILY_PRIVATE: braucht Sven-Freigabe und familiäre Kontextentscheidung
- QUARANTINE: braucht Review, weil Inhalte untrusted sind
- SACRED: bleibt Sven-only und wird nicht simuliert

## Demo-Ablauf

1. Manifest für Demo-Dateien erzeugen.
2. Nur PUBLIC/WORKSPACE-Einträge stagen.
3. Optional in Ingest/Embeddings speichern.
4. Retrieval mit Zone-Filter prüfen.
5. Insights als Vorschläge erzeugen, nicht als Wahrheit.

## Stop-Regel

Sobald echte private Inhalte ins Spiel kommen, endet der autonome Demo-Modus.
