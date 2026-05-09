# apps/mobile

**Verantwortlich:** kirobi-coder  
**Status:** Scaffold / nicht als unterstützte Oberfläche freigegeben

## Stand

Expo-/React-Native-Prototyp mit Splash Screen, Status-Tab und Platzhalter-Chat. Nützlich zum Experimentieren, aber noch kein supporteter Mobile-Client.

## Was vorhanden ist

- `App.tsx` mit Tabs für Chat, Status und Familie
- API-Health-Check gegen `EXPO_PUBLIC_API_URL`
- einfache UI-Struktur für spätere Mobile-Flows

## Was fehlt

- Authentifizierung
- echter Chat-Composer
- Upload / Suche / Voice-Flow
- Build- und Release-Pipeline

## Lokale Nutzung

```bash
cd apps/mobile
npm install
npm start
```
