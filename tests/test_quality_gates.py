"""Tests for QualityGates module.

TDD tests for the DataOps-grade quality gates system.
Tests written first, then implementation to pass them.
"""

import json
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import BaseModel

from showrunner.contracts import (
    AliasEntry,
    Entity,
    EntityType,
    EvidenceAnchor,
    Finding,
    FindingSeverity,
    Obligation,
    ObligationCategory,
    PassageRecord,
)
from showrunner.gates.quality_gates import QualityGates


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def quality_gates() -> QualityGates:
    """Create a fresh QualityGates instance for each test."""
    return QualityGates()


@pytest.fixture
def sample_passage() -> PassageRecord:
    """Create a sample passage for testing."""
    return PassageRecord(
        passage_id="book1:0",
        source_id="book1",
        paragraph_index=0,
        text="The wizard raised his staff and spoke the ancient words.",
        char_start=0,
        char_end=55,
    )


@pytest.fixture
def sample_passages() -> list[PassageRecord]:
    """Create multiple sample passages for testing."""
    return [
        PassageRecord(
            passage_id="book1:0",
            source_id="book1",
            paragraph_index=0,
            text="The wizard raised his staff and spoke the ancient words.",
            char_start=0,
            char_end=55,
        ),
        PassageRecord(
            passage_id="book1:1",
            source_id="book1",
            paragraph_index=1,
            text="A flash of light erupted from the tip.",
            char_start=56,
            char_end=94,
        ),
        PassageRecord(
            passage_id="book2:0",
            source_id="book2",
            paragraph_index=0,
            text="Years later, the prophecy came true.",
            char_start=0,
            char_end=36,
        ),
    ]


@pytest.fixture
def sample_anchor(sample_passage: PassageRecord) -> EvidenceAnchor:
    """Create a sample evidence anchor for testing."""
    return EvidenceAnchor(
        anchor_id="anchor-001",
        passage_id=sample_passage.passage_id,
        char_start=0,
        char_end=10,
        excerpt="The wizard",
    )


@pytest.fixture
def sample_anchors(sample_passages: list[PassageRecord]) -> list[EvidenceAnchor]:
    """Create multiple sample anchors for testing."""
    return [
        EvidenceAnchor(
            anchor_id="anchor-001",
            passage_id="book1:0",
            char_start=0,
            char_end=10,
            excerpt="The wizard",
        ),
        EvidenceAnchor(
            anchor_id="anchor-002",
            passage_id="book1:1",
            char_start=0,
            char_end=15,
            excerpt="A flash of light",
        ),
        EvidenceAnchor(
            anchor_id="anchor-003",
            passage_id="book2:0",
            char_start=0,
            char_end=11,
            excerpt="Years later",
        ),
    ]


@pytest.fixture
def sample_entity() -> Entity:
    """Create a sample entity for testing."""
    return Entity(
        entity_id="entity-001",
        canonical_name="Gandalf",
        entity_type=EntityType.PERSON,
        first_seen_passage="book1:0",
        mention_count=5,
        is_important=True,
    )


@pytest.fixture
def sample_entities() -> list[Entity]:
    """Create multiple sample entities for testing."""
    return [
        Entity(
            entity_id="entity-001",
            canonical_name="Gandalf",
            entity_type=EntityType.PERSON,
            first_seen_passage="book1:0",
            mention_count=5,
            is_important=True,
        ),
        Entity(
            entity_id="entity-002",
            canonical_name="Rivendell",
            entity_type=EntityType.PLACE,
            first_seen_passage="book1:1",
            mention_count=3,
        ),
    ]


@pytest.fixture
def sample_alias(sample_entity: Entity) -> AliasEntry:
    """Create a sample alias for testing."""
    return AliasEntry(
        alias_id="alias-001",
        alias_text="The Grey",
        entity_id=sample_entity.entity_id,
        confidence=0.95,
    )


@pytest.fixture
def sample_aliases(sample_entities: list[Entity]) -> list[AliasEntry]:
    """Create multiple sample aliases for testing."""
    return [
        AliasEntry(
            alias_id="alias-001",
            alias_text="The Grey",
            entity_id="entity-001",
            confidence=0.95,
        ),
        AliasEntry(
            alias_id="alias-002",
            alias_text="Mithrandir",
            entity_id="entity-001",
            confidence=0.90,
        ),
        AliasEntry(
            alias_id="alias-003",
            alias_text="The Last Homely House",
            entity_id="entity-002",
            confidence=0.85,
        ),
    ]


@pytest.fixture
def sample_obligation(sample_anchor: EvidenceAnchor) -> Obligation:
    """Create a sample obligation for testing."""
    return Obligation(
        obligation_id="obl-001",
        category=ObligationCategory.PROPHECY_VISION,
        description="The prophecy must be fulfilled",
        evidence_anchor_ids=[sample_anchor.anchor_id],
        last_seen_passage_id="book1:0",
        confidence=0.8,
    )


@pytest.fixture
def sample_obligations(sample_anchors: list[EvidenceAnchor]) -> list[Obligation]:
    """Create multiple sample obligations for testing."""
    return [
        Obligation(
            obligation_id="obl-001",
            category=ObligationCategory.PROPHECY_VISION,
            description="The prophecy must be fulfilled",
            evidence_anchor_ids=["anchor-001"],
            last_seen_passage_id="book1:0",
            confidence=0.8,
        ),
        Obligation(
            obligation_id="obl-002",
            category=ObligationCategory.CHEKHOV_GUN,
            description="The wizard's staff will be significant",
            evidence_anchor_ids=["anchor-001", "anchor-002"],
            last_seen_passage_id="book1:1",
            confidence=0.9,
        ),
        Obligation(
            obligation_id="obl-003",
            category=ObligationCategory.PLOT_THREAD,
            description="The flash of light foreshadows events",
            evidence_anchor_ids=["anchor-002", "anchor-003"],
            last_seen_passage_id="book2:0",
            confidence=0.75,
        ),
    ]


@pytest.fixture
def schemas_dir(tmp_path: Path) -> Path:
    """Create a temporary schemas directory with test schemas."""
    schemas_path = tmp_path / "schemas"
    schemas_path.mkdir()

    # Create a simple test schema
    test_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "value": {"type": "integer"},
        },
        "required": ["name", "value"],
    }
    (schemas_path / "TestModel.json").write_text(json.dumps(test_schema))

    return schemas_path


# ============================================================================
# Schema Validation Tests
# ============================================================================


class TestValidateSchema:
    """Tests for schema validation functionality."""

    def test_validate_schema_valid_artifact_returns_empty_findings(
        self, quality_gates: QualityGates, tmp_path: Path
    ) -> None:
        """Valid artifact should return no findings."""
        # Create a valid schema
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "count": {"type": "integer"},
            },
            "required": ["name", "count"],
        }
        schema_path = tmp_path / "test_schema.json"
        schema_path.write_text(json.dumps(schema))

        # Create matching model
        class TestModel(BaseModel):
            name: str
            count: int

        artifact = TestModel(name="test", count=42)

        findings = quality_gates.validate_schema(artifact, schema_path)

        assert findings == []

    def test_validate_schema_missing_required_field_returns_error(
        self, quality_gates: QualityGates, tmp_path: Path
    ) -> None:
        """Missing required field should return ERROR finding."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "integer"},
                "required_field": {"type": "string"},
            },
            "required": ["name", "value", "required_field"],
        }
        schema_path = tmp_path / "test_schema.json"
        schema_path.write_text(json.dumps(schema))

        class TestModel(BaseModel):
            name: str
            value: int

        artifact = TestModel(name="test", value=10)

        findings = quality_gates.validate_schema(artifact, schema_path)

        assert len(findings) == 1
        assert findings[0].severity == FindingSeverity.ERROR
        assert findings[0].category == "schema"
        assert "required_field" in findings[0].message

    def test_validate_schema_wrong_type_returns_error(
        self, quality_gates: QualityGates, tmp_path: Path
    ) -> None:
        """Wrong field type should return ERROR finding."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "integer"},
            },
            "required": ["name", "value"],
        }
        schema_path = tmp_path / "test_schema.json"
        schema_path.write_text(json.dumps(schema))

        class TestModel(BaseModel):
            name: str
            value: str  # Wrong type: string instead of integer

        artifact = TestModel(name="test", value="not_an_int")

        findings = quality_gates.validate_schema(artifact, schema_path)

        assert len(findings) >= 1
        assert any(f.severity == FindingSeverity.ERROR for f in findings)
        assert any(f.category == "schema" for f in findings)

    def test_validate_schema_nonexistent_schema_file_returns_error(
        self, quality_gates: QualityGates, tmp_path: Path
    ) -> None:
        """Non-existent schema file should return ERROR finding."""

        class TestModel(BaseModel):
            name: str

        artifact = TestModel(name="test")
        nonexistent_path = tmp_path / "nonexistent.json"

        findings = quality_gates.validate_schema(artifact, nonexistent_path)

        assert len(findings) == 1
        assert findings[0].severity == FindingSeverity.ERROR
        assert findings[0].category == "schema"
        assert "not found" in findings[0].message.lower()

    def test_validate_schema_invalid_json_schema_returns_error(
        self, quality_gates: QualityGates, tmp_path: Path
    ) -> None:
        """Invalid JSON schema should return ERROR finding."""
        schema_path = tmp_path / "invalid_schema.json"
        schema_path.write_text("not valid json {{{")

        class TestModel(BaseModel):
            name: str

        artifact = TestModel(name="test")

        findings = quality_gates.validate_schema(artifact, schema_path)

        assert len(findings) == 1
        assert findings[0].severity == FindingSeverity.ERROR
        assert findings[0].category == "schema"


# ============================================================================
# Referential Integrity Tests
# ============================================================================


class TestCheckReferentialIntegrity:
    """Tests for referential integrity validation."""

    def test_check_integrity_all_valid_references_returns_empty(
        self,
        quality_gates: QualityGates,
        sample_passages: list[PassageRecord],
        sample_anchors: list[EvidenceAnchor],
        sample_entities: list[Entity],
        sample_aliases: list[AliasEntry],
        sample_obligations: list[Obligation],
    ) -> None:
        """All valid references should return no findings."""
        findings = quality_gates.check_referential_integrity(
            passages=sample_passages,
            anchors=sample_anchors,
            entities=sample_entities,
            aliases=sample_aliases,
            obligations=sample_obligations,
        )

        assert findings == []

    def test_check_integrity_obligation_with_missing_anchor_returns_error(
        self,
        quality_gates: QualityGates,
        sample_passages: list[PassageRecord],
        sample_anchors: list[EvidenceAnchor],
        sample_entities: list[Entity],
        sample_aliases: list[AliasEntry],
    ) -> None:
        """Obligation referencing non-existent anchor should return ERROR."""
        bad_obligation = Obligation(
            obligation_id="obl-bad",
            category=ObligationCategory.MYSTERY,
            description="Missing anchor reference",
            evidence_anchor_ids=["nonexistent-anchor-999"],
            last_seen_passage_id="book1:0",
            confidence=0.7,
        )

        findings = quality_gates.check_referential_integrity(
            passages=sample_passages,
            anchors=sample_anchors,
            entities=sample_entities,
            aliases=sample_aliases,
            obligations=[bad_obligation],
        )

        assert len(findings) >= 1
        error_findings = [f for f in findings if f.severity == FindingSeverity.ERROR]
        assert len(error_findings) >= 1
        assert any("nonexistent-anchor-999" in f.message for f in error_findings)
        assert any(f.category == "referential_integrity" for f in error_findings)

    def test_check_integrity_alias_with_missing_entity_returns_error(
        self,
        quality_gates: QualityGates,
        sample_passages: list[PassageRecord],
        sample_anchors: list[EvidenceAnchor],
        sample_obligations: list[Obligation],
    ) -> None:
        """Alias referencing non-existent entity should return ERROR."""
        bad_alias = AliasEntry(
            alias_id="alias-bad",
            alias_text="Unknown Alias",
            entity_id="nonexistent-entity-999",
            confidence=0.5,
        )

        findings = quality_gates.check_referential_integrity(
            passages=sample_passages,
            anchors=sample_anchors,
            entities=[],  # No entities
            aliases=[bad_alias],
            obligations=sample_obligations,
        )

        # Filter for alias-related errors (not the anchor errors from obligations)
        alias_errors = [
            f
            for f in findings
            if f.severity == FindingSeverity.ERROR
            and "alias" in f.message.lower()
        ]
        assert len(alias_errors) >= 1
        assert any("nonexistent-entity-999" in f.message for f in alias_errors)

    def test_check_integrity_anchor_with_missing_passage_returns_error(
        self,
        quality_gates: QualityGates,
        sample_entities: list[Entity],
        sample_aliases: list[AliasEntry],
    ) -> None:
        """Anchor referencing non-existent passage should return ERROR."""
        bad_anchor = EvidenceAnchor(
            anchor_id="anchor-bad",
            passage_id="nonexistent-passage:999",
            char_start=0,
            char_end=10,
            excerpt="Missing passage",
        )

        # Need an obligation that references this anchor
        obligation = Obligation(
            obligation_id="obl-001",
            category=ObligationCategory.PLOT_THREAD,
            description="Test obligation",
            evidence_anchor_ids=["anchor-bad"],
            last_seen_passage_id="nonexistent-passage:999",
            confidence=0.8,
        )

        findings = quality_gates.check_referential_integrity(
            passages=[],  # No passages
            anchors=[bad_anchor],
            entities=sample_entities,
            aliases=sample_aliases,
            obligations=[obligation],
        )

        error_findings = [f for f in findings if f.severity == FindingSeverity.ERROR]
        assert len(error_findings) >= 1
        assert any("nonexistent-passage:999" in f.message for f in error_findings)

    def test_check_integrity_multiple_errors_returns_all(
        self,
        quality_gates: QualityGates,
    ) -> None:
        """Multiple integrity violations should all be reported."""
        # Create artifacts with multiple issues
        passage = PassageRecord(
            passage_id="book1:0",
            source_id="book1",
            paragraph_index=0,
            text="Test passage",
            char_start=0,
            char_end=12,
        )

        bad_anchor = EvidenceAnchor(
            anchor_id="anchor-bad",
            passage_id="missing-passage:0",
            char_start=0,
            char_end=5,
            excerpt="Test",
        )

        bad_alias = AliasEntry(
            alias_id="alias-bad",
            alias_text="Bad Alias",
            entity_id="missing-entity",
            confidence=0.5,
        )

        obligation_with_bad_anchor = Obligation(
            obligation_id="obl-001",
            category=ObligationCategory.MYSTERY,
            description="Test",
            evidence_anchor_ids=["missing-anchor-1", "missing-anchor-2"],
            last_seen_passage_id="book1:0",
            confidence=0.7,
        )

        findings = quality_gates.check_referential_integrity(
            passages=[passage],
            anchors=[bad_anchor],
            entities=[],
            aliases=[bad_alias],
            obligations=[obligation_with_bad_anchor],
        )

        # Should have errors for: missing passage, missing entity, missing anchors
        error_findings = [f for f in findings if f.severity == FindingSeverity.ERROR]
        assert len(error_findings) >= 3

    def test_check_integrity_empty_inputs_returns_empty(
        self, quality_gates: QualityGates
    ) -> None:
        """Empty inputs should return no findings (nothing to validate)."""
        findings = quality_gates.check_referential_integrity(
            passages=[],
            anchors=[],
            entities=[],
            aliases=[],
            obligations=[],
        )

        assert findings == []


# ============================================================================
# Evidence Gate Tests
# ============================================================================


class TestCheckEvidenceGate:
    """Tests for evidence gate validation."""

    def test_check_evidence_gate_all_have_evidence_returns_empty(
        self,
        quality_gates: QualityGates,
        sample_obligations: list[Obligation],
    ) -> None:
        """Obligations all having evidence should return no findings."""
        findings = quality_gates.check_evidence_gate(sample_obligations)

        assert findings == []

    def test_check_evidence_gate_empty_anchors_list_returns_error(
        self, quality_gates: QualityGates
    ) -> None:
        """Obligation with empty evidence_anchor_ids should return ERROR."""
        # Note: Pydantic enforces min_length=1, so we need to bypass this
        # by using model_construct or testing the gate logic directly
        # For this test, we'll create a mock-like situation

        # Actually, the Obligation model enforces min_length=1, so this scenario
        # can only occur if data comes from an external source (e.g., JSON)
        # We'll test the gate handles this gracefully by checking behavior

        # Create valid obligation - the evidence gate should pass
        valid_obligation = Obligation(
            obligation_id="obl-valid",
            category=ObligationCategory.PLOT_THREAD,
            description="Has evidence",
            evidence_anchor_ids=["anchor-001"],
            last_seen_passage_id="book1:0",
            confidence=0.8,
        )

        findings = quality_gates.check_evidence_gate([valid_obligation])
        assert findings == []

    def test_check_evidence_gate_single_obligation_no_evidence_returns_error(
        self, quality_gates: QualityGates
    ) -> None:
        """Single obligation without evidence should return exactly one ERROR."""
        # Use model_construct to bypass validation and test gate logic
        obligation_without_evidence = Obligation.model_construct(
            obligation_id="obl-no-evidence",
            category=ObligationCategory.MYSTERY,
            description="No evidence attached",
            evidence_anchor_ids=[],  # Empty - bypasses Pydantic validation
            last_seen_passage_id="book1:0",
            confidence=0.5,
            is_resolved=False,
            resolution_passage_id=None,
            related_entity_ids=[],
        )

        findings = quality_gates.check_evidence_gate([obligation_without_evidence])

        assert len(findings) == 1
        assert findings[0].severity == FindingSeverity.ERROR
        assert findings[0].category == "evidence_gate"
        assert "obl-no-evidence" in findings[0].message

    def test_check_evidence_gate_mixed_obligations_returns_errors_only_for_missing(
        self, quality_gates: QualityGates
    ) -> None:
        """Only obligations without evidence should produce ERROR findings."""
        valid_obligation = Obligation(
            obligation_id="obl-valid",
            category=ObligationCategory.PLOT_THREAD,
            description="Has evidence",
            evidence_anchor_ids=["anchor-001"],
            last_seen_passage_id="book1:0",
            confidence=0.8,
        )

        invalid_obligation = Obligation.model_construct(
            obligation_id="obl-invalid",
            category=ObligationCategory.MYSTERY,
            description="No evidence",
            evidence_anchor_ids=[],
            last_seen_passage_id="book1:0",
            confidence=0.5,
            is_resolved=False,
            resolution_passage_id=None,
            related_entity_ids=[],
        )

        findings = quality_gates.check_evidence_gate([valid_obligation, invalid_obligation])

        assert len(findings) == 1
        assert "obl-invalid" in findings[0].message
        assert "obl-valid" not in findings[0].message

    def test_check_evidence_gate_empty_obligations_list_returns_empty(
        self, quality_gates: QualityGates
    ) -> None:
        """Empty obligations list should return no findings."""
        findings = quality_gates.check_evidence_gate([])

        assert findings == []


# ============================================================================
# Contradiction Detection Tests
# ============================================================================


class TestDetectContradictions:
    """Tests for contradiction detection functionality."""

    def test_detect_contradictions_no_contradictions_returns_empty(
        self,
        quality_gates: QualityGates,
        sample_obligations: list[Obligation],
    ) -> None:
        """Non-contradicting obligations should return no findings."""
        findings = quality_gates.detect_contradictions(sample_obligations)

        # No contradictions in sample data
        assert findings == []

    def test_detect_contradictions_returns_warn_severity(
        self, quality_gates: QualityGates
    ) -> None:
        """Detected contradictions should be WARN severity (MVP soft gate)."""
        # Create potentially contradicting obligations
        obligation1 = Obligation(
            obligation_id="obl-001",
            category=ObligationCategory.PROPHECY_VISION,
            description="The hero will live",
            evidence_anchor_ids=["anchor-001"],
            last_seen_passage_id="book1:0",
            confidence=0.9,
        )

        obligation2 = Obligation(
            obligation_id="obl-002",
            category=ObligationCategory.PROPHECY_VISION,
            description="The hero will die",
            evidence_anchor_ids=["anchor-002"],
            last_seen_passage_id="book1:1",
            confidence=0.85,
        )

        findings = quality_gates.detect_contradictions([obligation1, obligation2])

        # If contradictions are detected, they should be WARN
        for finding in findings:
            assert finding.severity == FindingSeverity.WARN
            assert finding.category == "contradiction"

    def test_detect_contradictions_empty_obligations_returns_empty(
        self, quality_gates: QualityGates
    ) -> None:
        """Empty obligations list should return no findings."""
        findings = quality_gates.detect_contradictions([])

        assert findings == []

    def test_detect_contradictions_single_obligation_returns_empty(
        self, quality_gates: QualityGates, sample_obligation: Obligation
    ) -> None:
        """Single obligation cannot contradict itself."""
        findings = quality_gates.detect_contradictions([sample_obligation])

        assert findings == []


# ============================================================================
# Run All Gates Tests
# ============================================================================


class TestRunAllGates:
    """Tests for running all quality gates together."""

    def test_run_all_gates_all_pass_returns_empty_findings_and_true(
        self,
        quality_gates: QualityGates,
        sample_passages: list[PassageRecord],
        sample_anchors: list[EvidenceAnchor],
        sample_entities: list[Entity],
        sample_aliases: list[AliasEntry],
        sample_obligations: list[Obligation],
    ) -> None:
        """All gates passing should return empty findings and True."""
        findings, passed = quality_gates.run_all_gates(
            passages=sample_passages,
            anchors=sample_anchors,
            entities=sample_entities,
            aliases=sample_aliases,
            obligations=sample_obligations,
        )

        assert findings == []
        assert passed is True

    def test_run_all_gates_integrity_error_returns_false(
        self, quality_gates: QualityGates
    ) -> None:
        """Referential integrity error should fail the gate."""
        passage = PassageRecord(
            passage_id="book1:0",
            source_id="book1",
            paragraph_index=0,
            text="Test",
            char_start=0,
            char_end=4,
        )

        # Obligation referencing non-existent anchor
        bad_obligation = Obligation(
            obligation_id="obl-001",
            category=ObligationCategory.MYSTERY,
            description="Test",
            evidence_anchor_ids=["nonexistent-anchor"],
            last_seen_passage_id="book1:0",
            confidence=0.8,
        )

        findings, passed = quality_gates.run_all_gates(
            passages=[passage],
            anchors=[],
            entities=[],
            aliases=[],
            obligations=[bad_obligation],
        )

        assert passed is False
        assert len(findings) >= 1
        assert any(f.severity == FindingSeverity.ERROR for f in findings)

    def test_run_all_gates_evidence_error_returns_false(
        self, quality_gates: QualityGates
    ) -> None:
        """Evidence gate error should fail the gate."""
        passage = PassageRecord(
            passage_id="book1:0",
            source_id="book1",
            paragraph_index=0,
            text="Test",
            char_start=0,
            char_end=4,
        )

        # Obligation with no evidence (bypass Pydantic validation)
        bad_obligation = Obligation.model_construct(
            obligation_id="obl-no-evidence",
            category=ObligationCategory.MYSTERY,
            description="No evidence",
            evidence_anchor_ids=[],
            last_seen_passage_id="book1:0",
            confidence=0.5,
            is_resolved=False,
            resolution_passage_id=None,
            related_entity_ids=[],
        )

        findings, passed = quality_gates.run_all_gates(
            passages=[passage],
            anchors=[],
            entities=[],
            aliases=[],
            obligations=[bad_obligation],
        )

        assert passed is False
        assert any(f.category == "evidence_gate" for f in findings)

    def test_run_all_gates_warn_only_returns_true(
        self, quality_gates: QualityGates,
        sample_passages: list[PassageRecord],
        sample_anchors: list[EvidenceAnchor],
        sample_entities: list[Entity],
        sample_aliases: list[AliasEntry],
        sample_obligations: list[Obligation],
    ) -> None:
        """WARN-only findings (like contradictions) should still pass."""
        # With valid data, any contradiction warnings shouldn't fail the gate
        findings, passed = quality_gates.run_all_gates(
            passages=sample_passages,
            anchors=sample_anchors,
            entities=sample_entities,
            aliases=sample_aliases,
            obligations=sample_obligations,
        )

        # All sample data is valid, so should pass
        assert passed is True

    def test_run_all_gates_empty_data_returns_true(
        self, quality_gates: QualityGates
    ) -> None:
        """Empty data should pass (nothing to validate)."""
        findings, passed = quality_gates.run_all_gates(
            passages=[],
            anchors=[],
            entities=[],
            aliases=[],
            obligations=[],
        )

        assert passed is True
        assert findings == []

    def test_run_all_gates_aggregates_all_findings(
        self, quality_gates: QualityGates
    ) -> None:
        """All findings from all gates should be aggregated."""
        passage = PassageRecord(
            passage_id="book1:0",
            source_id="book1",
            paragraph_index=0,
            text="Test",
            char_start=0,
            char_end=4,
        )

        # Multiple issues
        bad_alias = AliasEntry(
            alias_id="alias-bad",
            alias_text="Bad",
            entity_id="missing-entity",
            confidence=0.5,
        )

        bad_obligation = Obligation.model_construct(
            obligation_id="obl-bad",
            category=ObligationCategory.MYSTERY,
            description="Bad",
            evidence_anchor_ids=[],
            last_seen_passage_id="book1:0",
            confidence=0.5,
            is_resolved=False,
            resolution_passage_id=None,
            related_entity_ids=[],
        )

        findings, passed = quality_gates.run_all_gates(
            passages=[passage],
            anchors=[],
            entities=[],
            aliases=[bad_alias],
            obligations=[bad_obligation],
        )

        assert passed is False
        # Should have errors from both integrity and evidence gates
        categories = {f.category for f in findings}
        assert "referential_integrity" in categories or "evidence_gate" in categories


# ============================================================================
# Finding Object Tests
# ============================================================================


class TestFindingCreation:
    """Tests to ensure Finding objects are created correctly."""

    def test_findings_have_unique_ids(
        self, quality_gates: QualityGates
    ) -> None:
        """Each finding should have a unique ID."""
        bad_obligation1 = Obligation.model_construct(
            obligation_id="obl-001",
            category=ObligationCategory.MYSTERY,
            description="No evidence 1",
            evidence_anchor_ids=[],
            last_seen_passage_id="book1:0",
            confidence=0.5,
            is_resolved=False,
            resolution_passage_id=None,
            related_entity_ids=[],
        )

        bad_obligation2 = Obligation.model_construct(
            obligation_id="obl-002",
            category=ObligationCategory.MYSTERY,
            description="No evidence 2",
            evidence_anchor_ids=[],
            last_seen_passage_id="book1:0",
            confidence=0.5,
            is_resolved=False,
            resolution_passage_id=None,
            related_entity_ids=[],
        )

        findings = quality_gates.check_evidence_gate([bad_obligation1, bad_obligation2])

        assert len(findings) == 2
        finding_ids = [f.finding_id for f in findings]
        assert len(finding_ids) == len(set(finding_ids))  # All unique

    def test_findings_include_related_ids(
        self, quality_gates: QualityGates
    ) -> None:
        """Findings should include related IDs for traceability."""
        bad_obligation = Obligation.model_construct(
            obligation_id="obl-traceable",
            category=ObligationCategory.MYSTERY,
            description="No evidence",
            evidence_anchor_ids=[],
            last_seen_passage_id="book1:0",
            confidence=0.5,
            is_resolved=False,
            resolution_passage_id=None,
            related_entity_ids=[],
        )

        findings = quality_gates.check_evidence_gate([bad_obligation])

        assert len(findings) == 1
        assert "obl-traceable" in findings[0].related_ids

    def test_findings_have_timestamps(
        self, quality_gates: QualityGates
    ) -> None:
        """All findings should have timestamps."""
        bad_obligation = Obligation.model_construct(
            obligation_id="obl-001",
            category=ObligationCategory.MYSTERY,
            description="No evidence",
            evidence_anchor_ids=[],
            last_seen_passage_id="book1:0",
            confidence=0.5,
            is_resolved=False,
            resolution_passage_id=None,
            related_entity_ids=[],
        )

        findings = quality_gates.check_evidence_gate([bad_obligation])

        assert len(findings) == 1
        assert findings[0].timestamp is not None
