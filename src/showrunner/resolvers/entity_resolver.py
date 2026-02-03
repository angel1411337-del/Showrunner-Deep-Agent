"""Entity resolution module for the Showrunner Orchestrator.

This module provides rule-based NER (Named Entity Recognition) for extracting
and resolving entities from passages. It supports:
- Entity extraction using regex patterns
- Alias table building for entity variants
- Human override rules (human wins policy)
- Entity type tagging (PERSON, PLACE, GROUP, TITLE, ARTIFACT, VEHICLE)
- Vehicle limiting rule (threshold-based creation)
"""

import re
import uuid
from collections import defaultdict
from dataclasses import dataclass, field

from showrunner.contracts import (
    PassageRecord,
    Entity,
    EntityType,
    AliasEntry,
    OverrideRule,
    OverrideAction,
    EvidenceAnchor,
)


# Known artifacts list (swords, weapons, significant items)
KNOWN_ARTIFACTS = {
    "Ice",
    "Longclaw",
    "Needle",
    "Oathkeeper",
    "Widow's Wail",
    "Dawn",
    "Heartsbane",
    "Blackfyre",
    "Dark Sister",
    "Lightbringer",
    "Catspaw",
    "Iron Throne",
}

# Common words to exclude from entity extraction
COMMON_WORDS = {
    "The",
    "A",
    "An",
    "He",
    "She",
    "It",
    "They",
    "We",
    "You",
    "I",
    "His",
    "Her",
    "Their",
    "My",
    "Your",
    "This",
    "That",
    "These",
    "Those",
    "And",
    "But",
    "Or",
    "If",
    "Then",
    "When",
    "Where",
    "What",
    "Who",
    "How",
    "Why",
    "All",
    "Some",
    "Any",
    "No",
    "Not",
    "Yes",
}

# Known place indicators
PLACE_INDICATORS = {
    "Winterfell",
    "Braavos",
    "Pentos",
    "Meereen",
    "Astapor",
    "Yunkai",
    "Volantis",
    "Dorne",
    "Highgarden",
    "Casterly Rock",
    "Storm's End",
    "Dragonstone",
    "Harrenhal",
    "The Eyrie",
    "Riverrun",
    "Pyke",
    "Oldtown",
    "Sunspear",
    "The Twins",
}


@dataclass
class MentionInfo:
    """Tracks information about entity mentions during extraction."""

    canonical_name: str
    entity_type: EntityType
    first_seen_passage: str
    first_seen_order: int
    mention_count: int = 1
    is_important: bool = False
    mentions: list[tuple[str, int, int, str]] = field(default_factory=list)
    # List of (passage_id, char_start, char_end, excerpt)


class EntityResolver:
    """Resolves entities from passages using rule-based NER.

    Supports entity extraction, alias building, human overrides,
    and the vehicle limiting rule.
    """

    def __init__(self, vehicle_min_mentions: int = 3) -> None:
        """Initialize the entity resolver.

        Args:
            vehicle_min_mentions: Minimum mentions required for vehicle entities
                                  to be created (default 3).
        """
        self.vehicle_min_mentions = vehicle_min_mentions
        self._overrides: list[OverrideRule] = []
        self._ignored_aliases: set[str] = set()
        self._forced_assignments: dict[str, str] = {}  # alias -> entity_id

    def add_override(self, override: OverrideRule) -> None:
        """Register a human override rule.

        Args:
            override: The override rule to add.
        """
        self._overrides.append(override)

        if override.action == OverrideAction.IGNORE:
            self._ignored_aliases.add(override.target_alias)
        elif override.action == OverrideAction.ASSIGN:
            if override.target_entity_id:
                self._forced_assignments[override.target_alias] = (
                    override.target_entity_id
                )

    def _generate_id(self, prefix: str) -> str:
        """Generate a unique ID with prefix."""
        return f"{prefix}_{uuid.uuid4().hex[:8]}"

    def _is_ignored(self, text: str) -> bool:
        """Check if text should be ignored due to override."""
        return text in self._ignored_aliases

    def _extract_title_patterns(
        self, text: str, passage_id: str, passage_order: int
    ) -> list[MentionInfo]:
        """Extract title patterns like 'Lord of X', 'King of X', etc."""
        mentions = []

        # Title patterns
        patterns = [
            (r"\bLord of (?:the )?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", "Lord of"),
            (r"\bKing of (?:the )?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", "King of"),
            (r"\bQueen of (?:the )?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", "Queen of"),
            (r"\bHand of the King\b", "Hand of the King"),
        ]

        for pattern, prefix in patterns:
            for match in re.finditer(pattern, text):
                matched_text = match.group(0)
                if self._is_ignored(matched_text):
                    continue

                char_start = match.start()
                char_end = match.end()

                info = MentionInfo(
                    canonical_name=matched_text,
                    entity_type=EntityType.TITLE,
                    first_seen_passage=passage_id,
                    first_seen_order=passage_order,
                    mentions=[(passage_id, char_start, char_end, matched_text)],
                )
                mentions.append(info)

        return mentions

    def _extract_house_patterns(
        self, text: str, passage_id: str, passage_order: int
    ) -> list[MentionInfo]:
        """Extract House patterns like 'House Stark'."""
        mentions = []

        pattern = r"\bHouse ([A-Z][a-z]+)\b"
        for match in re.finditer(pattern, text):
            matched_text = match.group(0)
            if self._is_ignored(matched_text):
                continue

            char_start = match.start()
            char_end = match.end()

            info = MentionInfo(
                canonical_name=matched_text,
                entity_type=EntityType.GROUP,
                first_seen_passage=passage_id,
                first_seen_order=passage_order,
                mentions=[(passage_id, char_start, char_end, matched_text)],
            )
            mentions.append(info)

        return mentions

    def _extract_artifact_patterns(
        self, text: str, passage_id: str, passage_order: int
    ) -> list[MentionInfo]:
        """Extract known artifact names."""
        mentions = []

        for artifact in KNOWN_ARTIFACTS:
            pattern = rf"\b{re.escape(artifact)}\b"
            for match in re.finditer(pattern, text):
                if self._is_ignored(artifact):
                    continue

                char_start = match.start()
                char_end = match.end()

                info = MentionInfo(
                    canonical_name=artifact,
                    entity_type=EntityType.ARTIFACT,
                    first_seen_passage=passage_id,
                    first_seen_order=passage_order,
                    mentions=[(passage_id, char_start, char_end, artifact)],
                )
                mentions.append(info)

        return mentions

    def _extract_place_patterns(
        self, text: str, passage_id: str, passage_order: int
    ) -> list[MentionInfo]:
        """Extract place patterns including 'The Wall' and named locations."""
        mentions = []

        # The Wall special case
        pattern = r"\bThe Wall\b"
        for match in re.finditer(pattern, text):
            matched_text = match.group(0)
            if self._is_ignored(matched_text):
                continue

            char_start = match.start()
            char_end = match.end()

            info = MentionInfo(
                canonical_name=matched_text,
                entity_type=EntityType.PLACE,
                first_seen_passage=passage_id,
                first_seen_order=passage_order,
                mentions=[(passage_id, char_start, char_end, matched_text)],
            )
            mentions.append(info)

        # King's Landing (special apostrophe handling)
        pattern = r"\bKing's Landing\b"
        for match in re.finditer(pattern, text):
            matched_text = match.group(0)
            if self._is_ignored(matched_text):
                continue

            char_start = match.start()
            char_end = match.end()

            info = MentionInfo(
                canonical_name=matched_text,
                entity_type=EntityType.PLACE,
                first_seen_passage=passage_id,
                first_seen_order=passage_order,
                mentions=[(passage_id, char_start, char_end, matched_text)],
            )
            mentions.append(info)

        # Extract known single-word place names
        for place in PLACE_INDICATORS:
            if " " not in place and "'" not in place:  # Single word places
                pattern = rf"\b{re.escape(place)}\b"
                for match in re.finditer(pattern, text):
                    matched_text = match.group(0)
                    if self._is_ignored(matched_text):
                        continue

                    char_start = match.start()
                    char_end = match.end()

                    info = MentionInfo(
                        canonical_name=matched_text,
                        entity_type=EntityType.PLACE,
                        first_seen_passage=passage_id,
                        first_seen_order=passage_order,
                        mentions=[(passage_id, char_start, char_end, matched_text)],
                    )
                    mentions.append(info)

        return mentions

    def _extract_vehicle_patterns(
        self, text: str, passage_id: str, passage_order: int
    ) -> list[MentionInfo]:
        """Extract potential vehicle (ship) names."""
        mentions = []

        # Pattern: "The <Capitalized Name>" or "the <Capitalized Name>"
        ship_pattern = r"\b[Tt]he ([A-Z][a-z]+(?: [A-Z][a-z]+)*)\b"

        for match in re.finditer(ship_pattern, text):
            full_match = match.group(0)
            name_part = match.group(1)

            # Normalize to "The X" format
            canonical_name = "The " + name_part

            if self._is_ignored(canonical_name):
                continue

            # Check if this looks like a ship reference
            context_before = text[max(0, match.start() - 100) : match.start()].lower()
            context_after = text[match.end() : match.end() + 100].lower()
            full_context = context_before + " " + text[match.start():match.end()].lower() + " " + context_after

            ship_indicators = [
                "sail",
                "sailed",
                "sailing",
                "ship",
                "aboard",
                "board",
                "boarded",
                "captain",
                "deck",
                "port",
                "harbor",
                "harbour",
                "voyage",
                "seas",
                "storm",
                "fleet",
                "vessel",
                "anchor",
            ]
            is_ship = any(ind in full_context for ind in ship_indicators)

            if is_ship:
                char_start = match.start()
                char_end = match.end()

                info = MentionInfo(
                    canonical_name=canonical_name,
                    entity_type=EntityType.VEHICLE,
                    first_seen_passage=passage_id,
                    first_seen_order=passage_order,
                    mentions=[(passage_id, char_start, char_end, full_match)],
                )
                mentions.append(info)

        return mentions

    def _extract_capitalized_sequences(
        self, text: str, passage_id: str, passage_order: int
    ) -> list[MentionInfo]:
        """Extract capitalized word sequences as potential person/place names."""
        mentions = []

        # Pattern for capitalized sequences (2+ words)
        # Also handles "Name the Epithet" patterns like "Aegon the Conqueror"
        pattern = r"\b([A-Z][a-z]+(?:\s+(?:the\s+)?[A-Z][a-z]+)+)\b"

        for match in re.finditer(pattern, text):
            matched_text = match.group(0)
            if self._is_ignored(matched_text):
                continue

            # Skip if starts with common word
            first_word = matched_text.split()[0]
            if first_word in COMMON_WORDS:
                continue

            # Skip if this is a House pattern (handled separately)
            if matched_text.startswith("House "):
                continue

            char_start = match.start()
            char_end = match.end()

            # Determine entity type
            entity_type = EntityType.PERSON  # Default for named sequences

            # Check if it's a known place
            if matched_text in PLACE_INDICATORS:
                entity_type = EntityType.PLACE

            info = MentionInfo(
                canonical_name=matched_text,
                entity_type=entity_type,
                first_seen_passage=passage_id,
                first_seen_order=passage_order,
                mentions=[(passage_id, char_start, char_end, matched_text)],
            )
            mentions.append(info)

        # Also extract "Name the Epithet" style names explicitly
        epithet_pattern = r"\b([A-Z][a-z]+) the ([A-Z][a-z]+)\b"
        for match in re.finditer(epithet_pattern, text):
            matched_text = match.group(0)
            if self._is_ignored(matched_text):
                continue

            char_start = match.start()
            char_end = match.end()

            info = MentionInfo(
                canonical_name=matched_text,
                entity_type=EntityType.PERSON,
                first_seen_passage=passage_id,
                first_seen_order=passage_order,
                mentions=[(passage_id, char_start, char_end, matched_text)],
            )
            mentions.append(info)

        return mentions

    def _merge_mentions(
        self, all_mentions: list[MentionInfo]
    ) -> dict[str, MentionInfo]:
        """Merge mentions of the same entity into single entries."""
        merged: dict[str, MentionInfo] = {}

        for mention in all_mentions:
            key = mention.canonical_name

            if key in merged:
                existing = merged[key]
                existing.mention_count += mention.mention_count
                existing.mentions.extend(mention.mentions)
                # Keep earliest first_seen
                if mention.first_seen_order < existing.first_seen_order:
                    existing.first_seen_passage = mention.first_seen_passage
                    existing.first_seen_order = mention.first_seen_order
            else:
                merged[key] = mention

        return merged

    def _apply_vehicle_threshold(
        self, mentions: dict[str, MentionInfo]
    ) -> dict[str, MentionInfo]:
        """Apply vehicle limiting rule - filter out vehicles below threshold."""
        filtered = {}

        for key, mention in mentions.items():
            if mention.entity_type == EntityType.VEHICLE:
                # Check if marked important via override
                is_important = key in self._forced_assignments
                if mention.mention_count >= self.vehicle_min_mentions or is_important:
                    mention.is_important = is_important
                    filtered[key] = mention
            else:
                filtered[key] = mention

        return filtered

    def extract_entities(self, passages: list[PassageRecord]) -> list[Entity]:
        """Extract entities from passages using rule-based NER.

        Args:
            passages: List of passages to extract entities from.

        Returns:
            List of deduplicated Entity objects.
        """
        all_mentions: list[MentionInfo] = []

        for order, passage in enumerate(passages):
            text = passage.text
            passage_id = passage.passage_id

            # Extract different entity types
            all_mentions.extend(
                self._extract_title_patterns(text, passage_id, order)
            )
            all_mentions.extend(
                self._extract_house_patterns(text, passage_id, order)
            )
            all_mentions.extend(
                self._extract_artifact_patterns(text, passage_id, order)
            )
            all_mentions.extend(
                self._extract_place_patterns(text, passage_id, order)
            )
            all_mentions.extend(
                self._extract_vehicle_patterns(text, passage_id, order)
            )
            all_mentions.extend(
                self._extract_capitalized_sequences(text, passage_id, order)
            )

        # Merge duplicate mentions
        merged = self._merge_mentions(all_mentions)

        # Apply vehicle threshold
        filtered = self._apply_vehicle_threshold(merged)

        # Convert to Entity objects
        entities = []
        for canonical_name, mention in filtered.items():
            entity_id = self._generate_id("entity")

            # Check if there's a forced assignment for this name
            if canonical_name in self._forced_assignments:
                entity_id = self._forced_assignments[canonical_name]

            entity = Entity(
                entity_id=entity_id,
                canonical_name=mention.canonical_name,
                entity_type=mention.entity_type,
                first_seen_passage=mention.first_seen_passage,
                mention_count=mention.mention_count,
                is_important=mention.is_important,
            )
            entities.append(entity)

        # Sort by entity_id for deterministic ordering
        entities.sort(key=lambda e: e.entity_id)

        return entities

    def build_alias_table(
        self, entities: list[Entity], passages: list[PassageRecord]
    ) -> list[AliasEntry]:
        """Build alias mappings for entity variants.

        Args:
            entities: List of canonical entities.
            passages: Original passages for context.

        Returns:
            List of AliasEntry objects mapping variants to canonical entities.
        """
        aliases: list[AliasEntry] = []
        entity_map = {e.canonical_name: e for e in entities}

        for entity in entities:
            # Check for forced assignment override
            if entity.canonical_name in self._forced_assignments:
                alias = AliasEntry(
                    alias_id=self._generate_id("alias"),
                    alias_text=entity.canonical_name,
                    entity_id=self._forced_assignments[entity.canonical_name],
                    confidence=1.0,
                )
                aliases.append(alias)
            else:
                # Create alias for canonical name itself
                alias = AliasEntry(
                    alias_id=self._generate_id("alias"),
                    alias_text=entity.canonical_name,
                    entity_id=entity.entity_id,
                    confidence=1.0,
                )
                aliases.append(alias)

            # Create aliases for partial names (e.g., "Jon" for "Jon Snow")
            name_parts = entity.canonical_name.split()
            if len(name_parts) > 1:
                # First name alias
                first_name = name_parts[0]
                if first_name not in COMMON_WORDS and first_name not in entity_map:
                    alias = AliasEntry(
                        alias_id=self._generate_id("alias"),
                        alias_text=first_name,
                        entity_id=entity.entity_id,
                        confidence=0.8,
                    )
                    aliases.append(alias)

                # Last name alias (for persons)
                if entity.entity_type == EntityType.PERSON and len(name_parts) >= 2:
                    last_name = name_parts[-1]
                    if last_name not in COMMON_WORDS:
                        alias = AliasEntry(
                            alias_id=self._generate_id("alias"),
                            alias_text=last_name,
                            entity_id=entity.entity_id,
                            confidence=0.7,
                        )
                        aliases.append(alias)

        # Sort aliases by alias_id for deterministic ordering
        aliases.sort(key=lambda a: a.alias_id)

        return aliases

    def _build_evidence_anchors(
        self, passages: list[PassageRecord], mentions: dict[str, MentionInfo]
    ) -> list[EvidenceAnchor]:
        """Build evidence anchors for entity mentions.

        Args:
            passages: Source passages.
            mentions: Merged mention information.

        Returns:
            List of EvidenceAnchor objects.
        """
        anchors: list[EvidenceAnchor] = []

        for mention in mentions.values():
            for passage_id, char_start, char_end, excerpt in mention.mentions:
                anchor = EvidenceAnchor(
                    anchor_id=self._generate_id("anchor"),
                    passage_id=passage_id,
                    char_start=char_start,
                    char_end=char_end,
                    excerpt=excerpt,
                )
                anchors.append(anchor)

        return anchors

    def resolve(
        self, passages: list[PassageRecord]
    ) -> tuple[list[Entity], list[AliasEntry], list[EvidenceAnchor]]:
        """Full resolution pipeline returning entities, aliases, and evidence anchors.

        Args:
            passages: List of passages to process.

        Returns:
            Tuple of (entities, aliases, evidence_anchors).
        """
        if not passages:
            return [], [], []

        # Extract all mentions
        all_mentions: list[MentionInfo] = []

        for order, passage in enumerate(passages):
            text = passage.text
            passage_id = passage.passage_id

            all_mentions.extend(
                self._extract_title_patterns(text, passage_id, order)
            )
            all_mentions.extend(
                self._extract_house_patterns(text, passage_id, order)
            )
            all_mentions.extend(
                self._extract_artifact_patterns(text, passage_id, order)
            )
            all_mentions.extend(
                self._extract_place_patterns(text, passage_id, order)
            )
            all_mentions.extend(
                self._extract_vehicle_patterns(text, passage_id, order)
            )
            all_mentions.extend(
                self._extract_capitalized_sequences(text, passage_id, order)
            )

        # Merge and filter
        merged = self._merge_mentions(all_mentions)
        filtered = self._apply_vehicle_threshold(merged)

        # Build entities
        entities = []
        for canonical_name, mention in filtered.items():
            entity_id = self._generate_id("entity")

            if canonical_name in self._forced_assignments:
                entity_id = self._forced_assignments[canonical_name]

            entity = Entity(
                entity_id=entity_id,
                canonical_name=mention.canonical_name,
                entity_type=mention.entity_type,
                first_seen_passage=mention.first_seen_passage,
                mention_count=mention.mention_count,
                is_important=mention.is_important,
            )
            entities.append(entity)

        entities.sort(key=lambda e: e.entity_id)

        # Build alias table
        aliases = self.build_alias_table(entities, passages)

        # Build evidence anchors
        anchors = self._build_evidence_anchors(passages, filtered)

        return entities, aliases, anchors
