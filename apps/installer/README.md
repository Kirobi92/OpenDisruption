# apps/installer – Setup-Wizard

**Verantwortlich:** installer-agent  
**Status:** Aktiv

## Zweck
Interaktiver Setup-Wizard für die Erstinstallation von Kirobi. Geführte Einrichtung für neue Nutzer.

## Funktionen

1. **Voraussetzungs-Check**: Docker, NVIDIA-Treiber, Festplattenspeicher
2. **Konfiguration**: .env-Datei ausfüllen
3. **Service-Start**: Docker-Compose starten
4. **Modell-Download**: Gewünschte Modelle herunterladen
5. **Test**: Alle Services testen
6. **Onboarding**: Erste Schritte zeigen

## Verwendung

```bash
make init
# oder direkt:
bash infra/scripts/bootstrap.sh
```
