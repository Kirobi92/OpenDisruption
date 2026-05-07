---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-08
reviewed_by: pending
version: "1.0"
---

# Einstellungen-Seite (`/settings`)

Benutzerprofil, Erscheinungsbild, Passwort-Änderung und Zonen-Berechtigungen auf einen Blick.

## Was diese Seite tut

- **Profil-Anzeige**: Zeigt Benutzername, Anzeigename und Rolle des eingeloggten Nutzers
- **Theme-Umschalter**: Wechsel zwischen dunklem und hellem Design — Einstellung wird in `localStorage` gespeichert und sofort auf `<html>` angewendet
- **Passwort ändern**: Formular mit Validierung (Mindestlänge 8 Zeichen, Übereinstimmungs-Prüfung) — sendet an `POST /api/auth/change-password`
- **Zonen-Berechtigungen**: Zeigt die Lese- und Schreibrechte des Nutzers pro Zone (PUBLIC, WORKSPACE, FAMILY_PRIVATE, QUARANTINE, SACRED) — farblich kodiert
- **Abmelden**: Löscht `access_token` und `refresh_token` aus `localStorage` und leitet auf `/` weiter

## API-Endpunkte

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| `GET` | `/api/auth/me` | Profildaten des eingeloggten Nutzers |
| `GET` | `/api/auth/me/permissions` | Zonen-Berechtigungen (optional — Fehler wird ignoriert) |
| `POST` | `/api/auth/change-password` | Passwort ändern (`current_password`, `new_password`) |

## Authentifizierung

Erfordert ein gültiges JWT-Token in `localStorage` (`access_token`). Ohne Token wird auf `/` weitergeleitet.

## Bekannte Einschränkungen

- Theme-Einstellung ist nur lokal im Browser gespeichert, nicht serverseitig synchronisiert
- Der Permissions-Endpunkt ist optional; fehlt er, wird eine Hinweismeldung angezeigt
