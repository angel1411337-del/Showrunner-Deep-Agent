#!/usr/bin/env python
"""Script to write the pipeline orchestrator module."""

from pathlib import Path

CODE = '''"""LangGraph Pipeline Orchestrator for Showrunner."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
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


class PipelineConfig(BaseModel):
    """Configuration for pipeline execution."""
    input_source: Path = Field(...)
    output_dir: Path = Field(...)
    segmentation_version: str = Field(default="1.0.0")
    vehicle_min_mentions: int = Field(default=3, ge=1)
    similarity_threshold: float = Field(default=0.8, ge=0.0, le=1.0)


class PipelineState(TypedDict, total=False):
    """State passed through the LangGraph DAG."""
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


@dataclass
class ComponentFactory:
    """Factory for creating pipeline components."""
    config: PipelineConfig

    def create_input_adapter(self) -> Any:
        from showrunner.adapters.input_adapter import create_adapter
        return create_adapter(self.config.input_source)

    def create_canon_indexer(self) -> Any:
        from showrunner.indexers.canon_indexer import CanonIndexer
        return CanonIndexer(segmentation_version=self.config.segmentation_version)

    def create_entity_resolver(self) -> Any:
        from showrunner.resolvers.entity_resolver import EntityResolver
        return EntityResolver(vehicle_min_mentions=self.config.vehicle_min_mentions)

    def create_obligation_extractor(self) -> Any:
        from showrunner.extractors.obligation_extractor import ObligationExtractor
        return ObligationExtractor()

    def create_dedupe_merger(self) -> Any:
        from showrunner.processors.dedupe_merger import DedupeMerger
        return DedupeMerger(similarity_threshold=self.config.similarity_threshold)

    def create_quality_gates(self) -> Any:
        from showrunner.gates.quality_gates import QualityGates
        return QualityGates()

    def create_export_renderer(self, passages, entities, anchors) -> Any:
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter
        return ExportRenderer(formatter=MarkdownFormatter(), passages=passages, entities=entities, anchors=anchors)


class ShowrunnerPipeline:
    """Main orchestrator using LangGraph."""

    def __init__(self, config: PipelineConfig, on_progress: Callable[[str, float], None] | None = None) -> None:
        self._config = config
        self._on_progress = on_progress
        self._factory = ComponentFactory(config=config)
        self._checkpointer = MemorySaver()
        self._graph = self._build_graph()

    def _report_progress(self, stage: str, progress: float) -> None:
        if self._on_progress:
            self._on_progress(stage, progress)

    def _build_graph(self) -> StateGraph:
        builder = StateGraph(PipelineState)
        builder.add_node("load_input", self._load_input)
        builder.add_node("index_canon", self._index_canon)
        builder.add_node("resolve_entities", self._resolve_entities)
        builder.add_node("extract_obligations", self._extract_obligations)
        builder.add_node("merge_duplicates", self._merge_duplicates)
        builder.add_node("validate_gates", self._validate_gates)
        builder.add_node("export_dossier", self._export_dossier)
        builder.add_node("handle_error", self._handle_error)
        builder.set_entry_point("load_input")
        builder.add_edge("load_input", "index_canon")
        builder.add_edge("index_canon", "resolve_entities")
        builder.add_edge("resolve_entities", "extract_obligations")
        builder.add_edge("extract_obligations", "merge_duplicates")
        builder.add_edge("merge_duplicates", "validate_gates")
        builder.add_conditional_edges("validate_gates", self._check_gates, {"pass": "export_dossier", "fail": "handle_error"})
        builder.add_edge("export_dossier", END)
        builder.add_edge("handle_error", END)
        return builder.compile(checkpointer=self._checkpointer)

    def _check_gates(self, state: PipelineState) -> str:
        return "pass" if state.get("gates_passed", False) else "fail"

    def _load_input(self, state: PipelineState) -> PipelineState:
        self._report_progress("load_input", 0.0)
        try:
            adapter = self._factory.create_input_adapter()
            documents = adapter.load(self._config.input_source)
            self._report_progress("load_input", 1.0)
            return {"documents": documents}
        except Exception as e:
            return {"error": f"Failed to load input: {e}"}

    def _index_canon(self, state: PipelineState) -> PipelineState:
        self._report_progress("index_canon", 0.0)
        try:
            indexer = self._factory.create_canon_indexer()
            documents = state.get("documents", [])
            all_passages = []
            for doc in documents:
                passages = indexer.segment_paragraphs(doc)
                all_passages.extend(passages)
            db_path = self._config.output_dir / "canon" / "index.sqlite"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            indexer.index(documents, db_path)
            jsonl_path = self._config.output_dir / "canon" / "passages.jsonl"
            indexer.write_passages_jsonl(all_passages, jsonl_path)
            self._report_progress("index_canon", 1.0)
            return {"passages": all_passages}
        except Exception as e:
            return {"error": f"Failed to index canon: {e}"}

    def _resolve_entities(self, state: PipelineState) -> PipelineState:
        self._report_progress("resolve_entities", 0.0)
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
            return {"entities": entities, "aliases": aliases, "evidence_anchors": anchors}
        except Exception as e:
            return {"error": f"Failed to resolve entities: {e}"}

    def _extract_obligations(self, state: PipelineState) -> PipelineState:
        self._report_progress("extract_obligations", 0.0)
        try:
            extractor = self._factory.create_obligation_extractor()
            passages = state.get("passages", [])
            entities = state.get("entities", [])
            obligations, anchors = extractor.extract(passages, entities)
            existing_anchors = state.get("evidence_anchors", [])
            all_anchors = existing_anchors + anchors
            self._report_progress("extract_obligations", 1.0)
            return {"obligations": obligations, "evidence_anchors": all_anchors}
        except Exception as e:
            return {"error": f"Failed to extract obligations: {e}"}

    def _merge_duplicates(self, state: PipelineState) -> PipelineState:
        self._report_progress("merge_duplicates", 0.0)
        try:
            merger = self._factory.create_dedupe_merger()
            obligations = state.get("obligations", [])
            merged, edges, dedupe_rate = merger.merge(obligations)
            obl_path = self._config.output_dir / "obligations" / "obligations.json"
            obl_path.parent.mkdir(parents=True, exist_ok=True)
            with open(obl_path, "w") as f:
                json.dump([o.model_dump() for o in merged], f, indent=2, default=str)
            self._report_progress("merge_duplicates", 1.0)
            return {"obligations": merged, "obligation_edges": edges}
        except Exception as e:
            return {"error": f"Failed to merge duplicates: {e}"}

    def _validate_gates(self, state: PipelineState) -> PipelineState:
        self._report_progress("validate_gates", 0.0)
        try:
            gates = self._factory.create_quality_gates()
            passages = state.get("passages", [])
            anchors = state.get("evidence_anchors", [])
            entities = state.get("entities", [])
            aliases = state.get("aliases", [])
            obligations = state.get("obligations", [])
            findings, passed = gates.run_all_gates(passages=passages, anchors=anchors, entities=entities, aliases=aliases, obligations=obligations)
            findings_path = self._config.output_dir / "qa" / "findings.jsonl"
            findings_path.parent.mkdir(parents=True, exist_ok=True)
            with open(findings_path, "w") as f:
                for finding in findings:
                    f.write(json.dumps(finding.model_dump(), default=str) + "\\n")
            self._report_progress("validate_gates", 1.0)
            return {"findings": findings, "gates_passed": passed}
        except Exception as e:
            return {"error": f"Failed to validate gates: {e}"}

    def _export_dossier(self, state: PipelineState) -> PipelineState:
        self._report_progress("export_dossier", 0.0)
        try:
            passages = state.get("passages", [])
            entities = state.get("entities", [])
            anchors = state.get("evidence_anchors", [])
            obligations = state.get("obligations", [])
            renderer = self._factory.create_export_renderer(passages, entities, anchors)
            dossier_content = renderer.render_dossier(obligations)
            dossier_path = self._config.output_dir / "exports" / "Unresolved_Threads_Dossier.md"
            dossier_path.parent.mkdir(parents=True, exist_ok=True)
            renderer.write_dossier(obligations, dossier_path)
            self._report_progress("export_dossier", 1.0)
            return {"dossier_content": dossier_content, "dossier_path": dossier_path}
        except Exception as e:
            return {"error": f"Failed to export dossier: {e}"}

    def _handle_error(self, state: PipelineState) -> PipelineState:
        error = state.get("error", "Unknown error")
        findings_path = self._config.output_dir / "qa" / "findings.jsonl"
        findings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(findings_path, "a") as f:
            finding = {"finding_id": f"error_{datetime.now().isoformat()}", "severity": "error", "category": "pipeline_error", "message": error, "timestamp": datetime.now().isoformat()}
            f.write(json.dumps(finding) + "\\n")
        return state

    def _get_git_sha(self) -> str:
        try:
            stream = os.popen("git rev-parse HEAD")
            return stream.read().strip()
        except Exception:
            return "unknown"

    def _compute_hash(self, content: str) -> str:
        return f"sha256:{hashlib.sha256(content.encode()).hexdigest()[:16]}"

    def run(self) -> tuple[PipelineState, RunManifest]:
        start_time = datetime.now()
        run_id = f"run_{start_time.strftime(\\"%Y%m%d_%H%M%S\\")}"
        self._config.output_dir.mkdir(parents=True, exist_ok=True)
        initial_state: PipelineState = {}
        config = {"configurable": {"thread_id": run_id}}
        final_state = None
        for state in self._graph.stream(initial_state, config):
            final_state = state
        actual_state = list(final_state.values())[0] if final_state else {}
        end_time = datetime.now()
        manifest = RunManifest(run_id=run_id, timestamp=start_time, git_sha=self._get_git_sha(), python_version="3.14.2", segmentation_version=self._config.segmentation_version, config_hash=self._compute_hash(self._config.model_dump_json()), input_dataset_hash=self._compute_hash(str(self._config.input_source)), completed_timestamp=end_time, status="completed" if not actual_state.get("error") else "failed")
        manifest_path = self._config.output_dir / "run_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest.model_dump(), f, indent=2, default=str)
        return actual_state, manifest

    def run_incremental(self, changed_files: list[Path]) -> PipelineState:
        return self.run()[0]
'''

if __name__ == "__main__":
    output_path = Path(__file__).parent.parent / "src" / "showrunner" / "pipeline" / "orchestrator.py"
    output_path.write_text(CODE)
    print(f"Written to {output_path}")
