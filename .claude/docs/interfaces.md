# Interface Contracts

## Pipeline Components

### InputAdapterProtocol
**Provided by:** adapters
**Consumed by:** pipeline/orchestrator

```python
class InputAdapterProtocol(Protocol):
    def load(self, source: Path) -> list[DocumentUnit]:
        ...
    def load_files(self, files: list[Path]) -> list[DocumentUnit]:
        ...
```

### CanonIndexerProtocol
**Provided by:** indexers
**Consumed by:** pipeline/orchestrator

```python
class CanonIndexerProtocol(Protocol):
    @property
    def segmentation_version(self) -> str: ...
    def segment_paragraphs(self, doc: DocumentUnit) -> list[PassageRecord]: ...
    def index(self, docs: list[DocumentUnit], db_path: Path) -> tuple[list[PassageRecord], Any]: ...
    def write_passages_jsonl(self, passages: list[PassageRecord], output_path: Path) -> None: ...
```

### EntityResolverProtocol
**Provided by:** resolvers
**Consumed by:** pipeline/orchestrator

```python
class EntityResolverProtocol(Protocol):
    def resolve(self, passages: list[PassageRecord]) -> tuple[list[Entity], list[AliasEntry], list[EvidenceAnchor]]: ...
```

### ObligationExtractorProtocol
**Provided by:** extractors
**Consumed by:** pipeline/orchestrator

```python
class ObligationExtractorProtocol(Protocol):
    def extract(self, passages: list[PassageRecord], entities: list[Entity]) -> tuple[list[Obligation], list[EvidenceAnchor]]: ...
```

### DedupeMergerProtocol
**Provided by:** processors
**Consumed by:** pipeline/orchestrator

```python
class DedupeMergerProtocol(Protocol):
    def merge(self, obligations: list[Obligation]) -> tuple[list[Obligation], list[ObligationGraphEdge], float]: ...
```

### QualityGatesProtocol
**Provided by:** gates
**Consumed by:** pipeline/orchestrator

```python
class QualityGatesProtocol(Protocol):
    def run_all_gates(self, passages, anchors, entities, aliases, obligations) -> tuple[list[Finding], bool]: ...
```

### ExportRendererProtocol
**Provided by:** renderers
**Consumed by:** pipeline/orchestrator

```python
class ExportRendererProtocol(Protocol):
    def render_dossier(self, obligations: list[Obligation]) -> str: ...
    def write_dossier(self, obligations: list[Obligation], output_path: Path) -> None: ...
```

## Provider Harness

### LLMProviderProtocol
**Provided by:** providers
**Consumed by:** resolvers / extractors / planners

```python
@runtime_checkable
class LLMProviderProtocol(Protocol):
    @property
    def model_name(self) -> str: ...
    def complete(self, prompt: str, system_prompt: str | None = None, temperature: float = 0.0, max_tokens: int = 4096) -> str: ...
    def complete_structured(self, prompt: str, response_model: type, system_prompt: str | None = None, temperature: float = 0.0): ...
```

## Agent Harness (v1)

### AgentHarnessProtocol
**Provided by:** agent/harness
**Consumed by:** future runtime integration, CLI/API wrappers

```python
class AgentHarnessProtocol(Protocol):
    def run_pipeline(self, input_source: Path, output_dir: Path) -> AgentRunResult: ...
    def list_artifacts(self, output_dir: Path) -> list[str]: ...
    def read_artifact(self, output_dir: Path, relative_path: str) -> str: ...
```

## Agent Runtime (planned)

### AgentRuntimeProtocol
**Provided by:** agent/runtime (planned)
**Consumed by:** CLI/API/GUI entrypoints

```python
class AgentRuntimeProtocol(Protocol):
    def run(self, input_source: Path, output_dir: Path) -> AgentRunResult: ...
    def list_artifacts(self, output_dir: Path) -> list[str]: ...
    def read_artifact(self, output_dir: Path, relative_path: str) -> str: ...
    def capabilities(self) -> dict[str, bool]: ...
```

### Runtime Modes
`pipeline` | `langchain` | `deepagents`

## Planning Modules (v0.2+)

### OutlinePlanner
```python
class OutlinePlanner(Protocol):
    def plan(self, obligations: list[Obligation], entities: list[Entity]) -> list[OutlineSection]: ...
```

### ConvergenceDetector
```python
class ConvergenceDetector(Protocol):
    def detect(self, outline: list[OutlineSection]) -> list[ConvergencePoint]: ...
```

### BridgingGenerator
```python
class BridgingGenerator(Protocol):
    def generate(self, outline: list[OutlineSection]) -> list[Beat]: ...
```

### RevealPlanner
```python
class RevealPlanner(Protocol):
    def plan(self, obligations: list[Obligation], anchors: list[EvidenceAnchor]) -> list[RevealEntry]: ...
```

### TwistPlanner
```python
class TwistPlanner(Protocol):
    def plan(self, obligations: list[Obligation], anchors: list[EvidenceAnchor]) -> list[TwistProposal]: ...
```

## Wiki Extraction (v1+)

### EventExtractorProtocol
```python
class EventExtractorProtocol(Protocol):
    def extract(
        self,
        passages: list[PassageRecord],
        entities: list[Entity],
        obligations: list[Obligation],
        anchors: list[EvidenceAnchor],
    ) -> list[Event]:
        """Return events referencing existing evidence_anchor_ids only."""
        ...
```

### RelationshipExtractorProtocol
```python
class RelationshipExtractorProtocol(Protocol):
    def extract(
        self,
        passages: list[PassageRecord],
        entities: list[Entity],
        obligations: list[Obligation],
        anchors: list[EvidenceAnchor],
    ) -> list[Relationship]:
        """Return relationships referencing existing evidence_anchor_ids only."""
        ...
```

## Incremental Hooks (v1)

### ChangeDetector
```python
class ChangeDetector(Protocol):
    def changed_text_files(self) -> list[Path]: ...
```

### IncrementalRunner
```python
class IncrementalRunner(Protocol):
    def run_incremental(self, changed_files: list[Path]) -> None: ...
```
