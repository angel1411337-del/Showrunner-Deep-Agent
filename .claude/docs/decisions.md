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

---

### 2026-02-04 - Research-Layer Capability Uplift Is Post-V1 and Layered
**Status:** Accepted

**Context:** We need to assess whether the proposed research-layered stack materially expands capabilities beyond the contract-first, evidence-gated MVP stack. "Capability" means reliably enabling new tasks or materially reducing errors and human cleanup.

**Decision:** Treat the research-layered stack as post-V1 and evaluate it by layer. Prioritize layers that unlock new capabilities: RLM-style tool environment, GraphRAG with temporal memory, hierarchical outlining, and multi-agent evaluation. Treat hallucination detection and mind-map hardening as reliability improvements, and context caching/speculative decoding as performance-only (no new capabilities).

**Consequences:** MVP remains contract-first with evidence gates. Future roadmap work must map each research layer to concrete new outputs or failure modes it fixes, and avoid spending on performance-only layers until scale demands it.

---

### 2026-02-05 - Agent Runtime Integration Sequencing
**Status:** Accepted

**Context:** We need to integrate LangChain and Deepagents while preserving deterministic
pipeline outputs and evidence gates. The system already uses LangGraph as the pipeline runtime.

**Decision:** Use a phased integration plan:
1) Introduce a runtime facade with a strict tool contract.
2) Add LangChain runtime mode using those tools.
3) Add Deepagents runtime mode behind a feature flag.
4) Integrate Graph/RLM tools and parity tests.

**Consequences:** Pipeline remains the source of truth. Agent runtimes become wrappers over
artifact outputs and gated tool calls, enabling gradual adoption without breaking CI or
determinism.

---

### 2026-02-05 - Code-OSS Writer Interface Strategy
**Status:** Accepted

**Context:** Writers need a full-featured editor with formatting, while the product needs
centralized agent interaction and distribution control.

**Decision:** Use a VS Code extension as the primary integration surface and ship it inside
a Code-OSS fork for distribution control. Avoid core editor changes; keep deltas to
branding, defaults, and bundled extensions.

**Consequences:** Editor functionality remains stable and maintained upstream. Agent UI
and hooks live in the extension layer, reducing fork maintenance cost.
