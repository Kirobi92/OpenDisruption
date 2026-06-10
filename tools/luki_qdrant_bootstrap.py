#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, TypedDict

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
CONFIG_PATH: Final = REPO_ROOT / "products" / "luki" / "config" / "luki.json"


class CollectionPayload(TypedDict):
    vectors: dict[str, str | int]


class BootstrapResult(TypedDict):
    collection: str
    status: Literal["created", "exists"]
    qdrant_url: str


@dataclass(frozen=True, slots=True)
class QdrantConfig:
    collection: str
    dimensions: int
    qdrant_url: str
    allowed_collections: tuple[str, ...]


class QdrantBootstrapError(RuntimeError):
    pass


def _read_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        msg = f"{path} must contain a JSON object"
        raise TypeError(msg)
    return payload


def load_qdrant_config(path: Path = CONFIG_PATH) -> QdrantConfig:
    payload = _read_json(path)
    policy = payload.get("policy")
    runtime = payload.get("runtime")
    collection = payload.get("collection")
    dimensions = payload.get("embedding_dimensions")
    if not isinstance(policy, dict) or not isinstance(runtime, dict):
        msg = "luki.json requires policy and runtime objects"
        raise TypeError(msg)
    allowed_collections = policy.get("allowed_collections")
    qdrant_url = runtime.get("qdrant_url")
    if not isinstance(collection, str):
        msg = "collection must be a string"
        raise TypeError(msg)
    if not isinstance(dimensions, int) or dimensions <= 0:
        msg = "embedding_dimensions must be a positive integer"
        raise TypeError(msg)
    if not isinstance(allowed_collections, list) or not all(
        isinstance(item, str) for item in allowed_collections
    ):
        msg = "policy.allowed_collections must be a list of strings"
        raise TypeError(msg)
    if collection not in allowed_collections:
        msg = f"collection {collection!r} is not in the LUKI allowlist"
        raise QdrantBootstrapError(msg)
    if not isinstance(qdrant_url, str) or not qdrant_url.startswith("http://127.0.0.1:"):
        msg = "runtime.qdrant_url must point at a local 127.0.0.1 endpoint"
        raise QdrantBootstrapError(msg)
    return QdrantConfig(
        collection=collection,
        dimensions=dimensions,
        qdrant_url=qdrant_url.rstrip("/"),
        allowed_collections=tuple(allowed_collections),
    )


def collection_payload(dimensions: int) -> CollectionPayload:
    return {"vectors": {"size": dimensions, "distance": "Cosine"}}


def _request_json(method: str, url: str, payload: object | None = None) -> tuple[int, dict[str, object]]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, method=method)
    request.add_header("accept", "application/json")
    if body is not None:
        request.add_header("content-type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read().decode("utf-8")
            parsed = json.loads(raw) if raw else {}
            if not isinstance(parsed, dict):
                msg = f"Qdrant returned non-object JSON from {url}"
                raise QdrantBootstrapError(msg)
            return response.status, parsed
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8")
        parsed = json.loads(raw) if raw else {}
        if not isinstance(parsed, dict):
            parsed = {"error": raw}
        return error.code, parsed


def bootstrap_collection(config: QdrantConfig) -> BootstrapResult:
    collection_url = f"{config.qdrant_url}/collections/{config.collection}"
    status, _ = _request_json("GET", collection_url)
    if status == 200:
        return {"collection": config.collection, "status": "exists", "qdrant_url": config.qdrant_url}
    if status != 404:
        msg = f"Qdrant collection check failed with HTTP {status}"
        raise QdrantBootstrapError(msg)
    create_status, payload = _request_json("PUT", collection_url, collection_payload(config.dimensions))
    if create_status not in {200, 201}:
        msg = f"Qdrant collection create failed with HTTP {create_status}: {payload}"
        raise QdrantBootstrapError(msg)
    return {"collection": config.collection, "status": "created", "qdrant_url": config.qdrant_url}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="luki_qdrant_bootstrap")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = bootstrap_collection(load_qdrant_config())
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    print(f"{result['collection']}: {result['status']} at {result['qdrant_url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
