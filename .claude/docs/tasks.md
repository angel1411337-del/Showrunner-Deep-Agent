# Work Units

## Unit 1: Provider Harness
**Agent:** tdd-oop
**Status:** Complete
**Branch:** unit-1-providers

**Owns:**
- `src/showrunner/providers/`
- `tests/test_providers.py`

**Dependencies:**
- None

**Provides:**
- `LLMProviderProtocol`, `BaseLLMProvider`, `RuleBasedProvider`
- Optional Anthropic/OpenAI providers via API keys

**Estimated:** 3h

---

## Unit 2: Multi-Format Input Adapters
**Agent:** data-models
**Status:** Complete
**Branch:** unit-2-input-formats

**Owns:**
- `src/showrunner/adapters/`
- `tests/test_input_adapter.py`

**Dependencies:**
- `DocumentUnit` contract

**Provides:**
- Input adapters supporting .txt, .md/.markdown, .docx, .pdf
- Deterministic page markers for PDF ingestion

**Estimated:** 3h

---

## Unit 3: Incremental Pipeline Path
**Agent:** tdd-oop
**Status:** Complete
**Branch:** unit-3-incremental

**Owns:**
- `src/showrunner/pipeline/orchestrator.py`
- `src/showrunner/pipeline/protocols.py`
- `tests/test_pipeline.py`

**Dependencies:**
- Unit 2 (adapter load_files)

**Provides:**
- Incremental run behavior aligned with tests
- Deterministic artifact writing

**Estimated:** 3h

---

## Unit 4: Outline Planning (v0.2)
**Agent:** tdd-oop
**Status:** Complete
**Branch:** unit-4-outline

**Owns:**
- `src/showrunner/contracts/outline.py`
- `src/showrunner/planners/outline_planner.py`
- `src/showrunner/planners/convergence_detector.py`
- `src/showrunner/planners/bridging_generator.py`

**Dependencies:**
- Obligations, entities, evidence contracts

**Provides:**
- `OutlineSection`, `Beat`, `ConvergencePoint` models
- Outline export to `exports/master_outline_books_6_7.md`

**Estimated:** 4h

---

## Unit 5: Reveal Ledger (v0.3)
**Agent:** tdd-oop
**Status:** Complete
**Branch:** unit-5-reveal-ledger

**Owns:**
- `src/showrunner/contracts/reveal.py`
- `src/showrunner/planners/reveal_planner.py`

**Dependencies:**
- Obligations and evidence anchors

**Provides:**
- Reveal ledger export to `exports/mysteries_reveals_table.csv`

**Estimated:** 3h

---

## Unit 6: Twist Bank (v0.4)
**Agent:** tdd-oop
**Status:** Complete
**Branch:** unit-6-twist-bank

**Owns:**
- `src/showrunner/contracts/twist.py`
- `src/showrunner/planners/twist_planner.py`

**Dependencies:**
- Obligations and evidence anchors

**Provides:**
- Twist bank export to `exports/twist_bank.md`

**Estimated:** 3h

---

## Unit 7: Passive Hooks (v1)
**Agent:** api-layer
**Status:** Complete
**Branch:** unit-7-hooks

**Owns:**
- `src/showrunner/hooks/`
- `review/queue.jsonl`

**Dependencies:**
- Unit 3 (incremental runner)

**Provides:**
- pre-commit / post-commit hooks for incremental updates
- review queue contract + queue writer for human review items

**Estimated:** 3h

---

## Unit 8: Wiki Event/Relationship Extraction (v1+)
**Agent:** tdd-oop
**Status:** Not Started
**Branch:** unit-8-wiki-extraction

**Owns:**
- `src/showrunner/extractors/event_extractor.py`
- `src/showrunner/extractors/relationship_extractor.py`
- `tests/test_event_extractor.py`
- `tests/test_relationship_extractor.py`

**Dependencies:**
- Evidence anchors + entities + obligations contracts
- Wiki contracts (StoryTime, StoryOrder, Event, Relationship)

**Provides:**
- Event extraction with provenance and story time/order fields
- Relationship extraction with provenance and story time/order fields
- JSON artifact outputs for events and relationships

**Estimated:** 4h
