"""Tests für die kanonische Qdrant-Collection-Policy."""

from kirobi_core.qdrant_collections import (
    collection_for_document,
    collection_names,
    collections_for_zone,
    unknown_collections,
)


def test_collection_names_are_canonical_and_unique():
    names = collection_names()

    assert len(names) == len(set(names))
    assert "kirobi_public" in names
    assert "kirobi_workspace" in names
    assert "kirobi_family" in names
    assert "kirobi_sacred" in names


def test_public_retrieval_only_uses_public_collection():
    assert collections_for_zone("PUBLIC") == ("kirobi_public",)


def test_workspace_retrieval_uses_workspace_collections_only():
    collections = set(collections_for_zone("WORKSPACE"))

    assert "kirobi_workspace" in collections
    assert "kirobi_code" in collections
    assert "kirobi_family" not in collections
    assert "kirobi_sacred" not in collections


def test_document_type_mapping_matches_retrieval_names():
    assert collection_for_document("PUBLIC", "document") == "kirobi_public"
    assert collection_for_document("WORKSPACE", "document") == "kirobi_workspace"
    assert collection_for_document("WORKSPACE", "code") == "kirobi_code"
    assert collection_for_document("FAMILY_PRIVATE", "note") == "kirobi_family"
    assert collection_for_document("SACRED", "document") == "kirobi_sacred"


def test_unknown_collections_detects_drift():
    assert unknown_collections(["kirobi_workspace", "kirobi_workspace_document"]) == {
        "kirobi_workspace_document"
    }
