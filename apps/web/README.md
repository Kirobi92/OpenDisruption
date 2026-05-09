# apps/web — Family PWA

**Verantwortlich:** kirobi-coder  
**Status:** Aktiv / produktionswürdig für das Familien-Web-UI

## Zweck

Die zentrale, unterstützte Web-Oberfläche für Familie und Alltag. Die App läuft als Next.js-15-PWA hinter Caddy und spricht primär mit `auth` und `api`.

## Unterstützte Flächen

| Route | Zweck |
|---|---|
| `/` | Login / Einstieg |
| `/chat` | Haupt-Chat mit sichtbarer MVP-Zone und Dateianhängen |
| `/search` | Wissenssuche über Retrieval + lokalen Upload-Fallback |
| `/upload` | Datei-/Text-Upload mit Zonenwahl und Index-Metadaten |
| `/settings` | Profil, Theme, Passwortwechsel, Berechtigungen |
| `/status` | Stack-Status und Links zu Nebensystemen |
| `/health` | Health-Probe für Caddy / Monitoring |

`/knowledge-graph` ist eine interne Demo-Seite, keine Kernoberfläche.

## Laufzeit

- **Kanonischer Einstieg:** `https://kirobi.local/` bzw. `http://kirobi.local/`
- **Direkter Dev-Port:** `http://localhost:3002`
- In Compose läuft die App als Service `web`; im Produktivpfad terminieren Caddy-Rewrites `/api/*`

## Entwicklung

```bash
cd apps/web
npm install
npm run dev
```

Für lokales `next dev` können `WEB_AUTH_UPSTREAM` und `WEB_API_UPSTREAM` gesetzt werden; im Compose-/Caddy-Betrieb bleiben sie leer.

## Checks

```bash
cd apps/web
npm run lint
npm run build
```

## Nicht enthalten

- Kein Root-Node-Workspace im Repo
- Kein Desktop-/Mobile-Wrapper in diesem Verzeichnis
- Kein Ersatz für Open WebUI oder Flowise
