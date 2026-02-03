"""DedupeMerger - Merge near-duplicate obligations across POVs.

Provides deduplication of narrative obligations using text-based similarity,
with bonuses for matching categories, overlapping entities, and shared evidence.
"""

import uuid
from typing import Union

from showrunner.contracts import (
    Obligation,
    ObligationGraphEdge,
    EdgeType,
)


def _tokenize(text: str) -> set[str]:
    """Tokenize text into lowercase words, removing punctuation.

    Args:
        text: Input text to tokenize.

    Returns:
        Set of lowercase word tokens.
    """
    # Simple tokenization: lowercase, split on whitespace, strip punctuation
    words = text.lower().split()
    tokens = set()
    for word in words:
        # Remove leading/trailing punctuation
        clean = word.strip(".,!?;:\"'()-[]{}").lower()
        if clean:
            tokens.add(clean)
    return tokens


def _jaccard_similarity(set_a: set, set_b: set) -> float:
    """Compute Jaccard similarity between two sets.

    Args:
        set_a: First set.
        set_b: Second set.

    Returns:
        Jaccard similarity coefficient (intersection/union).
    """
    if not set_a and not set_b:
        return 1.0  # Both empty = identical
    if not set_a or not set_b:
        return 0.0  # One empty = no overlap

    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union


def _compare_passage_ids(passage_id_1: str, passage_id_2: str) -> int:
    """Compare two passage IDs to determine which is more recent.

    Passage IDs are expected to follow a pattern like 'passage-NNN' where
    NNN is a numeric index. Higher numbers are more recent.

    Args:
        passage_id_1: First passage ID.
        passage_id_2: Second passage ID.

    Returns:
        1 if passage_id_1 is more recent, -1 if passage_id_2 is more recent, 0 if equal.
    """
    # Try to extract numeric suffix
    def extract_number(pid: str) -> int:
        # Split on common separators and take last numeric part
        parts = pid.replace("-", "_").split("_")
        for part in reversed(parts):
            try:
                return int(part)
            except ValueError:
                continue
        # Fallback to string comparison
        return 0

    num1 = extract_number(passage_id_1)
    num2 = extract_number(passage_id_2)

    if num1 > num2:
        return 1
    elif num1 < num2:
        return -1
    else:
        # Fallback to lexicographic comparison
        if passage_id_1 > passage_id_2:
            return 1
        elif passage_id_1 < passage_id_2:
            return -1
        return 0


class DedupeMerger:
    """Merges near-duplicate obligations across different POVs.

    Uses text-based similarity (Jaccard on tokenized descriptions) with
    bonuses for matching categories, overlapping entities, and shared
    evidence passages. Designed to be swappable for embedding-based
    similarity in the future.

    Attributes:
        similarity_threshold: Minimum similarity score (0-1) to consider
            obligations as duplicates. Defaults to 0.8.
    """

    # Weights for similarity computation
    _CATEGORY_BONUS = 0.1
    _ENTITY_OVERLAP_BONUS = 0.1
    _EVIDENCE_OVERLAP_BONUS = 0.05

    def __init__(self, similarity_threshold: float = 0.8) -> None:
        """Initialize the DedupeMerger.

        Args:
            similarity_threshold: Minimum similarity to consider duplicates.
        """
        self.similarity_threshold = similarity_threshold

    def compute_similarity(self, obl1: Obligation, obl2: Obligation) -> float:
        """Compute semantic similarity between two obligations.

        MVP implementation uses Jaccard similarity on tokenized descriptions,
        with bonuses for:
        - Same category (+0.1)
        - Overlapping related_entity_ids (+0.1 * overlap_ratio)
        - Overlapping evidence anchor sources (+0.05 * overlap_ratio)

        Args:
            obl1: First obligation.
            obl2: Second obligation.

        Returns:
            Similarity score between 0 and 1.
        """
        # Base similarity: Jaccard on tokenized descriptions
        tokens1 = _tokenize(obl1.description)
        tokens2 = _tokenize(obl2.description)
        base_similarity = _jaccard_similarity(tokens1, tokens2)

        # Category bonus
        category_bonus = 0.0
        if obl1.category == obl2.category:
            category_bonus = self._CATEGORY_BONUS

        # Entity overlap bonus
        entity_bonus = 0.0
        if obl1.related_entity_ids and obl2.related_entity_ids:
            entities1 = set(obl1.related_entity_ids)
            entities2 = set(obl2.related_entity_ids)
            entity_overlap = _jaccard_similarity(entities1, entities2)
            entity_bonus = self._ENTITY_OVERLAP_BONUS * entity_overlap

        # Evidence overlap bonus (based on anchor IDs)
        evidence_bonus = 0.0
        if obl1.evidence_anchor_ids and obl2.evidence_anchor_ids:
            evidence1 = set(obl1.evidence_anchor_ids)
            evidence2 = set(obl2.evidence_anchor_ids)
            evidence_overlap = _jaccard_similarity(evidence1, evidence2)
            evidence_bonus = self._EVIDENCE_OVERLAP_BONUS * evidence_overlap

        # Combine and cap at 1.0
        total = base_similarity + category_bonus + entity_bonus + evidence_bonus
        return min(1.0, total)

    def find_duplicates(
        self, obligations: list[Obligation]
    ) -> list[tuple[str, str, float]]:
        """Find pairs of potentially duplicate obligations.

        Compares all pairs of obligations and returns those with similarity
        scores at or above the configured threshold.

        Args:
            obligations: List of obligations to check for duplicates.

        Returns:
            List of tuples (obl_id_1, obl_id_2, similarity_score) for pairs
            above the similarity threshold.
        """
        if len(obligations) < 2:
            return []

        duplicates: list[tuple[str, str, float]] = []

        # Compare all pairs (O(n^2) - acceptable for MVP)
        for i, obl1 in enumerate(obligations):
            for obl2 in obligations[i + 1:]:
                similarity = self.compute_similarity(obl1, obl2)
                if similarity >= self.similarity_threshold:
                    duplicates.append((obl1.obligation_id, obl2.obligation_id, similarity))

        return duplicates

    def merge_obligations(self, obl1: Obligation, obl2: Obligation) -> Obligation:
        """Merge two obligations into one, preserving all evidence.

        Merge rules:
        - Keep obligation with more evidence anchors as "primary"
        - Combine all evidence_anchor_ids
        - Use higher confidence score
        - Use more recent last_seen_passage_id
        - Combine related_entity_ids

        Args:
            obl1: First obligation.
            obl2: Second obligation.

        Returns:
            Merged obligation.
        """
        # Determine primary (more evidence anchors)
        if len(obl1.evidence_anchor_ids) >= len(obl2.evidence_anchor_ids):
            primary = obl1
            secondary = obl2
        else:
            primary = obl2
            secondary = obl1

        # Combine evidence anchors (preserve order, primary first)
        combined_anchors = list(primary.evidence_anchor_ids)
        for anchor_id in secondary.evidence_anchor_ids:
            if anchor_id not in combined_anchors:
                combined_anchors.append(anchor_id)

        # Use higher confidence
        merged_confidence = max(primary.confidence, secondary.confidence)

        # Use more recent last_seen_passage_id
        if _compare_passage_ids(primary.last_seen_passage_id, secondary.last_seen_passage_id) >= 0:
            merged_last_seen = primary.last_seen_passage_id
        else:
            merged_last_seen = secondary.last_seen_passage_id

        # Combine related entity IDs
        combined_entities = list(primary.related_entity_ids)
        for entity_id in secondary.related_entity_ids:
            if entity_id not in combined_entities:
                combined_entities.append(entity_id)

        # Handle resolution status: if either is resolved, merged is resolved
        merged_is_resolved = primary.is_resolved or secondary.is_resolved
        merged_resolution_passage_id = (
            primary.resolution_passage_id
            if primary.is_resolved
            else secondary.resolution_passage_id
        )

        return Obligation(
            obligation_id=primary.obligation_id,
            category=primary.category,
            description=primary.description,
            evidence_anchor_ids=combined_anchors,
            last_seen_passage_id=merged_last_seen,
            confidence=merged_confidence,
            is_resolved=merged_is_resolved,
            resolution_passage_id=merged_resolution_passage_id,
            related_entity_ids=combined_entities,
        )

    def merge(
        self, obligations: list[Obligation]
    ) -> tuple[list[Obligation], list[ObligationGraphEdge], float]:
        """Full merge pipeline.

        Finds all duplicate pairs, merges them, and creates DUPLICATES edges
        linking primary obligations to absorbed ones.

        Args:
            obligations: List of obligations to deduplicate.

        Returns:
            Tuple of:
            - merged_obligations: Deduplicated list of obligations
            - duplicate_edges: DUPLICATES edges linking primaries to absorbed
            - dedupe_rate: Fraction of obligations that were duplicates
                          (original - merged) / original
        """
        if not obligations:
            return [], [], 0.0

        original_count = len(obligations)

        if original_count == 1:
            return list(obligations), [], 0.0

        # Build lookup by ID
        obl_by_id: dict[str, Obligation] = {obl.obligation_id: obl for obl in obligations}

        # Find all duplicate pairs
        duplicate_pairs = self.find_duplicates(obligations)

        if not duplicate_pairs:
            return list(obligations), [], 0.0

        # Track which obligations have been absorbed
        absorbed: set[str] = set()
        # Track merge mappings: absorbed_id -> (primary_id, similarity)
        merge_map: dict[str, tuple[str, float]] = {}
        # Track updated obligations
        updated_obls: dict[str, Obligation] = dict(obl_by_id)

        # Sort by similarity descending to merge most similar first
        duplicate_pairs.sort(key=lambda x: x[2], reverse=True)

        for obl_id_1, obl_id_2, similarity in duplicate_pairs:
            # Skip if either is already absorbed
            if obl_id_1 in absorbed or obl_id_2 in absorbed:
                continue

            # Get current versions (may have been updated by previous merges)
            obl1 = updated_obls.get(obl_id_1)
            obl2 = updated_obls.get(obl_id_2)

            if obl1 is None or obl2 is None:
                continue

            # Merge
            merged = self.merge_obligations(obl1, obl2)

            # Determine which was absorbed
            primary_id = merged.obligation_id
            absorbed_id = obl_id_2 if primary_id == obl_id_1 else obl_id_1

            # Update tracking
            absorbed.add(absorbed_id)
            merge_map[absorbed_id] = (primary_id, similarity)
            updated_obls[primary_id] = merged
            if absorbed_id in updated_obls:
                del updated_obls[absorbed_id]

        # Build result list
        merged_obligations = list(updated_obls.values())

        # Build duplicate edges
        edges: list[ObligationGraphEdge] = []
        for absorbed_id, (primary_id, similarity) in merge_map.items():
            edge = ObligationGraphEdge(
                edge_id=f"edge-dup-{uuid.uuid4().hex[:8]}",
                source_obligation_id=primary_id,
                target_obligation_id=absorbed_id,
                edge_type=EdgeType.DUPLICATES,
                weight=similarity,
            )
            edges.append(edge)

        # Calculate dedupe rate
        merged_count = len(merged_obligations)
        dedupe_rate = (original_count - merged_count) / original_count

        return merged_obligations, edges, dedupe_rate
