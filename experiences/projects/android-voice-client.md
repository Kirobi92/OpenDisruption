---
project_id: ANDROID-VOICE-CLIENT
zone: WORKSPACE
status: geplant
priority: mittel
agent: kirobi-coder
tags: [mobile, android, voice, kotlin]
---

# Projekt: Android Voice Client

## Ziel
Native Android App die per Sprache mit Kirobi kommuniziert. Lokal-first: Audio-Verarbeitung auf dem Gerät, Server-Kommunikation nur für LLM-Anfragen.

## Konzept
- Wake-Word-Erkennung (on-device)
- Audio-Aufnahme und -Übertragung
- TTS-Wiedergabe
- Offline-Modus für Basis-Befehle

## Technologie-Optionen
- Kotlin + Jetpack Compose
- Rhasspy-Integration oder OpenHome
- Whisper.cpp für on-device STT

## Status
Konzeptphase – wird in Phase 2 implementiert
