"""ObligationExtractor module for extracting narrative obligations from passages.

This module implements rule-based extraction (MVP, swappable for LLM) to identify:
- PROPHECY_VISION: Prophecies, visions, dreams, foreshadowings
- CHEKHOV_GUN: Items/weapons introduced with narrative emphasis
- MYSTERY: Unresolved questions and secrets
- PLOT_THREAD: Ongoing plot threads, oaths, promises, journeys

Each obligation MUST have >= 1 evidence anchor (hard gate).
"""

from __future__ import annotations

import hashlib
import re
from re import Pattern
from typing import TYPE_CHECKING

from showrunner.contracts import (
    Entity,
    EntityType,
    EvidenceAnchor,
    Obligation,
    ObligationCategory,
    PassageRecord,
)
from showrunner.providers import RuleBasedProvider

if TYPE_CHECKING:
    from showrunner.providers.base import LLMProviderProtocol


class ObligationExtractor:
    """Extracts narrative obligations from passages with evidence anchors.

    Rule-based extraction (MVP) - patterns are swappable for LLM extraction later.
    Every extracted obligation MUST have at least one evidence anchor for provenance.
    """

    # --- Prophecy/Vision Patterns ---
    PROPHECY_KEYWORDS: list[Pattern[str]] = [
        re.compile(r"\bprophec\w*\b", re.IGNORECASE),
        re.compile(r"\bvision\b", re.IGNORECASE),
        re.compile(r"\bdreams?\b", re.IGNORECASE),
        re.compile(r"\bforetold\b", re.IGNORECASE),
        re.compile(r"\bforeseen\b", re.IGNORECASE),
    ]

    PROPHECY_PHRASES: list[Pattern[str]] = [
        re.compile(r"three heads", re.IGNORECASE),
        re.compile(r"prince that was promised", re.IGNORECASE),
        re.compile(r"azor ahai", re.IGNORECASE),
    ]

    # --- Chekhov's Gun Patterns ---
    CHEKHOV_PATTERNS: list[Pattern[str]] = [
        re.compile(r"\bwould need it later\b", re.IGNORECASE),
        re.compile(r"\bkept it hidden\b", re.IGNORECASE),
        re.compile(r"\bshe kept it hidden\b", re.IGNORECASE),
        re.compile(r"\bhe kept it hidden\b", re.IGNORECASE),
        re.compile(r"\bkeep it hidden\b", re.IGNORECASE),
    ]

    CHEKHOV_ITEM_PATTERNS: list[Pattern[str]] = [
        re.compile(r"\b(sword|blade|dagger|weapon)\b.*\b(valyrian|steel|forged)\b", re.IGNORECASE),
        re.compile(r"\b(valyrian|steel|forged)\b.*\b(sword|blade|dagger|weapon)\b", re.IGNORECASE),
        re.compile(r"\bvial\b.*\b(poison|potion)\b", re.IGNORECASE),
        re.compile(r"\b(poison|potion)\b.*\bvial\b", re.IGNORECASE),
        re.compile(r"\bpoison\b", re.IGNORECASE),
        re.compile(r"\bsword\s+\w+\s+hung\b", re.IGNORECASE),
    ]

    # --- Mystery Patterns ---
    MYSTERY_QUESTIONS: list[Pattern[str]] = [
        re.compile(r"\bwho had\b[^?]*\?", re.IGNORECASE),
        re.compile(r"\bwhy would\b[^?]*\?", re.IGNORECASE),
        re.compile(r"\bwhat was\b[^?]*\?", re.IGNORECASE),
        re.compile(r"\bwho had\b", re.IGNORECASE),  # Also match without question mark in narration
        re.compile(r"\bwhy would\b", re.IGNORECASE),
        re.compile(r"\bwhat was\b", re.IGNORECASE),
    ]

    MYSTERY_KEYWORDS: list[Pattern[str]] = [
        re.compile(r"\bsecret\b", re.IGNORECASE),
        re.compile(r"\bhidden truth\b", re.IGNORECASE),
        re.compile(r"\bno one knew\b", re.IGNORECASE),
        re.compile(r"\btrue parentage\b", re.IGNORECASE),
        re.compile(r"\breal name\b", re.IGNORECASE),
    ]

    # --- Plot Thread Patterns ---
    PLOT_THREAD_OATH_PATTERNS: list[Pattern[str]] = [
        re.compile(r"\bswear\b", re.IGNORECASE),
        re.compile(r"\boath\b", re.IGNORECASE),
        re.compile(r"\bpromise\b", re.IGNORECASE),
        re.compile(r"\bvow\b", re.IGNORECASE),
    ]

    PLOT_THREAD_JOURNEY_PATTERNS: list[Pattern[str]] = [
        re.compile(r"\bset off toward\b", re.IGNORECASE),
        re.compile(r"\bjourney\b.*\b(ahead|long)\b", re.IGNORECASE),
        re.compile(r"\b(ahead|long)\b.*\bjourney\b", re.IGNORECASE),
    ]

    PLOT_THREAD_CONFLICT_PATTERNS: list[Pattern[str]] = [
        re.compile(r"\bwar\b.*\b(inevitable|brewing|coming)\b", re.IGNORECASE),
        re.compile(r"\bconflict\b.*\b(would not|wouldn't|not end)\b", re.IGNORECASE),
    ]

    def __init__(self, provider: LLMProviderProtocol | None = None) -> None:
        """Initialize the ObligationExtractor.

        Args:
            provider: Optional LLM provider (future enhancement).
        """
        self._provider = provider or RuleBasedProvider()

    def extract(
        self,
        passages: list[PassageRecord],
        entities: list[Entity],
    ) -> tuple[list[Obligation], list[EvidenceAnchor]]:
        """Extract obligations from passages with evidence anchors.

        Args:
            passages: List of passage records to analyze
            entities: List of known entities for linking

        Returns:
            Tuple of (obligations list, evidence anchors list)
        """
        if not passages:
            return [], []

        all_results: list[tuple[Obligation, EvidenceAnchor]] = []

        # Extract each category
        all_results.extend(self._extract_prophecies(passages))
        all_results.extend(self._extract_chekhov_guns(passages, entities))
        all_results.extend(self._extract_mysteries(passages))
        all_results.extend(self._extract_plot_threads(passages, entities))

        # Separate obligations and anchors
        obligations = [r[0] for r in all_results]
        anchors = [r[1] for r in all_results]

        return obligations, anchors

    def _extract_prophecies(
        self,
        passages: list[PassageRecord],
    ) -> list[tuple[Obligation, EvidenceAnchor]]:
        """Extract prophecy/vision obligations.

        Patterns:
        - Keywords: prophecy, vision, dream, foretold, foreseen
        - Phrases: three heads, prince that was promised, azor ahai

        Args:
            passages: List of passages to analyze

        Returns:
            List of (Obligation, EvidenceAnchor) tuples
        """
        results: list[tuple[Obligation, EvidenceAnchor]] = []

        for passage in passages:
            text = passage.text

            # Check keyword patterns
            for pattern in self.PROPHECY_KEYWORDS:
                for match in pattern.finditer(text):
                    obligation, anchor = self._create_obligation_with_anchor(
                        passage=passage,
                        match=match,
                        category=ObligationCategory.PROPHECY_VISION,
                        confidence=0.7,
                        description=f"Prophecy/vision reference: '{match.group()}'",
                    )
                    results.append((obligation, anchor))

            # Check phrase patterns (higher confidence)
            for pattern in self.PROPHECY_PHRASES:
                for match in pattern.finditer(text):
                    obligation, anchor = self._create_obligation_with_anchor(
                        passage=passage,
                        match=match,
                        category=ObligationCategory.PROPHECY_VISION,
                        confidence=0.9,
                        description=f"Known prophecy phrase: '{match.group()}'",
                    )
                    results.append((obligation, anchor))

        return results

    def _extract_chekhov_guns(
        self,
        passages: list[PassageRecord],
        entities: list[Entity],
    ) -> list[tuple[Obligation, EvidenceAnchor]]:
        """Extract Chekhov's gun setups (introduced items that may be important).

        Patterns:
        - "would need it later", "kept it hidden"
        - Named weapons with description
        - Poison/vial/letter with emphasis

        Args:
            passages: List of passages to analyze
            entities: Known entities for linking

        Returns:
            List of (Obligation, EvidenceAnchor) tuples
        """
        results: list[tuple[Obligation, EvidenceAnchor]] = []
        artifact_entities = {
            e.entity_id: e for e in entities if e.entity_type == EntityType.ARTIFACT
        }

        for passage in passages:
            text = passage.text

            # Check narrative setup patterns
            for pattern in self.CHEKHOV_PATTERNS:
                for match in pattern.finditer(text):
                    # Find related entities mentioned in passage
                    related_ids = self._find_related_entities(text, artifact_entities)

                    obligation, anchor = self._create_obligation_with_anchor(
                        passage=passage,
                        match=match,
                        category=ObligationCategory.CHEKHOV_GUN,
                        confidence=0.8,
                        description=f"Narrative setup: '{match.group()}'",
                        related_entity_ids=related_ids,
                    )
                    results.append((obligation, anchor))

            # Check item patterns
            for pattern in self.CHEKHOV_ITEM_PATTERNS:
                for match in pattern.finditer(text):
                    related_ids = self._find_related_entities(text, artifact_entities)

                    obligation, anchor = self._create_obligation_with_anchor(
                        passage=passage,
                        match=match,
                        category=ObligationCategory.CHEKHOV_GUN,
                        confidence=0.75,
                        description=f"Significant item: '{match.group()}'",
                        related_entity_ids=related_ids,
                    )
                    results.append((obligation, anchor))

        return results

    def _extract_mysteries(
        self,
        passages: list[PassageRecord],
    ) -> list[tuple[Obligation, EvidenceAnchor]]:
        """Extract unresolved mysteries and questions.

        Patterns:
        - Questions: "Who had...", "Why would...", "What was..."
        - Keywords: secret, hidden truth, no one knew
        - Identity: true parentage, real name

        Args:
            passages: List of passages to analyze

        Returns:
            List of (Obligation, EvidenceAnchor) tuples
        """
        results: list[tuple[Obligation, EvidenceAnchor]] = []

        for passage in passages:
            text = passage.text

            # Check question patterns
            for pattern in self.MYSTERY_QUESTIONS:
                for match in pattern.finditer(text):
                    obligation, anchor = self._create_obligation_with_anchor(
                        passage=passage,
                        match=match,
                        category=ObligationCategory.MYSTERY,
                        confidence=0.75,
                        description=f"Unresolved question: '{match.group()}'",
                    )
                    results.append((obligation, anchor))

            # Check keyword patterns
            for pattern in self.MYSTERY_KEYWORDS:
                for match in pattern.finditer(text):
                    obligation, anchor = self._create_obligation_with_anchor(
                        passage=passage,
                        match=match,
                        category=ObligationCategory.MYSTERY,
                        confidence=0.7,
                        description=f"Mystery keyword: '{match.group()}'",
                    )
                    results.append((obligation, anchor))

        return results

    def _extract_plot_threads(
        self,
        passages: list[PassageRecord],
        entities: list[Entity],
    ) -> list[tuple[Obligation, EvidenceAnchor]]:
        """Extract ongoing plot threads.

        Patterns:
        - Oaths/promises: swear, oath, promise, vow
        - Journeys: set off toward, journey ahead
        - Conflicts: war inevitable, conflict unresolved

        Args:
            passages: List of passages to analyze
            entities: Known entities for linking

        Returns:
            List of (Obligation, EvidenceAnchor) tuples
        """
        results: list[tuple[Obligation, EvidenceAnchor]] = []
        person_entities = {e.entity_id: e for e in entities if e.entity_type == EntityType.PERSON}
        place_entities = {e.entity_id: e for e in entities if e.entity_type == EntityType.PLACE}

        for passage in passages:
            text = passage.text

            # Check oath/promise patterns
            for pattern in self.PLOT_THREAD_OATH_PATTERNS:
                for match in pattern.finditer(text):
                    related_ids = self._find_related_entities(text, person_entities)

                    obligation, anchor = self._create_obligation_with_anchor(
                        passage=passage,
                        match=match,
                        category=ObligationCategory.PLOT_THREAD,
                        confidence=0.75,
                        description=f"Oath/promise: '{match.group()}'",
                        related_entity_ids=related_ids,
                    )
                    results.append((obligation, anchor))

            # Check journey patterns
            for pattern in self.PLOT_THREAD_JOURNEY_PATTERNS:
                for match in pattern.finditer(text):
                    related_ids = self._find_related_entities(text, place_entities)

                    obligation, anchor = self._create_obligation_with_anchor(
                        passage=passage,
                        match=match,
                        category=ObligationCategory.PLOT_THREAD,
                        confidence=0.7,
                        description=f"Journey thread: '{match.group()}'",
                        related_entity_ids=related_ids,
                    )
                    results.append((obligation, anchor))

            # Check conflict patterns
            for pattern in self.PLOT_THREAD_CONFLICT_PATTERNS:
                for match in pattern.finditer(text):
                    obligation, anchor = self._create_obligation_with_anchor(
                        passage=passage,
                        match=match,
                        category=ObligationCategory.PLOT_THREAD,
                        confidence=0.7,
                        description=f"Unresolved conflict: '{match.group()}'",
                    )
                    results.append((obligation, anchor))

        return results

    def _create_obligation_with_anchor(
        self,
        passage: PassageRecord,
        match: re.Match[str],
        category: ObligationCategory,
        confidence: float,
        description: str,
        related_entity_ids: list[str] | None = None,
    ) -> tuple[Obligation, EvidenceAnchor]:
        """Create an obligation and its evidence anchor from a regex match.

        Args:
            passage: The source passage
            match: The regex match object
            category: Obligation category
            confidence: Confidence score (0-1)
            description: Human-readable description
            related_entity_ids: Optional list of related entity IDs

        Returns:
            Tuple of (Obligation, EvidenceAnchor)
        """
        # Generate stable IDs based on content
        anchor_id = self._generate_anchor_id(passage.passage_id, match.start(), match.end())
        obligation_id = self._generate_obligation_id(category, passage.passage_id, match.group())

        # Create evidence anchor
        anchor = EvidenceAnchor(
            anchor_id=anchor_id,
            passage_id=passage.passage_id,
            char_start=match.start(),
            char_end=match.end(),
            excerpt=match.group(),
        )

        # Create obligation
        obligation = Obligation(
            obligation_id=obligation_id,
            category=category,
            description=description,
            evidence_anchor_ids=[anchor_id],
            last_seen_passage_id=passage.passage_id,
            confidence=confidence,
            is_resolved=False,
            resolution_passage_id=None,
            related_entity_ids=related_entity_ids or [],
        )

        return obligation, anchor

    def _generate_obligation_id(
        self,
        category: ObligationCategory,
        passage_id: str,
        matched_text: str,
    ) -> str:
        """Generate a stable, deterministic obligation ID.

        The ID is derived from the category, passage, and matched text
        to ensure the same input always produces the same ID.

        Args:
            category: Obligation category
            passage_id: Source passage ID
            matched_text: The matched text excerpt

        Returns:
            Stable obligation ID with 'obl_' prefix
        """
        content = f"{category.value}:{passage_id}:{matched_text.lower()}"
        hash_digest = hashlib.sha256(content.encode()).hexdigest()[:12]
        return f"obl_{hash_digest}"

    def _generate_anchor_id(
        self,
        passage_id: str,
        char_start: int,
        char_end: int,
    ) -> str:
        """Generate a stable, deterministic anchor ID.

        The ID is derived from the passage and character positions.

        Args:
            passage_id: Source passage ID
            char_start: Start character offset
            char_end: End character offset

        Returns:
            Stable anchor ID with 'anc_' prefix
        """
        content = f"{passage_id}:{char_start}:{char_end}"
        hash_digest = hashlib.sha256(content.encode()).hexdigest()[:12]
        return f"anc_{hash_digest}"

    def _find_related_entities(
        self,
        text: str,
        entities: dict[str, Entity],
    ) -> list[str]:
        """Find entities mentioned in the text.

        Simple substring matching for MVP - can be enhanced with fuzzy matching.

        Args:
            text: Text to search
            entities: Dict of entity_id -> Entity to search for

        Returns:
            List of matching entity IDs
        """
        related: list[str] = []
        text_lower = text.lower()

        for entity_id, entity in entities.items():
            if entity.canonical_name.lower() in text_lower:
                related.append(entity_id)

        return related
