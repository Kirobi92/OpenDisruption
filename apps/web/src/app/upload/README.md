---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-08
reviewed_by: pending
version: "1.0"
---

# Upload-Seite (`/upload`)

Ermöglicht das Hochladen von Dateien in den Kirobi-Stack mit expliziter Zonen-Zuweisung.

## Was diese Seite tut

- **Drag-and-Drop-Upload**: Dateien können direkt in die Drop-Zone gezogen oder per Klick ausgewählt werden
- **Zonen-Auswahl**: Jede Datei wird einer Sicherheitszone zugewiesen (`PUBLIC`, `WORKSPACE`, `FAMILY_PRIVATE`) — die Zone bestimmt, wer die Datei lesen darf
- **Upload-Fortschritt**: Echtzeit-Fortschrittsanzeige pro Datei via `axios` `onUploadProgress`
- **Dateiliste**: Zeigt alle bereits hochgeladenen Dateien mit Typ-Icon, Dateigröße, Zone und Datum
- **Download**: Direkt-Download einzelner Dateien über `/api/uploads/{id}/download`

## Unterstützte Dateitypen

`image/*`, `application/pdf`, `.doc`, `.docx`, `.txt`, `.md`

## API-Endpunkte

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| `POST` | `/api/upload` | Datei hochladen (`multipart/form-data`, Felder: `file`, `zone`) |
| `GET` | `/api/uploads` | Liste aller hochgeladenen Dateien |
| `GET` | `/api/uploads/{id}/download` | Datei herunterladen |

## Authentifizierung

Erfordert ein gültiges JWT-Token in `localStorage` (`access_token`). Ohne Token wird auf `/` weitergeleitet.

## Bekannte Einschränkungen

- Der `/api/uploads`-Endpunkt ist optional — fehlt er, bleibt die Dateiliste leer (kein Fehler)
- Keine Mehrfach-Auswahl per Tastatur (nur Maus/Touch und Drag-and-Drop)
- Dateigröße wird clientseitig nicht vorab validiert
