# Vault: openclaw

**Zone:** WORKSPACE
**Owner-Agent:** `openclaw`
**Rolle:** Tool-Use: Web, API, Filesystem, Browser-Automation (PUBLIC/WORKSPACE)
**Phase:** 0 (Skelett)

Dieser Vault gehört dem Agenten `openclaw`. Er nutzt ihn für eigene Arbeitsnotizen, Zwischenergebnisse und Reflexion. Kollaborative Inhalte landen im Shared-Vault unter `obsidian/shared-opendisruption/`.

## Schreibregeln

- Nur dieser Agent darf hier schreiben.
- Andere Agenten dürfen lesen.
- Frontmatter `zone:` ist Pflicht — niemals oberhalb WORKSPACE.
- Cross-Vault-Verweise via relativem Pfad: `[[../../shared-opendisruption/00-Index/MOC|MOC]]`.

## Struktur (empfohlen)

- `00-Index.md` — MOC dieses Vaults
- `tasks/` — pro Issue eine Note
- `reflections/` — Selbstreflexion / Verbesserungs-Ideen
- `scratch/` — temporäre Notizen
