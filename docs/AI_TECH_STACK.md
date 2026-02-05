# Showrunner Deep Agent - Tech Stack and Architecture (AI Brief)

## Purpose
This document is an AI-oriented overview of the current technology stack and
system architecture used by the Showrunner Deep Agent codebase. It is intended
to help future AI assistants or collaborators reason about the system without
guesswork.

For a direct implemented-vs-planned runtime map, see
`docs/AGENT_RUNTIME_STATUS.md`.

## Tech Stack
- Language: Python 3.14.x (project requires >= 3.14.2)
- Packaging: PEP 621 + Hatchling
- Core libraries: Pydantic v2, LangGraph v1
- LLM integration layer: LangChain + LangChain Core provider wrappers
- Optional LLM provider backends: langchain-anthropic, langchain-openai
- Data formats: JSON, JSONL, Markdown, SQLite
- Dev tooling: pytest, pytest-cov, ruff, pyright, jsonschema, pre-commit
- Environment tool: uv (lockfile present)
- CI: GitHub Actions (tests-first guard, lint/format, typecheck, unit tests,
  golden tests, schema validation, integrity checks)

## Architectural Overview
The system is contract-driven and pipeline-orchestrated. It ingests narrative
corpus, normalizes it into evidence-addressable passages, resolves entities,
extracts narrative obligations, validates quality gates, and exports a dossier
plus additional planning artifacts.

The main orchestration layer is `ShowrunnerPipeline` in
`src/showrunner/pipeline/orchestrator.py`. It runs a LangGraph DAG when
available and falls back to a sequential runner if LangGraph is unavailable.

## Agent Runtime Status
- LangGraph: active orchestration runtime in production pipeline.
- LangChain: active as provider integration boundary (for Anthropic/OpenAI adapters).
- Minimal agent harness: available in `src/showrunner/agent/harness.py`.
- Deepagents: not integrated yet as an execution runtime. Planned for a later
  integration phase.

## Key Layers and Components
### Contracts (Pydantic Models)
Contracts live in `src/showrunner/contracts/` and define the system's source of
truth for data shape and validation.
- DocumentUnit, PassageRecord
- Entity, AliasEntry, OverrideRule
- EvidenceAnchor, EvidenceIndex
- Obligation, ObligationGraphEdge
- Finding, MetricsReport, RunManifest, DatasetManifest
- Planning contracts: OutlineSection, Beat, ConvergencePoint, CandidateTruth,
  RevealEntry, TwistProposal
- Review queue contract: ReviewQueueItem

### Pipeline Orchestration
Pipeline stages are composed as nodes in a DAG:
- load_input
- index_canon
- resolve_entities
- extract_obligations
- merge_duplicates
- validate_gates
- extract_wiki
- export_dossier
- export_planning_artifacts

Each stage is implemented via a component that conforms to a protocol in
`src/showrunner/pipeline/protocols.py`. Components are created by
`ComponentFactory`, enabling dependency injection for testing or alternate
implementations.

### Input Adapters
Input adapters normalize files/folders into `DocumentUnit` objects:
- `src/showrunner/adapters/input_adapter.py`

### Canon Indexer
The canon indexer segments corpus text into paragraph passages and indexes
them into SQLite:
- `src/showrunner/indexers/canon_indexer.py`
- Outputs `canon/index.sqlite` and `canon/passages.jsonl`

### Entity Resolver
Entity resolution extracts and links people, places, artifacts, vehicles, and
groups with evidence anchors:
- `src/showrunner/resolvers/entity_resolver.py`

### Obligation Extractor
Rule-based extractor detects narrative obligations in four categories:
prophecy/vision, mystery, Chekhov's gun, and plot thread. Each obligation has
evidence anchors with char offsets and deterministic IDs:
- `src/showrunner/extractors/obligation_extractor.py`

### Dedupe Merger
Merges near-duplicate obligations and emits edges for absorbed duplicates:
- `src/showrunner/processors/dedupe_merger.py`

### Quality Gates
DataOps-style validation checks:
- JSON schema validation
- Referential integrity
- Evidence gate (hard fail if missing evidence)
- Contradiction detection (WARN only in MVP)
Implementation: `src/showrunner/gates/quality_gates.py`

### Export Renderer
Renders the Unresolved Threads Dossier in Markdown:
- `src/showrunner/renderers/export_renderer.py`

### Planning Modules
These are separate planners used to produce downstream writer planning docs:
- Outline planner: `src/showrunner/planners/outline_planner.py`
- Convergence detection: `src/showrunner/planners/convergence_detector.py`
- Bridging generator: `src/showrunner/planners/bridging_generator.py`
- Reveal ledger planner: `src/showrunner/planners/reveal_planner.py`
- Twist bank planner: `src/showrunner/planners/twist_planner.py`

### Providers (LLM Abstraction)
LLM providers implement a shared protocol and are injected into extractors or
resolvers via the pipeline factory.
- Base protocol: `src/showrunner/providers/base.py`
- Rule-based default: `src/showrunner/providers/rule_based.py`
- Anthropic provider via LangChain: `src/showrunner/providers/anthropic.py`

### Passive Hooks (V1)
Passive mode runs incremental updates on git events and appends review items
to a queue for human review.
- Hook utilities: `src/showrunner/hooks/`
- Hook entrypoint: `src/showrunner/hooks/git_hook_handler.py`
- Installer: `scripts/install_git_hooks.py`
- Review queue output: `review/queue.jsonl`

## Data Flow and Artifacts
The pipeline writes structured outputs to the configured output directory:
- `canon/` (SQLite index, passages JSONL)
- `kb/` (entities, aliases)
- `obligations/` (obligations JSON)
- `qa/` (findings JSONL)
- `exports/` (Unresolved Threads Dossier Markdown)
- `run_manifest.json` (run metadata)

Schema snapshots live in `schemas/` and are validated in CI via
`scripts/validate_schemas.py`. Referential integrity is validated via
`scripts/check_integrity.py`.

## Determinism and IDs
IDs for obligations and anchors are deterministic and derived from content
using SHA-256 hashing. This enables stable outputs for the same inputs and is
covered by golden tests.

## Testing, Guardrails, and CI
- Tests are written first and enforced by `showrunner.guards.tests_first`
  (pre-commit + CI job).
- Linting and formatting via Ruff.
- Type checking via Pyright (strict mode).
- Unit tests via Pytest.
- Golden determinism tests and schema/integrity checks in CI.

## Extension Points
This system is designed to be extensible without changing the core contracts:
- Swap or extend providers via `LLMProviderProtocol`
- Inject custom components using `ComponentFactory`
- Add new planning outputs with new contracts and planners
- Add additional quality gates without altering extraction logic

## Notes
The interactive GUI is a separate future deliverable and is intentionally out
of scope for the current V1 implementation. The current system focuses on
pipeline correctness, evidence provenance, and deterministic outputs.
