# services/auth

**Verantwortlich:** kirobi-coder  
**Status:** Aktiv

## Zweck

FastAPI-Authentifizierungsservice für Family PWA und andere lokale Clients. Verwaltet Benutzer, JWTs, Sessions und zonenbezogene Rechte.

## Kernaufgaben

- erster Bootstrap-Admin aus `.env`
- Login via Form (`/token`) und JSON (`/login`)
- User-/Permissions-Endpunkte für die PWA
- Passwortwechsel, Logout, Token-Validierung und Benutzeranlage
- Audit-Log für Auth-Aktionen

## Wichtige Endpunkte

| Methode | Pfad |
|---|---|
| `GET` | `/health`, `/me`, `/me/permissions`, `/verify` |
| `POST` | `/token`, `/login`, `/change-password`, `/logout`, `/register` |

## Hinweise

- CORS ist auf lokale Origins (`localhost`, `*.local`, LAN, Tailscale) begrenzt, nicht auf `*`
- Legt `users`, `zone_permissions`, `user_sessions`, `user_preferences` und `audit_log` bei Bedarf selbst an
