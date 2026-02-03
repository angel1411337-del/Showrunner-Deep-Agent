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
