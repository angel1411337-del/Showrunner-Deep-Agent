# Showrunner Deep Agent — V1 Spec (Simple Agent Harness)

**Purpose**
Build a local-first, evidence-gated story-intelligence system that turns long-form text into deterministic, provenance-anchored artifacts (dossier + wiki data) with a minimal agent harness.

**Goals**
- Convert input text into canonical artifacts with evidence guarantees.
- Produce writer-facing exports (dossier) and structured stores.
- Establish contracts, schema snapshots, and quality gates.
- Add a minimal agent harness for orchestration (no long-term memory, no subagents).

**Non-Goals**
- No graph DB (Neo4j/Falkor) yet.
- No temporal memory service (Zep-style).
- No multi-agent evaluation loops.
- No heavy LLM toolloop; rule-based or stubbed provider acceptable.

**Architecture**
**Pipeline (deterministic + contract-first)**
1. Ingest text → paragraph segmentation with stable IDs.
2. Canon stores (`canon/*`) + evidence index.
3. Entity resolution + alias map (`kb/*`).
4. Obligation extraction (`obligations/*`).
5. Wiki extraction (events/relationships).
6. QA gates (schema + evidence + referential integrity).
7. Writer-facing exports (dossier).
8. Run manifests + QA logs.

**Agent harness (minimal)**
- Deep agent wrapper that can call `run_pipeline` and read artifacts.
- Filesystem access restricted to repo workspace.
- No subagent dispatch.

**Core Artifacts**
**Writer-facing exports**
- `exports/Unresolved_Threads_Dossier.md`

**Canonical stores**
- `canon/passages.jsonl`
- `canon/evidence_index.jsonl`
- `canon/index.sqlite`
- `kb/entities.json`
- `kb/aliases.json`
- `obligations/obligations.json`
- `wiki/events.json`
- `wiki/relationships.json`

**QA + run bookkeeping**
- `qa/findings.jsonl`
- `qa/metrics.json`
- `run_manifest.json`
- `dataset_manifest.json`
- `tool_call_audit.jsonl`
- `review/queue.jsonl` (optional in V1)

**Contracts & Schemas**
- All artifacts have Pydantic contracts + JSON schema snapshots.
- Evidence anchors required for all extracted claims.
- Dual time axes for wiki artifacts:
- `story_time` (in-world)
- `story_order` (narrative order)
- `created_at` (real-world timestamp)

**Quality Gates**
- Schema validation.
- Evidence gate (no claims without anchors).
- Referential integrity.
- Contradiction detection (WARN in MVP).
- TDD enforced by tests-first guard.

**Interfaces (stable)**
- Protocols: input adapter, indexer, entity resolver, obligation extractor, event extractor, relationship extractor, QA gates, export renderer.
- Server API: read artifacts and trigger pipeline.

**Success Criteria**
- Deterministic outputs across runs.
- CI gates green (pytest, ruff, pyright).
- Dossier export matches expectations with evidence.

**Acceptance Criteria**
- Running the pipeline with a sample corpus produces all V1 artifacts under a new output directory.
- Every obligation, event, and relationship has at least one evidence anchor.
- Referential integrity checks return no errors for canonical stores.
- Dossier export is reproducible across repeated runs (same inputs).
- Agent harness can invoke the pipeline and read artifacts without direct file edits.

**Test Matrix**
| Area | Test Type | Tests / Evidence |
| --- | --- | --- |
| Canon ingestion | Unit + integration | Passage segmentation tests; indexer workflow tests |
| Contracts + schemas | Unit + schema snapshot | Pydantic contract tests; JSON schema snapshots present |
| Evidence gating | Unit + integration | Evidence gate tests; QA gate integration tests |
| Wiki extraction | Unit | Event/relationship extraction tests |
| Dossier export | Unit | Export renderer tests |
| Agent harness | Integration | Agent run triggers pipeline and reads artifacts |
| CI gates | Automation | `pytest`, `ruff`, `pyright` pass |
