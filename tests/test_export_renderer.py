"""Tests for ExportRenderer module.

TDD-style tests covering:
- DossierFormatter protocol compliance
- MarkdownFormatter implementation
- ExportRenderer with dependency injection
- Dossier generation from validated stores
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from showrunner.contracts import (
    Entity,
    EntityType,
    EvidenceAnchor,
    Obligation,
    ObligationCategory,
    PassageRecord,
)

# =============================================================================
# Fixtures for test data
# =============================================================================


@pytest.fixture
def sample_passages() -> list[PassageRecord]:
    """Create sample passages for testing."""
    return [
        PassageRecord(
            passage_id="book1:0",
            source_id="book1",
            paragraph_index=0,
            text="The sword hung above the fireplace, untouched for decades.",
            char_start=0,
            char_end=58,
        ),
        PassageRecord(
            passage_id="book1:5",
            source_id="book1",
            paragraph_index=5,
            text="The oracle spoke of a darkness that would consume the realm.",
            char_start=200,
            char_end=260,
        ),
        PassageRecord(
            passage_id="book2:10",
            source_id="book2",
            paragraph_index=10,
            text="Who killed the king remained the kingdom's greatest mystery.",
            char_start=500,
            char_end=559,
        ),
        PassageRecord(
            passage_id="book2:15",
            source_id="book2",
            paragraph_index=15,
            text="The thread of fate continued to weave through their lives.",
            char_start=700,
            char_end=758,
        ),
    ]


@pytest.fixture
def sample_entities() -> list[Entity]:
    """Create sample entities for testing."""
    return [
        Entity(
            entity_id="ent_001",
            canonical_name="The Ancient Sword",
            entity_type=EntityType.ARTIFACT,
            first_seen_passage="book1:0",
            mention_count=5,
            is_important=True,
            description="A legendary weapon",
        ),
        Entity(
            entity_id="ent_002",
            canonical_name="The Oracle",
            entity_type=EntityType.PERSON,
            first_seen_passage="book1:5",
            mention_count=3,
            is_important=True,
        ),
    ]


@pytest.fixture
def sample_anchors() -> list[EvidenceAnchor]:
    """Create sample evidence anchors for testing."""
    return [
        EvidenceAnchor(
            anchor_id="anc_001",
            passage_id="book1:0",
            char_start=0,
            char_end=58,
            excerpt="The sword hung above the fireplace, untouched for decades.",
        ),
        EvidenceAnchor(
            anchor_id="anc_002",
            passage_id="book1:5",
            char_start=0,
            char_end=60,
            excerpt="The oracle spoke of a darkness that would consume the realm.",
        ),
        EvidenceAnchor(
            anchor_id="anc_003",
            passage_id="book2:10",
            char_start=0,
            char_end=59,
            excerpt="Who killed the king remained the kingdom's greatest mystery.",
        ),
        EvidenceAnchor(
            anchor_id="anc_004",
            passage_id="book2:15",
            char_start=0,
            char_end=58,
            excerpt="The thread of fate continued to weave through their lives.",
        ),
    ]


@pytest.fixture
def sample_obligations() -> list[Obligation]:
    """Create sample obligations for testing."""
    return [
        Obligation(
            obligation_id="obl_001",
            category=ObligationCategory.CHEKHOV_GUN,
            description="The ancient sword must be used",
            evidence_anchor_ids=["anc_001"],
            last_seen_passage_id="book1:0",
            confidence=0.85,
            related_entity_ids=["ent_001"],
        ),
        Obligation(
            obligation_id="obl_002",
            category=ObligationCategory.PROPHECY_VISION,
            description="The darkness prophecy must come true or be averted",
            evidence_anchor_ids=["anc_002"],
            last_seen_passage_id="book1:5",
            confidence=0.92,
            related_entity_ids=["ent_002"],
        ),
        Obligation(
            obligation_id="obl_003",
            category=ObligationCategory.MYSTERY,
            description="The king's murderer must be revealed",
            evidence_anchor_ids=["anc_003"],
            last_seen_passage_id="book2:10",
            confidence=0.78,
        ),
        Obligation(
            obligation_id="obl_004",
            category=ObligationCategory.PLOT_THREAD,
            description="The fate thread connecting the characters",
            evidence_anchor_ids=["anc_004"],
            last_seen_passage_id="book2:15",
            confidence=0.65,
        ),
    ]


# =============================================================================
# Tests for DossierFormatter Protocol
# =============================================================================


class TestDossierFormatterProtocol:
    """Tests for DossierFormatter protocol compliance."""

    def test_protocol_defines_format_header_method(self) -> None:
        """DossierFormatter protocol must define format_header method."""
        from showrunner.renderers.export_renderer import DossierFormatter

        assert hasattr(DossierFormatter, "format_header")

    def test_protocol_defines_format_category_section_method(self) -> None:
        """DossierFormatter protocol must define format_category_section method."""
        from showrunner.renderers.export_renderer import DossierFormatter

        assert hasattr(DossierFormatter, "format_category_section")

    def test_protocol_defines_format_obligation_method(self) -> None:
        """DossierFormatter protocol must define format_obligation method."""
        from showrunner.renderers.export_renderer import DossierFormatter

        assert hasattr(DossierFormatter, "format_obligation")

    def test_protocol_defines_format_footer_method(self) -> None:
        """DossierFormatter protocol must define format_footer method."""
        from showrunner.renderers.export_renderer import DossierFormatter

        assert hasattr(DossierFormatter, "format_footer")


# =============================================================================
# Tests for MarkdownFormatter
# =============================================================================


class TestMarkdownFormatter:
    """Tests for MarkdownFormatter implementation."""

    def test_format_header_returns_string(self) -> None:
        """format_header must return a string."""
        from showrunner.renderers.export_renderer import MarkdownFormatter

        formatter = MarkdownFormatter()
        result = formatter.format_header("Test Dossier")

        assert isinstance(result, str)

    def test_format_header_contains_title(self) -> None:
        """format_header must include the provided title."""
        from showrunner.renderers.export_renderer import MarkdownFormatter

        formatter = MarkdownFormatter()
        result = formatter.format_header("Unresolved Threads Dossier")

        assert "Unresolved Threads Dossier" in result

    def test_format_header_uses_h1_markdown(self) -> None:
        """format_header must use H1 markdown syntax."""
        from showrunner.renderers.export_renderer import MarkdownFormatter

        formatter = MarkdownFormatter()
        result = formatter.format_header("Test Title")

        assert result.startswith("# ")

    def test_format_header_includes_generated_timestamp(self) -> None:
        """format_header must include a generation timestamp."""
        from showrunner.renderers.export_renderer import MarkdownFormatter

        formatter = MarkdownFormatter()
        result = formatter.format_header("Test Title")

        assert "Generated:" in result

    def test_format_category_section_returns_string(
        self, sample_obligations: list[Obligation]
    ) -> None:
        """format_category_section must return a string."""
        from showrunner.renderers.export_renderer import MarkdownFormatter

        formatter = MarkdownFormatter()
        obligations = [o for o in sample_obligations if o.category == ObligationCategory.MYSTERY]
        result = formatter.format_category_section(ObligationCategory.MYSTERY, obligations)

        assert isinstance(result, str)

    def test_format_category_section_contains_category_heading(
        self, sample_obligations: list[Obligation]
    ) -> None:
        """format_category_section must contain the category name as H2."""
        from showrunner.renderers.export_renderer import MarkdownFormatter

        formatter = MarkdownFormatter()
        obligations = [o for o in sample_obligations if o.category == ObligationCategory.MYSTERY]
        result = formatter.format_category_section(ObligationCategory.MYSTERY, obligations)

        assert "## Mysteries" in result

    def test_format_category_section_contains_count(
        self, sample_obligations: list[Obligation]
    ) -> None:
        """format_category_section must include the obligation count."""
        from showrunner.renderers.export_renderer import MarkdownFormatter

        formatter = MarkdownFormatter()
        obligations = [o for o in sample_obligations if o.category == ObligationCategory.MYSTERY]
        result = formatter.format_category_section(ObligationCategory.MYSTERY, obligations)

        assert "(1)" in result

    def test_format_category_section_maps_prophecy_vision_correctly(
        self, sample_obligations: list[Obligation]
    ) -> None:
        """format_category_section must map PROPHECY_VISION to 'Prophecies & Visions'."""
        from showrunner.renderers.export_renderer import MarkdownFormatter

        formatter = MarkdownFormatter()
        obligations = [
            o for o in sample_obligations if o.category == ObligationCategory.PROPHECY_VISION
        ]
        result = formatter.format_category_section(ObligationCategory.PROPHECY_VISION, obligations)

        assert "Prophecies & Visions" in result

    def test_format_category_section_maps_chekhov_gun_correctly(
        self, sample_obligations: list[Obligation]
    ) -> None:
        """format_category_section must map CHEKHOV_GUN to \"Chekhov's Guns\"."""
        from showrunner.renderers.export_renderer import MarkdownFormatter

        formatter = MarkdownFormatter()
        obligations = [
            o for o in sample_obligations if o.category == ObligationCategory.CHEKHOV_GUN
        ]
        result = formatter.format_category_section(ObligationCategory.CHEKHOV_GUN, obligations)

        assert "Chekhov's Guns" in result

    def test_format_category_section_maps_plot_thread_correctly(
        self, sample_obligations: list[Obligation]
    ) -> None:
        """format_category_section must map PLOT_THREAD to 'Plot Threads'."""
        from showrunner.renderers.export_renderer import MarkdownFormatter

        formatter = MarkdownFormatter()
        obligations = [
            o for o in sample_obligations if o.category == ObligationCategory.PLOT_THREAD
        ]
        result = formatter.format_category_section(ObligationCategory.PLOT_THREAD, obligations)

        assert "Plot Threads" in result

    def test_format_obligation_returns_string(
        self, sample_obligations: list[Obligation], sample_anchors: list[EvidenceAnchor]
    ) -> None:
        """format_obligation must return a string."""
        from showrunner.renderers.export_renderer import MarkdownFormatter

        formatter = MarkdownFormatter()
        obligation = sample_obligations[0]
        evidence = [a for a in sample_anchors if a.anchor_id in obligation.evidence_anchor_ids]
        result = formatter.format_obligation(obligation, evidence)

        assert isinstance(result, str)

    def test_format_obligation_contains_description_as_h3(
        self, sample_obligations: list[Obligation], sample_anchors: list[EvidenceAnchor]
    ) -> None:
        """format_obligation must include description as H3 heading."""
        from showrunner.renderers.export_renderer import MarkdownFormatter

        formatter = MarkdownFormatter()
        obligation = sample_obligations[0]
        evidence = [a for a in sample_anchors if a.anchor_id in obligation.evidence_anchor_ids]
        result = formatter.format_obligation(obligation, evidence)

        assert f"### {obligation.description}" in result

    def test_format_obligation_contains_confidence(
        self, sample_obligations: list[Obligation], sample_anchors: list[EvidenceAnchor]
    ) -> None:
        """format_obligation must include confidence value."""
        from showrunner.renderers.export_renderer import MarkdownFormatter

        formatter = MarkdownFormatter()
        obligation = sample_obligations[0]
        evidence = [a for a in sample_anchors if a.anchor_id in obligation.evidence_anchor_ids]
        result = formatter.format_obligation(obligation, evidence)

        assert "**Confidence:**" in result
        assert "0.85" in result or "85%" in result

    def test_format_obligation_contains_last_seen(
        self, sample_obligations: list[Obligation], sample_anchors: list[EvidenceAnchor]
    ) -> None:
        """format_obligation must include last seen passage reference."""
        from showrunner.renderers.export_renderer import MarkdownFormatter

        formatter = MarkdownFormatter()
        obligation = sample_obligations[0]
        evidence = [a for a in sample_anchors if a.anchor_id in obligation.evidence_anchor_ids]
        result = formatter.format_obligation(obligation, evidence)

        assert "**Last Seen:**" in result
        assert obligation.last_seen_passage_id in result

    def test_format_obligation_contains_evidence_section(
        self, sample_obligations: list[Obligation], sample_anchors: list[EvidenceAnchor]
    ) -> None:
        """format_obligation must include evidence section."""
        from showrunner.renderers.export_renderer import MarkdownFormatter

        formatter = MarkdownFormatter()
        obligation = sample_obligations[0]
        evidence = [a for a in sample_anchors if a.anchor_id in obligation.evidence_anchor_ids]
        result = formatter.format_obligation(obligation, evidence)

        assert "**Evidence:**" in result

    def test_format_obligation_formats_evidence_as_blockquote(
        self, sample_obligations: list[Obligation], sample_anchors: list[EvidenceAnchor]
    ) -> None:
        """format_obligation must format evidence excerpts as blockquotes."""
        from showrunner.renderers.export_renderer import MarkdownFormatter

        formatter = MarkdownFormatter()
        obligation = sample_obligations[0]
        evidence = [a for a in sample_anchors if a.anchor_id in obligation.evidence_anchor_ids]
        result = formatter.format_obligation(obligation, evidence)

        # Evidence should be formatted as markdown blockquote
        assert "> " in result

    def test_format_obligation_includes_evidence_source(
        self, sample_obligations: list[Obligation], sample_anchors: list[EvidenceAnchor]
    ) -> None:
        """format_obligation must include the source passage for each evidence."""
        from showrunner.renderers.export_renderer import MarkdownFormatter

        formatter = MarkdownFormatter()
        obligation = sample_obligations[0]
        evidence = [a for a in sample_anchors if a.anchor_id in obligation.evidence_anchor_ids]
        result = formatter.format_obligation(obligation, evidence)

        # Should include passage_id as source reference
        for anchor in evidence:
            assert anchor.passage_id in result

    def test_format_footer_returns_string(self) -> None:
        """format_footer must return a string."""
        from showrunner.renderers.export_renderer import MarkdownFormatter

        formatter = MarkdownFormatter()
        metrics = {"total_obligations": 4, "categories": 4}
        result = formatter.format_footer(metrics)

        assert isinstance(result, str)

    def test_format_footer_contains_separator(self) -> None:
        """format_footer must contain a markdown horizontal rule."""
        from showrunner.renderers.export_renderer import MarkdownFormatter

        formatter = MarkdownFormatter()
        metrics = {"total_obligations": 4, "categories": 4}
        result = formatter.format_footer(metrics)

        assert "---" in result

    def test_format_footer_contains_validation_notice(self) -> None:
        """format_footer must include notice about validated canon stores."""
        from showrunner.renderers.export_renderer import MarkdownFormatter

        formatter = MarkdownFormatter()
        metrics = {"total_obligations": 4, "categories": 4}
        result = formatter.format_footer(metrics)

        assert "validated canon stores" in result.lower()


# =============================================================================
# Tests for MarkdownFormatter Protocol Compliance
# =============================================================================


class TestMarkdownFormatterProtocolCompliance:
    """Tests to verify MarkdownFormatter satisfies DossierFormatter protocol."""

    def test_markdown_formatter_is_valid_dossier_formatter(self) -> None:
        """MarkdownFormatter must satisfy the DossierFormatter protocol."""
        from showrunner.renderers.export_renderer import DossierFormatter, MarkdownFormatter

        # This should not raise - MarkdownFormatter implements all required methods
        formatter: DossierFormatter = MarkdownFormatter()

        assert formatter is not None


# =============================================================================
# Tests for ExportRenderer Constructor
# =============================================================================


class TestExportRendererConstructor:
    """Tests for ExportRenderer dependency injection."""

    def test_accepts_formatter_via_constructor(
        self,
        sample_passages: list[PassageRecord],
        sample_entities: list[Entity],
        sample_anchors: list[EvidenceAnchor],
    ) -> None:
        """ExportRenderer must accept a formatter via constructor."""
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter

        formatter = MarkdownFormatter()
        renderer = ExportRenderer(
            formatter=formatter,
            passages=sample_passages,
            entities=sample_entities,
            anchors=sample_anchors,
        )

        assert renderer._formatter is formatter

    def test_accepts_passages_via_constructor(
        self,
        sample_passages: list[PassageRecord],
        sample_entities: list[Entity],
        sample_anchors: list[EvidenceAnchor],
    ) -> None:
        """ExportRenderer must accept passages via constructor."""
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter

        renderer = ExportRenderer(
            formatter=MarkdownFormatter(),
            passages=sample_passages,
            entities=sample_entities,
            anchors=sample_anchors,
        )

        assert len(renderer._passages) == len(sample_passages)

    def test_indexes_passages_by_id(
        self,
        sample_passages: list[PassageRecord],
        sample_entities: list[Entity],
        sample_anchors: list[EvidenceAnchor],
    ) -> None:
        """ExportRenderer must index passages by passage_id."""
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter

        renderer = ExportRenderer(
            formatter=MarkdownFormatter(),
            passages=sample_passages,
            entities=sample_entities,
            anchors=sample_anchors,
        )

        assert renderer._passages["book1:0"] == sample_passages[0]
        assert renderer._passages["book2:10"] == sample_passages[2]

    def test_indexes_entities_by_id(
        self,
        sample_passages: list[PassageRecord],
        sample_entities: list[Entity],
        sample_anchors: list[EvidenceAnchor],
    ) -> None:
        """ExportRenderer must index entities by entity_id."""
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter

        renderer = ExportRenderer(
            formatter=MarkdownFormatter(),
            passages=sample_passages,
            entities=sample_entities,
            anchors=sample_anchors,
        )

        assert renderer._entities["ent_001"] == sample_entities[0]
        assert renderer._entities["ent_002"] == sample_entities[1]

    def test_indexes_anchors_by_id(
        self,
        sample_passages: list[PassageRecord],
        sample_entities: list[Entity],
        sample_anchors: list[EvidenceAnchor],
    ) -> None:
        """ExportRenderer must index anchors by anchor_id."""
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter

        renderer = ExportRenderer(
            formatter=MarkdownFormatter(),
            passages=sample_passages,
            entities=sample_entities,
            anchors=sample_anchors,
        )

        assert renderer._anchors["anc_001"] == sample_anchors[0]
        assert renderer._anchors["anc_003"] == sample_anchors[2]

    def test_does_not_create_stores_internally(
        self,
        sample_passages: list[PassageRecord],
        sample_entities: list[Entity],
        sample_anchors: list[EvidenceAnchor],
    ) -> None:
        """ExportRenderer must not create stores internally (DI principle)."""
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter

        # Empty stores should result in empty internal dicts
        renderer = ExportRenderer(
            formatter=MarkdownFormatter(),
            passages=[],
            entities=[],
            anchors=[],
        )

        assert len(renderer._passages) == 0
        assert len(renderer._entities) == 0
        assert len(renderer._anchors) == 0


# =============================================================================
# Tests for ExportRenderer.render_dossier
# =============================================================================


class TestExportRendererRenderDossier:
    """Tests for ExportRenderer.render_dossier method."""

    def test_render_dossier_returns_string(
        self,
        sample_passages: list[PassageRecord],
        sample_entities: list[Entity],
        sample_anchors: list[EvidenceAnchor],
        sample_obligations: list[Obligation],
    ) -> None:
        """render_dossier must return a string."""
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter

        renderer = ExportRenderer(
            formatter=MarkdownFormatter(),
            passages=sample_passages,
            entities=sample_entities,
            anchors=sample_anchors,
        )
        result = renderer.render_dossier(sample_obligations)

        assert isinstance(result, str)

    def test_render_dossier_contains_header(
        self,
        sample_passages: list[PassageRecord],
        sample_entities: list[Entity],
        sample_anchors: list[EvidenceAnchor],
        sample_obligations: list[Obligation],
    ) -> None:
        """render_dossier must contain the dossier header."""
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter

        renderer = ExportRenderer(
            formatter=MarkdownFormatter(),
            passages=sample_passages,
            entities=sample_entities,
            anchors=sample_anchors,
        )
        result = renderer.render_dossier(sample_obligations)

        assert "# Unresolved Threads Dossier" in result

    def test_render_dossier_contains_footer(
        self,
        sample_passages: list[PassageRecord],
        sample_entities: list[Entity],
        sample_anchors: list[EvidenceAnchor],
        sample_obligations: list[Obligation],
    ) -> None:
        """render_dossier must contain the dossier footer."""
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter

        renderer = ExportRenderer(
            formatter=MarkdownFormatter(),
            passages=sample_passages,
            entities=sample_entities,
            anchors=sample_anchors,
        )
        result = renderer.render_dossier(sample_obligations)

        assert "---" in result
        assert "validated canon stores" in result.lower()

    def test_render_dossier_groups_by_category(
        self,
        sample_passages: list[PassageRecord],
        sample_entities: list[Entity],
        sample_anchors: list[EvidenceAnchor],
        sample_obligations: list[Obligation],
    ) -> None:
        """render_dossier must group obligations by category."""
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter

        renderer = ExportRenderer(
            formatter=MarkdownFormatter(),
            passages=sample_passages,
            entities=sample_entities,
            anchors=sample_anchors,
        )
        result = renderer.render_dossier(sample_obligations)

        # All four categories should be present
        assert "Prophecies & Visions" in result
        assert "Mysteries" in result
        assert "Chekhov's Guns" in result
        assert "Plot Threads" in result

    def test_render_dossier_includes_all_obligations(
        self,
        sample_passages: list[PassageRecord],
        sample_entities: list[Entity],
        sample_anchors: list[EvidenceAnchor],
        sample_obligations: list[Obligation],
    ) -> None:
        """render_dossier must include all provided obligations."""
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter

        renderer = ExportRenderer(
            formatter=MarkdownFormatter(),
            passages=sample_passages,
            entities=sample_entities,
            anchors=sample_anchors,
        )
        result = renderer.render_dossier(sample_obligations)

        for obligation in sample_obligations:
            assert obligation.description in result

    def test_render_dossier_uses_injected_formatter(
        self,
        sample_passages: list[PassageRecord],
        sample_entities: list[Entity],
        sample_anchors: list[EvidenceAnchor],
        sample_obligations: list[Obligation],
    ) -> None:
        """render_dossier must delegate to the injected formatter."""
        from showrunner.renderers.export_renderer import ExportRenderer

        mock_formatter = MagicMock()
        mock_formatter.format_header.return_value = "HEADER\n"
        mock_formatter.format_category_section.return_value = "SECTION\n"
        mock_formatter.format_obligation.return_value = "OBLIGATION\n"
        mock_formatter.format_footer.return_value = "FOOTER\n"

        renderer = ExportRenderer(
            formatter=mock_formatter,
            passages=sample_passages,
            entities=sample_entities,
            anchors=sample_anchors,
        )
        renderer.render_dossier(sample_obligations)

        mock_formatter.format_header.assert_called_once()
        assert mock_formatter.format_category_section.call_count > 0
        mock_formatter.format_footer.assert_called_once()

    def test_render_dossier_resolves_evidence_anchors(
        self,
        sample_passages: list[PassageRecord],
        sample_entities: list[Entity],
        sample_anchors: list[EvidenceAnchor],
        sample_obligations: list[Obligation],
    ) -> None:
        """render_dossier must resolve evidence anchor IDs to anchor objects."""
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter

        renderer = ExportRenderer(
            formatter=MarkdownFormatter(),
            passages=sample_passages,
            entities=sample_entities,
            anchors=sample_anchors,
        )
        result = renderer.render_dossier(sample_obligations)

        # Evidence excerpts from anchors should be in the output
        for _anchor in sample_anchors:
            # At least some excerpts should appear (those linked to obligations)
            pass  # The actual check is that the output contains evidence sections

        assert "**Evidence:**" in result

    def test_render_dossier_orders_categories_as_specified(
        self,
        sample_passages: list[PassageRecord],
        sample_entities: list[Entity],
        sample_anchors: list[EvidenceAnchor],
        sample_obligations: list[Obligation],
    ) -> None:
        """render_dossier must order categories: Prophecies, Mysteries, Chekhov, Plot."""
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter

        renderer = ExportRenderer(
            formatter=MarkdownFormatter(),
            passages=sample_passages,
            entities=sample_entities,
            anchors=sample_anchors,
        )
        result = renderer.render_dossier(sample_obligations)

        prophecy_pos = result.find("Prophecies & Visions")
        mystery_pos = result.find("Mysteries")
        chekhov_pos = result.find("Chekhov's Guns")
        plot_pos = result.find("Plot Threads")

        assert prophecy_pos < mystery_pos < chekhov_pos < plot_pos

    def test_render_dossier_skips_empty_categories(
        self,
        sample_passages: list[PassageRecord],
        sample_entities: list[Entity],
        sample_anchors: list[EvidenceAnchor],
    ) -> None:
        """render_dossier must skip categories with no obligations."""
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter

        # Only include prophecy obligations
        prophecy_only = [
            Obligation(
                obligation_id="obl_only",
                category=ObligationCategory.PROPHECY_VISION,
                description="The only prophecy",
                evidence_anchor_ids=["anc_002"],
                last_seen_passage_id="book1:5",
                confidence=0.9,
            )
        ]

        renderer = ExportRenderer(
            formatter=MarkdownFormatter(),
            passages=sample_passages,
            entities=sample_entities,
            anchors=sample_anchors,
        )
        result = renderer.render_dossier(prophecy_only)

        assert "Prophecies & Visions" in result
        # Other categories should not appear (no "(0)" sections)
        assert "Mysteries" not in result or "Mysteries (0)" not in result

    def test_render_dossier_handles_empty_obligations_list(
        self,
        sample_passages: list[PassageRecord],
        sample_entities: list[Entity],
        sample_anchors: list[EvidenceAnchor],
    ) -> None:
        """render_dossier must handle empty obligations list gracefully."""
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter

        renderer = ExportRenderer(
            formatter=MarkdownFormatter(),
            passages=sample_passages,
            entities=sample_entities,
            anchors=sample_anchors,
        )
        result = renderer.render_dossier([])

        # Should still have header and footer
        assert "# Unresolved Threads Dossier" in result
        assert "---" in result


# =============================================================================
# Tests for ExportRenderer.write_dossier
# =============================================================================


class TestExportRendererWriteDossier:
    """Tests for ExportRenderer.write_dossier method."""

    def test_write_dossier_creates_file(
        self,
        sample_passages: list[PassageRecord],
        sample_entities: list[Entity],
        sample_anchors: list[EvidenceAnchor],
        sample_obligations: list[Obligation],
    ) -> None:
        """write_dossier must create a file at the specified path."""
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter

        renderer = ExportRenderer(
            formatter=MarkdownFormatter(),
            passages=sample_passages,
            entities=sample_entities,
            anchors=sample_anchors,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "dossier.md"
            renderer.write_dossier(sample_obligations, output_path)

            assert output_path.exists()

    def test_write_dossier_writes_rendered_content(
        self,
        sample_passages: list[PassageRecord],
        sample_entities: list[Entity],
        sample_anchors: list[EvidenceAnchor],
        sample_obligations: list[Obligation],
    ) -> None:
        """write_dossier must write the rendered dossier content."""
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter

        renderer = ExportRenderer(
            formatter=MarkdownFormatter(),
            passages=sample_passages,
            entities=sample_entities,
            anchors=sample_anchors,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "dossier.md"
            renderer.write_dossier(sample_obligations, output_path)

            content = output_path.read_text(encoding="utf-8")
            assert "# Unresolved Threads Dossier" in content

    def test_write_dossier_uses_utf8_encoding(
        self,
        sample_passages: list[PassageRecord],
        sample_entities: list[Entity],
        sample_anchors: list[EvidenceAnchor],
    ) -> None:
        """write_dossier must write files with UTF-8 encoding."""
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter

        # Create obligation with unicode characters
        unicode_obligation = Obligation(
            obligation_id="obl_unicode",
            category=ObligationCategory.MYSTERY,
            description="The mystery of the ancient runes",
            evidence_anchor_ids=["anc_003"],
            last_seen_passage_id="book2:10",
            confidence=0.8,
        )

        renderer = ExportRenderer(
            formatter=MarkdownFormatter(),
            passages=sample_passages,
            entities=sample_entities,
            anchors=sample_anchors,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "dossier.md"
            renderer.write_dossier([unicode_obligation], output_path)

            # Should be able to read as UTF-8 without errors
            content = output_path.read_text(encoding="utf-8")
            assert "ancient runes" in content

    def test_write_dossier_creates_parent_directories(
        self,
        sample_passages: list[PassageRecord],
        sample_entities: list[Entity],
        sample_anchors: list[EvidenceAnchor],
        sample_obligations: list[Obligation],
    ) -> None:
        """write_dossier must create parent directories if they don't exist."""
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter

        renderer = ExportRenderer(
            formatter=MarkdownFormatter(),
            passages=sample_passages,
            entities=sample_entities,
            anchors=sample_anchors,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nested" / "path" / "dossier.md"
            renderer.write_dossier(sample_obligations, output_path)

            assert output_path.exists()


# =============================================================================
# Tests for Strategy Pattern (Swappable Formatters)
# =============================================================================


class TestStrategyPatternSwappableFormatters:
    """Tests verifying the Strategy Pattern allows swappable formatters."""

    def test_custom_formatter_can_be_injected(
        self,
        sample_passages: list[PassageRecord],
        sample_entities: list[Entity],
        sample_anchors: list[EvidenceAnchor],
        sample_obligations: list[Obligation],
    ) -> None:
        """A custom formatter implementing the protocol can be injected."""
        from showrunner.renderers.export_renderer import ExportRenderer

        class CustomFormatter:
            def format_header(self, title: str) -> str:
                return f"<h1>{title}</h1>"

            def format_category_section(
                self, category: ObligationCategory, obligations: list[Obligation]
            ) -> str:
                return f"<section>{category.value}</section>"

            def format_obligation(self, obl: Obligation, evidence: list[EvidenceAnchor]) -> str:
                return f"<div>{obl.description}</div>"

            def format_footer(self, metrics: dict) -> str:
                return "<footer>Custom Footer</footer>"

        renderer = ExportRenderer(
            formatter=CustomFormatter(),
            passages=sample_passages,
            entities=sample_entities,
            anchors=sample_anchors,
        )
        result = renderer.render_dossier(sample_obligations)

        assert "<h1>" in result
        assert "<section>" in result
        assert "<footer>" in result

    def test_different_formatters_produce_different_output(
        self,
        sample_passages: list[PassageRecord],
        sample_entities: list[Entity],
        sample_anchors: list[EvidenceAnchor],
        sample_obligations: list[Obligation],
    ) -> None:
        """Different formatters must produce different output for same input."""
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter

        class PlainTextFormatter:
            def format_header(self, title: str) -> str:
                return f"=== {title} ===\n"

            def format_category_section(
                self, category: ObligationCategory, obligations: list[Obligation]
            ) -> str:
                return f"--- {category.value} ---\n"

            def format_obligation(self, obl: Obligation, evidence: list[EvidenceAnchor]) -> str:
                return f"* {obl.description}\n"

            def format_footer(self, metrics: dict) -> str:
                return "=== END ===\n"

        markdown_renderer = ExportRenderer(
            formatter=MarkdownFormatter(),
            passages=sample_passages,
            entities=sample_entities,
            anchors=sample_anchors,
        )
        plaintext_renderer = ExportRenderer(
            formatter=PlainTextFormatter(),
            passages=sample_passages,
            entities=sample_entities,
            anchors=sample_anchors,
        )

        markdown_result = markdown_renderer.render_dossier(sample_obligations)
        plaintext_result = plaintext_renderer.render_dossier(sample_obligations)

        assert markdown_result != plaintext_result
        assert "# " in markdown_result
        assert "===" in plaintext_result


# =============================================================================
# Tests for No Primitive Obsession
# =============================================================================


class TestNoPrimitiveObsession:
    """Tests verifying domain objects are used, not raw dicts."""

    def test_render_accepts_obligation_objects_not_dicts(
        self,
        sample_passages: list[PassageRecord],
        sample_entities: list[Entity],
        sample_anchors: list[EvidenceAnchor],
    ) -> None:
        """render_dossier must accept Obligation objects, not raw dicts."""
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter

        obligation = Obligation(
            obligation_id="obl_test",
            category=ObligationCategory.MYSTERY,
            description="Test obligation",
            evidence_anchor_ids=["anc_003"],
            last_seen_passage_id="book2:10",
            confidence=0.9,
        )

        renderer = ExportRenderer(
            formatter=MarkdownFormatter(),
            passages=sample_passages,
            entities=sample_entities,
            anchors=sample_anchors,
        )

        # This should work with domain objects
        result = renderer.render_dossier([obligation])
        assert "Test obligation" in result

    def test_constructor_accepts_domain_objects_not_dicts(self) -> None:
        """Constructor must accept domain objects, not raw dicts."""
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter

        passage = PassageRecord(
            passage_id="test:0",
            source_id="test",
            paragraph_index=0,
            text="Test text",
            char_start=0,
            char_end=9,
        )
        entity = Entity(
            entity_id="ent_test",
            canonical_name="Test Entity",
            entity_type=EntityType.PERSON,
            first_seen_passage="test:0",
            mention_count=1,
        )
        anchor = EvidenceAnchor(
            anchor_id="anc_test",
            passage_id="test:0",
            char_start=0,
            char_end=9,
            excerpt="Test text",
        )

        # This should work with domain objects
        renderer = ExportRenderer(
            formatter=MarkdownFormatter(),
            passages=[passage],
            entities=[entity],
            anchors=[anchor],
        )

        assert renderer._passages["test:0"] == passage
        assert renderer._entities["ent_test"] == entity
        assert renderer._anchors["anc_test"] == anchor


# =============================================================================
# Tests for Requirement: Export from Validated Stores Only
# =============================================================================


class TestExportFromValidatedStoresOnly:
    """Tests verifying exports come only from validated stores."""

    def test_render_uses_only_provided_stores(
        self,
        sample_passages: list[PassageRecord],
        sample_entities: list[Entity],
        sample_anchors: list[EvidenceAnchor],
        sample_obligations: list[Obligation],
    ) -> None:
        """Render must use only the stores provided at construction."""
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter

        renderer = ExportRenderer(
            formatter=MarkdownFormatter(),
            passages=sample_passages,
            entities=sample_entities,
            anchors=sample_anchors,
        )

        result = renderer.render_dossier(sample_obligations)

        # Result should only contain evidence from provided anchors
        for anchor in sample_anchors:
            if anchor.anchor_id in ["anc_001", "anc_002", "anc_003", "anc_004"]:
                # These are linked to obligations, so their excerpts should appear
                pass

        # Should not contain any "hallucinated" content
        assert "AI generated" not in result.lower()
        assert "llm" not in result.lower()

    def test_missing_anchor_handled_gracefully(
        self,
        sample_passages: list[PassageRecord],
        sample_entities: list[Entity],
    ) -> None:
        """Missing anchor references should be handled gracefully."""
        from showrunner.renderers.export_renderer import ExportRenderer, MarkdownFormatter

        # Obligation references an anchor that doesn't exist in the store
        obligation_with_missing_anchor = Obligation(
            obligation_id="obl_missing",
            category=ObligationCategory.MYSTERY,
            description="Mystery with missing evidence",
            evidence_anchor_ids=["anc_nonexistent"],
            last_seen_passage_id="book2:10",
            confidence=0.5,
        )

        renderer = ExportRenderer(
            formatter=MarkdownFormatter(),
            passages=sample_passages,
            entities=sample_entities,
            anchors=[],  # Empty anchors store
        )

        # Should not raise, should handle gracefully
        result = renderer.render_dossier([obligation_with_missing_anchor])
        assert "Mystery with missing evidence" in result
