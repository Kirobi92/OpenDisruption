"""Contract tests for the safe Personal-Memory ingestion pipeline.

These tests use only synthetic PUBLIC/WORKSPACE data. They do not call Ollama,
Qdrant, Postgres or external services. Their purpose is to pin the local
contracts between ingest, embeddings, Qdrant collection naming and retrieval
zone filters so future refactors cannot silently reopen private-zone flows.
"""

from fastapi import HTTPException

from kirobi_core.qdrant_collections import collection_for_document, collections_for_zone


def test_autonomous_pipeline_contract_for_workspace_document() -> None:
    """WORKSPACE documents flow through the canonical store/search contract."""
    import services.embeddings.main as embeddings
    import services.ingest.main as ingest
    import services.retrieval.main as retrieval

    ingest._validate_zone("WORKSPACE")
    embeddings._validate_autonomous_store_zone("WORKSPACE")

    collection = collection_for_document("WORKSPACE", "document")
    assert collection == "kirobi_workspace"
    assert collection in collections_for_zone("WORKSPACE")
    assert collection in retrieval.ZONE_COLLECTIONS["WORKSPACE"]
    assert retrieval._zone_filter("WORKSPACE") == {
        "must": [{"key": "zone", "match": {"value": "WORKSPACE"}}]
    }


def test_autonomous_pipeline_contract_blocks_sensitive_zones() -> None:
    """Sensitive zones are blocked before autonomous store/retrieval context."""
    import services.embeddings.main as embeddings
    import services.ingest.main as ingest
    import services.retrieval.main as retrieval

    for zone in ("FAMILY_PRIVATE", "QUARANTINE", "SACRED"):
        try:
            ingest._validate_zone(zone)
        except HTTPException as exc:
            assert exc.status_code == 403
        else:  # pragma: no cover - documents expected fail-closed branch
            raise AssertionError(f"ingest allowed sensitive zone {zone}")

        try:
            embeddings._validate_autonomous_store_zone(zone)
        except HTTPException as exc:
            assert exc.status_code == 403
        else:  # pragma: no cover - documents expected fail-closed branch
            raise AssertionError(f"embeddings store allowed sensitive zone {zone}")

    assert collections_for_zone("SACRED") == ()
    assert "SACRED" not in retrieval.ZONE_COLLECTIONS
    assert "QUARANTINE" not in retrieval.ZONE_COLLECTIONS


def test_public_pipeline_never_uses_workspace_or_private_collections() -> None:
    """PUBLIC retrieval is constrained to the public collection plus zone filter."""
    import services.retrieval.main as retrieval

    assert collections_for_zone("PUBLIC") == ("kirobi_public",)
    assert retrieval.ZONE_COLLECTIONS["PUBLIC"] == ["kirobi_public"]
    assert retrieval._zone_filter("PUBLIC") == {
        "must": [{"key": "zone", "match": {"value": "PUBLIC"}}]
    }


def test_pipeline_logs_do_not_include_document_content_templates() -> None:
    """Pipeline log templates must not interpolate raw document text."""
    import services.embeddings.main as embeddings
    import services.ingest.main as ingest

    safe_ingest_templates = (
        "Text ingest completed. job_id=%s zone=%s",
        "Text ingest failed. job_id=%s error=%s",
        "File ingest completed. job_id=%s zone=%s file=%s",
    )
    safe_embedding_templates = (
        "Embedding-Anfrage für Text der Länge %d",
        "GET /embed/single Anfrage für Text der Länge %d",
        "Speichere Dokument '%s' in Collection '%s' (Zone: %s)",
    )

    source = ingest.__loader__.get_source(ingest.__name__) + embeddings.__loader__.get_source(embeddings.__name__)
    assert all(template in source for template in safe_ingest_templates)
    assert all(template in source for template in safe_embedding_templates)
    assert "logger.info(request.text" not in source
    assert "logger.error(request.text" not in source
    assert "logger.info(text)" not in source
    assert "logger.error(text)" not in source
    assert "logger.info(f\"{text}" not in source
    assert "logger.error(f\"{text}" not in source
    assert "logger.info(request.text" not in source
    assert "logger.error(request.text" not in source
