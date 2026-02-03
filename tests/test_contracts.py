"""Tests for Pydantic contract models."""

import json
from datetime import datetime

from showrunner.contracts.document import DocumentUnit, PassageRecord
from showrunner.contracts.entity import (
    AliasEntry,
    Entity,
    EntityType,
    OverrideAction,
    OverrideRule,
)
from showrunner.contracts.evidence import EvidenceAnchor, EvidenceIndex
from showrunner.contracts.manifest import DatasetManifest, RunManifest
from showrunner.contracts.obligation import (
    EdgeType,
    Obligation,
    ObligationCategory,
    ObligationGraphEdge,
)
from showrunner.contracts.quality import Finding, FindingSeverity, MetricsReport


class TestDocumentUnit:
    """Tests for DocumentUnit contract."""

    def test_create_document_unit_with_required_fields(self):
        """DocumentUnit requires source_id, source_path, order_hint, raw_text."""
        doc = DocumentUnit(
            source_id="book1",
            source_path="/corpus/book1.txt",
            order_hint=0,
            raw_text="Once upon a time...",
        )
        assert doc.source_id == "book1"
        assert doc.source_path == "/corpus/book1.txt"
        assert doc.order_hint == 0
        assert doc.raw_text == "Once upon a time..."

    def test_document_unit_optional_metadata(self):
        """DocumentUnit can have optional book/chapter metadata."""
        doc = DocumentUnit(
            source_id="book1_ch1",
            source_path="/corpus/book1/chapter1.txt",
            order_hint=1,
            raw_text="The chapter begins...",
            book_label="A Game of Thrones",
            chapter_label="Bran I",
        )
        assert doc.book_label == "A Game of Thrones"
        assert doc.chapter_label == "Bran I"

    def test_document_unit_serializes_to_json(self):
        """DocumentUnit must be JSON-serializable."""
        doc = DocumentUnit(
            source_id="test",
            source_path="/test.txt",
            order_hint=0,
            raw_text="Test content",
        )
        json_str = doc.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["source_id"] == "test"


class TestPassageRecord:
    """Tests for PassageRecord contract."""

    def test_create_passage_with_stable_id(self):
        """PassageRecord has stable paragraph-level ID."""
        passage = PassageRecord(
            passage_id="book1:0",
            source_id="book1",
            paragraph_index=0,
            text="The morning had dawned clear and cold.",
            char_start=0,
            char_end=38,
        )
        assert passage.passage_id == "book1:0"
        assert passage.paragraph_index == 0

    def test_passage_id_format_validation(self):
        """PassageRecord ID must follow source_id:paragraph_index format."""
        passage = PassageRecord(
            passage_id="book1:42",
            source_id="book1",
            paragraph_index=42,
            text="Some text",
            char_start=100,
            char_end=109,
        )
        # ID format is enforced by construction convention
        assert ":" in passage.passage_id
        parts = passage.passage_id.split(":")
        assert parts[0] == passage.source_id
        assert int(parts[1]) == passage.paragraph_index


class TestEvidenceAnchor:
    """Tests for EvidenceAnchor contract."""

    def test_evidence_anchor_references_passage(self):
        """EvidenceAnchor must reference a passage_id."""
        anchor = EvidenceAnchor(
            anchor_id="ev_001",
            passage_id="book1:42",
            char_start=10,
            char_end=50,
            excerpt="the prophecy speaks of three heads",
        )
        assert anchor.passage_id == "book1:42"
        assert anchor.excerpt == "the prophecy speaks of three heads"

    def test_evidence_anchor_requires_excerpt(self):
        """EvidenceAnchor must have excerpt text."""
        anchor = EvidenceAnchor(
            anchor_id="ev_002",
            passage_id="book1:100",
            char_start=0,
            char_end=20,
            excerpt="Winter is coming",
        )
        assert len(anchor.excerpt) > 0


class TestEvidenceIndex:
    """Tests for EvidenceIndex contract."""

    def test_evidence_index_groups_by_entity_or_obligation(self):
        """EvidenceIndex links evidence to entities/obligations."""
        index = EvidenceIndex(
            index_id="idx_001",
            target_type="obligation",
            target_id="obl_prophecy_001",
            anchor_ids=["ev_001", "ev_002", "ev_003"],
        )
        assert index.target_type == "obligation"
        assert len(index.anchor_ids) == 3


class TestEntity:
    """Tests for Entity contract."""

    def test_create_person_entity(self):
        """Entity can represent a person with type."""
        entity = Entity(
            entity_id="ent_001",
            canonical_name="Jon Snow",
            entity_type=EntityType.PERSON,
            first_seen_passage="book1:10",
            mention_count=500,
        )
        assert entity.entity_type == EntityType.PERSON
        assert entity.canonical_name == "Jon Snow"

    def test_create_place_entity(self):
        """Entity can represent a place."""
        entity = Entity(
            entity_id="ent_002",
            canonical_name="Winterfell",
            entity_type=EntityType.PLACE,
            first_seen_passage="book1:1",
            mention_count=300,
        )
        assert entity.entity_type == EntityType.PLACE

    def test_entity_types_cover_all_er_targets(self):
        """EntityType enum includes all MVP ER targets."""
        expected = {"PERSON", "PLACE", "GROUP", "TITLE", "ARTIFACT", "VEHICLE"}
        actual = {t.name for t in EntityType}
        assert expected == actual

    def test_vehicle_entity_requires_importance_flag_or_count(self):
        """Vehicle entities track importance for limiting rule."""
        entity = Entity(
            entity_id="ent_veh_001",
            canonical_name="Silence",
            entity_type=EntityType.VEHICLE,
            first_seen_passage="book4:100",
            mention_count=5,
            is_important=True,
        )
        assert entity.is_important is True


class TestAliasEntry:
    """Tests for AliasEntry contract."""

    def test_alias_links_variant_to_entity(self):
        """AliasEntry maps variant name to canonical entity."""
        alias = AliasEntry(
            alias_id="alias_001",
            alias_text="Lord Snow",
            entity_id="ent_001",
            confidence=0.95,
        )
        assert alias.alias_text == "Lord Snow"
        assert alias.entity_id == "ent_001"

    def test_alias_has_confidence_score(self):
        """AliasEntry includes confidence score."""
        alias = AliasEntry(
            alias_id="alias_002",
            alias_text="The Bastard of Winterfell",
            entity_id="ent_001",
            confidence=0.85,
        )
        assert 0.0 <= alias.confidence <= 1.0


class TestOverrideRule:
    """Tests for OverrideRule contract."""

    def test_override_rule_human_wins(self):
        """OverrideRule allows human corrections."""
        override = OverrideRule(
            override_id="ovr_001",
            target_alias="The Young Wolf",
            action=OverrideAction.ASSIGN,
            target_entity_id="ent_robb",
            reason="Human correction: this refers to Robb Stark",
        )
        assert override.action == OverrideAction.ASSIGN


class TestObligation:
    """Tests for Obligation contract."""

    def test_obligation_requires_evidence_anchors(self):
        """Obligation must have at least one evidence anchor."""
        obligation = Obligation(
            obligation_id="obl_001",
            category=ObligationCategory.PROPHECY_VISION,
            description="The dragon has three heads",
            evidence_anchor_ids=["ev_001"],
            last_seen_passage_id="book5:1200",
            confidence=0.9,
        )
        assert len(obligation.evidence_anchor_ids) >= 1

    def test_obligation_categories_match_spec(self):
        """ObligationCategory includes all MVP categories."""
        expected = {"PLOT_THREAD", "CHEKHOV_GUN", "PROPHECY_VISION", "MYSTERY"}
        actual = {c.name for c in ObligationCategory}
        assert expected == actual

    def test_obligation_has_last_seen_reference(self):
        """Obligation tracks last-seen passage for recency."""
        obligation = Obligation(
            obligation_id="obl_002",
            category=ObligationCategory.CHEKHOV_GUN,
            description="Valyrian steel dagger",
            evidence_anchor_ids=["ev_010", "ev_011"],
            last_seen_passage_id="book5:500",
            confidence=0.85,
        )
        assert obligation.last_seen_passage_id == "book5:500"

    def test_obligation_has_confidence_score(self):
        """Obligation includes confidence score."""
        obligation = Obligation(
            obligation_id="obl_003",
            category=ObligationCategory.MYSTERY,
            description="Who is Jon Snow's mother?",
            evidence_anchor_ids=["ev_020"],
            last_seen_passage_id="book1:50",
            confidence=0.95,
        )
        assert 0.0 <= obligation.confidence <= 1.0


class TestObligationGraphEdge:
    """Tests for ObligationGraphEdge contract."""

    def test_edge_links_obligations(self):
        """Edge connects two obligations with relationship type."""
        edge = ObligationGraphEdge(
            edge_id="edge_001",
            source_obligation_id="obl_001",
            target_obligation_id="obl_002",
            edge_type=EdgeType.DEPENDS_ON,
            weight=0.8,
        )
        assert edge.edge_type == EdgeType.DEPENDS_ON


class TestFinding:
    """Tests for Finding contract."""

    def test_finding_captures_validation_result(self):
        """Finding records validation issues."""
        finding = Finding(
            finding_id="find_001",
            severity=FindingSeverity.ERROR,
            category="evidence_gate",
            message="Obligation obl_003 has no evidence anchors",
            source_location="obligations.json:line 45",
        )
        assert finding.severity == FindingSeverity.ERROR

    def test_finding_severity_levels(self):
        """FindingSeverity includes ERROR and WARN."""
        expected = {"ERROR", "WARN", "INFO"}
        actual = {s.name for s in FindingSeverity}
        assert expected == actual


class TestMetricsReport:
    """Tests for MetricsReport contract."""

    def test_metrics_report_tracks_mvp_metrics(self):
        """MetricsReport includes all MVP quality metrics."""
        report = MetricsReport(
            run_id="run_001",
            timestamp=datetime.now(),
            obligations_with_evidence_rate=1.0,
            er_ambiguity_rate=0.05,
            obligation_dedupe_rate=0.1,
            total_passages=5000,
            total_entities=150,
            total_obligations=75,
            runtime_seconds=120.5,
        )
        assert report.obligations_with_evidence_rate == 1.0
        assert report.total_obligations == 75


class TestRunManifest:
    """Tests for RunManifest contract."""

    def test_run_manifest_captures_run_metadata(self):
        """RunManifest tracks git SHA, versions, hashes."""
        manifest = RunManifest(
            run_id="run_001",
            timestamp=datetime.now(),
            git_sha="abc123def456",
            python_version="3.14.2",
            segmentation_version="1.0.0",
            config_hash="sha256:abc...",
            input_dataset_hash="sha256:def...",
        )
        assert manifest.git_sha == "abc123def456"
        assert manifest.segmentation_version == "1.0.0"


class TestDatasetManifest:
    """Tests for DatasetManifest contract."""

    def test_dataset_manifest_lists_sources(self):
        """DatasetManifest enumerates input sources."""
        manifest = DatasetManifest(
            manifest_id="ds_001",
            total_documents=5,
            total_characters=1700000,
            source_files=[
                "/corpus/book1.txt",
                "/corpus/book2.txt",
            ],
            content_hash="sha256:xyz...",
        )
        assert manifest.total_documents == 5
        assert len(manifest.source_files) == 2
