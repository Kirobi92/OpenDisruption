# Global Data Structure

Die kanonische OpenDisruption-Datenwurzel liegt unter:

`/Datenspeicher/OpenDisruption_Datenstruktur/`

Sie dient als dateibasierte Gesamtstruktur fuer:

- personenspezifische Benutzerbereiche
- geteiltes Wissen und Familien-/Business-Kontext
- externe Importe und Integrationen
- Agenten- und Orchestrierungsdaten
- Systemkonfiguration und Betriebsdaten
- Backups, Exporte und Vorlagen

## Ziel

Jeder relevante Ordner soll eine **menschen- und agentenlesbare Beschreibung** enthalten. Dafuer wird in jedem Ordner eine `ORDNERINFO.md` erzeugt.

Diese Datei beschreibt:

- was in dem Ordner zu finden ist
- welchem Zweck und Bereich er dient
- welche Nachbar- oder Unterbereiche von ihm betroffen sind
- wie Menschen den Ordner nutzen
- wie KI-Agenten mit dem Ordner umgehen sollen

## Top-Level-Struktur

| Ordner | Zweck |
|---|---|
| `Benutzer-Ordner/` | kanonische Lebens-, Dokument-, Medien- und Agentenbereiche pro Person |
| `Geteilte-Wissensbasis/` | gemeinsames Wissen, Regeln, Familie, Business, Quellen |
| `Integrationen-und-Importe/` | Rohimporte, Chat-Exporte, OCR, Web- und Messenger-Material |
| `Orchestrierung-und-Agenten/` | Hermes, KeyCodi, Workflows, Policies, Audit |
| `Systemkonfiguration/` | Routing, Modelle, Sicherheitsregeln, Umgebungsstruktur |
| `Systembetrieb-und-Indizes/` | Ingest-Protokolle, Suchindizes, Metriken, Healthchecks |
| `Backups-und-Exporte/` | Sicherungen, Audits, Snapshots, Migrationen |
| `_Vorlagen/` | wiederverwendbare Muster und Mapping-Vorlagen |
| `eNVenta-Agent/` | spezialisierter Integrationsbereich fuer eNVenta-Material |

## Benutzerordner

Die Benutzerordner bleiben der wichtigste personalisierte Bereich. Dort werden weiterhin pro Benutzer unter anderem gepflegt:

- `00-Inbox/`
- `01-Wissen/`
- `02-Projekte/`
- `03-Erfahrungen/`
- `04-Referenzen/`
- `05-Archiv/`
- `Dokumente/`
- `Medien/`
- `agent/`

## Bootstrap

Das Script `infra/scripts/bootstrap-global-data-structure.sh` erzeugt:

1. die globale Top-Level-Struktur
2. die Benutzerstruktur ueber das bestehende User-Bootstrap-Script
3. eine `ORDNERINFO.md` in **jedem** Ordner unterhalb der Datenwurzel

Aufruf:

```bash
bash infra/scripts/bootstrap-global-data-structure.sh
```

## Wichtige Klarstellung

Die Struktur ist auf den **kompletten Ziel-Funktionsumfang** von OpenDisruption ausgelegt. Nicht jede Automatisierung existiert schon produktiv fuer jede Dateiklasse.

Aktuell verifiziert:

- Benutzerprofile und `knowledge_graph.json` laufen bereits kanonisch ueber `Benutzer-Ordner/`
- Ingest verarbeitet heute vor allem `txt`, `md` und `pdf`
- Retrieval arbeitet zone-aware auf den semantischen Indizes

Die Datenstruktur ist damit absichtlich **groesser als der heutige Parser-Stand**, damit OpenDisruption sauber wachsen kann, ohne spaeter chaotisch umzubauen.
