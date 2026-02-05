# Showrunner Orchestrator - Next Steps Specification

## Related Docs
- `docs/V1_SPEC.md`
- `docs/V2_SPEC.md`
- `docs/OUTPUTS_CONTRACT.md`
- `docs/GUI_INPUT_CONTRACT.md`
- `docs/LANGCHAIN_LANGGRAPH_UPGRADE.md`
- `docs/AGENTIC_TRAVERSAL.md`
- `docs/AGENT_RUNTIME_STATUS.md`
- `docs/AGENT_V1.md`

## Current State: v0.1-v0.4 Pipeline Pack Complete

| Artifact | Status |
|----------|--------|
| Unresolved Threads Dossier (v0.1) | Complete |
| Master Outline export + store (v0.2) | Complete |
| Reveal Ledger export + store (v0.3) | Complete |
| Twist Bank export + store (v0.4) | Complete |
| Wiki Events/Relationships extraction | Complete |
| Neo4j graph schema + loader + query layer | Complete |
| Evidence Gates (hard) + Contradiction WARN | Complete |
| JSON Schema + determinism + CI guard for v0.1-v0.4 exports | Complete |

### Runtime Integration Status

| Runtime Layer | Status | Notes |
|---------------|--------|-------|
| LangGraph | Active | Primary orchestration runtime in `ShowrunnerPipeline` |
| LangChain | Partial | Used at provider layer, not as full agent loop runtime |
| Deepagents | Planned | No `src/showrunner/agent/` runtime integration yet |

---

## Phase 1: Immediate Refinements (1-2 days)

Status: mostly completed. Keep this section as historical implementation notes.

### 1.1 Fix Pipeline Test Interface Mismatches

**Location:** `tests/test_pipeline.py`

The tests expect additional interfaces that need to be added to `orchestrator.py`:

```python
# Add to orchestrator.py

# Protocol definitions for dependency injection
class InputAdapterProtocol(Protocol):
    def load(self, source: Path) -> list[DocumentUnit]: ...

class CanonIndexerProtocol(Protocol):
    def segment_paragraphs(self, doc: DocumentUnit) -> list[PassageRecord]: ...
    def index(self, docs: list[DocumentUnit], db_path: Path) -> tuple[list[PassageRecord], Any]: ...

# ... etc for each component

# Add factory injection to ShowrunnerPipeline.__init__
def __init__(
    self,
    config: PipelineConfig,
    factory: ComponentFactory | None = None,  # Add this
    on_progress: Callable[[str, float], None] | None = None,
) -> None:
    self._factory = factory or ComponentFactory(config=config)
```

**Task:** Update `ShowrunnerPipeline` to accept optional `factory` parameter for testing.

### 1.2 Add LLM Provider Interface

**Location:** `src/showrunner/providers/`

```python
# src/showrunner/providers/base.py
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """Abstract base for LLM providers (Claude, OpenAI, local)."""

    @abstractmethod
    async def extract_entities(self, text: str, context: dict) -> list[dict]:
        """Extract entities using LLM."""
        ...

    @abstractmethod
    async def extract_obligations(self, text: str, entities: list, context: dict) -> list[dict]:
        """Extract obligations using LLM."""
        ...

    @abstractmethod
    async def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute semantic similarity."""
        ...

# src/showrunner/providers/anthropic.py
class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        ...

# src/showrunner/providers/rule_based.py (current implementation)
class RuleBasedProvider(LLMProvider):
    """Current regex-based implementation wrapped as provider."""
    ...
```

---

## Phase 2: v0.2 Master Outline (1-2 weeks)

### 2.1 Requirements (from PRD)

**Output:** `exports/master_outline_books_6_7.md`

**Functionality:**
- Outline derived from obligations + entity/state substrate
- Include convergence points (where plot threads meet)
- Include required bridging beats (high level)
- Coverage mapping: "which obligations are addressed where"

### 2.2 New Components

```
src/showrunner/
├── planners/
│   ├── __init__.py
│   ├── outline_planner.py      # Master outline generation
│   ├── convergence_detector.py # Find where threads converge
│   └── bridging_generator.py   # Generate bridging beats
├── models/
│   ├── __init__.py
│   ├── outline.py              # OutlineSection, Beat, ConvergencePoint
│   └── coverage.py             # CoverageMap, ObligationCoverage
```

### 2.3 Contracts

```python
# src/showrunner/contracts/outline.py

class Beat(BaseModel):
    """A story beat in the outline."""
    beat_id: str
    description: str
    chapter_hint: str | None
    pov_character: str | None
    obligations_addressed: list[str]  # obligation_ids
    entities_involved: list[str]      # entity_ids
    is_bridging: bool = False

class ConvergencePoint(BaseModel):
    """Where multiple plot threads converge."""
    convergence_id: str
    description: str
    converging_obligations: list[str]
    suggested_placement: str
    dramatic_weight: float  # 0-1

class OutlineSection(BaseModel):
    """A section of the master outline."""
    section_id: str
    title: str
    book_number: int
    beats: list[Beat]
    convergence_points: list[ConvergencePoint]

class CoverageMap(BaseModel):
    """Tracks which obligations are addressed where."""
    obligation_id: str
    addressed_in_beats: list[str]
    coverage_status: Literal["fully_addressed", "partially_addressed", "unaddressed"]
    notes: str | None
```

### 2.4 Pipeline Extension

Add new nodes to the LangGraph DAG:

```python
# After export_dossier, add:
builder.add_node("plan_outline", self._plan_outline)
builder.add_node("detect_convergences", self._detect_convergences)
builder.add_node("generate_bridging", self._generate_bridging)
builder.add_node("export_outline", self._export_outline)
```

---

## Phase 3: v0.3 Reveal Ledger (1 week)

### 3.1 Requirements (from PRD)

**Output:** `exports/mysteries_reveals_table.csv`

**Tracks:**
- Mystery (linked to obligation)
- Candidate truths (possible answers)
- Reveal placement slot
- Who learns what when (coarse)

### 3.2 New Contracts

```python
# src/showrunner/contracts/reveal.py

class CandidateTruth(BaseModel):
    """A possible answer to a mystery."""
    truth_id: str
    description: str
    evidence_for: list[str]    # evidence_anchor_ids supporting
    evidence_against: list[str] # evidence_anchor_ids contradicting
    likelihood: float          # 0-1

class RevealEntry(BaseModel):
    """A mystery with its reveal plan."""
    reveal_id: str
    mystery_obligation_id: str
    mystery_description: str
    candidate_truths: list[CandidateTruth]
    selected_truth: str | None  # truth_id if decided
    reveal_placement: str | None  # book/chapter hint
    characters_who_learn: list[str]  # entity_ids
    dramatic_impact: str  # "major", "moderate", "minor"
```

---

## Phase 4: v0.4 Twist Bank (1 week)

### 4.1 Requirements (from PRD)

**Output:** `exports/twist_bank.md`

**Constraints:**
- Twists constrained by obligations ledger
- State plausibility (coarse)
- Evidence congruence (no invented canon claims)

**Each twist includes:**
- Affected obligations
- Required setup/backfill suggestions
- Risk notes

### 4.2 New Contracts

```python
# src/showrunner/contracts/twist.py

class TwistProposal(BaseModel):
    """A proposed narrative twist."""
    twist_id: str
    description: str
    twist_type: Literal["revelation", "reversal", "betrayal", "death", "return", "identity"]
    affected_obligations: list[str]
    affected_entities: list[str]

    # Validation
    evidence_support: list[str]  # Evidence anchors that support this twist
    contradictions: list[str]    # Evidence anchors that contradict (must be resolvable)

    # Planning
    required_setup: list[str]    # Beats needed before twist
    backfill_suggestions: list[str]  # Retroactive plants if needed

    # Risk assessment
    reader_predictability: float  # 0-1 (0 = shocking, 1 = obvious)
    thematic_alignment: float     # 0-1
    risk_notes: list[str]
```

---

## Phase 5: Passive Mode - Git Hooks (V1)

### 5.1 Architecture

```
.git/hooks/
├── pre-commit          # Trigger incremental analysis
└── post-commit         # Update review queue

src/showrunner/
├── hooks/
│   ├── __init__.py
│   ├── git_hook_handler.py   # Main hook entry point
│   ├── change_detector.py    # Detect changed text files
│   └── incremental_runner.py # Run pipeline on changes only
```

### 5.2 Hook Flow

```
1. pre-commit triggers
2. Detect changed .txt files in corpus/
3. Re-index only changed sources (delta passages)
4. Re-run ER/obligations only on impacted passages
5. Update manifests + findings
6. Add questions to review/queue.jsonl (non-blocking)
7. Commit proceeds (silent capture)
```

### 5.3 Review Queue Contract

```python
class ReviewQueueItem(BaseModel):
    """An item requiring human review."""
    item_id: str
    created_at: datetime
    category: Literal["ambiguous_entity", "low_confidence_obligation", "potential_contradiction"]
    description: str
    related_ids: list[str]
    suggested_actions: list[str]
    status: Literal["pending", "reviewed", "dismissed"]
```

---

## Phase 6: Advanced Tech Stack Integration

Based on your research, here's the integration roadmap:

### 6.0 Capability Uplift Assessment (Research Layered Stack)

**Question:** Does the research-layered stack add real capabilities beyond the contract-first, evidence-gated MVP?  
**Definition:** A "capability" either enables new tasks reliably or significantly reduces error rates and human cleanup.  
**Decision:** Prioritize layers that unlock new tasks; treat reliability and performance layers as secondary.

| Layer | Capability Uplift | New Outputs or Failure Modes It Fixes | Notes |
|------|------------------|----------------------------------------|------|
| RLM tool environment | Yes | Massive-corpus queries without context stuffing; deeper evidence-anchored searches | Enables recursive, multi-step analysis |
| GraphRAG + graph backend | Yes | Multi-hop queries across entities, events, obligations; reduces manual joins | Strong cross-thread reasoning |
| Temporal memory (Zep-like) | Yes | Tracks "what changed when"; detects drift over time | Essential for long-running writing |
| Hierarchical outlining (DOME) | Yes | Long-horizon outline generation with conflict checks | More systematic than heuristics |
| Multi-agent evaluation | Yes | Generates and scores alternatives; reduces "cool but breaks canon" | Improves selection quality |
| Hallucination detection | Partial | Flags low-confidence claims for review | Reliability improvement |
| Mind-map hardening | Partial | Dependency tracking and repair loops | Reliability improvement |
| Context caching + speculative decoding | No | Faster and cheaper inference only | Performance, not new capability |

### 6.1 RLM (Recursive Language Model) Integration

**Purpose:** Handle 1.7M word corpus without context limits

```python
# src/showrunner/rlm/
├── __init__.py
├── repl_executor.py      # Python REPL for corpus queries
├── corpus_variable.py    # Corpus as queryable variable
└── sub_llm_delegator.py  # Launch sub-LLM calls on snippets
```

**Interface:**
```python
class RLMCorpusManager:
    def __init__(self, corpus_path: Path):
        self._corpus = self._load_as_variable(corpus_path)

    def query(self, query: str) -> list[PassageRecord]:
        """Query corpus programmatically."""
        # Generate Python code to search
        # Execute in REPL
        # Return matching passages
        ...

    def delegate_to_llm(self, passages: list[PassageRecord], prompt: str) -> str:
        """Delegate specific passages to LLM for analysis."""
        ...
```

### 6.2 GraphRAG Integration (FalkorDB + Cognee)

**Purpose:** 90% hallucination reduction, sub-50ms queries

```python
# src/showrunner/graph/
├── __init__.py
├── entity_graph.py       # Entity relationship graph
├── temporal_edges.py     # Time-aware relationships
├── community_detector.py # Faction dynamics
└── query_engine.py       # Natural language graph queries
```

**Schema:**
```
(Entity)-[:ALLIED_WITH {from: date, to: date}]->(Entity)
(Entity)-[:OWES_DEBT {amount: str, reason: str}]->(Entity)
(Prophecy)-[:MENTIONS]->(Entity)
(Obligation)-[:BLOCKS]->(Obligation)
```

### 6.3 Zep Temporal Knowledge Graph

**Purpose:** Track when relationships changed over time

```python
class TemporalRelationship(BaseModel):
    source_entity: str
    target_entity: str
    relationship_type: str
    valid_from: str  # passage_id where relationship started
    valid_to: str | None  # passage_id where relationship ended
    evidence: list[str]
```

### 6.4 DOME Hierarchical Outlining

**Purpose:** 87% conflict reduction through memory-enhanced planning

```python
class DOMEOutliner:
    def __init__(self, tkg: TemporalKnowledgeGraph):
        self._tkg = tkg

    def generate_outline(self, obligations: list[Obligation]) -> list[OutlineSection]:
        """Generate outline with TKG-based conflict detection."""
        # Query TKG for relationship states
        # Detect potential conflicts
        # Adjust outline to avoid contradictions
        ...
```

### 6.5 A-HMAD Multi-Agent Debate

**Purpose:** 4-6% accuracy gains, 30% fewer factual errors

```python
# src/showrunner/agents/
├── __init__.py
├── lore_expert.py        # Trained on wiki/supplementary
├── prophecy_interpreter.py
├── character_psychologist.py
├── plot_architect.py
├── foreshadowing_tracker.py
└── debate_coordinator.py  # Orchestrates agent consensus
```

### 6.6 Character Voice Models (V1+)

**Purpose:** POV-specific fine-tuned generation

```python
class CharacterVoice:
    def __init__(self, character_name: str, pov_chapters: list[PassageRecord]):
        self._voice_model = self._fine_tune(pov_chapters)

    def generate(self, prompt: str, context: dict) -> str:
        """Generate text in character's voice."""
        ...
```

---

## Future Spec (Post-V1, Non-binding): Interactive Visualization UI

This is a placeholder spec to keep the idea visible without constraining post-V1 design choices.

**Concept:** A separate GUI deliverable for non-technical users to explore obligations and canon links.

**Possible capabilities (not commitments):**
- Interactive graph view of entities, obligations, and evidence anchors
- Per-entity ledger (oaths, promises, mysteries, setups) with timelines
- Faceted filtering by entity type, obligation category, confidence, and source
- Drill-down from dossier entries to the exact evidence excerpts
- Exportable views (PNG/SVG/JSON) for reports and review

---

## Implementation Priority Matrix

Note: The interactive GUI deliverable is explicitly out of scope for V1 and is tracked only in the Future Spec section.

| Phase | Component | Effort | Value | Priority |
|-------|-----------|--------|-------|----------|
| 1.1 | Pipeline test fixes | Low | Medium | P1 |
| 1.2 | LLM Provider interface | Medium | High | P1 |
| 2 | Master Outline (v0.2) | High | High | P1 |
| 3 | Reveal Ledger (v0.3) | Medium | High | P2 |
| 4 | Twist Bank (v0.4) | Medium | High | P2 |
| 5 | Git Hooks (passive) | Medium | Medium | P2 |
| 6.1 | RLM integration | High | Very High | P2 |
| 6.2 | GraphRAG | High | Very High | P3 |
| 6.3 | Temporal KG | Medium | High | P3 |
| 6.4 | DOME outlining | Medium | High | P3 |
| 6.5 | Multi-agent debate | High | Medium | P4 |
| 6.6 | Character voices | Very High | Medium | P4 |

---

## Immediate Next Actions

### This Week

1. **Fix pipeline tests** - Add factory injection support
2. **Create LLM provider interface** - Enable swapping rule-based for Claude
3. **Test with real corpus** - Run on sample ASOIAF text
4. **Benchmark extraction quality** - Measure precision/recall on known obligations

### Next Week

1. **Start v0.2 Master Outline** - Design outline contracts
2. **Implement convergence detection** - Find where plot threads meet
3. **Add coverage mapping** - Track obligation → outline beat mapping

### Month 1

1. Complete v0.2, v0.3, v0.4
2. Implement git hooks for passive mode
3. Begin RLM integration for large corpus handling

---

## File Structure After V1

```
showrunner/
├── src/showrunner/
│   ├── contracts/           # Pydantic models (expanded)
│   ├── adapters/            # Input adapters
│   ├── indexers/            # Canon indexing
│   ├── resolvers/           # Entity resolution
│   ├── extractors/          # Obligation extraction
│   ├── processors/          # Deduplication
│   ├── renderers/           # Export rendering
│   ├── gates/               # Quality validation
│   ├── pipeline/            # LangGraph orchestrator
│   ├── planners/            # Outline/reveal/twist planning (NEW)
│   ├── providers/           # LLM provider interface (NEW)
│   ├── graph/               # GraphRAG integration (NEW)
│   ├── rlm/                 # RLM corpus handling (NEW)
│   ├── hooks/               # Git hook handlers (NEW)
│   └── agents/              # Multi-agent debate (NEW)
├── tests/
├── schemas/
├── exports/
│   ├── Unresolved_Threads_Dossier.md
│   ├── master_outline_books_6_7.md  (v0.2)
│   ├── mysteries_reveals_table.csv  (v0.3)
│   └── twist_bank.md                (v0.4)
├── canon/
├── kb/
├── obligations/
├── qa/
└── review/
    └── queue.jsonl  (passive mode)
```
