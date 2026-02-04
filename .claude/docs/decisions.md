# Architectural Decisions

## Decisions

### 2026-02-03 - Multi-Format Input Scope
**Status:** Accepted

**Context:** The pipeline currently supports .txt only, but requirements include .md, .docx, and .pdf.

**Decision:** Accept .txt, .md/.markdown, .docx, and .pdf inputs. Directory inputs are non-recursive and unsupported files are ignored with warnings.

**Consequences:** Adapter logic grows to handle multiple loaders, and tests must cover additional formats.

---

### 2026-02-03 - LLM Provider Harness
**Status:** Accepted

**Context:** LLM calls must be pluggable and optional, with deterministic offline defaults.

**Decision:** Define LLMProviderProtocol with complete and complete_structured methods. Provide RuleBasedProvider as the default implementation, with optional Anthropic/OpenAI providers via API keys.

**Consequences:** Call sites depend on the provider interface. Tests and CI remain offline by default.

---

### 2026-02-03 - Deterministic PDF Ingestion
**Status:** Accepted

**Context:** PDF text extraction can be variable; determinism is required for golden tests.

**Decision:** Normalize PDFs with stable page markers (e.g., === Page N ===) and deterministic ordering per file.

**Consequences:** PDF loaders must insert page markers and avoid nondeterministic ordering.

---

### 2026-02-03 - DocumentUnit Per File
**Status:** Accepted

**Context:** Canon segmentation is centralized in the indexer.

**Decision:** Each file produces one DocumentUnit; paragraph segmentation remains in CanonIndexer.

**Consequences:** Input adapters remain thin and deterministic; segmentation rules stay in indexers.

---

### 2026-02-03 - Tests-First Guard
**Status:** Accepted

**Context:** We need enforcement to ensure tests are written before implementation changes.

**Decision:** Add a tests-first guard (pre-commit hook + CI step) that blocks `src/` changes without corresponding `tests/` updates. Document the rule in the constitution.

**Consequences:** Commits that modify production code without tests will fail locally and in CI unless tests are added.

---

### 2026-02-04 - Wiki Events and Relationships With Dual Time Axes
**Status:** Accepted

**Context:** We need wiki-ready artifacts that preserve provenance and distinguish in-world time, narrative order, and real-world creation time.

**Decision:** Introduce StoryTime and StoryOrder value objects and require `created_at` on Event and Relationship records. All events and relationships must carry evidence anchors for provenance.

**Consequences:** Extraction logic must populate StoryTime, StoryOrder, and created_at. Schema validation and artifact exports must include these fields.

---

### 2026-02-04 - Wiki Artifact Output Location
**Status:** Accepted

**Context:** We need deterministic locations for wiki artifacts to support UI and graph ingestion without colliding with existing exports.

**Decision:** Write wiki artifacts under `output_dir/wiki/` as `events.json` and `relationships.json`.

**Consequences:** Pipeline orchestration must create the wiki folder and write JSON outputs there. UI/graph ingestion should read from this location.

---

### 2026-02-04 - Wiki Extractors Reuse Existing Evidence Anchors
**Status:** Accepted

**Context:** Evidence anchors are already produced by canon indexing and obligation/entity extraction. Adding new anchors in wiki extraction increases complexity and risks nondeterminism.

**Decision:** Event and relationship extractors must reference existing `EvidenceAnchor` IDs only; they do not emit new anchors in v1.

**Consequences:** Extractors must select evidence from the existing anchor store. Anchor stores remain single-source-of-truth for provenance.
