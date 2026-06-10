# tools/ — CLI und Operator-Tools

`opendisruption-cli/`, `doctor/`, `templates/` (.gitignore-Template, Benutzerstruktur).

## Ultimate Control Plane

```bash
python3 tools/opendisruption_ultimate.py status --json
python3 tools/opendisruption_ultimate.py blueprint
python3 tools/opendisruption_ultimate.py graph --json
python3 tools/luki_qdrant_bootstrap.py --json
python3 tools/luki_mvp_server.py --host 127.0.0.1 --port 8411
```

Die CLI ist read-only und fasst KIROBI, LUKI, Shared Infra, Labs, Security,
Archive, Graphify und LazyCodex/OmO als pruefbare OpenDisruption-Feature-Planes
zusammen.

`luki_mvp_server.py` startet die minimale LUKI-Knowledge-Oberflaeche. Der
MVP-Endpunkt verweigert ohne belegte Retrieval-Quelle und schreibt nur Hashes in
`/Datenspeicher/OpenDisruption-Data/luki/audit/`.

Graphify ist als eigene Knowledge-Plane integriert: CLI `graph --json`,
MVP-API `/api/graphify`, UI-Karte und Runbook `docs/runbooks/graphify.md`.

`luki_qdrant_bootstrap.py` legt die allowlist-konforme Qdrant-Collection
`luki_knowledge_v1` lokal auf `127.0.0.1:6333` an.
