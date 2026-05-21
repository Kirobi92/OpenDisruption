# User Folder Template

Die kanonische Benutzerdatenstruktur fuer OpenDisruption liegt unter:

`/Datenspeicher/OpenDisruption_Datenstruktur/Benutzer-Ordner/`

Diese Struktur soll pro Benutzer das komplette personalisierte Leben abbilden: Rohimporte, Wissen, Projekte, Erfahrungen, Referenzen, Dokumente, Medien, Agentenprofil, semantische Langzeitspeicherung und den Aufbau eines digitalen Zwillings.

## Warum diese Struktur?

OpenDisruption ist dateisystembasiert. Das bedeutet:

- das Dateisystem bleibt die **kanonische Quelle**
- Qdrant, Postgres und Agent-Memory sind **abgeleitete Indizes**
- jede Person braucht eine sauber getrennte, langfristig stabile Wissens- und Dokumentenablage

Die Struktur ist so gebaut, dass sie gleichzeitig drei Dinge erlaubt:

1. **schnelle Erfassung** neuer Inhalte
2. **saubere spaetere Verdichtung** in Wissen und Agenten-Memory
3. **personalisierte Assistenz** bis hin zum Digital-Twin-Aufbau

## Abdeckung des OpenDisruption-Funktionsumfangs

| Bereich | Ordner | Zweck |
|---|---|---|
| Schnelleingang | `00-Inbox/` | Rohimporte, Uploads, Chat-Exporte, OCR, Medien-Rohmaterial |
| Verifiziertes Wissen | `01-Wissen/` | Biografie, Werte, Muster, Timeline, Stammbaum, Digital Twin |
| Aktive Umsetzung | `02-Projekte/` | Vorhaben ueber Familie, Business, Kreativitaet, Alltag, Lernen |
| Selbstreflexion | `03-Erfahrungen/` | Tagebuch, Emotionen, Coaching, Learnings, Retros |
| Stabile Referenzen | `04-Referenzen/` | Kontakte, Konten, Services, Literatur, Vorlagen, Geraete |
| Langzeitablage | `Dokumente/` | Nachweise, Geburtsurkunden, Stammbuch, Vertrage, Scans |
| Multimodale Inhalte | `Medien/` | Fotos, Videos, Audio, Musik, Design, 3D |
| Agentische Personalisierung | `agent/` | `profil.yaml`, Memory, Hermes-Configs, Ingest-Queues, Digital Twin |
| Historie | `05-Archiv/` | Import-Snapshots, Exporte, ersetzte Inhalte |

## Rohimport-Strategie

Alle nicht sofort strukturierten Inhalte landen zuerst in `00-Inbox/`.

Dort ist nach Quellen und Medienarten getrennt:

- `02-Chat-Exporte/` fuer Chatverlaeufe von OpenAI, Anthropic, Google, Meta, xAI, Perplexity, GitHub Copilot und anderen
- `03-Dokumente-Roh/` fuer PDF, Office, Tabellen, Datenbanken, EPUB/eBooks, Archive, OCR-Scans
- `04-Medien-Roh/` fuer Fotos, Videos, Audio und Musik
- `05-Web-und-Research-Importe/` fuer Webmaterial und Recherchen
- `06-Messenger-und-Soziale-Kanaele/` fuer Kommunikations-Exporte
- `07-Review-Queue/` und `08-Import-Protokolle/` fuer Sichtung und Nachvollziehbarkeit

## Wichtige Klarstellung zum Ist-Stand

Die Ordnerstruktur ist bereits auf den **Ziel-Funktionsumfang** ausgelegt, aber nicht jeder Parser existiert heute schon.

Aktuell verifiziert im Code:

- `services/ingest/main.py` akzeptiert heute vor allem **txt, md und pdf**
- `services/retrieval/main.py` ermoeglicht zone-aware semantische Suche
- `services/personal-agents/app/main.py` nutzt den Benutzerordner bereits als kanonische Quelle fuer `profil.yaml` und `memory/knowledge_graph.json`

Das heisst:

- **alles** kann heute schon sauber abgelegt und fuer spaetere Extraktion vorbereitet werden
- aber **nicht jede Dateiklasse** wird bereits automatisch extrahiert oder eingebettet

Die Struktur ist also bewusst zukunftsfest fuer:

- Office/Excel/CSV/DB-Import
- Chat-Export-Pipelines
- OCR-gestuetzte Dokumentenextraktion
- Medienanalyse fuer Bild/Video/Audio
- Stammbaum- und Beziehungsgraphen
- emotional intelligentes Tagebuch
- Digital-Twin-Synthese

## Sicherheitsgedanke

Besonders vertrauliche Originale gehoeren in `Dokumente/99-Vertraulich-SACRED/` oder muessen lokal entsprechend klassifiziert werden.

Das ersetzt keine Zonenkontrolle in Services, erleichtert aber die sichere Ablage im Dateisystem.

## Bootstrap

Das Script `infra/scripts/bootstrap-user-folder-structure.sh` erstellt:

- die Musterstruktur `_Muster-Benutzerstruktur`
- fehlende Ordner in bestehenden Benutzerverzeichnissen
- fehlende Basisdateien wie `README.md`, `AGENTS.md`, `agent/profil.yaml`, `agent/memory/knowledge_graph.json`

Beispiele:

```bash
bash infra/scripts/bootstrap-user-folder-structure.sh all-existing
bash infra/scripts/bootstrap-user-folder-structure.sh template-only
bash infra/scripts/bootstrap-user-folder-structure.sh user Alex
```

Das Script ist **nicht-destruktiv** und ueberschreibt bestehende Dateien nicht.

Fuer die komplette Datenwurzel inklusive globaler Bereiche und `ORDNERINFO.md` in jedem Ordner siehe auch `docs/GLOBAL-DATA-STRUCTURE.md` und `infra/scripts/bootstrap-global-data-structure.sh`.
