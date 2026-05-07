"""
agents/obsidian/agent.py — Obsidian-Vault-Agent (Phase 3)

Zuständigkeit (aus AGENT-DECISION-MATRIX.md §B.2):
  - Vault-Read (Note-Abruf)
  - Vault-Write (neue Note / Update) — FAMILY_PRIVATE nur mit Approval
  - Knowledge-Graph-Query (Link-Graph aus Markdown-Backlinks)
  - Daily-Note-Generierung
  - MOC (Map of Content) Generierung

Erlaubte Zonen:
  Input:  PUBLIC, WORKSPACE, FAMILY_PRIVATE (lokal-only)
  Output: PUBLIC, WORKSPACE, FAMILY_PRIVATE (lokal-only)

Invariante: FAMILY_PRIVATE nur bei KIROBI_EGRESS_ALLOWED=false (lokal).
            Sacred-Pfade sind immer abgelehnt.
            Keine Embeddings: Qdrant-Collections werden von hermes-extractor befüllt,
            ObsidianAgent liest/schreibt nur Markdown-Dateien.

Zone: WORKSPACE
Autor: keycodi
Version: 2.0 (Phase 3 — echtes Vault-CRUD)
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents._base.agent import BaseAgent, AgentResult, Task

# Default-Vault-Pfad: obsidian/ im Repo (Dev-Default laut ROADMAP.md Phase 3)
DEFAULT_VAULT_PATH = Path("obsidian")

# Qdrant-Collection-Mapping (aus metadata/COLLECTION-MAPPING.md)
# Zone → Collection-Name → erlaubte Embedding-Dimensionen
ZONE_TO_COLLECTION: dict[str, dict[str, Any]] = {
    "PUBLIC": {"collection": "kirobi_public", "model": "nomic-embed-text", "dim": 768},
    "WORKSPACE": {"collection": "kirobi_workspace", "model": "bge-m3", "dim": 1024},
    "FAMILY_PRIVATE": {"collection": "kirobi_family", "model": "bge-m3", "dim": 1024},
}

# Sacred-Pfade sind immer verboten
_SACRED_NAMES = frozenset({"sacred"})


def _is_sacred_path(path_str: str) -> bool:
    """Prüft ob ein Pfad in den sacred/-Bereich zeigt."""
    if not path_str:
        return False
    p = Path(path_str)
    parts = {str(part).lower() for part in p.parts}
    return bool(parts & _SACRED_NAMES)


def _extract_backlinks(content: str) -> list[str]:
    """Extrahiert [[Wikilinks]] aus Markdown-Inhalt."""
    return re.findall(r"\[\[([^\]|#]+?)(?:\|[^\]]+?)?\]\]", content)


def _make_frontmatter(zone: str, agent_id: str, extra: dict[str, Any] | None = None) -> str:
    """Erzeugt YAML-Frontmatter für eine neue Note."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        "---",
        f"zone: {zone}",
        f"agent: {agent_id}",
        f"created: {now}",
        f"updated: {now}",
    ]
    if extra:
        for k, v in extra.items():
            if isinstance(v, list):
                lines.append(f"{k}: [{', '.join(str(i) for i in v)}]")
            else:
                lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


class ObsidianAgent(BaseAgent):
    """
    Vault-Agent: Liest und schreibt den Obsidian-Vault, generiert MOCs und Daily Notes.

    Unterstützte task_type-Werte:
        vault_read           — Note lesen
        vault_write          — Note schreiben / anlegen
        vault_delete         — Note löschen (reversibel via git)
        vault_list           — Alle Notes in einem Verzeichnis auflisten
        vault_query_links    — Backlinks einer Note ermitteln
        daily_note           — Daily-Note für heute anlegen/aktualisieren
        moc                  — Map-of-Content für einen Agenten generieren
        zone_collection_map  — Mapping Zone → Qdrant-Collection zurückgeben

    Headless-Aufruf:
        agent = ObsidianAgent()
        result = agent.run(Task(task_type="vault_read", payload={"path": "agents/opencode/00-Index.md"}))
    """

    agent_id = "obsidian"
    allowed_input_zones = frozenset({"PUBLIC", "WORKSPACE", "FAMILY_PRIVATE"})
    allowed_output_zones = frozenset({"PUBLIC", "WORKSPACE", "FAMILY_PRIVATE"})

    APPROVAL_REQUIRED_ZONES = frozenset({"FAMILY_PRIVATE"})
    APPROVAL_REQUIRED_WRITE_TYPES = frozenset({"vault_write", "vault_delete"})

    def __init__(
        self,
        context_db=None,
        event_log_path: str = "kirobi-core/core-events.log",
        vault_path: Path | str | None = None,
    ) -> None:
        super().__init__(context_db=context_db, event_log_path=event_log_path)
        self._vault_path = Path(
            vault_path
            or os.environ.get("KIROBI_VAULT_PATH", str(DEFAULT_VAULT_PATH))
        )

    # ─── handle() ─────────────────────────────────────────────────────────────

    def handle(self, task: Task) -> AgentResult:
        """Dispatch auf die spezifische Vault-Operation."""
        payload = task.payload

        # Sacred-Pfad-Check (unabhängig von Zone)
        target_path = str(payload.get("path", ""))
        if target_path and _is_sacred_path(target_path):
            return self._refuse(task, f"REFUSE: Vault-Zugriff auf Sacred-Pfad '{target_path}' ist nicht erlaubt.")

        # FAMILY_PRIVATE + Schreiben → Approval
        if (
            task.task_type in self.APPROVAL_REQUIRED_WRITE_TYPES
            and task.zone in self.APPROVAL_REQUIRED_ZONES
            and not task.approval_token
        ):
            return self._refuse(
                task,
                f"Vault-Write in Zone '{task.zone}' erfordert Human-Approval-Token.",
            )

        dispatch = {
            "vault_read": self._vault_read,
            "vault_write": self._vault_write,
            "vault_delete": self._vault_delete,
            "vault_list": self._vault_list,
            "vault_query_links": self._vault_query_links,
            "daily_note": self._daily_note,
            "moc": self._moc,
            "zone_collection_map": self._zone_collection_map,
        }

        handler = dispatch.get(task.task_type)
        if handler is None:
            # Unbekannter Task-Typ → graceful fallback
            return AgentResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                zone=task.zone,
                success=True,
                payload={
                    "task_type": task.task_type,
                    "vault_path": str(self._vault_path),
                    "status": "unknown_task_type_noop",
                },
                confidence=0.5,
            )

        return handler(task)

    # ─── Vault-CRUD ───────────────────────────────────────────────────────────

    def _vault_read(self, task: Task) -> AgentResult:
        path = self._resolve_path(task.payload.get("path", ""))
        if path is None:
            return self._refuse(task, "vault_read erfordert 'path' im Payload.")

        if not path.exists():
            return self._refuse(task, f"Note nicht gefunden: {path}")

        if not path.is_file():
            return self._refuse(task, f"Pfad ist kein File: {path}")

        content = path.read_text(encoding="utf-8")
        backlinks = _extract_backlinks(content)

        return AgentResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            zone=task.zone,
            success=True,
            payload={
                "path": str(path.relative_to(self._vault_path)),
                "content": content,
                "backlinks": backlinks,
                "size_bytes": len(content.encode("utf-8")),
            },
            confidence=1.0,
        )

    def _vault_write(self, task: Task) -> AgentResult:
        path_str = task.payload.get("path", "")
        if not path_str:
            return self._refuse(task, "vault_write erfordert 'path' im Payload.")

        path = self._resolve_path(path_str)
        if path is None:
            return self._refuse(task, f"Ungültiger Pfad: {path_str}")

        content: str = task.payload.get("content", "")
        prepend_frontmatter: bool = task.payload.get("prepend_frontmatter", False)

        if prepend_frontmatter and not content.startswith("---"):
            fm_extra = task.payload.get("frontmatter_extra", {})
            content = _make_frontmatter(task.zone, self.agent_id, fm_extra) + content

        path.parent.mkdir(parents=True, exist_ok=True)
        existed = path.exists()
        path.write_text(content, encoding="utf-8")

        return AgentResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            zone=task.zone,
            success=True,
            payload={
                "path": str(path.relative_to(self._vault_path)),
                "created": not existed,
                "size_bytes": len(content.encode("utf-8")),
            },
            confidence=1.0,
        )

    def _vault_delete(self, task: Task) -> AgentResult:
        path_str = task.payload.get("path", "")
        if not path_str:
            return self._refuse(task, "vault_delete erfordert 'path' im Payload.")

        path = self._resolve_path(path_str)
        if path is None or not path.exists():
            return self._refuse(task, f"Note zum Löschen nicht gefunden: {path_str}")

        # Nur Dateien löschen, keine Verzeichnisse
        if not path.is_file():
            return self._refuse(task, f"vault_delete nur für Files, nicht Verzeichnisse: {path}")

        path.unlink()
        return AgentResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            zone=task.zone,
            success=True,
            payload={"deleted": str(path.relative_to(self._vault_path))},
            confidence=1.0,
        )

    def _vault_list(self, task: Task) -> AgentResult:
        subdir = task.payload.get("path", "")
        base = self._vault_path / subdir if subdir else self._vault_path
        if not base.exists():
            return self._refuse(task, f"Verzeichnis nicht gefunden: {base}")

        files = [
            str(f.relative_to(self._vault_path))
            for f in sorted(base.rglob("*.md"))
            if not _is_sacred_path(str(f))
        ]
        return AgentResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            zone=task.zone,
            success=True,
            payload={"files": files, "count": len(files)},
            confidence=1.0,
        )

    def _vault_query_links(self, task: Task) -> AgentResult:
        """Gibt alle Backlinks einer Note zurück."""
        path = self._resolve_path(task.payload.get("path", ""))
        if path is None or not path.exists():
            return self._refuse(task, f"Note nicht gefunden: {task.payload.get('path')}")

        content = path.read_text(encoding="utf-8")
        outgoing = _extract_backlinks(content)

        # Eingehende Links: alle Notes die auf diese Note verweisen
        note_name = path.stem
        incoming: list[str] = []
        for md_file in self._vault_path.rglob("*.md"):
            if md_file == path:
                continue
            try:
                other_content = md_file.read_text(encoding="utf-8")
            except OSError:
                continue
            if note_name in _extract_backlinks(other_content):
                incoming.append(str(md_file.relative_to(self._vault_path)))

        return AgentResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            zone=task.zone,
            success=True,
            payload={
                "path": str(path.relative_to(self._vault_path)),
                "outgoing_links": outgoing,
                "incoming_links": incoming,
            },
            confidence=1.0,
        )

    # ─── Daily Note + MOC ─────────────────────────────────────────────────────

    def _daily_note(self, task: Task) -> AgentResult:
        """Legt die Daily-Note für heute an (idempotent)."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        note_path = self._vault_path / "shared-opendisruption" / "99-Inbox" / f"{today}-daily.md"

        if note_path.exists():
            return AgentResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                zone=task.zone,
                success=True,
                payload={
                    "path": str(note_path.relative_to(self._vault_path)),
                    "created": False,
                    "note": "Daily-Note bereits vorhanden",
                },
                confidence=1.0,
            )

        title = task.payload.get("title", f"Daily Note {today}")
        sections = task.payload.get("sections", ["## Ziele", "## Erledigte Tasks", "## Notizen"])

        content = _make_frontmatter(
            zone=task.zone,
            agent_id=self.agent_id,
            extra={"tags": ["daily", "inbox"], "date": today},
        )
        content += f"# {title}\n\n"
        content += "\n\n".join(f"{s}\n\n" for s in sections)

        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text(content, encoding="utf-8")

        return AgentResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            zone=task.zone,
            success=True,
            payload={
                "path": str(note_path.relative_to(self._vault_path)),
                "created": True,
                "date": today,
            },
            confidence=1.0,
        )

    def _moc(self, task: Task) -> AgentResult:
        """
        Generiert/aktualisiert den Map-of-Content (00-Index.md) für einen Agenten.
        Scannt obsidian/agents/<agent_name>/ und listet alle Markdown-Dateien.
        """
        agent_name = task.payload.get("agent", "")
        if not agent_name:
            return self._refuse(task, "moc erfordert 'agent' im Payload (z.B. 'opencode').")

        agent_dir = self._vault_path / "agents" / agent_name
        if not agent_dir.exists():
            # Verzeichnis anlegen
            agent_dir.mkdir(parents=True, exist_ok=True)

        # Alle Notes im Agenten-Verzeichnis
        notes = sorted(
            f.relative_to(agent_dir)
            for f in agent_dir.rglob("*.md")
            if f.name != "00-Index.md"
        )

        now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        content = _make_frontmatter(
            zone=task.zone,
            agent_id=self.agent_id,
            extra={"tags": ["moc", "index"], "updated": now},
        )
        content += f"# {agent_name} — Vault Map of Content\n\n"
        content += f"_Automatisch generiert von ObsidianAgent am {now}_\n\n"
        content += "## Notes\n\n"

        if notes:
            for note in notes:
                stem = note.stem.replace("-", " ").replace("_", " ").title()
                content += f"- [[{note.with_suffix('')}|{stem}]]\n"
        else:
            content += "_noch keine Notes_\n"

        content += "\n## Verweise\n\n"
        content += "- [[../../shared-opendisruption/00-Index/MOC|Shared OpenDisruption MOC]]\n"
        content += f"- [[../../../keycodi/ROADMAP|KeyCodi Roadmap]]\n"

        moc_path = agent_dir / "00-Index.md"
        moc_path.write_text(content, encoding="utf-8")

        return AgentResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            zone=task.zone,
            success=True,
            payload={
                "path": str(moc_path.relative_to(self._vault_path)),
                "agent": agent_name,
                "notes_listed": len(notes),
                "updated": now,
            },
            confidence=1.0,
        )

    # ─── Zone→Collection-Mapping ──────────────────────────────────────────────

    def _zone_collection_map(self, task: Task) -> AgentResult:
        """Gibt das Mapping Zone → Qdrant-Collection zurück."""
        zone_filter = task.payload.get("zone")
        if zone_filter:
            mapping = {zone_filter: ZONE_TO_COLLECTION.get(zone_filter)}
            if mapping[zone_filter] is None:
                return self._refuse(task, f"Keine Collection für Zone '{zone_filter}' definiert.")
        else:
            mapping = dict(ZONE_TO_COLLECTION)

        return AgentResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            zone=task.zone,
            success=True,
            payload={"zone_collection_map": mapping},
            confidence=1.0,
        )

    # ─── Hilfsmethoden ────────────────────────────────────────────────────────

    def _resolve_path(self, path_str: str) -> Path | None:
        """Löst einen relativen oder absoluten Pfad gegen den Vault auf."""
        if not path_str:
            return None
        p = Path(path_str)
        if not p.is_absolute():
            p = self._vault_path / p
        return p

    def _refuse(self, task: Task, reason: str) -> AgentResult:
        return AgentResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            zone=task.zone,
            success=False,
            error=reason,
            confidence=0.0,
        )
