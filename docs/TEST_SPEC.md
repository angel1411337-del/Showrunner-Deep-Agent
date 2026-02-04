# Showrunner Test Specification

## Purpose
Define test coverage for both the GUI (separate deliverable) and the current
repository (backend + pipeline). This spec is meant to guide the GUI agent and
backend work in parallel without over-constraining future UI or architecture.

## Scope
- GUI: end-to-end user workflows for non-technical users.
- Repo: backend pipeline, contracts, gates, artifacts, and hooks.

## Assumptions
- The GUI consumes pipeline outputs from disk (current default) or via a thin
  service layer to be defined later. Tests should be written to allow either
  implementation by abstracting the data source.
- Core artifacts remain schema-validated (Pydantic models + JSON schema).
- V1 scope stays centered on dossier + planning artifacts, not advanced
  research stack items.

## Out of Scope
- Advanced research stack (GraphRAG, Zep, RLM, DOME, multi-agent debate).
- Full text generation or authoring tools.
- Any external managed database or cloud deployment requirements.

## Test Environments
### GUI
- Desktop: Windows 11, macOS (latest), Ubuntu LTS.
- Browsers: Chrome, Edge, Firefox, Safari (macOS).
- Screen sizes: 13", 15", ultrawide, tablet.

### Backend
- Python 3.14.x
- Local file system (Windows paths verified)

## Shared Test Data
- Golden fixtures: `tests/golden/fixtures/*`
- Sample corpus: `tests/golden/fixtures/sample_corpus.txt`
- Synthetic small corpora for fast tests (2-5 paragraphs)

---

## GUI Test Specification (Non-Technical User UX)

### Core User Stories
1. Import a corpus (folder or file) and run analysis.
2. View the Unresolved Threads Dossier with filtering and search.
3. Explore obligations by entity (character/place/artifact/vehicle/group).
4. Inspect evidence anchors and read excerpts in context.
5. Export outputs (Markdown, CSV, JSON).
6. Review reveal ledger and twist bank as read-only views.

### Functional Test Areas
1. Onboarding and setup
   - First-run walkthrough (if present)
   - Input selection (file or folder)
   - Clear error for unsupported inputs
2. Run pipeline
   - Progress indicator updates per stage
   - Successful completion shows outputs
   - Failure states show actionable errors
3. Dossier view
   - Category sections appear in correct order
   - Counts match underlying obligations
   - Evidence excerpts open in detail panel
4. Entity explorer
   - Entities list filters by type
   - Entity detail shows linked obligations
   - Related evidence anchors are visible
5. Obligation explorer
   - Filters by category, confidence, entity
   - Search by description keyword
6. Exports
   - Download dossier Markdown
   - Download reveal ledger CSV
   - Download twist bank Markdown
7. Review queue (optional)
   - If queue.jsonl exists, display review items
   - Allow mark as reviewed/dismissed (client-side state only)
8. Resilience
   - Empty corpus handled gracefully
   - Missing artifacts show clear guidance

### Non-Functional Tests
1. Performance
   - UI remains responsive with 1k+ obligations
   - Search and filter response under 300ms on desktop
2. Accessibility
   - Keyboard navigation for main flows
   - Color contrast meets WCAG AA
3. Reliability
   - No data loss on refresh
   - Repeatable render for same inputs

### GUI Test Artifacts
- E2E test suite (Playwright or Cypress)
- Snapshot tests for dossier rendering
- Accessibility checks (axe-core or equivalent)

---

## Backend / Repo Test Specification

### Pipeline Functional Tests
1. Input adapters
   - Load .txt, .md, .docx, .pdf
   - Deterministic parsing
2. Canon indexing
   - Paragraph segmentation deterministic
   - SQLite index creation
3. Entity resolution
   - Entity type assignment and alias mapping
4. Obligation extraction
   - All four categories detected
   - Evidence anchors required
5. Dedupe merger
   - Duplicate detection and merge edges
6. Quality gates
   - Schema validation
   - Referential integrity
   - Evidence gate (hard fail)
   - Contradiction detection (warn)
7. Exports
   - Dossier output matches expected format
   - Reveal ledger CSV and twist bank outputs

### Determinism Tests
- Golden fixtures produce stable outputs
- Obligation and anchor IDs stable across runs

### Hook Tests (Passive Mode)
1. Detect changed corpus files
2. Run incremental pipeline without crash
3. Append review queue with findings
4. Hook handler is non-blocking on errors

### Non-Functional Tests
1. Lint + format checks via Ruff
2. Type check via Pyright (strict)
3. CI pipeline must pass all gates

---

## Acceptance Criteria (V1)
1. Pipeline completes on sample corpus without errors.
2. Dossier, reveal ledger, twist bank generated.
3. Quality gates pass (no ERROR-level findings).
4. Hooks can be installed and run without blocking commits.
5. GUI (if shipped) can load outputs and display dossier with evidence.

---

## Open Questions (TBD)
1. GUI data source: file-based outputs or API?
2. Preferred UI test framework: Playwright or Cypress?
3. Accessibility target: WCAG 2.1 AA or higher?
4. Minimum performance targets for large corpora?
