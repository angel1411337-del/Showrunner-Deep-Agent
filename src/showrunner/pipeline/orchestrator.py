"""LangGraph Pipeline Orchestrator for Showrunner."""

from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from pydantic import BaseModel, Field

from showrunner.contracts import (
    AliasEntry,
    DocumentUnit,
    Entity,
    EvidenceAnchor,
    Finding,
    Obligation,
    ObligationGraphEdge,
    PassageRecord,
    RunManifest,
)

_langgraph_memory_saver: type[Any]
_langgraph_stategraph: type[Any] | None
_langgraph_end: object
_langgraph_available: bool

_langgraph_end = object()


class _FallbackMemorySaver:  # minimal stub for tests
    pass


_langgraph_memory_saver = _FallbackMemorySaver
_langgraph_stategraph = None
_langgraph_available = False

try:  # pragma: no cover - optional dependency
    graph_module = importlib.import_module("langgraph.graph")
    checkpoint_module = importlib.import_module("langgraph.checkpoint.memory")
    _langgraph_end = cast("object", graph_module.END)
    _langgraph_stategraph = cast("type[Any]", graph_module.StateGraph)
    _langgraph_memory_saver = cast("type[Any]", checkpoint_module.MemorySaver)
    _langgraph_available = True
except Exception:
    _langgraph_available = False

END: object = _langgraph_end
MemorySaver: type[Any] = _langgraph_memory_saver
StateGraph: type[Any] | None = _langgraph_stategraph

if TYPE_CHECKING:
    from collections.abc import Callable

    from showrunner.pipeline.protocols import (
        CanonIndexerProtocol,
        DedupeMergerProtocol,
        EntityResolverProtocol,
        ExportRendererProtocol,
        InputAdapterProtocol,
        ObligationExtractorProtocol,
        QualityGatesProtocol,
    )
else:
    from showrunner.pipeline import protocols as _protocols

    CanonIndexerProtocol = _protocols.CanonIndexerProtocol
    DedupeMergerProtocol = _protocols.DedupeMergerProtocol
    EntityResolverProtocol = _protocols.EntityResolverProtocol
    ExportRendererProtocol = _protocols.ExportRendererProtocol
    InputAdapterProtocol = _protocols.InputAdapterProtocol
    ObligationExtractorProtocol = _protocols.ObligationExtractorProtocol
    QualityGatesProtocol = _protocols.QualityGatesProtocol


class PipelineConfig(BaseModel):
    """Configuration for pipeline execution."""

    input_source: Path = Field(...)
    output_dir: Path = Field(...)
    segmentation_version: str = Field(default="1.0.0")
    vehicle_min_mentions: int = Field(default=3, ge=1)
    similarity_threshold: float = Field(default=0.8, ge=0.0, le=1.0)


class PipelineState(dict[str, Any]):
    """State passed through the LangGraph DAG (dict with attribute access)."""

    documents: list[DocumentUnit]
    passages: list[PassageRecord]
    entities: list[Entity]
    aliases: list[AliasEntry]
    evidence_anchors: list[EvidenceAnchor]
    obligations: list[Obligation]
    obligation_edges: list[ObligationGraphEdge]
    findings: list[Finding]
    dossier_content: str
    dossier_path: Path
    error: str | None
    gates_passed: bool

    def __getattr__(self, item: str) -> Any:
        return self.get(item)

    def __setattr__(self, key: str, value: object) -> None:
        self[key] = value


class _FallbackGraph:
    """Fallback graph runner when LangGraph is unavailable."""

    def __init__(self, pipeline: ShowrunnerPipeline) -> None:
        self._pipeline = pipeline

    def invoke(
        self, initial_state: PipelineState, config: dict[str, Any] | None = None
    ) -> PipelineState:
        return self._pipeline._run_sequential(initial_state)  # pyright: ignore[reportPrivateUsage]

    def stream(self, initial_state: PipelineState, config: dict[str, Any] | None = None):
        yield {"final": self.invoke(initial_state, config)}


@dataclass
class ComponentFactory:
    """Factory for creating pipeline components.

    This factory creates concrete implementations by default but can be
    subclassed to provide mock implementations for testing.
    """

    config: PipelineConfig

    def create_input_adapter(self) -> InputAdapterProtocol:
        """Create an input adapter for loading documents."""
        from showrunner.adapters.input_adapter import create_adapter

        return create_adapter(self.config.input_source)

    def create_canon_indexer(self) -> CanonIndexerProtocol:
        """Create a canon indexer for segmenting and indexing passages."""
        from showrunner.indexers.canon_indexer import CanonIndexer

        return CanonIndexer(segmentation_version=self.config.segmentation_version)

    def create_entity_resolver(self) -> EntityResolverProtocol:
        """Create an entity resolver for extracting and linking entities."""
        from showrunner.resolvers.entity_resolver import EntityResolver

        return EntityResolver(vehicle_min_mentions=self.config.vehicle_min_mentions)

    def create_obligation_extractor(self) -> ObligationExtractorProtocol:
        """Create an obligation extractor."""
        from showrunner.extractors.obligation_extractor import ObligationExtractor

        return ObligationExtractor()

    def create_dedupe_merger(self) -> DedupeMergerProtocol:
        """Create a dedupe merger for obligation deduplication."""
        from showrunner.processors.dedupe_merger import DedupeMerger

        return DedupeMerger(similarity_threshold=self.config.similarity_threshold)

    def create_quality_gates(self) -> QualityGatesProtocol:
        """Create quality gates for validation."""
        from showrunner.gates.quality_gates import QualityGates

        return QualityGates()

    def create_export_renderer(
        self,
        passages: list[PassageRecord] | None = None,
        entities: list[Entity] | None = None,
        anchors: list[EvidenceAnchor] | None = None,
    ) -> ExportRendererProtocol:
        """Create an export renderer for dossier output."""
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter

        return ExportRenderer(
            formatter=MarkdownFormatter(),
            passages=passages or [],
            entities=entities or [],
            anchors=anchors or [],
        )


class ShowrunnerPipeline:
    """Main orchestrator using LangGraph.

    Supports dependency injection via factory parameter for testing
    and swapping component implementations.
    """

    def __init__(
        self,
        config: PipelineConfig,
        factory: ComponentFactory | None = None,
        on_progress: Callable[[str, float], None] | None = None,
    ) -> None:
        """Initialize the pipeline.

        Args:
            config: Pipeline configuration
            factory: Optional component factory for dependency injection.
                     If None, uses default ComponentFactory.
            on_progress: Optional callback for progress reporting.
        """
        self._config = config
        self._on_progress = on_progress
        self._factory = factory if factory is not None else ComponentFactory(config=config)
        self._checkpointer = MemorySaver()
        self._checkpoint_states: dict[str, PipelineState] = {}
        self._graph: Any = None
        self._compiled_graph: Any = self._build_graph()

    def _report_progress(self, stage: str, progress: float) -> None:
        if self._on_progress:
            self._on_progress(stage, progress)

    def _build_graph(self) -> object:
        self._node_names = [
            "load_input",
            "index_canon",
            "resolve_entities",
            "extract_obligations",
            "merge_duplicates",
            "validate_gates",
            "export_dossier",
            "handle_error",
        ]
        self._entry_point = "load_input"
        self._conditional_nodes = {"validate_gates"}
        if not _langgraph_available:
            self._graph = object()
            return _FallbackGraph(self)

        builder = StateGraph(PipelineState) if StateGraph is not None else None
        if builder is None:
            self._graph = object()
            return _FallbackGraph(self)
        builder.add_node("load_input", self._load_input)
        builder.add_node("index_canon", self._index_canon)
        builder.add_node("resolve_entities", self._resolve_entities)
        builder.add_node("extract_obligations", self._extract_obligations)
        builder.add_node("merge_duplicates", self._merge_duplicates)
        builder.add_node("validate_gates", self._validate_gates)
        builder.add_node("export_dossier", self._export_dossier)
        builder.add_node("handle_error", self._handle_error)
        builder.set_entry_point(self._entry_point)
        builder.add_edge("load_input", "index_canon")
        builder.add_edge("index_canon", "resolve_entities")
        builder.add_edge("resolve_entities", "extract_obligations")
        builder.add_edge("extract_obligations", "merge_duplicates")
        builder.add_edge("merge_duplicates", "validate_gates")
        builder.add_conditional_edges(
            "validate_gates", self._check_gates, {"pass": "export_dossier", "fail": "handle_error"}
        )
        builder.add_edge("export_dossier", END)
        builder.add_edge("handle_error", END)
        self._graph = builder
        return builder.compile(checkpointer=self._checkpointer)

    def get_node_names(self) -> list[str]:
        return list(self._node_names)

    def has_conditional_edge(self, node_name: str) -> bool:
        return node_name in self._conditional_nodes

    def get_entry_point(self) -> str:
        return self._entry_point

    def _check_gates(self, state: PipelineState) -> str:
        return "pass" if state.get("gates_passed", False) else "fail"

    def _run_sequential(self, initial_state: PipelineState) -> PipelineState:
        """Fallback sequential execution when LangGraph is unavailable."""
        state = PipelineState(initial_state)
        for stage in (
            self._load_input,
            self._index_canon,
            self._resolve_entities,
            self._extract_obligations,
            self._merge_duplicates,
            self._validate_gates,
        ):
            update = stage(state)
            state.update(update)
            if stage is not self._validate_gates and state.get("error"):
                state.update(self._handle_error(state))
                return state
        if state.get("error"):
            state.update(self._handle_error(state))
            return state
        if state.get("gates_passed", False):
            state.update(self._export_dossier(state))
        else:
            state.update(self._handle_error(state))
        return state

    def _load_input(self, state: PipelineState) -> PipelineState:
        self._report_progress("load_input", 0.0)
        if state.get("error"):
            return state
        if "documents" in state:
            self._report_progress("load_input", 1.0)
            return state
        try:
            adapter = self._factory.create_input_adapter()
            documents = adapter.load(self._config.input_source)
            self._report_progress("load_input", 1.0)
            return PipelineState({"documents": documents})
        except Exception as e:
            return PipelineState({"error": f"Failed to load input: {e}"})

    def _index_canon(self, state: PipelineState) -> PipelineState:
        self._report_progress("index_canon", 0.0)
        if state.get("error"):
            return state
        try:
            indexer = self._factory.create_canon_indexer()
            documents = state.get("documents", [])
            all_passages: list[PassageRecord] = []
            for doc in documents:
                passages = indexer.segment_paragraphs(doc)
                all_passages.extend(passages)
            db_path = self._config.output_dir / "canon" / "index.sqlite"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            indexer.index(documents, db_path)
            jsonl_path = self._config.output_dir / "canon" / "passages.jsonl"
            if hasattr(indexer, "write_passages_jsonl"):
                indexer.write_passages_jsonl(all_passages, jsonl_path)
            jsonl_path.parent.mkdir(parents=True, exist_ok=True)
            with open(jsonl_path, "w") as f:
                for passage in all_passages:
                    f.write(json.dumps(passage.model_dump(), default=str) + "\n")
            self._report_progress("index_canon", 1.0)
            return PipelineState({"passages": all_passages})
        except Exception as e:
            return PipelineState({"error": f"Failed to index canon: {e}"})

    def _resolve_entities(self, state: PipelineState) -> PipelineState:
        self._report_progress("resolve_entities", 0.0)
        if state.get("error"):
            return state
        try:
            resolver = self._factory.create_entity_resolver()
            passages = state.get("passages", [])
            entities, aliases, anchors = resolver.resolve(passages)
            entities_path = self._config.output_dir / "kb" / "entities.json"
            entities_path.parent.mkdir(parents=True, exist_ok=True)
            with open(entities_path, "w") as f:
                json.dump([e.model_dump() for e in entities], f, indent=2, default=str)
            aliases_path = self._config.output_dir / "kb" / "aliases.json"
            with open(aliases_path, "w") as f:
                json.dump([a.model_dump() for a in aliases], f, indent=2, default=str)
            self._report_progress("resolve_entities", 1.0)
            return PipelineState(
                {"entities": entities, "aliases": aliases, "evidence_anchors": anchors}
            )
        except Exception as e:
            return PipelineState({"error": f"Failed to resolve entities: {e}"})

    def _extract_obligations(self, state: PipelineState) -> PipelineState:
        self._report_progress("extract_obligations", 0.0)
        if state.get("error"):
            return state
        try:
            extractor = self._factory.create_obligation_extractor()
            passages = state.get("passages", [])
            entities = state.get("entities", [])
            obligations, anchors = extractor.extract(passages, entities)
            existing_anchors = state.get("evidence_anchors", [])
            all_anchors = existing_anchors + anchors
            self._report_progress("extract_obligations", 1.0)
            return PipelineState({"obligations": obligations, "evidence_anchors": all_anchors})
        except Exception as e:
            return PipelineState({"error": f"Failed to extract obligations: {e}"})

    def _merge_duplicates(self, state: PipelineState) -> PipelineState:
        self._report_progress("merge_duplicates", 0.0)
        if state.get("error"):
            return state
        try:
            merger = self._factory.create_dedupe_merger()
            obligations = state.get("obligations", [])
            merged, edges, _dedupe_rate = merger.merge(obligations)
            obl_path = self._config.output_dir / "obligations" / "obligations.json"
            obl_path.parent.mkdir(parents=True, exist_ok=True)
            with open(obl_path, "w") as f:
                json.dump([o.model_dump() for o in merged], f, indent=2, default=str)
            self._report_progress("merge_duplicates", 1.0)
            return PipelineState({"obligations": merged, "obligation_edges": edges})
        except Exception as e:
            return PipelineState({"error": f"Failed to merge duplicates: {e}"})

    def _validate_gates(self, state: PipelineState) -> PipelineState:
        self._report_progress("validate_gates", 0.0)
        if state.get("error"):
            return state
        try:
            gates = self._factory.create_quality_gates()
            passages = state.get("passages", [])
            anchors = state.get("evidence_anchors", [])
            entities = state.get("entities", [])
            aliases = state.get("aliases", [])
            obligations = state.get("obligations", [])
            passed, findings = gates.validate(
                passages=passages,
                anchors=anchors,
                entities=entities,
                aliases=aliases,
                obligations=obligations,
            )
            findings_path = self._config.output_dir / "qa" / "findings.jsonl"
            findings_path.parent.mkdir(parents=True, exist_ok=True)
            with open(findings_path, "w") as f:
                for finding in findings:
                    f.write(json.dumps(finding.model_dump(), default=str) + "\n")
            self._report_progress("validate_gates", 1.0)
            if not passed:
                return PipelineState(
                    {
                        "findings": findings,
                        "gates_passed": passed,
                        "error": "Quality gates failed",
                    }
                )
            return PipelineState({"findings": findings, "gates_passed": passed})
        except Exception as e:
            return PipelineState({"error": f"Failed to validate gates: {e}"})

    def _export_dossier(self, state: PipelineState) -> PipelineState:
        self._report_progress("export_dossier", 0.0)
        if state.get("error"):
            return state
        try:
            passages = state.get("passages", [])
            entities = state.get("entities", [])
            anchors = state.get("evidence_anchors", [])
            obligations = state.get("obligations", [])
            renderer = self._factory.create_export_renderer(passages, entities, anchors)
            dossier_path = self._config.output_dir / "exports" / "Unresolved_Threads_Dossier.md"
            dossier_path.parent.mkdir(parents=True, exist_ok=True)
            render_result = renderer.render(obligations)
            dossier_content = ""
            if isinstance(render_result, Path):
                dossier_path = render_result
            else:
                dossier_content = render_result

            if hasattr(renderer, "write_dossier"):
                renderer.write_dossier(obligations, dossier_path)
            self._report_progress("export_dossier", 1.0)
            return PipelineState({"dossier_content": dossier_content, "dossier_path": dossier_path})
        except Exception as e:
            return PipelineState({"error": f"Failed to export dossier: {e}"})

    def _handle_error(self, state: PipelineState) -> PipelineState:
        error = state.get("error", "Unknown error")
        findings_path = self._config.output_dir / "qa" / "findings.jsonl"
        findings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(findings_path, "a") as f:
            finding = {
                "finding_id": f"error_{datetime.now().isoformat()}",
                "severity": "error",
                "category": "pipeline_error",
                "message": error,
                "timestamp": datetime.now().isoformat(),
            }
            f.write(json.dumps(finding) + "\n")
        return state

    def _get_git_sha(self) -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"

    def _compute_hash(self, content: str) -> str:
        return f"sha256:{hashlib.sha256(content.encode()).hexdigest()[:16]}"

    def _execute_graph(self, initial_state: PipelineState, thread_id: str) -> PipelineState:
        config = {"configurable": {"thread_id": thread_id}}
        final_state: dict[str, PipelineState] | None = None
        for state in self._compiled_graph.stream(initial_state, config):
            final_state = state
        actual_state = list(final_state.values())[0] if final_state else PipelineState()
        return PipelineState(actual_state)

    def run(self, thread_id: str | None = None) -> tuple[PipelineState, RunManifest]:
        start_time = datetime.now()
        run_id = f"run_{start_time.strftime('%Y%m%d_%H%M%S')}"
        self._config.output_dir.mkdir(parents=True, exist_ok=True)
        actual_thread_id = thread_id or run_id
        initial_state = PipelineState()
        actual_state = self._execute_graph(initial_state, actual_thread_id)
        end_time = datetime.now()
        manifest = RunManifest(
            run_id=run_id,
            timestamp=start_time,
            git_sha=self._get_git_sha(),
            python_version="3.14.2",
            segmentation_version=self._config.segmentation_version,
            config_hash=self._compute_hash(self._config.model_dump_json()),
            input_dataset_hash=self._compute_hash(str(self._config.input_source)),
            completed_timestamp=end_time,
            status="completed" if not actual_state.get("error") else "failed",
        )
        manifest_path = self._config.output_dir / "run_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest.model_dump(), f, indent=2, default=str)
        self._checkpoint_states[actual_thread_id] = actual_state
        return actual_state, manifest

    def run_incremental(self, changed_files: list[Path]) -> PipelineState:
        adapter = self._factory.create_input_adapter()
        documents: list[DocumentUnit]
        if hasattr(adapter, "load_files"):
            documents = adapter.load_files(changed_files)
        else:
            documents = []
            for path in changed_files:
                from showrunner.adapters.input_adapter import create_adapter

                file_adapter = create_adapter(path)
                documents.extend(file_adapter.load(path))
        initial_state = PipelineState({"documents": documents})
        thread_id = f"incremental_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        state = self._execute_graph(initial_state, thread_id)
        self._checkpoint_states[thread_id] = state
        return state

    def get_checkpoint_state(self, thread_id: str) -> PipelineState | None:
        return self._checkpoint_states.get(thread_id)

    def can_resume(self, thread_id: str) -> bool:
        return thread_id in self._checkpoint_states
