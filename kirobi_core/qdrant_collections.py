"""Canonical Qdrant collection names for Kirobi services.

The filesystem remains the source of truth; Qdrant collections are derived
indices. This module keeps init scripts, embedding writes and retrieval reads
on the same naming policy so RAG cannot drift silently.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


VECTOR_SIZE = 768


@dataclass(frozen=True)
class CollectionSpec:
    """Declarative Qdrant collection specification."""

    name: str
    zone: str
    description: str
    vector_size: int = VECTOR_SIZE


COLLECTION_SPECS: tuple[CollectionSpec, ...] = (
    CollectionSpec("kirobi_public", "PUBLIC", "Öffentliche Dokumente und freigegebene Inhalte"),
    CollectionSpec("kirobi_workspace", "WORKSPACE", "Allgemeine Workspace-Dokumente"),
    CollectionSpec("kirobi_code", "WORKSPACE", "Code-Artefakte aus Apps, Services und Infra"),
    CollectionSpec("kirobi_canon", "WORKSPACE", "Kanonische Workspace-Dokumente"),
    CollectionSpec("kirobi_experiences", "WORKSPACE", "Projekt- und Lern-Erfahrungen ohne Family-Privates"),
    CollectionSpec("kirobi_research", "WORKSPACE", "Recherche-Ergebnisse und technische Analysen"),
    CollectionSpec("kirobi_conversations", "WORKSPACE", "Zonierte Konversations-Indizes"),
    CollectionSpec("kirobi_metadata", "WORKSPACE", "Metadaten, Taxonomien und Systemwissen"),
    CollectionSpec("nutzi_enventa", "WORKSPACE", "Nutzi eNVenta ERP Wissensbasis (4559 Kapitel)"),
    CollectionSpec("kirobi_family", "FAMILY_PRIVATE", "Lokale Family-Private Indizes"),
    CollectionSpec("kirobi_user_sven", "FAMILY_PRIVATE", "Svens persönliche Wissensbasis (Second Brain Vault)"),
    CollectionSpec("kirobi_user_samira", "FAMILY_PRIVATE", "Samiras persönliche Wissensbasis (Second Brain Vault)"),
    CollectionSpec("kirobi_user_sineo", "FAMILY_PRIVATE", "Sineos persönliche Wissensbasis (Second Brain Vault)"),
    CollectionSpec("kirobi_sacred", "SACRED", "Lokaler verschlüsselter SACRED-Sonderindex"),
)


ZONE_COLLECTIONS: dict[str, tuple[str, ...]] = {
    "PUBLIC": ("kirobi_public",),
    "WORKSPACE": (
        "kirobi_workspace",
        "kirobi_code",
        "kirobi_canon",
        "kirobi_experiences",
        "kirobi_research",
        "kirobi_conversations",
        "kirobi_metadata",
        "nutzi_enventa",
    ),
    "FAMILY_PRIVATE": ("kirobi_family", "kirobi_user_sven", "kirobi_user_samira", "kirobi_user_sineo"),
}


_DOC_TYPE_COLLECTIONS: dict[tuple[str, str], str] = {
    ("PUBLIC", "document"): "kirobi_public",
    ("PUBLIC", "documents"): "kirobi_public",
    ("WORKSPACE", "document"): "kirobi_workspace",
    ("WORKSPACE", "documents"): "kirobi_workspace",
    ("WORKSPACE", "note"): "kirobi_workspace",
    ("WORKSPACE", "notes"): "kirobi_workspace",
    ("WORKSPACE", "code"): "kirobi_code",
    ("WORKSPACE", "canon"): "kirobi_canon",
    ("WORKSPACE", "experience"): "kirobi_experiences",
    ("WORKSPACE", "experiences"): "kirobi_experiences",
    ("WORKSPACE", "research"): "kirobi_research",
    ("WORKSPACE", "conversation"): "kirobi_conversations",
    ("WORKSPACE", "conversations"): "kirobi_conversations",
    ("WORKSPACE", "metadata"): "kirobi_metadata",
    ("FAMILY_PRIVATE", "document"): "kirobi_family",
    ("FAMILY_PRIVATE", "documents"): "kirobi_family",
    ("FAMILY_PRIVATE", "note"): "kirobi_family",
    ("FAMILY_PRIVATE", "notes"): "kirobi_family",
    ("SACRED", "document"): "kirobi_sacred",
    ("SACRED", "documents"): "kirobi_sacred",
}


def collection_names() -> tuple[str, ...]:
    """Return all canonical collection names in creation order."""

    return tuple(spec.name for spec in COLLECTION_SPECS)


def collection_descriptions() -> dict[str, str]:
    """Return ``name -> description`` for init scripts and diagnostics."""

    return {spec.name: spec.description for spec in COLLECTION_SPECS}


def collections_for_zone(zone: str) -> tuple[str, ...]:
    """Return searchable collections for a zone.

    Unknown zones return an empty tuple so callers can deny/fail closed.
    ``SACRED`` is intentionally absent from retrieval collections.
    """

    return ZONE_COLLECTIONS.get(zone.upper(), ())


def collection_for_document(zone: str, doc_type: str = "document") -> str:
    """Return the canonical write collection for a zone/doc-type pair."""

    normalized_zone = zone.upper()
    normalized_type = doc_type.strip().lower() or "document"
    mapped = _DOC_TYPE_COLLECTIONS.get((normalized_zone, normalized_type))
    if mapped:
        return mapped
    return f"kirobi_{normalized_zone.lower()}_{normalized_type}"


def unknown_collections(names: Iterable[str]) -> set[str]:
    """Return names that are not part of the canonical collection set."""

    canonical = set(collection_names())
    return {name for name in names if name not in canonical}
