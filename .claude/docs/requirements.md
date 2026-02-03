# Clarified Requirements

## Date
2026-02-03

## Original Requirements
- Source: `docs/NEXT_STEPS.md` (Showrunner Orchestrator roadmap and phases).
- Additions: Provide an LLM harness that can plug in any provider via API keys; accept PDFs, Markdown files, DOCX, and plain text as inputs.

## Clarified Functional Requirements

### FR-1: Pipeline Test Compatibility
**Description:** Update the pipeline to match the test interface expectations by adding protocol definitions and factory injection to `ShowrunnerPipeline`.
**Acceptance Criteria:**
- [ ] `ShowrunnerPipeline.__init__` accepts an optional `factory` for dependency injection.
- [ ] Protocol definitions exist for core pipeline components to support test doubles.
- [ ] `tests/test_pipeline.py` passes without modifying test expectations.

### FR-2: Provider Harness
**Description:** Introduce a provider interface so LLM usage can be swapped via API keys and optional providers.
**Acceptance Criteria:**
- [ ] `LLMProvider` abstract interface exists with entity extraction, obligation extraction, and similarity methods.
- [ ] A rule-based provider is the default implementation and is used when no API keys are configured.
- [ ] Optional Anthropic and OpenAI providers are supported via API keys.

### FR-3: Multi-Format Input Support
**Description:** Accept input as a single file or a directory of files (non-recursive) in `.txt`, `.md`, `.markdown`, `.docx`, and `.pdf` formats.
**Acceptance Criteria:**
- [ ] A single input file is normalized into one `DocumentUnit`.
- [ ] A directory input loads all supported files and ignores unsupported files with a warning.
- [ ] PDF inputs are converted to text with deterministic page markers (e.g., `=== Page N ===`).

### FR-4: Master Outline (v0.2)
**Description:** Generate an outline for books 6-7 derived from obligations and entity/state substrate, including convergence points and bridging beats.
**Acceptance Criteria:**
- [ ] `exports/master_outline_books_6_7.md` is produced.
- [ ] Convergence points and bridging beats are included.
- [ ] Coverage mapping identifies which obligations are addressed where.

### FR-5: Reveal Ledger (v0.3)
**Description:** Produce a reveal ledger that maps mysteries to candidate truths and reveal placement.
**Acceptance Criteria:**
- [ ] `exports/mysteries_reveals_table.csv` is produced.
- [ ] Each entry links to a mystery obligation and includes candidate truths and placement info.

### FR-6: Twist Bank (v0.4)
**Description:** Generate a twist bank with constraints based on obligations and evidence congruence.
**Acceptance Criteria:**
- [ ] `exports/twist_bank.md` is produced.
- [ ] Each twist includes affected obligations/entities, setup needs, and risk notes.

### FR-7: Passive Mode Hooks (v1)
**Description:** Add git hooks to run incremental analysis on changed files and maintain a review queue.
**Acceptance Criteria:**
- [ ] `pre-commit` detects changed text files and runs incremental analysis.
- [ ] `post-commit` updates review queue without blocking commits.
- [ ] Review queue entries conform to the defined contract.

### FR-8: Advanced Integrations (roadmap)
**Description:** Provide integration points for RLM, GraphRAG, temporal knowledge graph, DOME outlining, and multi-agent debate.
**Acceptance Criteria:**
- [ ] Integration modules are defined per roadmap when phases 6.x are started.

## Non-Functional Requirements

### NFR-1: Determinism
**Description:** Outputs must be deterministic for identical inputs.
**Metric:** Golden determinism tests pass without manual edits.

### NFR-2: Offline/Optional LLMs
**Description:** LLM features must be optional and disabled by default in tests/CI.
**Metric:** All tests pass without API keys or network access.

### NFR-3: Type Safety
**Description:** Strict typing is enforced for production code.
**Metric:** `pyright` passes in strict mode for `src/`.

### NFR-4: Code Quality
**Description:** Linting and formatting must remain clean.
**Metric:** `ruff` passes for `src/` and `tests/`.

### NFR-5: Tests-First Workflow
**Description:** Production changes must be accompanied by tests, enforced by local and CI guards.
**Metric:** Tests-first guard passes for commits and CI runs.

## Scope

### In Scope
- Phase 1 immediate refinements (test compatibility, provider interface).
- Multi-format input support (txt, md/markdown, docx, pdf).
- v0.2 outline planning, v0.3 reveal ledger, v0.4 twist bank.
- Passive mode hooks (v1).

### Out of Scope (for now)
- Production deployment, hosting, or web UI.
- Full GraphRAG/Temporal KG/DOME implementation details until Phase 6 begins.
- Fine-tuning or training new LLMs beyond provider integration.

## Assumptions
- A directory input is non-recursive by default.
- Unsupported file types are ignored with warnings, not errors.
- PDF/DOCX text extraction will rely on standard Python libraries (to be selected).
- LLM usage is optional; rule-based extraction remains the default path.

## Open Risks / Unknowns
- PDF/DOCX extraction quality may vary by library and source formatting.
- Performance impacts for large corpora need benchmarking.
- API-provider differences may affect extraction consistency.

## Decisions Made During Clarification
- Input formats include `.txt`, `.md`, `.markdown`, `.docx`, and `.pdf`.
- LLM providers must be pluggable via API keys, with an offline default.
- Directory inputs are non-recursive and deterministic.
