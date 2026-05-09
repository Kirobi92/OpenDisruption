---
zone: WORKSPACE
created_by: github-copilot
created_at: 2026-05-09
reviewed_by: pending
version: 1.0
---

# Unique MVP Scope — OpenDisruption

## Decisive MVP

The smallest real MVP is a **local-first, zone-aware knowledge copilot**:

- authenticated users log in locally,
- upload documents with an explicit zone,
- search and chat only within allowed zones,
- get a hard refusal for SACRED retrieval,
- and let an admin verify system health and zone activity.

That proves what is unique here: **privacy boundaries, explicit refusal rules, and local-first knowledge operations**, not commodity chat UI or media generation. (PROJECT-ARCHITECTURE.md:11-18, 124-140; PROJECT-CHARTER.md:41-52; metadata/ZONE-POLICY-MATRIX.md:77-117)

## IN

1. **Canonical Family PWA** as the main product surface: login, chat, search, upload, settings, status. `knowledge-graph` stays demo-only. (README.md:139-150; apps/web/README.md:10-23)
2. **Auth + zone permissions**: JWT login, sessions, `/me/permissions`, audit log, zone-based read/write checks. (services/auth/main.py:107-156, 347-475)
3. **Zone-scoped conversations and grounded chat**: persisted conversations, zone-specific chat history, retrieval-backed responses. (services/api/main.py:52-97, 334-365, 512-706)
4. **Document ingest/search pipeline** for:
   - `WORKSPACE` end-to-end immediately,
   - `FAMILY_PRIVATE` only through an explicit human-approved ingest path,
   - `SACRED` always denied for retrieval/RAG.  
   (services/ingest/main.py:62-70, 272-285; services/embeddings/main.py:58-63, 170-189; services/retrieval/main.py:47-61, 142-198, 239-297)
5. **Read-only admin dashboard** for service health and zone analytics. (apps/dashboard/README.md:13-19, 54-57; apps/dashboard/src/app/api/proxy/[service]/[...path]/route.ts:25-37)
6. **Local deployment path** via Compose/Caddy with localhost-by-default networking. (PROJECT-ARCHITECTURE.md:86-119, 168-177; README.md:109-137)

## OUT

1. Mobile, desktop, installer apps. They are scaffold/docs-only and do not help prove uniqueness now. (README.md:143-150)
2. Voice UI for MVP. Valuable later, but not required to prove zone-aware local knowledge workflows. (README.md:70-74, 139-146)
3. Image/music/video/media-generation surfaces unless break/fix only. They are adjacent, not differentiating for the first proof. (docker-compose.yml:198-259; apps/dashboard/src/app/services/page.tsx:90-116)
4. Open WebUI and Flowise as primary UX. They remain auxiliary. (README.md:73-74, 146-147)
5. Knowledge graph page as a promise surface. It is explicitly demo-only. (apps/web/README.md:22-23)
6. Autonomous write-capable supervisor flows. Current `kirobi_core` autonomy is dry-run and zone-gated; that is not the MVP proof point yet. (DEVELOPER-RUNBOOK.md:14-15, 72-83)

## Required end-to-end journeys

1. **Local sign-in and trust bootstrap**  
   User signs in, sees their profile and zone permissions, and understands that data stays local. (services/auth/main.py:165-211, 437-475; apps/web/src/app/page.tsx:22-40, 101-116)

2. **Upload → ingest → search in WORKSPACE**  
   User uploads a workspace document, it is indexed locally, appears in search, and can ground chat answers with citations/snippets. (apps/web/src/app/upload/page.tsx:96-141, 192-238; services/ingest/main.py:247-320; services/retrieval/main.py:142-198; services/api/main.py:458-483, 663-667)

3. **Upload → approved ingest → private search in FAMILY_PRIVATE**  
   A private family document is ingested only through an explicit approval path, becomes searchable in `FAMILY_PRIVATE`, and stays inaccessible from `WORKSPACE` queries. This is the strongest uniqueness proof. (metadata/ZONE-POLICY-MATRIX.md:79-85, 98-105; services/retrieval/main.py:147-157, 244-250; tests/unit/test_retrieval_service.py:131-188)

4. **SACRED refusal**  
   A user or service attempting SACRED retrieval receives an explicit refusal instead of a silent leak or fuzzy answer. (metadata/ZONE-POLICY-MATRIX.md:98-105; services/retrieval/main.py:244-250)

5. **Admin verification**  
   Admin opens the dashboard and sees service health, zone usage, and whether the MVP is operational without shell access. (apps/dashboard/README.md:13-19; apps/dashboard/src/app/page.tsx:58-68, 135-193, 224-259)

## Repo surfaces that must be production-credible

### Core product surfaces

- `apps/web` — canonical user-facing MVP. (README.md:139-150; apps/web/README.md:1-29)
- `services/auth` — identity, JWT, sessions, zone permissions, audit log. (services/auth/main.py:107-156, 406-489)
- `services/api` — conversation, uploads, permission checks, search bridge, chat bridge. (services/api/main.py:334-365, 458-509, 512-877)
- `services/ingest` — safe ingest workflow and job tracking. (services/ingest/main.py:104-120, 247-320)
- `services/embeddings` — local embeddings and controlled storage into Qdrant. (services/embeddings/main.py:46-63, 165-247)
- `services/retrieval` — zone-enforced search/RAG and SACRED refusal. (services/retrieval/main.py:47-61, 142-198, 239-297)
- `services/analytics-service` — zone activity + usage reporting for trust and observability. (services/analytics-service/main.py:39-60, 107-113, 196-227)

### Supporting runtime surfaces

- `postgres`, `qdrant`, `ollama` — required because the MVP promise is grounded local retrieval, not stateless chat. (PROJECT-ARCHITECTURE.md:90-99, 122-140; docker-compose.yml:21-78, 107-145)
- `caddy` + Compose profile path — required because the PWA is the canonical entry point and local/LAN access is part of the real-showable product. (README.md:114-137; PROJECT-ARCHITECTURE.md:168-177)
- `apps/dashboard` — keep as operator-facing support surface, not the product centerpiece. (README.md:141-145; apps/dashboard/README.md:9-19)

## Recommended execution order

1. **Lock the product narrative and UI** around “local-first, zone-aware knowledge copilot,” removing demo expectations from the main flow. (apps/web/README.md:10-23)
2. **Harden auth + permission UX** so users can see what each zone means and what they can access. (services/auth/main.py:467-475)
3. **Ship WORKSPACE ingest/search/chat end-to-end** as the first fully reliable loop. (services/ingest/main.py:272-285; services/retrieval/main.py:142-198; services/api/main.py:458-483, 616-706)
4. **Add explicit human-approved FAMILY_PRIVATE ingest** while preserving hard blocks for autonomous sensitive writes. Right now ingest and embeddings only allow autonomous `PUBLIC`/`WORKSPACE`, which is a real MVP gap. (services/ingest/main.py:62-63, 272-285; services/embeddings/main.py:62-63, 179-189; tests/unit/test_ingest_service.py:161-171)
5. **Make SACRED refusal visible and testable in UI and API** so the boundary is productized, not just documented. (services/retrieval/main.py:244-250)
6. **Polish dashboard/service health** so demos do not depend on shell troubleshooting. (apps/dashboard/src/app/services/page.tsx:32-88; apps/dashboard/src/app/api/proxy/[service]/[...path]/route.ts:25-99)
7. **Only then** consider extra surfaces like voice or broader supervisor features. (DEVELOPER-RUNBOOK.md:72-89)

## Honest non-MVP items

- Full five-zone authoring/editing lifecycle across every surface.
- Autonomous task execution that safely writes across domains.
- Rich family/business/creative agent specialization in one release.
- Voice-first interaction as a required path.
- Knowledge graph as a dependable user value surface.
- Media generation as part of the core proof.

Those can become Phase 2 once the zone-aware local knowledge loop is trusted and used. (PROJECT-CHARTER.md:77-93; README.md:139-150; DEVELOPER-RUNBOOK.md:72-89)

## Bottom line

If OpenDisruption ships as “yet another local chat UI,” it will look generic.  
If it ships as **the local copilot that knows what zone your data lives in, grounds answers locally, and explicitly refuses forbidden retrieval**, it has a real and defensible MVP.
