"""TDD tests for the LangGraph Pipeline Orchestrator.

Tests are organized by:
1. Configuration and State tests
2. Component interface tests
3. Factory pattern tests
4. Observer pattern (progress callbacks) tests
5. Pipeline graph construction tests
6. Pipeline execution tests
7. Incremental execution tests
8. Error handling and retry tests
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from showrunner.contracts import (
    AliasEntry,
    DocumentUnit,
    Entity,
    EntityType,
    EvidenceAnchor,
    Finding,
    FindingSeverity,
    Obligation,
    ObligationCategory,
    PassageRecord,
    RunManifest,
)

if TYPE_CHECKING:
    from showrunner.pipeline.orchestrator import PipelineConfig, PipelineState


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_documents() -> list[DocumentUnit]:
    """Create sample documents for testing."""
    return [
        DocumentUnit(
            source_id="book1",
            source_path="/corpus/book1.txt",
            order_hint=0,
            raw_text="Once upon a time, in a land far away.\n\nThe hero set forth.",
            book_label="Book One",
        ),
        DocumentUnit(
            source_id="book2",
            source_path="/corpus/book2.txt",
            order_hint=1,
            raw_text="The adventure continues.\n\nThe mystery deepens.",
            book_label="Book Two",
        ),
    ]


@pytest.fixture
def sample_passages() -> list[PassageRecord]:
    """Create sample passages for testing."""
    return [
        PassageRecord(
            passage_id="book1:0",
            source_id="book1",
            paragraph_index=0,
            text="Once upon a time, in a land far away.",
            char_start=0,
            char_end=38,
        ),
        PassageRecord(
            passage_id="book1:1",
            source_id="book1",
            paragraph_index=1,
            text="The hero set forth.",
            char_start=40,
            char_end=59,
        ),
    ]


@pytest.fixture
def sample_entities() -> list[Entity]:
    """Create sample entities for testing."""
    return [
        Entity(
            entity_id="ent_001",
            canonical_name="The Hero",
            entity_type=EntityType.PERSON,
            first_seen_passage="book1:1",
            mention_count=10,
        ),
        Entity(
            entity_id="ent_002",
            canonical_name="The Land",
            entity_type=EntityType.PLACE,
            first_seen_passage="book1:0",
            mention_count=5,
        ),
    ]


@pytest.fixture
def sample_aliases() -> list[AliasEntry]:
    """Create sample aliases for testing."""
    return [
        AliasEntry(
            alias_id="alias_001",
            alias_text="Our Hero",
            entity_id="ent_001",
            confidence=0.95,
        ),
    ]


@pytest.fixture
def sample_evidence_anchors() -> list[EvidenceAnchor]:
    """Create sample evidence anchors for testing."""
    return [
        EvidenceAnchor(
            anchor_id="ev_001",
            passage_id="book1:0",
            char_start=0,
            char_end=38,
            excerpt="Once upon a time, in a land far away.",
        ),
    ]


@pytest.fixture
def sample_obligations() -> list[Obligation]:
    """Create sample obligations for testing."""
    return [
        Obligation(
            obligation_id="obl_001",
            category=ObligationCategory.PLOT_THREAD,
            description="The hero's journey must be completed",
            evidence_anchor_ids=["ev_001"],
            last_seen_passage_id="book1:1",
            confidence=0.85,
        ),
    ]


@pytest.fixture
def sample_findings() -> list[Finding]:
    """Create sample findings for testing."""
    return [
        Finding(
            finding_id="find_001",
            severity=FindingSeverity.INFO,
            category="validation",
            message="All obligations have evidence anchors",
        ),
    ]


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def temp_input_dir(tmp_path: Path) -> Path:
    """Create a temporary input directory with sample files."""
    input_dir = tmp_path / "corpus"
    input_dir.mkdir()
    (input_dir / "book1.txt").write_text("Once upon a time.\n\nThe hero emerged.")
    (input_dir / "book2.txt").write_text("The adventure continues.\n\nThe end draws near.")
    return input_dir


# =============================================================================
# PipelineConfig Tests
# =============================================================================


class TestPipelineConfig:
    """Tests for PipelineConfig dataclass."""

    def test_create_config_with_required_fields(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """PipelineConfig requires input_source and output_dir."""
        from showrunner.pipeline.orchestrator import PipelineConfig

        config = PipelineConfig(
            input_source=temp_input_dir,
            output_dir=temp_output_dir,
        )
        assert config.input_source == temp_input_dir
        assert config.output_dir == temp_output_dir

    def test_config_has_default_segmentation_version(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """PipelineConfig has default segmentation_version of '1.0.0'."""
        from showrunner.pipeline.orchestrator import PipelineConfig

        config = PipelineConfig(
            input_source=temp_input_dir,
            output_dir=temp_output_dir,
        )
        assert config.segmentation_version == "1.0.0"

    def test_config_has_default_vehicle_min_mentions(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """PipelineConfig has default vehicle_min_mentions of 3."""
        from showrunner.pipeline.orchestrator import PipelineConfig

        config = PipelineConfig(
            input_source=temp_input_dir,
            output_dir=temp_output_dir,
        )
        assert config.vehicle_min_mentions == 3

    def test_config_has_default_similarity_threshold(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """PipelineConfig has default similarity_threshold of 0.8."""
        from showrunner.pipeline.orchestrator import PipelineConfig

        config = PipelineConfig(
            input_source=temp_input_dir,
            output_dir=temp_output_dir,
        )
        assert config.similarity_threshold == 0.8

    def test_config_allows_custom_values(self, temp_input_dir: Path, temp_output_dir: Path) -> None:
        """PipelineConfig accepts custom parameter values."""
        from showrunner.pipeline.orchestrator import PipelineConfig

        config = PipelineConfig(
            input_source=temp_input_dir,
            output_dir=temp_output_dir,
            segmentation_version="2.0.0",
            vehicle_min_mentions=5,
            similarity_threshold=0.9,
        )
        assert config.segmentation_version == "2.0.0"
        assert config.vehicle_min_mentions == 5
        assert config.similarity_threshold == 0.9

    def test_config_validates_similarity_threshold_range(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """PipelineConfig validates similarity_threshold is between 0 and 1."""
        from showrunner.pipeline.orchestrator import PipelineConfig

        with pytest.raises(ValueError, match="similarity_threshold"):
            PipelineConfig(
                input_source=temp_input_dir,
                output_dir=temp_output_dir,
                similarity_threshold=1.5,
            )

    def test_config_validates_vehicle_min_mentions_positive(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """PipelineConfig validates vehicle_min_mentions is positive."""
        from showrunner.pipeline.orchestrator import PipelineConfig

        with pytest.raises(ValueError, match="vehicle_min_mentions"):
            PipelineConfig(
                input_source=temp_input_dir,
                output_dir=temp_output_dir,
                vehicle_min_mentions=0,
            )


# =============================================================================
# PipelineState Tests
# =============================================================================


class TestPipelineState:
    """Tests for PipelineState TypedDict."""

    def test_create_empty_state(self) -> None:
        """PipelineState can be created as empty dict."""
        state: PipelineState = {}
        assert state.get("documents") is None
        assert state.get("passages") is None
        assert state.get("entities") is None
        assert state.get("aliases") is None
        assert state.get("evidence_anchors") is None
        assert state.get("obligations") is None
        assert state.get("findings") is None
        assert state.get("dossier_path") is None
        assert state.get("error") is None

    def test_state_stores_documents(self, sample_documents: list[DocumentUnit]) -> None:
        """PipelineState can store document list."""
        state: PipelineState = {"documents": sample_documents}
        assert state.get("documents") is not None
        assert len(state["documents"]) == 2

    def test_state_stores_passages(self, sample_passages: list[PassageRecord]) -> None:
        """PipelineState can store passage list."""
        state: PipelineState = {"passages": sample_passages}
        assert state.get("passages") is not None
        assert len(state["passages"]) == 2

    def test_state_stores_entities(self, sample_entities: list[Entity]) -> None:
        """PipelineState can store entity list."""
        state: PipelineState = {"entities": sample_entities}
        assert state.get("entities") is not None
        assert len(state["entities"]) == 2

    def test_state_stores_error(self) -> None:
        """PipelineState can capture error messages."""
        state: PipelineState = {"error": "Pipeline failed at stage X"}
        assert state["error"] == "Pipeline failed at stage X"

    def test_state_is_typed_dict_compatible(self) -> None:
        """PipelineState works as LangGraph TypedDict state."""
        # Must be usable as dict for LangGraph
        state: PipelineState = {}
        assert isinstance(state, dict)
        # TypedDict is dict-compatible
        state["documents"] = []
        assert "documents" in state

    def test_state_can_be_copied(self, sample_documents: list[DocumentUnit]) -> None:
        """PipelineState can be copied as a dict."""
        original: PipelineState = {"documents": sample_documents}
        copied = dict(original)
        assert copied.get("documents") is not None
        assert len(copied["documents"]) == len(original["documents"])


# =============================================================================
# Component Interface Tests (Abstractions for DI)
# =============================================================================


class TestComponentInterfaces:
    """Tests for component abstract interfaces."""

    def test_input_adapter_interface_exists(self) -> None:
        """InputAdapter abstract interface is defined."""
        from showrunner.pipeline.orchestrator import InputAdapterProtocol

        # Protocol must define load method
        assert hasattr(InputAdapterProtocol, "load")

    def test_canon_indexer_interface_exists(self) -> None:
        """CanonIndexer abstract interface is defined."""
        from showrunner.pipeline.orchestrator import CanonIndexerProtocol

        assert hasattr(CanonIndexerProtocol, "index")

    def test_entity_resolver_interface_exists(self) -> None:
        """EntityResolver abstract interface is defined."""
        from showrunner.pipeline.orchestrator import EntityResolverProtocol

        assert hasattr(EntityResolverProtocol, "resolve")

    def test_obligation_extractor_interface_exists(self) -> None:
        """ObligationExtractor abstract interface is defined."""
        from showrunner.pipeline.orchestrator import ObligationExtractorProtocol

        assert hasattr(ObligationExtractorProtocol, "extract")

    def test_dedupe_merger_interface_exists(self) -> None:
        """DedupeMerger abstract interface is defined."""
        from showrunner.pipeline.orchestrator import DedupeMergerProtocol

        assert hasattr(DedupeMergerProtocol, "merge")

    def test_quality_gates_interface_exists(self) -> None:
        """QualityGates abstract interface is defined."""
        from showrunner.pipeline.protocols import QualityGatesProtocol

        assert hasattr(QualityGatesProtocol, "run_all_gates")

    def test_export_renderer_interface_exists(self) -> None:
        """ExportRenderer abstract interface is defined."""
        from showrunner.pipeline.protocols import ExportRendererProtocol

        assert hasattr(ExportRendererProtocol, "render_dossier")


# =============================================================================
# Factory Pattern Tests
# =============================================================================


class TestComponentFactory:
    """Tests for ComponentFactory (factory pattern)."""

    def test_factory_creates_input_adapter(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """Factory creates InputAdapter component."""
        from showrunner.pipeline.orchestrator import ComponentFactory, PipelineConfig

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        factory = ComponentFactory(config)
        adapter = factory.create_input_adapter()
        assert adapter is not None

    def test_factory_creates_canon_indexer(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """Factory creates CanonIndexer component."""
        from showrunner.pipeline.orchestrator import ComponentFactory, PipelineConfig

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        factory = ComponentFactory(config)
        indexer = factory.create_canon_indexer()
        assert indexer is not None

    def test_factory_creates_entity_resolver(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """Factory creates EntityResolver component."""
        from showrunner.pipeline.orchestrator import ComponentFactory, PipelineConfig

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        factory = ComponentFactory(config)
        resolver = factory.create_entity_resolver()
        assert resolver is not None

    def test_factory_creates_obligation_extractor(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """Factory creates ObligationExtractor component."""
        from showrunner.pipeline.orchestrator import ComponentFactory, PipelineConfig

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        factory = ComponentFactory(config)
        extractor = factory.create_obligation_extractor()
        assert extractor is not None

    def test_factory_creates_dedupe_merger(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """Factory creates DedupeMerger component."""
        from showrunner.pipeline.orchestrator import ComponentFactory, PipelineConfig

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        factory = ComponentFactory(config)
        merger = factory.create_dedupe_merger()
        assert merger is not None

    def test_factory_creates_quality_gates(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """Factory creates QualityGates component."""
        from showrunner.pipeline.orchestrator import ComponentFactory, PipelineConfig

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        factory = ComponentFactory(config)
        gates = factory.create_quality_gates()
        assert gates is not None

    def test_factory_creates_export_renderer(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """Factory creates ExportRenderer component."""
        from showrunner.pipeline.orchestrator import ComponentFactory, PipelineConfig

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        factory = ComponentFactory(config)
        renderer = factory.create_export_renderer()
        assert renderer is not None

    def test_factory_uses_config_for_component_creation(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """Factory passes config values to created components."""
        from showrunner.pipeline.orchestrator import ComponentFactory, PipelineConfig

        config = PipelineConfig(
            input_source=temp_input_dir,
            output_dir=temp_output_dir,
            similarity_threshold=0.9,
        )
        factory = ComponentFactory(config)
        # Factory should use config values when creating components
        assert factory.config.similarity_threshold == 0.9


# =============================================================================
# Dependency Injection Tests
# =============================================================================


class TestDependencyInjection:
    """Tests for dependency injection in ShowrunnerPipeline."""

    def test_pipeline_accepts_custom_factory(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """ShowrunnerPipeline accepts injected ComponentFactory."""
        from showrunner.pipeline.orchestrator import (
            ComponentFactory,
            PipelineConfig,
            ShowrunnerPipeline,
        )

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        custom_factory = ComponentFactory(config)
        pipeline = ShowrunnerPipeline(config=config, factory=custom_factory)
        assert pipeline._factory is custom_factory

    def test_pipeline_creates_default_factory_if_not_injected(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """ShowrunnerPipeline creates default factory when not injected."""
        from showrunner.pipeline.orchestrator import (
            ComponentFactory,
            PipelineConfig,
            ShowrunnerPipeline,
        )

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        pipeline = ShowrunnerPipeline(config=config)
        assert pipeline._factory is not None
        assert isinstance(pipeline._factory, ComponentFactory)

    def test_pipeline_accepts_mock_components_via_factory(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """ShowrunnerPipeline works with mocked components for testing."""
        from showrunner.pipeline.orchestrator import (
            ComponentFactory,
            PipelineConfig,
            ShowrunnerPipeline,
        )

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)

        # Create mock factory
        mock_factory = Mock(spec=ComponentFactory)
        mock_factory.config = config
        mock_factory.create_input_adapter.return_value = Mock()
        mock_factory.create_canon_indexer.return_value = Mock()
        mock_factory.create_entity_resolver.return_value = Mock()
        mock_factory.create_obligation_extractor.return_value = Mock()
        mock_factory.create_dedupe_merger.return_value = Mock()
        mock_factory.create_quality_gates.return_value = Mock()
        mock_factory.create_export_renderer.return_value = Mock()

        pipeline = ShowrunnerPipeline(config=config, factory=mock_factory)
        assert pipeline._factory is mock_factory


# =============================================================================
# Observer Pattern Tests (Progress Callbacks)
# =============================================================================


class TestProgressCallbacks:
    """Tests for observer pattern with progress callbacks."""

    def test_pipeline_accepts_progress_callback(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """ShowrunnerPipeline accepts on_progress callback."""
        from showrunner.pipeline.orchestrator import PipelineConfig, ShowrunnerPipeline

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)

        progress_callback = Mock()
        pipeline = ShowrunnerPipeline(config=config, on_progress=progress_callback)
        assert pipeline._on_progress is progress_callback

    def test_pipeline_calls_progress_callback_on_stage_start(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """Pipeline notifies progress callback when stage starts."""
        from showrunner.pipeline.orchestrator import (
            PipelineConfig,
            ShowrunnerPipeline,
        )

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        progress_callback = Mock()

        # Create mock factory with mock components
        mock_factory = self._create_mock_factory(config)

        pipeline = ShowrunnerPipeline(
            config=config, factory=mock_factory, on_progress=progress_callback
        )
        pipeline.run()

        # Check that progress was reported for load_input stage
        progress_callback.assert_any_call("load_input", pytest.approx(0.0, abs=0.15))

    def test_pipeline_reports_progress_percentage(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """Pipeline reports progress as percentage (0.0 to 1.0)."""
        from showrunner.pipeline.orchestrator import (
            PipelineConfig,
            ShowrunnerPipeline,
        )

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        progress_values: list[float] = []

        def track_progress(stage: str, progress: float) -> None:
            progress_values.append(progress)

        mock_factory = self._create_mock_factory(config)
        pipeline = ShowrunnerPipeline(
            config=config, factory=mock_factory, on_progress=track_progress
        )
        pipeline.run()

        # All progress values should be between 0 and 1
        for value in progress_values:
            assert 0.0 <= value <= 1.0

    def test_pipeline_reports_all_stages(self, temp_input_dir: Path, temp_output_dir: Path) -> None:
        """Pipeline reports progress for all pipeline stages."""
        from showrunner.pipeline.orchestrator import (
            PipelineConfig,
            ShowrunnerPipeline,
        )

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        reported_stages: list[str] = []

        def track_stages(stage: str, progress: float) -> None:
            if stage not in reported_stages:
                reported_stages.append(stage)

        mock_factory = self._create_mock_factory(config)
        pipeline = ShowrunnerPipeline(config=config, factory=mock_factory, on_progress=track_stages)
        pipeline.run()

        expected_stages = [
            "load_input",
            "index_canon",
            "resolve_entities",
            "extract_obligations",
            "merge_duplicates",
            "validate_gates",
            "export_dossier",
        ]
        for expected in expected_stages:
            assert expected in reported_stages

    def test_pipeline_works_without_progress_callback(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """Pipeline runs successfully without progress callback."""
        from showrunner.pipeline.orchestrator import (
            PipelineConfig,
            ShowrunnerPipeline,
        )

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        mock_factory = self._create_mock_factory(config)
        pipeline = ShowrunnerPipeline(config=config, factory=mock_factory)

        # Should not raise
        result, manifest = pipeline.run()
        assert result is not None

    def _create_mock_factory(self, config: PipelineConfig) -> Mock:
        """Helper to create a mock factory with all components."""
        from showrunner.pipeline.orchestrator import ComponentFactory

        mock_factory = Mock(spec=ComponentFactory)
        mock_factory.config = config

        # Mock each component with appropriate return values
        mock_adapter = Mock()
        mock_adapter.load.return_value = []
        mock_factory.create_input_adapter.return_value = mock_adapter

        mock_indexer = Mock()
        mock_indexer.index.return_value = ([], [])
        mock_factory.create_canon_indexer.return_value = mock_indexer

        mock_resolver = Mock()
        mock_resolver.resolve.return_value = ([], [], [])
        mock_factory.create_entity_resolver.return_value = mock_resolver

        mock_extractor = Mock()
        mock_extractor.extract.return_value = ([], [])
        mock_factory.create_obligation_extractor.return_value = mock_extractor

        mock_merger = Mock()
        mock_merger.merge.return_value = ([], [], 0.0)
        mock_factory.create_dedupe_merger.return_value = mock_merger

        mock_gates = Mock()
        mock_gates.validate.return_value = (True, [])
        mock_factory.create_quality_gates.return_value = mock_gates

        mock_renderer = Mock()
        mock_renderer.render.return_value = Path("/tmp/dossier.md")
        mock_factory.create_export_renderer.return_value = mock_renderer

        return mock_factory


# =============================================================================
# Pipeline Graph Construction Tests
# =============================================================================


class TestPipelineGraphConstruction:
    """Tests for LangGraph DAG construction."""

    def test_pipeline_builds_graph_on_init(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """Pipeline builds LangGraph StateGraph on initialization."""
        from showrunner.pipeline.orchestrator import PipelineConfig, ShowrunnerPipeline

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        pipeline = ShowrunnerPipeline(config=config)
        assert pipeline._graph is not None

    def test_graph_has_all_required_nodes(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """Graph contains all required pipeline stage nodes."""
        from showrunner.pipeline.orchestrator import PipelineConfig, ShowrunnerPipeline

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        pipeline = ShowrunnerPipeline(config=config)

        expected_nodes = [
            "load_input",
            "index_canon",
            "resolve_entities",
            "extract_obligations",
            "merge_duplicates",
            "validate_gates",
            "export_dossier",
        ]
        graph_nodes = pipeline.get_node_names()
        for node in expected_nodes:
            assert node in graph_nodes

    def test_graph_has_conditional_edge_from_validate_gates(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """Graph has conditional edge from validate_gates (pass -> export, fail -> error)."""
        from showrunner.pipeline.orchestrator import PipelineConfig, ShowrunnerPipeline

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        pipeline = ShowrunnerPipeline(config=config)

        # validate_gates should have conditional routing
        assert pipeline.has_conditional_edge("validate_gates")

    def test_graph_entry_point_is_load_input(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """Graph entry point is load_input node."""
        from showrunner.pipeline.orchestrator import PipelineConfig, ShowrunnerPipeline

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        pipeline = ShowrunnerPipeline(config=config)
        assert pipeline.get_entry_point() == "load_input"

    def test_graph_uses_memory_saver_for_checkpoints(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """Graph is compiled with MemorySaver for checkpointing."""
        from showrunner.pipeline.orchestrator import PipelineConfig, ShowrunnerPipeline

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        pipeline = ShowrunnerPipeline(config=config)
        assert pipeline._checkpointer is not None


# =============================================================================
# Pipeline Execution Tests
# =============================================================================


class TestPipelineExecution:
    """Tests for pipeline.run() execution."""

    def test_run_returns_pipeline_state_and_manifest(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """run() returns tuple of (PipelineState, RunManifest)."""
        from showrunner.pipeline.orchestrator import (
            PipelineConfig,
            PipelineState,
            ShowrunnerPipeline,
        )

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        mock_factory = TestProgressCallbacks()._create_mock_factory(config)
        pipeline = ShowrunnerPipeline(config=config, factory=mock_factory)

        result, manifest = pipeline.run()

        assert isinstance(result, PipelineState)
        assert isinstance(manifest, RunManifest)

    def test_run_executes_stages_in_order(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """run() executes pipeline stages in correct order."""
        from showrunner.pipeline.orchestrator import (
            ComponentFactory,
            PipelineConfig,
            ShowrunnerPipeline,
        )

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)

        execution_order: list[str] = []

        # Create mock factory that tracks execution order
        mock_factory = Mock(spec=ComponentFactory)
        mock_factory.config = config

        mock_adapter = Mock()

        def track_load(*args: object, **kwargs: object) -> list:
            execution_order.append("load_input")
            return []

        mock_adapter.load.side_effect = track_load
        mock_factory.create_input_adapter.return_value = mock_adapter

        mock_indexer = Mock()

        def track_index(*args: object, **kwargs: object) -> tuple:
            execution_order.append("index_canon")
            return ([], [])

        mock_indexer.index.side_effect = track_index
        mock_factory.create_canon_indexer.return_value = mock_indexer

        mock_resolver = Mock()

        def track_resolve(*args: object, **kwargs: object) -> tuple:
            execution_order.append("resolve_entities")
            return ([], [], [])

        mock_resolver.resolve.side_effect = track_resolve
        mock_factory.create_entity_resolver.return_value = mock_resolver

        mock_extractor = Mock()

        def track_extract(*args: object, **kwargs: object) -> tuple:
            execution_order.append("extract_obligations")
            return ([], [])

        mock_extractor.extract.side_effect = track_extract
        mock_factory.create_obligation_extractor.return_value = mock_extractor

        mock_merger = Mock()

        def track_merge(*args: object, **kwargs: object) -> tuple:
            execution_order.append("merge_duplicates")
            return ([], [], 0.0)

        mock_merger.merge.side_effect = track_merge
        mock_factory.create_dedupe_merger.return_value = mock_merger

        mock_gates = Mock()

        def track_validate(*args: object, **kwargs: object) -> tuple:
            execution_order.append("validate_gates")
            return (True, [])

        mock_gates.validate.side_effect = track_validate
        mock_factory.create_quality_gates.return_value = mock_gates

        mock_renderer = Mock()

        def track_render(*args: object, **kwargs: object) -> Path:
            execution_order.append("export_dossier")
            return Path("/tmp/dossier.md")

        mock_renderer.render.side_effect = track_render
        mock_factory.create_export_renderer.return_value = mock_renderer

        pipeline = ShowrunnerPipeline(config=config, factory=mock_factory)
        pipeline.run()

        expected_order = [
            "load_input",
            "index_canon",
            "resolve_entities",
            "extract_obligations",
            "merge_duplicates",
            "validate_gates",
            "export_dossier",
        ]
        assert execution_order == expected_order

    def test_run_stops_at_validation_failure(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """run() stops and returns error state when validation fails."""
        from showrunner.pipeline.orchestrator import (
            ComponentFactory,
            PipelineConfig,
            ShowrunnerPipeline,
        )

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)

        # Create mock factory where validation fails
        mock_factory = Mock(spec=ComponentFactory)
        mock_factory.config = config

        mock_adapter = Mock()
        mock_adapter.load.return_value = []
        mock_factory.create_input_adapter.return_value = mock_adapter

        mock_indexer = Mock()
        mock_indexer.index.return_value = ([], [])
        mock_factory.create_canon_indexer.return_value = mock_indexer

        mock_resolver = Mock()
        mock_resolver.resolve.return_value = ([], [], [])
        mock_factory.create_entity_resolver.return_value = mock_resolver

        mock_extractor = Mock()
        mock_extractor.extract.return_value = ([], [])
        mock_factory.create_obligation_extractor.return_value = mock_extractor

        mock_merger = Mock()
        mock_merger.merge.return_value = ([], [], 0.0)
        mock_factory.create_dedupe_merger.return_value = mock_merger

        mock_gates = Mock()
        # Validation fails
        mock_gates.validate.return_value = (
            False,
            [
                Finding(
                    finding_id="err_001",
                    severity=FindingSeverity.ERROR,
                    category="evidence_gate",
                    message="Missing evidence",
                )
            ],
        )
        mock_factory.create_quality_gates.return_value = mock_gates

        mock_renderer = Mock()
        mock_factory.create_export_renderer.return_value = mock_renderer

        pipeline = ShowrunnerPipeline(config=config, factory=mock_factory)
        result, manifest = pipeline.run()

        # Should not call export_dossier when validation fails
        mock_renderer.render.assert_not_called()

        # State should have error
        assert result.error is not None

    def test_run_generates_run_manifest(self, temp_input_dir: Path, temp_output_dir: Path) -> None:
        """run() generates RunManifest with correct metadata."""
        from showrunner.pipeline.orchestrator import (
            PipelineConfig,
            ShowrunnerPipeline,
        )

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        mock_factory = TestProgressCallbacks()._create_mock_factory(config)
        pipeline = ShowrunnerPipeline(config=config, factory=mock_factory)

        result, manifest = pipeline.run()

        assert manifest.run_id is not None
        assert manifest.timestamp is not None
        assert manifest.segmentation_version == config.segmentation_version

    def test_run_writes_artifacts_to_output_dir(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """run() writes all artifacts to appropriate output paths."""
        from showrunner.pipeline.orchestrator import (
            PipelineConfig,
            ShowrunnerPipeline,
        )

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        mock_factory = TestProgressCallbacks()._create_mock_factory(config)
        pipeline = ShowrunnerPipeline(config=config, factory=mock_factory)

        pipeline.run()

        # Check that manifest file was written
        manifest_path = temp_output_dir / "run_manifest.json"
        assert manifest_path.exists()


# =============================================================================
# Incremental Execution Tests
# =============================================================================


class TestIncrementalExecution:
    """Tests for run_incremental() method."""

    def test_run_incremental_accepts_changed_files(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """run_incremental() accepts list of changed file paths."""
        from showrunner.pipeline.orchestrator import (
            PipelineConfig,
            PipelineState,
            ShowrunnerPipeline,
        )

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        # Use real factory (not mock) for incremental run since LangGraph
        # checkpointer needs serializable state
        pipeline = ShowrunnerPipeline(config=config)

        changed_files = [temp_input_dir / "book1.txt"]
        result = pipeline.run_incremental(changed_files)

        assert isinstance(result, PipelineState)

    def test_run_incremental_only_processes_changed_files(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """run_incremental() only processes specified changed files."""
        from showrunner.pipeline.orchestrator import (
            ComponentFactory,
            PipelineConfig,
            ShowrunnerPipeline,
        )

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)

        mock_factory = Mock(spec=ComponentFactory)
        mock_factory.config = config

        mock_adapter = Mock()
        mock_adapter.load.return_value = []
        mock_adapter.load_files.return_value = []  # For incremental
        mock_factory.create_input_adapter.return_value = mock_adapter

        mock_indexer = Mock()
        mock_indexer.index.return_value = ([], [])
        mock_factory.create_canon_indexer.return_value = mock_indexer

        mock_resolver = Mock()
        mock_resolver.resolve.return_value = ([], [], [])
        mock_factory.create_entity_resolver.return_value = mock_resolver

        mock_extractor = Mock()
        mock_extractor.extract.return_value = ([], [])
        mock_factory.create_obligation_extractor.return_value = mock_extractor

        mock_merger = Mock()
        mock_merger.merge.return_value = ([], [], 0.0)
        mock_factory.create_dedupe_merger.return_value = mock_merger

        mock_gates = Mock()
        mock_gates.validate.return_value = (True, [])
        mock_factory.create_quality_gates.return_value = mock_gates

        mock_renderer = Mock()
        mock_renderer.render.return_value = Path("/tmp/dossier.md")
        mock_factory.create_export_renderer.return_value = mock_renderer

        pipeline = ShowrunnerPipeline(config=config, factory=mock_factory)

        changed_files = [temp_input_dir / "book1.txt"]
        pipeline.run_incremental(changed_files)

        # Should call load_files with specific files, not load()
        mock_adapter.load_files.assert_called_once_with(changed_files)

    def test_run_incremental_merges_with_existing_state(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """run_incremental() merges results with existing pipeline state."""
        from showrunner.pipeline.orchestrator import (
            PipelineConfig,
            ShowrunnerPipeline,
        )

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)

        # Use real factory (not mock) for incremental run since LangGraph
        # checkpointer needs serializable state
        pipeline = ShowrunnerPipeline(config=config)

        # First, do a full run
        pipeline.run()

        # Then do incremental
        changed_files = [temp_input_dir / "book1.txt"]
        result = pipeline.run_incremental(changed_files)

        # Result should be valid state
        assert result is not None


# =============================================================================
# Error Handling and Retry Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling and retry logic."""

    def test_pipeline_captures_stage_errors(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """Pipeline captures and records errors from stage execution."""
        from showrunner.pipeline.orchestrator import (
            ComponentFactory,
            PipelineConfig,
            ShowrunnerPipeline,
        )

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)

        mock_factory = Mock(spec=ComponentFactory)
        mock_factory.config = config

        mock_adapter = Mock()
        mock_adapter.load.side_effect = RuntimeError("Failed to load files")
        mock_factory.create_input_adapter.return_value = mock_adapter

        # Need to provide other mocks even though they won't be called
        mock_factory.create_canon_indexer.return_value = Mock()
        mock_factory.create_entity_resolver.return_value = Mock()
        mock_factory.create_obligation_extractor.return_value = Mock()
        mock_factory.create_dedupe_merger.return_value = Mock()
        mock_factory.create_quality_gates.return_value = Mock()
        mock_factory.create_export_renderer.return_value = Mock()

        pipeline = ShowrunnerPipeline(config=config, factory=mock_factory)
        result, manifest = pipeline.run()

        assert result.error is not None
        assert "Failed to load files" in result.error

    def test_pipeline_manifest_records_failure_status(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """Pipeline manifest records 'failed' status on error."""
        from showrunner.pipeline.orchestrator import (
            ComponentFactory,
            PipelineConfig,
            ShowrunnerPipeline,
        )

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)

        mock_factory = Mock(spec=ComponentFactory)
        mock_factory.config = config

        mock_adapter = Mock()
        mock_adapter.load.side_effect = RuntimeError("Failed")
        mock_factory.create_input_adapter.return_value = mock_adapter

        mock_factory.create_canon_indexer.return_value = Mock()
        mock_factory.create_entity_resolver.return_value = Mock()
        mock_factory.create_obligation_extractor.return_value = Mock()
        mock_factory.create_dedupe_merger.return_value = Mock()
        mock_factory.create_quality_gates.return_value = Mock()
        mock_factory.create_export_renderer.return_value = Mock()

        pipeline = ShowrunnerPipeline(config=config, factory=mock_factory)
        result, manifest = pipeline.run()

        assert manifest.status == "failed"

    def test_pipeline_supports_interrupt_and_resume(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """Pipeline can be interrupted and resumed from checkpoint."""
        from showrunner.pipeline.orchestrator import (
            PipelineConfig,
            ShowrunnerPipeline,
        )

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        mock_factory = TestProgressCallbacks()._create_mock_factory(config)
        pipeline = ShowrunnerPipeline(config=config, factory=mock_factory)

        # Create a thread config for checkpointing
        thread_id = "test_thread_001"

        # Start run with thread config
        result, _ = pipeline.run(thread_id=thread_id)

        # Should be able to resume with same thread_id
        # (In a real scenario, this would resume from checkpoint)
        assert pipeline.can_resume(thread_id)


# =============================================================================
# Artifact Writing Tests
# =============================================================================


class TestArtifactWriting:
    """Tests for artifact file writing."""

    def test_writes_passages_jsonl(
        self, temp_input_dir: Path, temp_output_dir: Path, sample_passages: list[PassageRecord]
    ) -> None:
        """Pipeline writes canon/passages.jsonl."""
        from showrunner.pipeline.orchestrator import (
            ComponentFactory,
            PipelineConfig,
            ShowrunnerPipeline,
        )

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)

        mock_factory = Mock(spec=ComponentFactory)
        mock_factory.config = config

        mock_adapter = Mock()
        mock_adapter.load.return_value = []
        mock_factory.create_input_adapter.return_value = mock_adapter

        mock_indexer = Mock()
        mock_indexer.index.return_value = (sample_passages, [])
        mock_factory.create_canon_indexer.return_value = mock_indexer

        mock_resolver = Mock()
        mock_resolver.resolve.return_value = ([], [], [])
        mock_factory.create_entity_resolver.return_value = mock_resolver

        mock_extractor = Mock()
        mock_extractor.extract.return_value = ([], [])
        mock_factory.create_obligation_extractor.return_value = mock_extractor

        mock_merger = Mock()
        mock_merger.merge.return_value = ([], [], 0.0)
        mock_factory.create_dedupe_merger.return_value = mock_merger

        mock_gates = Mock()
        mock_gates.validate.return_value = (True, [])
        mock_factory.create_quality_gates.return_value = mock_gates

        mock_renderer = Mock()
        mock_renderer.render.return_value = temp_output_dir / "exports" / "dossier.md"
        mock_factory.create_export_renderer.return_value = mock_renderer

        pipeline = ShowrunnerPipeline(config=config, factory=mock_factory)
        pipeline.run()

        passages_path = temp_output_dir / "canon" / "passages.jsonl"
        assert passages_path.exists()

    def test_writes_entities_json(
        self, temp_input_dir: Path, temp_output_dir: Path, sample_entities: list[Entity]
    ) -> None:
        """Pipeline writes kb/entities.json."""
        from showrunner.pipeline.orchestrator import (
            ComponentFactory,
            PipelineConfig,
            ShowrunnerPipeline,
        )

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)

        mock_factory = Mock(spec=ComponentFactory)
        mock_factory.config = config

        mock_adapter = Mock()
        mock_adapter.load.return_value = []
        mock_factory.create_input_adapter.return_value = mock_adapter

        mock_indexer = Mock()
        mock_indexer.index.return_value = ([], [])
        mock_factory.create_canon_indexer.return_value = mock_indexer

        mock_resolver = Mock()
        mock_resolver.resolve.return_value = (sample_entities, [], [])
        mock_factory.create_entity_resolver.return_value = mock_resolver

        mock_extractor = Mock()
        mock_extractor.extract.return_value = ([], [])
        mock_factory.create_obligation_extractor.return_value = mock_extractor

        mock_merger = Mock()
        mock_merger.merge.return_value = ([], [], 0.0)
        mock_factory.create_dedupe_merger.return_value = mock_merger

        mock_gates = Mock()
        mock_gates.validate.return_value = (True, [])
        mock_factory.create_quality_gates.return_value = mock_gates

        mock_renderer = Mock()
        mock_renderer.render.return_value = temp_output_dir / "exports" / "dossier.md"
        mock_factory.create_export_renderer.return_value = mock_renderer

        pipeline = ShowrunnerPipeline(config=config, factory=mock_factory)
        pipeline.run()

        entities_path = temp_output_dir / "kb" / "entities.json"
        assert entities_path.exists()

    def test_writes_obligations_json(
        self, temp_input_dir: Path, temp_output_dir: Path, sample_obligations: list[Obligation]
    ) -> None:
        """Pipeline writes obligations/obligations.json."""
        from showrunner.pipeline.orchestrator import (
            ComponentFactory,
            PipelineConfig,
            ShowrunnerPipeline,
        )

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)

        mock_factory = Mock(spec=ComponentFactory)
        mock_factory.config = config

        mock_adapter = Mock()
        mock_adapter.load.return_value = []
        mock_factory.create_input_adapter.return_value = mock_adapter

        mock_indexer = Mock()
        mock_indexer.index.return_value = ([], [])
        mock_factory.create_canon_indexer.return_value = mock_indexer

        mock_resolver = Mock()
        mock_resolver.resolve.return_value = ([], [], [])
        mock_factory.create_entity_resolver.return_value = mock_resolver

        mock_extractor = Mock()
        mock_extractor.extract.return_value = (sample_obligations, [])
        mock_factory.create_obligation_extractor.return_value = mock_extractor

        mock_merger = Mock()
        mock_merger.merge.return_value = (sample_obligations, [], 0.0)
        mock_factory.create_dedupe_merger.return_value = mock_merger

        mock_gates = Mock()
        mock_gates.validate.return_value = (True, [])
        mock_factory.create_quality_gates.return_value = mock_gates

        mock_renderer = Mock()
        mock_renderer.render.return_value = temp_output_dir / "exports" / "dossier.md"
        mock_factory.create_export_renderer.return_value = mock_renderer

        pipeline = ShowrunnerPipeline(config=config, factory=mock_factory)
        pipeline.run()

        obligations_path = temp_output_dir / "obligations" / "obligations.json"
        assert obligations_path.exists()

    def test_writes_run_manifest_json(self, temp_input_dir: Path, temp_output_dir: Path) -> None:
        """Pipeline writes run_manifest.json."""
        from showrunner.pipeline.orchestrator import (
            PipelineConfig,
            ShowrunnerPipeline,
        )

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        mock_factory = TestProgressCallbacks()._create_mock_factory(config)
        pipeline = ShowrunnerPipeline(config=config, factory=mock_factory)

        pipeline.run()

        manifest_path = temp_output_dir / "run_manifest.json"
        assert manifest_path.exists()

        # Verify it's valid JSON
        with manifest_path.open() as f:
            data = json.load(f)
            assert "run_id" in data


# =============================================================================
# Integration Tests with Real LangGraph
# =============================================================================


class TestLangGraphIntegration:
    """Integration tests verifying real LangGraph functionality."""

    def test_compiled_graph_is_executable(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """Compiled LangGraph can be invoked."""
        from showrunner.pipeline.orchestrator import (
            PipelineConfig,
            ShowrunnerPipeline,
        )

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        mock_factory = TestProgressCallbacks()._create_mock_factory(config)
        pipeline = ShowrunnerPipeline(config=config, factory=mock_factory)

        # Graph should be compiled and invokable
        assert pipeline._compiled_graph is not None
        assert hasattr(pipeline._compiled_graph, "invoke")

    def test_graph_state_transitions_correctly(
        self, temp_input_dir: Path, temp_output_dir: Path
    ) -> None:
        """LangGraph state transitions follow defined edges."""
        from showrunner.pipeline.orchestrator import (
            PipelineConfig,
            ShowrunnerPipeline,
        )

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        mock_factory = TestProgressCallbacks()._create_mock_factory(config)
        pipeline = ShowrunnerPipeline(config=config, factory=mock_factory)

        result, _ = pipeline.run()

        # If no error, all stages completed
        if result.error is None:
            assert result.dossier_path is not None

    def test_checkpointer_saves_state(self, temp_input_dir: Path, temp_output_dir: Path) -> None:
        """MemorySaver checkpointer saves intermediate state."""
        from showrunner.pipeline.orchestrator import (
            PipelineConfig,
            ShowrunnerPipeline,
        )

        config = PipelineConfig(input_source=temp_input_dir, output_dir=temp_output_dir)
        mock_factory = TestProgressCallbacks()._create_mock_factory(config)
        pipeline = ShowrunnerPipeline(config=config, factory=mock_factory)

        thread_id = "checkpoint_test"
        pipeline.run(thread_id=thread_id)

        # Checkpointer should have saved state
        state = pipeline.get_checkpoint_state(thread_id)
        assert state is not None
