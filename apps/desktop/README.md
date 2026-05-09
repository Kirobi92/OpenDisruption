# apps/desktop

**Verantwortlich:** kirobi-coder  
**Status:** Scaffold / nicht als unterstützte Oberfläche freigegeben

## Stand

Tauri- + React-/Vite-Grundgerüst mit Sidebar, einfachem Dashboard, Chat-Stub und Einstellungen. Die App ist als Prototyp vorhanden, aber kein freigegebener Produktpfad.

## Was vorhanden ist

- `src/App.tsx` mit drei Views (`dashboard`, `chat`, `einstellungen`)
- Health-Check gegen `VITE_API_URL`
- einfacher Chat-Request gegen `/chat`

## Was fehlt

- Login/JWT-Flow
- produktionsreife Navigation und Persistenz
- Upload, Suche, Familienprofile
- fertig integriertes Tray-/Tauri-Paket

## Lokale Nutzung

```bash
cd apps/desktop
npm install
npm run dev
```

`npm run tauri:dev` benötigt zusätzlich die Rust-/Tauri-Toolchain.
