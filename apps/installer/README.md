# apps/installer – Setup-Wizard

**Verantwortlich:** installer-agent  
**Status:** Docs-only / kein fertiger Installer-Client im Repo

## Zweck
Reservierter Platz für eine spätere Installer-Oberfläche. Der produktive Setup-Pfad läuft aktuell **nicht** über diese App, sondern über Shell-/Make-Workflows.

## Aktueller Stand

- keine lauffähige UI-App
- kein eigener Build- oder Dev-Entry
- README/Planungsfläche für spätere Installer-Arbeit

## Verwendung

```bash
bash install.sh --dry-run --no-clone --auto --skip-checks --no-pull --no-models --no-start --profile=cpu
make init
make bootstrap
```
