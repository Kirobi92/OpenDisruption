# KIDI Engine — Collective Intelligence Design

**Version:** 0.1 (Phase 0 — design only)
**Zone:** WORKSPACE
**Status:** Draft for review
**Owner:** kirobi-architect
**Last Updated:** 2026-05-06

---

## 1. What KIDI is (and is not)

**KIDI** (Kollektive Integrale Disruptive Intelligenz) is a **synthesis layer**, not a model and not a separate vector store. It reads zone-tagged entries from the ContextDB, optionally retrieves related embeddings from the existing Qdrant collections, and writes back a single synthesized entry with a confidence score and a list of source entry IDs.

**KIDI is:**
- A pure function over ContextDB entries: `synthesize(entries) -> SynthesisEntry`.
- Auditable: every output cites its inputs by ContextDB key.
- Zone-preserving: an output is at most as permissive as its most restrictive input.

**KIDI is not:**
- A model. It does not fine-tune or train weights.
- A new database. It writes only to ContextDB and (optionally) the existing Qdrant collections.
- An autonomous decider. It produces synthesis entries; routing decisions stay in `keybrodi`.

---

## 2. Inputs

KIDI consumes ContextDB entries with this shape (defined fully in `CONTEXT-WINDOW.md`):

```
{
  "key":        "ctx:<zone>:<agent>:<uuid>",
  "agent":      "opencode" | "openclaw" | "hermes-reasoner" | "obsidian" | ...,
  "zone":       "PUBLIC" | "WORKSPACE" | "FAMILY_PRIVATE" | "QUARANTINE" | "SACRED",
  "timestamp":  "ISO-8601",
  "task_id":    "<uuid>",
  "payload":    { ... },
  "confidence": 0.0–1.0,
  "embedding_ref": { "collection": "kirobi_workspace", "point_id": "<uuid>" } | null
}
```

The `embedding_ref` always points into a collection from `metadata/COLLECTION-MAPPING.md`. KIDI **never** creates a new collection.

---

## 3. Synthesis algorithm (Phase 4 target)

The Phase 4 implementation will be deliberately conservative:

1. **Filter by zone.** Caller specifies the maximum zone (e.g. `WORKSPACE`). Inputs above that zone are dropped *before* any processing.
2. **Group by `task_id`** (or by semantic similarity if `task_id` is absent and embeddings are available).
3. **Confidence-weighted merge.** Numeric fields are weighted-averaged by `confidence`; categorical fields take the highest-confidence value; conflicts above a threshold are flagged rather than silently resolved.
4. **Cite sources.** Output entry includes `sources: [<input keys>]`.
5. **Downgrade with logging.** If the output zone is lower than any input zone, log a `ZONE_DOWNGRADE` event to `kirobi-core/core-events.log` with the input keys.

No clustering, no prompt-time LLM calls, no learned weights in Phase 4. Adding any of those is a separate proposal.

---

## 4. Outputs

```
{
  "key":        "ctx:<zone>:kidi:<uuid>",
  "agent":      "kidi",
  "zone":       "<= max(input zones)",
  "timestamp":  "ISO-8601",
  "task_id":    "<uuid>",
  "payload":    {
    "summary":     "<text>",
    "claims":      [ { "text": "...", "confidence": 0.0–1.0 } ],
    "conflicts":   [ { "field": "...", "options": [...] } ]
  },
  "confidence": 0.0–1.0,
  "sources":    [ "ctx:WORKSPACE:opencode:...", "ctx:WORKSPACE:hermes-reasoner:..." ]
}
```

---

## 5. Embedding policy (reuse only)

| Input zone        | Allowed Qdrant collection           | Notes                                 |
|-------------------|-------------------------------------|---------------------------------------|
| PUBLIC            | `kirobi_public`                     | nomic-embed-text, 768                 |
| WORKSPACE         | `kirobi_workspace` / `kirobi_canon` / `kirobi_experiences` / `kirobi_code` | bge-m3 1024 / nomic 768 (code) |
| FAMILY_PRIVATE    | `kirobi_family`                     | bge-m3 1024, **local embedding only** |
| QUARANTINE        | none — embedding forbidden          | per `ZONE-POLICY-MATRIX.md`           |
| SACRED            | `kirobi_sacred`                     | encrypted, requires human approval    |

KIDI must **refuse** to embed if the requested collection does not match the entry's zone. Mismatches are logged as `EMBEDDING_ZONE_VIOLATION` and the call returns an error.

---

## 6. Zone preservation rules

1. `output.zone <= max(input.zone)` — never escalate.
2. If any input is `QUARANTINE`, the output is `QUARANTINE` and is not eligible for further synthesis without human review.
3. If any input is `SACRED`, the output is `SACRED` and KIDI does not run unless the caller passes an explicit human-approval token.
4. `FAMILY_PRIVATE` inputs may only be processed locally; KIDI must verify it is not running in a context that has any network egress to external services (checked via env flag `KIROBI_EGRESS_ALLOWED=false` for the relevant process).

---

## 7. What KIDI explicitly does not learn

Per `CLAUDE.md` §17, no opaque self-modification:

- No weight updates from runtime data.
- No automatic prompt mutation.
- No persistent "memory" beyond what ContextDB and Qdrant already provide.
- Any change to the synthesis algorithm is a code change, reviewed via PR.

The "KIDI learning loop" described in the original problem statement is, in this rollout, a **metric loop**: agent performance metrics are written to `kirobi-core/core-events.log` and surfaced in dashboards, but they do not modify KIDI behavior at runtime.

---

## 8. Failure modes

| Scenario                                  | Behavior                                              |
|-------------------------------------------|-------------------------------------------------------|
| ContextDB unreachable                     | Return error; do not fall back to a different store   |
| Qdrant collection missing                 | Return error; do not auto-create                      |
| Zone mismatch input vs requested output   | Reject; log `ZONE_REJECT`                             |
| Conflicting high-confidence claims        | Emit `conflicts[]`; do not pick a winner silently     |
| Embedding model unavailable               | Return error; do not switch to a different model      |

---

## 9. Cross-references

- `docs/agent/CONTEXT-WINDOW.md` — input/output schema authority
- `docs/agent/KEYBRODI-SUPERINTELLIGENZ.md` — who calls KIDI and when
- `metadata/COLLECTION-MAPPING.md` — Qdrant collections (reused)
- `metadata/ZONE-POLICY-MATRIX.md` — zone authority
- `metadata/MODEL-REGISTRY.md` — embedding models (reused)
