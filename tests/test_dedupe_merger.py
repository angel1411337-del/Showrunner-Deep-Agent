"""Tests for DedupeMerger - obligation deduplication and merging.

TDD tests written before implementation.
"""

import pytest

from showrunner.contracts import (
    EdgeType,
    Obligation,
    ObligationCategory,
)
from showrunner.processors.dedupe_merger import DedupeMerger

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def merger() -> DedupeMerger:
    """Default merger with 0.8 threshold."""
    return DedupeMerger(similarity_threshold=0.8)


@pytest.fixture
def low_threshold_merger() -> DedupeMerger:
    """Merger with low threshold for testing edge cases."""
    return DedupeMerger(similarity_threshold=0.3)


@pytest.fixture
def sample_obligation_1() -> Obligation:
    """First sample obligation about a mysterious sword."""
    return Obligation(
        obligation_id="obl-001",
        category=ObligationCategory.CHEKHOV_GUN,
        description="The ancient sword hidden in the attic must be used eventually",
        evidence_anchor_ids=["ev-001", "ev-002"],
        last_seen_passage_id="passage-100",
        confidence=0.85,
        related_entity_ids=["entity-sword", "entity-attic"],
    )


@pytest.fixture
def sample_obligation_2() -> Obligation:
    """Second sample obligation - near duplicate of first."""
    return Obligation(
        obligation_id="obl-002",
        category=ObligationCategory.CHEKHOV_GUN,
        description="The ancient sword hidden in the attic must be used later",
        evidence_anchor_ids=["ev-003"],
        last_seen_passage_id="passage-150",
        confidence=0.90,
        related_entity_ids=["entity-sword", "entity-attic"],
    )


@pytest.fixture
def sample_obligation_3() -> Obligation:
    """Third sample obligation - completely different."""
    return Obligation(
        obligation_id="obl-003",
        category=ObligationCategory.MYSTERY,
        description="Who killed the merchant in chapter 3",
        evidence_anchor_ids=["ev-004"],
        last_seen_passage_id="passage-50",
        confidence=0.75,
        related_entity_ids=["entity-merchant"],
    )


@pytest.fixture
def sample_obligation_4() -> Obligation:
    """Fourth sample - somewhat similar to third."""
    return Obligation(
        obligation_id="obl-004",
        category=ObligationCategory.MYSTERY,
        description="The identity of the merchant's killer remains unknown",
        evidence_anchor_ids=["ev-005", "ev-006"],
        last_seen_passage_id="passage-200",
        confidence=0.80,
        related_entity_ids=["entity-merchant", "entity-killer"],
    )


# =============================================================================
# Test: compute_similarity
# =============================================================================


class TestComputeSimilarity:
    """Tests for compute_similarity method."""

    def test_compute_similarity_identical_descriptions_returns_high_score(
        self, merger: DedupeMerger
    ) -> None:
        """Identical descriptions should return similarity of 1.0."""
        obl1 = Obligation(
            obligation_id="obl-1",
            category=ObligationCategory.PLOT_THREAD,
            description="The hero must find the treasure",
            evidence_anchor_ids=["ev-1"],
            last_seen_passage_id="p-1",
            confidence=0.9,
        )
        obl2 = Obligation(
            obligation_id="obl-2",
            category=ObligationCategory.PLOT_THREAD,
            description="The hero must find the treasure",
            evidence_anchor_ids=["ev-2"],
            last_seen_passage_id="p-2",
            confidence=0.8,
        )

        similarity = merger.compute_similarity(obl1, obl2)

        assert similarity == 1.0

    def test_compute_similarity_completely_different_returns_low_score(
        self, merger: DedupeMerger
    ) -> None:
        """Completely different descriptions should return low similarity."""
        obl1 = Obligation(
            obligation_id="obl-1",
            category=ObligationCategory.PLOT_THREAD,
            description="The hero must find the treasure",
            evidence_anchor_ids=["ev-1"],
            last_seen_passage_id="p-1",
            confidence=0.9,
        )
        obl2 = Obligation(
            obligation_id="obl-2",
            category=ObligationCategory.MYSTERY,
            description="xyz abc qrs completely unrelated words",
            evidence_anchor_ids=["ev-2"],
            last_seen_passage_id="p-2",
            confidence=0.8,
        )

        similarity = merger.compute_similarity(obl1, obl2)

        assert similarity < 0.3

    def test_compute_similarity_same_category_bonus(self, merger: DedupeMerger) -> None:
        """Same category should boost similarity score."""
        base_desc = "The sword was mentioned"
        obl1 = Obligation(
            obligation_id="obl-1",
            category=ObligationCategory.CHEKHOV_GUN,
            description=base_desc,
            evidence_anchor_ids=["ev-1"],
            last_seen_passage_id="p-1",
            confidence=0.9,
        )
        obl_same_cat = Obligation(
            obligation_id="obl-2",
            category=ObligationCategory.CHEKHOV_GUN,
            description="The blade was referenced",
            evidence_anchor_ids=["ev-2"],
            last_seen_passage_id="p-2",
            confidence=0.8,
        )
        obl_diff_cat = Obligation(
            obligation_id="obl-3",
            category=ObligationCategory.MYSTERY,
            description="The blade was referenced",
            evidence_anchor_ids=["ev-3"],
            last_seen_passage_id="p-3",
            confidence=0.8,
        )

        sim_same = merger.compute_similarity(obl1, obl_same_cat)
        sim_diff = merger.compute_similarity(obl1, obl_diff_cat)

        assert sim_same > sim_diff

    def test_compute_similarity_overlapping_entities_bonus(self, merger: DedupeMerger) -> None:
        """Overlapping related_entity_ids should boost similarity."""
        obl1 = Obligation(
            obligation_id="obl-1",
            category=ObligationCategory.PLOT_THREAD,
            description="The sword was found",
            evidence_anchor_ids=["ev-1"],
            last_seen_passage_id="p-1",
            confidence=0.9,
            related_entity_ids=["entity-sword", "entity-hero"],
        )
        obl_overlap = Obligation(
            obligation_id="obl-2",
            category=ObligationCategory.PLOT_THREAD,
            description="The blade was discovered",
            evidence_anchor_ids=["ev-2"],
            last_seen_passage_id="p-2",
            confidence=0.8,
            related_entity_ids=["entity-sword", "entity-cave"],
        )
        obl_no_overlap = Obligation(
            obligation_id="obl-3",
            category=ObligationCategory.PLOT_THREAD,
            description="The blade was discovered",
            evidence_anchor_ids=["ev-3"],
            last_seen_passage_id="p-3",
            confidence=0.8,
            related_entity_ids=["entity-dragon", "entity-cave"],
        )

        sim_overlap = merger.compute_similarity(obl1, obl_overlap)
        sim_no_overlap = merger.compute_similarity(obl1, obl_no_overlap)

        assert sim_overlap > sim_no_overlap

    def test_compute_similarity_returns_value_between_0_and_1(
        self, merger: DedupeMerger, sample_obligation_1: Obligation, sample_obligation_3: Obligation
    ) -> None:
        """Similarity score should always be between 0 and 1."""
        similarity = merger.compute_similarity(sample_obligation_1, sample_obligation_3)

        assert 0.0 <= similarity <= 1.0

    def test_compute_similarity_is_symmetric(
        self, merger: DedupeMerger, sample_obligation_1: Obligation, sample_obligation_2: Obligation
    ) -> None:
        """Similarity should be symmetric: sim(a,b) == sim(b,a)."""
        sim_1_2 = merger.compute_similarity(sample_obligation_1, sample_obligation_2)
        sim_2_1 = merger.compute_similarity(sample_obligation_2, sample_obligation_1)

        assert sim_1_2 == pytest.approx(sim_2_1, rel=1e-6)


# =============================================================================
# Test: find_duplicates
# =============================================================================


class TestFindDuplicates:
    """Tests for find_duplicates method."""

    def test_find_duplicates_empty_list_returns_empty(self, merger: DedupeMerger) -> None:
        """Empty input should return empty list."""
        result = merger.find_duplicates([])

        assert result == []

    def test_find_duplicates_single_obligation_returns_empty(
        self, merger: DedupeMerger, sample_obligation_1: Obligation
    ) -> None:
        """Single obligation has no duplicates."""
        result = merger.find_duplicates([sample_obligation_1])

        assert result == []

    def test_find_duplicates_finds_near_duplicates(
        self, merger: DedupeMerger, sample_obligation_1: Obligation, sample_obligation_2: Obligation
    ) -> None:
        """Should find pair of near-duplicate obligations."""
        result = merger.find_duplicates([sample_obligation_1, sample_obligation_2])

        assert len(result) == 1
        pair = result[0]
        assert pair[0] in ["obl-001", "obl-002"]
        assert pair[1] in ["obl-001", "obl-002"]
        assert pair[0] != pair[1]
        assert pair[2] >= 0.8  # Above threshold

    def test_find_duplicates_does_not_find_non_duplicates(
        self, merger: DedupeMerger, sample_obligation_1: Obligation, sample_obligation_3: Obligation
    ) -> None:
        """Should not find pairs below similarity threshold."""
        result = merger.find_duplicates([sample_obligation_1, sample_obligation_3])

        assert result == []

    def test_find_duplicates_returns_tuple_with_ids_and_score(
        self,
        low_threshold_merger: DedupeMerger,
        sample_obligation_1: Obligation,
        sample_obligation_2: Obligation,
    ) -> None:
        """Result tuples should be (obl_id_1, obl_id_2, similarity_score)."""
        result = low_threshold_merger.find_duplicates([sample_obligation_1, sample_obligation_2])

        assert len(result) >= 1
        obl_id_1, obl_id_2, score = result[0]
        assert isinstance(obl_id_1, str)
        assert isinstance(obl_id_2, str)
        assert isinstance(score, float)
        assert score >= 0.0 and score <= 1.0

    def test_find_duplicates_multiple_pairs(
        self,
        low_threshold_merger: DedupeMerger,
        sample_obligation_1: Obligation,
        sample_obligation_2: Obligation,
        sample_obligation_3: Obligation,
        sample_obligation_4: Obligation,
    ) -> None:
        """Should find multiple duplicate pairs when they exist."""
        obligations = [
            sample_obligation_1,
            sample_obligation_2,
            sample_obligation_3,
            sample_obligation_4,
        ]
        result = low_threshold_merger.find_duplicates(obligations)

        # Should find at least obl-001/obl-002 pair
        found_ids = {(p[0], p[1]) for p in result} | {(p[1], p[0]) for p in result}
        assert ("obl-001", "obl-002") in found_ids or ("obl-002", "obl-001") in found_ids

    def test_find_duplicates_respects_threshold(self, merger: DedupeMerger) -> None:
        """Should only return pairs above the configured threshold."""
        obl1 = Obligation(
            obligation_id="obl-1",
            category=ObligationCategory.PLOT_THREAD,
            description="The quick brown fox jumps over the lazy dog",
            evidence_anchor_ids=["ev-1"],
            last_seen_passage_id="p-1",
            confidence=0.9,
        )
        obl2 = Obligation(
            obligation_id="obl-2",
            category=ObligationCategory.MYSTERY,
            description="Something completely different with no overlap whatsoever xyz",
            evidence_anchor_ids=["ev-2"],
            last_seen_passage_id="p-2",
            confidence=0.8,
        )

        result = merger.find_duplicates([obl1, obl2])

        assert result == []


# =============================================================================
# Test: merge_obligations
# =============================================================================


class TestMergeObligations:
    """Tests for merge_obligations method."""

    def test_merge_obligations_combines_evidence_anchor_ids(
        self, merger: DedupeMerger, sample_obligation_1: Obligation, sample_obligation_2: Obligation
    ) -> None:
        """Merged obligation should have all evidence anchors from both."""
        merged = merger.merge_obligations(sample_obligation_1, sample_obligation_2)

        expected_anchors = set(sample_obligation_1.evidence_anchor_ids) | set(
            sample_obligation_2.evidence_anchor_ids
        )
        assert set(merged.evidence_anchor_ids) == expected_anchors

    def test_merge_obligations_uses_higher_confidence(self, merger: DedupeMerger) -> None:
        """Merged obligation should use the higher confidence score."""
        obl_low = Obligation(
            obligation_id="obl-low",
            category=ObligationCategory.PLOT_THREAD,
            description="Test obligation",
            evidence_anchor_ids=["ev-1"],
            last_seen_passage_id="p-1",
            confidence=0.5,
        )
        obl_high = Obligation(
            obligation_id="obl-high",
            category=ObligationCategory.PLOT_THREAD,
            description="Test obligation similar",
            evidence_anchor_ids=["ev-2"],
            last_seen_passage_id="p-2",
            confidence=0.95,
        )

        merged = merger.merge_obligations(obl_low, obl_high)

        assert merged.confidence == 0.95

    def test_merge_obligations_uses_more_recent_last_seen(self, merger: DedupeMerger) -> None:
        """Merged obligation should use the more recent last_seen_passage_id."""
        obl_old = Obligation(
            obligation_id="obl-old",
            category=ObligationCategory.PLOT_THREAD,
            description="Test obligation",
            evidence_anchor_ids=["ev-1"],
            last_seen_passage_id="passage-050",
            confidence=0.9,
        )
        obl_new = Obligation(
            obligation_id="obl-new",
            category=ObligationCategory.PLOT_THREAD,
            description="Test obligation similar",
            evidence_anchor_ids=["ev-2"],
            last_seen_passage_id="passage-200",
            confidence=0.8,
        )

        merged = merger.merge_obligations(obl_old, obl_new)

        assert merged.last_seen_passage_id == "passage-200"

    def test_merge_obligations_keeps_primary_with_more_evidence(self, merger: DedupeMerger) -> None:
        """Should keep obligation with more evidence as primary (use its ID)."""
        obl_less = Obligation(
            obligation_id="obl-less",
            category=ObligationCategory.PLOT_THREAD,
            description="Test obligation",
            evidence_anchor_ids=["ev-1"],
            last_seen_passage_id="p-1",
            confidence=0.9,
        )
        obl_more = Obligation(
            obligation_id="obl-more",
            category=ObligationCategory.PLOT_THREAD,
            description="Test obligation similar",
            evidence_anchor_ids=["ev-2", "ev-3", "ev-4"],
            last_seen_passage_id="p-2",
            confidence=0.8,
        )

        merged = merger.merge_obligations(obl_less, obl_more)

        assert merged.obligation_id == "obl-more"

    def test_merge_obligations_combines_related_entity_ids(self, merger: DedupeMerger) -> None:
        """Merged obligation should combine related_entity_ids from both."""
        obl1 = Obligation(
            obligation_id="obl-1",
            category=ObligationCategory.PLOT_THREAD,
            description="Test obligation",
            evidence_anchor_ids=["ev-1"],
            last_seen_passage_id="p-1",
            confidence=0.9,
            related_entity_ids=["entity-a", "entity-b"],
        )
        obl2 = Obligation(
            obligation_id="obl-2",
            category=ObligationCategory.PLOT_THREAD,
            description="Test obligation similar",
            evidence_anchor_ids=["ev-2", "ev-3"],
            last_seen_passage_id="p-2",
            confidence=0.8,
            related_entity_ids=["entity-b", "entity-c"],
        )

        merged = merger.merge_obligations(obl1, obl2)

        assert set(merged.related_entity_ids) == {"entity-a", "entity-b", "entity-c"}

    def test_merge_obligations_preserves_category(
        self, merger: DedupeMerger, sample_obligation_1: Obligation, sample_obligation_2: Obligation
    ) -> None:
        """Merged obligation should preserve the primary's category."""
        merged = merger.merge_obligations(sample_obligation_1, sample_obligation_2)

        # Primary is obl-001 (more evidence)
        assert merged.category == sample_obligation_1.category

    def test_merge_obligations_preserves_description(
        self, merger: DedupeMerger, sample_obligation_1: Obligation, sample_obligation_2: Obligation
    ) -> None:
        """Merged obligation should preserve the primary's description."""
        merged = merger.merge_obligations(sample_obligation_1, sample_obligation_2)

        # Primary is obl-001 (more evidence)
        assert merged.description == sample_obligation_1.description

    def test_merge_obligations_preserves_resolved_status_if_either_resolved(
        self, merger: DedupeMerger
    ) -> None:
        """If either obligation is resolved, merged should be resolved."""
        obl_unresolved = Obligation(
            obligation_id="obl-unresolved",
            category=ObligationCategory.PLOT_THREAD,
            description="Test obligation",
            evidence_anchor_ids=["ev-1"],
            last_seen_passage_id="p-1",
            confidence=0.9,
            is_resolved=False,
        )
        obl_resolved = Obligation(
            obligation_id="obl-resolved",
            category=ObligationCategory.PLOT_THREAD,
            description="Test obligation similar",
            evidence_anchor_ids=["ev-2", "ev-3"],
            last_seen_passage_id="p-2",
            confidence=0.8,
            is_resolved=True,
            resolution_passage_id="resolution-p",
        )

        merged = merger.merge_obligations(obl_unresolved, obl_resolved)

        assert merged.is_resolved is True
        assert merged.resolution_passage_id == "resolution-p"


# =============================================================================
# Test: merge (full pipeline)
# =============================================================================


class TestMerge:
    """Tests for the full merge pipeline."""

    def test_merge_empty_list_returns_empty_and_zero_rate(self, merger: DedupeMerger) -> None:
        """Empty input returns empty list and 0.0 dedupe rate."""
        merged_obls, edges, rate = merger.merge([])

        assert merged_obls == []
        assert edges == []
        assert rate == 0.0

    def test_merge_single_obligation_returns_unchanged(
        self, merger: DedupeMerger, sample_obligation_1: Obligation
    ) -> None:
        """Single obligation returns as-is with 0.0 dedupe rate."""
        merged_obls, edges, rate = merger.merge([sample_obligation_1])

        assert len(merged_obls) == 1
        assert merged_obls[0] == sample_obligation_1
        assert edges == []
        assert rate == 0.0

    def test_merge_no_duplicates_returns_all_unchanged(
        self, merger: DedupeMerger, sample_obligation_1: Obligation, sample_obligation_3: Obligation
    ) -> None:
        """Non-duplicate obligations are returned unchanged."""
        merged_obls, edges, rate = merger.merge([sample_obligation_1, sample_obligation_3])

        assert len(merged_obls) == 2
        assert edges == []
        assert rate == 0.0

    def test_merge_duplicates_reduces_count(
        self, merger: DedupeMerger, sample_obligation_1: Obligation, sample_obligation_2: Obligation
    ) -> None:
        """Duplicate pair should be merged into single obligation."""
        merged_obls, edges, rate = merger.merge([sample_obligation_1, sample_obligation_2])

        assert len(merged_obls) == 1
        # All evidence should be preserved
        merged_anchors = set(merged_obls[0].evidence_anchor_ids)
        expected_anchors = set(sample_obligation_1.evidence_anchor_ids) | set(
            sample_obligation_2.evidence_anchor_ids
        )
        assert merged_anchors == expected_anchors

    def test_merge_creates_duplicate_edges(
        self, merger: DedupeMerger, sample_obligation_1: Obligation, sample_obligation_2: Obligation
    ) -> None:
        """Merging should create DUPLICATES edge linking primary to absorbed."""
        merged_obls, edges, rate = merger.merge([sample_obligation_1, sample_obligation_2])

        assert len(edges) == 1
        edge = edges[0]
        assert edge.edge_type == EdgeType.DUPLICATES
        assert edge.source_obligation_id == merged_obls[0].obligation_id
        # Target should be the absorbed obligation
        absorbed_id = "obl-002" if merged_obls[0].obligation_id == "obl-001" else "obl-001"
        assert edge.target_obligation_id == absorbed_id

    def test_merge_calculates_dedupe_rate(
        self, merger: DedupeMerger, sample_obligation_1: Obligation, sample_obligation_2: Obligation
    ) -> None:
        """Dedupe rate should be (original - merged) / original."""
        merged_obls, edges, rate = merger.merge([sample_obligation_1, sample_obligation_2])

        # 2 -> 1 = 50% reduction
        expected_rate = (2 - 1) / 2
        assert rate == pytest.approx(expected_rate)

    def test_merge_handles_multiple_duplicate_pairs(
        self, low_threshold_merger: DedupeMerger
    ) -> None:
        """Should handle multiple independent duplicate pairs."""
        # Create two pairs of duplicates
        pair1_a = Obligation(
            obligation_id="p1a",
            category=ObligationCategory.PLOT_THREAD,
            description="The hero must find the sword",
            evidence_anchor_ids=["ev-1"],
            last_seen_passage_id="p-1",
            confidence=0.9,
        )
        pair1_b = Obligation(
            obligation_id="p1b",
            category=ObligationCategory.PLOT_THREAD,
            description="The hero needs to find the sword",
            evidence_anchor_ids=["ev-2", "ev-3"],
            last_seen_passage_id="p-2",
            confidence=0.85,
        )
        pair2_a = Obligation(
            obligation_id="p2a",
            category=ObligationCategory.MYSTERY,
            description="Who killed the dragon",
            evidence_anchor_ids=["ev-4"],
            last_seen_passage_id="p-3",
            confidence=0.8,
        )
        pair2_b = Obligation(
            obligation_id="p2b",
            category=ObligationCategory.MYSTERY,
            description="The dragon killer's identity",
            evidence_anchor_ids=["ev-5", "ev-6"],
            last_seen_passage_id="p-4",
            confidence=0.75,
        )

        merged_obls, edges, rate = low_threshold_merger.merge([pair1_a, pair1_b, pair2_a, pair2_b])

        # Should have 2 merged obligations (one from each pair)
        assert len(merged_obls) == 2
        # Should have 2 duplicate edges
        assert len(edges) == 2
        # 4 -> 2 = 50% reduction
        assert rate == pytest.approx(0.5)

    def test_merge_preserves_unrelated_obligations(
        self,
        merger: DedupeMerger,
        sample_obligation_1: Obligation,
        sample_obligation_2: Obligation,
        sample_obligation_3: Obligation,
    ) -> None:
        """Unrelated obligations should be preserved unchanged."""
        merged_obls, edges, rate = merger.merge(
            [
                sample_obligation_1,
                sample_obligation_2,
                sample_obligation_3,
            ]
        )

        # obl-001 and obl-002 are duplicates, obl-003 is unique
        assert len(merged_obls) == 2
        obl_ids = {o.obligation_id for o in merged_obls}
        assert "obl-003" in obl_ids
        # One of obl-001 or obl-002 should be primary
        assert "obl-001" in obl_ids or "obl-002" in obl_ids

    def test_merge_edge_has_valid_id(
        self, merger: DedupeMerger, sample_obligation_1: Obligation, sample_obligation_2: Obligation
    ) -> None:
        """Created edges should have valid edge_ids."""
        merged_obls, edges, rate = merger.merge([sample_obligation_1, sample_obligation_2])

        assert len(edges) == 1
        assert edges[0].edge_id is not None
        assert len(edges[0].edge_id) > 0

    def test_merge_edge_weight_equals_similarity(
        self, merger: DedupeMerger, sample_obligation_1: Obligation, sample_obligation_2: Obligation
    ) -> None:
        """Edge weight should equal the similarity score between obligations."""
        expected_sim = merger.compute_similarity(sample_obligation_1, sample_obligation_2)

        merged_obls, edges, rate = merger.merge([sample_obligation_1, sample_obligation_2])

        assert len(edges) == 1
        assert edges[0].weight == pytest.approx(expected_sim, rel=1e-6)


# =============================================================================
# Test: Initialization
# =============================================================================


class TestInitialization:
    """Tests for DedupeMerger initialization."""

    def test_default_threshold(self) -> None:
        """Default similarity threshold should be 0.8."""
        merger = DedupeMerger()
        assert merger.similarity_threshold == 0.8

    def test_custom_threshold(self) -> None:
        """Custom similarity threshold should be stored."""
        merger = DedupeMerger(similarity_threshold=0.5)
        assert merger.similarity_threshold == 0.5

    def test_threshold_at_boundary_zero(self) -> None:
        """Threshold of 0 should work."""
        merger = DedupeMerger(similarity_threshold=0.0)
        assert merger.similarity_threshold == 0.0

    def test_threshold_at_boundary_one(self) -> None:
        """Threshold of 1 should work."""
        merger = DedupeMerger(similarity_threshold=1.0)
        assert merger.similarity_threshold == 1.0
