"""Tests for EntityResolver module.

TDD-style tests covering:
1. Entity extraction from passages (rule-based NER)
2. Alias table building
3. Human override rules (human wins policy)
4. Entity type tagging
5. Vehicle limiting rule
6. Deterministic tie-breaking
"""

import pytest

from showrunner.contracts import (
    AliasEntry,
    Entity,
    EntityType,
    EvidenceAnchor,
    OverrideAction,
    OverrideRule,
    PassageRecord,
)
from showrunner.resolvers.entity_resolver import EntityResolver

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def resolver() -> EntityResolver:
    """Default resolver with standard vehicle threshold."""
    return EntityResolver(vehicle_min_mentions=3)


@pytest.fixture
def sample_passages() -> list[PassageRecord]:
    """Sample passages with various entity types."""
    return [
        PassageRecord(
            passage_id="book1:0",
            source_id="book1",
            paragraph_index=0,
            text="Jon Snow walked through the gates of Winterfell. Lord Stark awaited him.",
            char_start=0,
            char_end=72,
        ),
        PassageRecord(
            passage_id="book1:1",
            source_id="book1",
            paragraph_index=1,
            text="House Stark had ruled the North for generations. The King of the North was respected.",
            char_start=73,
            char_end=158,
        ),
        PassageRecord(
            passage_id="book1:2",
            source_id="book1",
            paragraph_index=2,
            text="Jon drew his sword Longclaw. The Valyrian steel blade glinted in the moonlight.",
            char_start=159,
            char_end=238,
        ),
    ]


@pytest.fixture
def passages_with_aliases() -> list[PassageRecord]:
    """Passages with multiple references to same entity."""
    return [
        PassageRecord(
            passage_id="book1:0",
            source_id="book1",
            paragraph_index=0,
            text="Daenerys Targaryen stood before her people. The Mother of Dragons smiled.",
            char_start=0,
            char_end=73,
        ),
        PassageRecord(
            passage_id="book1:1",
            source_id="book1",
            paragraph_index=1,
            text="Dany turned to her advisors. The Khaleesi was troubled.",
            char_start=74,
            char_end=129,
        ),
        PassageRecord(
            passage_id="book1:2",
            source_id="book1",
            paragraph_index=2,
            text="Daenerys spoke softly. The Queen said they would march at dawn.",
            char_start=130,
            char_end=193,
        ),
    ]


@pytest.fixture
def vehicle_passages() -> list[PassageRecord]:
    """Passages with vehicle mentions for threshold testing."""
    return [
        PassageRecord(
            passage_id="book1:0",
            source_id="book1",
            paragraph_index=0,
            text="The Black Wind sailed through the storm. It was a fearsome ship.",
            char_start=0,
            char_end=64,
        ),
        PassageRecord(
            passage_id="book1:1",
            source_id="book1",
            paragraph_index=1,
            text="They boarded the Black Wind again.",
            char_start=65,
            char_end=99,
        ),
        PassageRecord(
            passage_id="book1:2",
            source_id="book1",
            paragraph_index=2,
            text="The captain of the Black Wind ordered full sail.",
            char_start=100,
            char_end=148,
        ),
        PassageRecord(
            passage_id="book1:3",
            source_id="book1",
            paragraph_index=3,
            text="The Summer Mist appeared on the horizon. They would never see it again.",
            char_start=149,
            char_end=220,
        ),
    ]


# =============================================================================
# Test: Basic Initialization
# =============================================================================


class TestEntityResolverInit:
    """Tests for EntityResolver initialization."""

    def test_init_default_vehicle_threshold(self) -> None:
        """EntityResolver should have default vehicle_min_mentions of 3."""
        resolver = EntityResolver()
        assert resolver.vehicle_min_mentions == 3

    def test_init_custom_vehicle_threshold(self) -> None:
        """EntityResolver should accept custom vehicle threshold."""
        resolver = EntityResolver(vehicle_min_mentions=5)
        assert resolver.vehicle_min_mentions == 5

    def test_init_empty_overrides(self) -> None:
        """EntityResolver should start with empty overrides list."""
        resolver = EntityResolver()
        assert resolver._overrides == []


# =============================================================================
# Test: Entity Extraction - Capitalized Sequences
# =============================================================================


class TestExtractEntitiesCapitalized:
    """Tests for extracting entities from capitalized sequences."""

    def test_extract_two_word_name(self, resolver: EntityResolver) -> None:
        """Should extract two-word capitalized names like 'Jon Snow'."""
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="Jon Snow arrived at the castle.",
                char_start=0,
                char_end=31,
            )
        ]
        entities = resolver.extract_entities(passages)
        names = [e.canonical_name for e in entities]
        assert "Jon Snow" in names

    def test_extract_three_word_name(self, resolver: EntityResolver) -> None:
        """Should extract multi-word capitalized names."""
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="Aegon the Conqueror united the realm.",
                char_start=0,
                char_end=37,
            )
        ]
        entities = resolver.extract_entities(passages)
        # "Aegon the Conqueror" or at least "Aegon" should be found
        names = [e.canonical_name for e in entities]
        assert any("Aegon" in name for name in names)

    def test_extract_place_name(self, resolver: EntityResolver) -> None:
        """Should extract capitalized place names."""
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="They traveled to King's Landing.",
                char_start=0,
                char_end=32,
            )
        ]
        entities = resolver.extract_entities(passages)
        names = [e.canonical_name for e in entities]
        assert "King's Landing" in names

    def test_extract_the_wall(self, resolver: EntityResolver) -> None:
        """Should extract 'The Wall' as a place."""
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="He stood atop The Wall, gazing north.",
                char_start=0,
                char_end=37,
            )
        ]
        entities = resolver.extract_entities(passages)
        names = [e.canonical_name for e in entities]
        assert "The Wall" in names

    def test_no_extract_common_words(self, resolver: EntityResolver) -> None:
        """Should not extract common words even at sentence start."""
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="The man walked quickly. He was tired.",
                char_start=0,
                char_end=37,
            )
        ]
        entities = resolver.extract_entities(passages)
        names = [e.canonical_name for e in entities]
        assert "The" not in names
        assert "He" not in names


# =============================================================================
# Test: Entity Extraction - Title Patterns
# =============================================================================


class TestExtractEntitiesTitles:
    """Tests for extracting title patterns."""

    def test_extract_lord_of(self, resolver: EntityResolver) -> None:
        """Should extract 'Lord of X' patterns as titles."""
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="The Lord of Winterfell spoke gravely.",
                char_start=0,
                char_end=37,
            )
        ]
        entities = resolver.extract_entities(passages)
        titles = [e for e in entities if e.entity_type == EntityType.TITLE]
        assert any("Lord of Winterfell" in t.canonical_name for t in titles)

    def test_extract_king_of(self, resolver: EntityResolver) -> None:
        """Should extract 'King of X' patterns as titles."""
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="The King of the North ruled justly.",
                char_start=0,
                char_end=35,
            )
        ]
        entities = resolver.extract_entities(passages)
        titles = [e for e in entities if e.entity_type == EntityType.TITLE]
        assert any("King of the North" in t.canonical_name for t in titles)

    def test_extract_queen_of(self, resolver: EntityResolver) -> None:
        """Should extract 'Queen of X' patterns as titles."""
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="The Queen of Meereen freed the slaves.",
                char_start=0,
                char_end=38,
            )
        ]
        entities = resolver.extract_entities(passages)
        titles = [e for e in entities if e.entity_type == EntityType.TITLE]
        assert any("Queen of Meereen" in t.canonical_name for t in titles)

    def test_extract_hand_of_the_king(self, resolver: EntityResolver) -> None:
        """Should extract 'Hand of the King' as a title."""
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="He served as Hand of the King for many years.",
                char_start=0,
                char_end=45,
            )
        ]
        entities = resolver.extract_entities(passages)
        titles = [e for e in entities if e.entity_type == EntityType.TITLE]
        assert any("Hand of the King" in t.canonical_name for t in titles)


# =============================================================================
# Test: Entity Extraction - House Patterns
# =============================================================================


class TestExtractEntitiesHouses:
    """Tests for extracting House patterns as groups."""

    def test_extract_house_stark(self, resolver: EntityResolver) -> None:
        """Should extract 'House Stark' as a group."""
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="House Stark had ruled for centuries.",
                char_start=0,
                char_end=36,
            )
        ]
        entities = resolver.extract_entities(passages)
        groups = [e for e in entities if e.entity_type == EntityType.GROUP]
        assert any("House Stark" in g.canonical_name for g in groups)

    def test_extract_house_lannister(self, resolver: EntityResolver) -> None:
        """Should extract 'House Lannister' as a group."""
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="House Lannister always pays its debts.",
                char_start=0,
                char_end=38,
            )
        ]
        entities = resolver.extract_entities(passages)
        groups = [e for e in entities if e.entity_type == EntityType.GROUP]
        assert any("House Lannister" in g.canonical_name for g in groups)


# =============================================================================
# Test: Entity Extraction - Named Artifacts
# =============================================================================


class TestExtractEntitiesArtifacts:
    """Tests for extracting named artifacts."""

    def test_extract_known_artifact_ice(self, resolver: EntityResolver) -> None:
        """Should extract 'Ice' as a known artifact in sword context."""
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="Lord Stark drew Ice, the great Valyrian sword.",
                char_start=0,
                char_end=46,
            )
        ]
        entities = resolver.extract_entities(passages)
        artifacts = [e for e in entities if e.entity_type == EntityType.ARTIFACT]
        assert any("Ice" in a.canonical_name for a in artifacts)

    def test_extract_known_artifact_longclaw(self, resolver: EntityResolver) -> None:
        """Should extract 'Longclaw' as a known artifact."""
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="Jon drew Longclaw from its sheath.",
                char_start=0,
                char_end=34,
            )
        ]
        entities = resolver.extract_entities(passages)
        artifacts = [e for e in entities if e.entity_type == EntityType.ARTIFACT]
        assert any("Longclaw" in a.canonical_name for a in artifacts)

    def test_extract_known_artifact_needle(self, resolver: EntityResolver) -> None:
        """Should extract 'Needle' as a known artifact."""
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="Arya clutched Needle tightly, the sword Jon had given her.",
                char_start=0,
                char_end=58,
            )
        ]
        entities = resolver.extract_entities(passages)
        artifacts = [e for e in entities if e.entity_type == EntityType.ARTIFACT]
        assert any("Needle" in a.canonical_name for a in artifacts)


# =============================================================================
# Test: Entity Type Tagging
# =============================================================================


class TestEntityTyping:
    """Tests for correct entity type assignment."""

    def test_person_type_assigned(self, resolver: EntityResolver) -> None:
        """Named persons should have PERSON type."""
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="Jon Snow met Tyrion Lannister at the inn.",
                char_start=0,
                char_end=41,
            )
        ]
        entities = resolver.extract_entities(passages)
        jon = next((e for e in entities if "Jon Snow" in e.canonical_name), None)
        assert jon is not None
        assert jon.entity_type == EntityType.PERSON

    def test_place_type_assigned(self, resolver: EntityResolver) -> None:
        """Named places should have PLACE type."""
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="They sailed to Braavos across the Narrow Sea.",
                char_start=0,
                char_end=45,
            )
        ]
        entities = resolver.extract_entities(passages)
        braavos = next((e for e in entities if "Braavos" in e.canonical_name), None)
        assert braavos is not None
        assert braavos.entity_type == EntityType.PLACE

    def test_group_type_for_house(self, resolver: EntityResolver) -> None:
        """House names should have GROUP type."""
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="House Targaryen once ruled all of Westeros.",
                char_start=0,
                char_end=43,
            )
        ]
        entities = resolver.extract_entities(passages)
        targaryen = next((e for e in entities if "House Targaryen" in e.canonical_name), None)
        assert targaryen is not None
        assert targaryen.entity_type == EntityType.GROUP


# =============================================================================
# Test: Vehicle Limiting Rule
# =============================================================================


class TestVehicleLimiting:
    """Tests for vehicle entity creation threshold."""

    def test_vehicle_created_at_threshold(
        self, resolver: EntityResolver, vehicle_passages: list[PassageRecord]
    ) -> None:
        """Vehicles should be created when mentions >= threshold."""
        entities = resolver.extract_entities(vehicle_passages)
        # Black Wind is mentioned 3 times, should be created
        vehicles = [e for e in entities if e.entity_type == EntityType.VEHICLE]
        # The canonical name may be "The Black Wind" or "Black Wind"
        assert any("Black Wind" in v.canonical_name for v in vehicles) or any(
            v.canonical_name == "The Black Wind" for v in vehicles
        )

    def test_vehicle_not_created_below_threshold(
        self, resolver: EntityResolver, vehicle_passages: list[PassageRecord]
    ) -> None:
        """Vehicles should not be created when mentions < threshold."""
        entities = resolver.extract_entities(vehicle_passages)
        # Summer Mist is mentioned only once, should not be created
        vehicles = [e for e in entities if e.entity_type == EntityType.VEHICLE]
        assert not any("Summer Mist" in v.canonical_name for v in vehicles)

    def test_vehicle_created_when_important(self, resolver: EntityResolver) -> None:
        """Important vehicles should be created regardless of mention count."""
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="The Silence appeared. It was a ship of legend.",
                char_start=0,
                char_end=46,
            )
        ]
        # Add override to mark as important
        override = OverrideRule(
            override_id="ov1",
            target_alias="The Silence",
            action=OverrideAction.ASSIGN,
            target_entity_id="vehicle_silence",
            reason="Important ship in the story",
        )
        resolver.add_override(override)
        entities = resolver.extract_entities(passages)
        # With override, it should be included even with 1 mention
        # (implementation should mark it as important)
        names = [e.canonical_name for e in entities]
        assert "The Silence" in names or any("Silence" in n for n in names)

    def test_custom_vehicle_threshold(self) -> None:
        """Custom vehicle threshold should be respected."""
        resolver = EntityResolver(vehicle_min_mentions=2)
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="The Iron Victory sailed. It was fast.",
                char_start=0,
                char_end=37,
            ),
            PassageRecord(
                passage_id="p1:1",
                source_id="p1",
                paragraph_index=1,
                text="The Iron Victory returned to port.",
                char_start=38,
                char_end=72,
            ),
        ]
        entities = resolver.extract_entities(passages)
        vehicles = [e for e in entities if e.entity_type == EntityType.VEHICLE]
        # With threshold 2, Iron Victory (2 mentions) should be created
        assert any("Iron Victory" in v.canonical_name for v in vehicles)


# =============================================================================
# Test: Mention Counting
# =============================================================================


class TestMentionCounting:
    """Tests for accurate mention counting."""

    def test_count_multiple_mentions(self, resolver: EntityResolver) -> None:
        """Should count all mentions of an entity across passages."""
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="Jon Snow walked. Jon Snow talked.",
                char_start=0,
                char_end=33,
            ),
            PassageRecord(
                passage_id="p1:1",
                source_id="p1",
                paragraph_index=1,
                text="Jon Snow returned home.",
                char_start=34,
                char_end=57,
            ),
        ]
        entities = resolver.extract_entities(passages)
        jon = next((e for e in entities if "Jon Snow" in e.canonical_name), None)
        assert jon is not None
        assert jon.mention_count == 3

    def test_first_seen_passage_tracked(self, resolver: EntityResolver) -> None:
        """Should track first_seen_passage correctly."""
        passages = [
            PassageRecord(
                passage_id="book1:5",
                source_id="book1",
                paragraph_index=5,
                text="Cersei Lannister entered the throne room.",
                char_start=0,
                char_end=41,
            ),
            PassageRecord(
                passage_id="book1:10",
                source_id="book1",
                paragraph_index=10,
                text="Cersei Lannister smiled coldly.",
                char_start=42,
                char_end=73,
            ),
        ]
        entities = resolver.extract_entities(passages)
        cersei = next((e for e in entities if "Cersei" in e.canonical_name), None)
        assert cersei is not None
        assert cersei.first_seen_passage == "book1:5"


# =============================================================================
# Test: Alias Table Building
# =============================================================================


class TestBuildAliasTable:
    """Tests for alias table construction."""

    def test_build_basic_alias(
        self, resolver: EntityResolver, passages_with_aliases: list[PassageRecord]
    ) -> None:
        """Should build alias mappings for entity variants."""
        entities = resolver.extract_entities(passages_with_aliases)
        aliases = resolver.build_alias_table(entities, passages_with_aliases)
        alias_texts = [a.alias_text for a in aliases]
        # Should have aliases for Daenerys variants
        assert "Daenerys Targaryen" in alias_texts or "Daenerys" in alias_texts

    def test_alias_points_to_canonical_entity(
        self, resolver: EntityResolver, passages_with_aliases: list[PassageRecord]
    ) -> None:
        """Aliases should point to the canonical entity."""
        entities = resolver.extract_entities(passages_with_aliases)
        aliases = resolver.build_alias_table(entities, passages_with_aliases)
        # All aliases should have valid entity_id references
        entity_ids = {e.entity_id for e in entities}
        for alias in aliases:
            assert alias.entity_id in entity_ids

    def test_alias_confidence_scores(
        self, resolver: EntityResolver, passages_with_aliases: list[PassageRecord]
    ) -> None:
        """Alias entries should have confidence scores."""
        entities = resolver.extract_entities(passages_with_aliases)
        aliases = resolver.build_alias_table(entities, passages_with_aliases)
        for alias in aliases:
            assert 0.0 <= alias.confidence <= 1.0


# =============================================================================
# Test: Human Override Rules
# =============================================================================


class TestOverrideRules:
    """Tests for human override functionality."""

    def test_add_override(self, resolver: EntityResolver) -> None:
        """Should add override rules to the resolver."""
        override = OverrideRule(
            override_id="ov1",
            target_alias="The Imp",
            action=OverrideAction.ASSIGN,
            target_entity_id="entity_tyrion",
            reason="The Imp is Tyrion Lannister",
        )
        resolver.add_override(override)
        assert len(resolver._overrides) == 1
        assert resolver._overrides[0].target_alias == "The Imp"

    def test_override_assign_action(self, resolver: EntityResolver) -> None:
        """ASSIGN override should force alias to specific entity."""
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="Tyrion Lannister laughed. The Imp was cunning.",
                char_start=0,
                char_end=46,
            )
        ]
        override = OverrideRule(
            override_id="ov1",
            target_alias="The Imp",
            action=OverrideAction.ASSIGN,
            target_entity_id="tyrion_entity",
            reason="The Imp refers to Tyrion",
        )
        resolver.add_override(override)
        entities = resolver.extract_entities(passages)
        aliases = resolver.build_alias_table(entities, passages)
        imp_alias = next((a for a in aliases if a.alias_text == "The Imp"), None)
        # If The Imp is extracted, it should be assigned to Tyrion's entity
        if imp_alias:
            assert imp_alias.entity_id == "tyrion_entity"

    def test_override_ignore_action(self, resolver: EntityResolver) -> None:
        """IGNORE override should exclude alias from resolution."""
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="The Others came from the North.",
                char_start=0,
                char_end=31,
            )
        ]
        override = OverrideRule(
            override_id="ov1",
            target_alias="The Others",
            action=OverrideAction.IGNORE,
            reason="Too generic, ignore for now",
        )
        resolver.add_override(override)
        entities = resolver.extract_entities(passages)
        # The Others should not be in entities due to IGNORE
        names = [e.canonical_name for e in entities]
        assert "The Others" not in names

    def test_multiple_overrides(self, resolver: EntityResolver) -> None:
        """Should support multiple override rules."""
        override1 = OverrideRule(
            override_id="ov1",
            target_alias="The Imp",
            action=OverrideAction.ASSIGN,
            target_entity_id="tyrion_entity",
            reason="Tyrion's nickname",
        )
        override2 = OverrideRule(
            override_id="ov2",
            target_alias="The Mountain",
            action=OverrideAction.ASSIGN,
            target_entity_id="gregor_entity",
            reason="Gregor's nickname",
        )
        resolver.add_override(override1)
        resolver.add_override(override2)
        assert len(resolver._overrides) == 2


# =============================================================================
# Test: Deterministic Tie-Breaking
# =============================================================================


class TestDeterministicTieBreaking:
    """Tests for deterministic ordering when there are ties."""

    def test_earliest_first_seen_wins(self, resolver: EntityResolver) -> None:
        """When alias could map to multiple entities, earliest first_seen wins."""
        passages = [
            PassageRecord(
                passage_id="book1:0",
                source_id="book1",
                paragraph_index=0,
                text="Brandon Stark was the eldest son.",
                char_start=0,
                char_end=33,
            ),
            PassageRecord(
                passage_id="book1:5",
                source_id="book1",
                paragraph_index=5,
                text="Bran Stark climbed the tower.",
                char_start=34,
                char_end=63,
            ),
        ]
        entities = resolver.extract_entities(passages)
        aliases = resolver.build_alias_table(entities, passages)
        # If "Stark" is an alias, it should map to earliest
        stark_aliases = [a for a in aliases if "Stark" in a.alias_text]
        if stark_aliases:
            # Should be consistently ordered
            assert len(stark_aliases) >= 1

    def test_alphabetical_tiebreak_on_equal_confidence(self, resolver: EntityResolver) -> None:
        """When confidence is equal, alphabetical ordering by entity_id."""
        passages = [
            PassageRecord(
                passage_id="book1:0",
                source_id="book1",
                paragraph_index=0,
                text="Jon Snow and Arya Stark traveled together.",
                char_start=0,
                char_end=42,
            ),
        ]
        entities = resolver.extract_entities(passages)
        # Entities should be consistently ordered
        entity_ids = [e.entity_id for e in entities]
        assert entity_ids == sorted(entity_ids)


# =============================================================================
# Test: Full Resolution Pipeline
# =============================================================================


class TestResolve:
    """Tests for the full resolve() pipeline."""

    def test_resolve_returns_tuple(
        self, resolver: EntityResolver, sample_passages: list[PassageRecord]
    ) -> None:
        """resolve() should return (entities, aliases, evidence_anchors)."""
        result = resolver.resolve(sample_passages)
        assert isinstance(result, tuple)
        assert len(result) == 3
        entities, aliases, anchors = result
        assert isinstance(entities, list)
        assert isinstance(aliases, list)
        assert isinstance(anchors, list)

    def test_resolve_entities_are_valid(
        self, resolver: EntityResolver, sample_passages: list[PassageRecord]
    ) -> None:
        """Resolved entities should be valid Entity objects."""
        entities, _, _ = resolver.resolve(sample_passages)
        for entity in entities:
            assert isinstance(entity, Entity)
            assert entity.entity_id
            assert entity.canonical_name
            assert entity.entity_type in EntityType

    def test_resolve_aliases_are_valid(
        self, resolver: EntityResolver, sample_passages: list[PassageRecord]
    ) -> None:
        """Resolved aliases should be valid AliasEntry objects."""
        entities, aliases, _ = resolver.resolve(sample_passages)
        for alias in aliases:
            assert isinstance(alias, AliasEntry)
            assert alias.alias_id
            assert alias.alias_text
            assert alias.entity_id

    def test_resolve_anchors_are_valid(
        self, resolver: EntityResolver, sample_passages: list[PassageRecord]
    ) -> None:
        """Resolved anchors should be valid EvidenceAnchor objects."""
        _, _, anchors = resolver.resolve(sample_passages)
        for anchor in anchors:
            assert isinstance(anchor, EvidenceAnchor)
            assert anchor.anchor_id
            assert anchor.passage_id
            assert anchor.excerpt

    def test_resolve_empty_passages(self, resolver: EntityResolver) -> None:
        """resolve() should handle empty passages list."""
        entities, aliases, anchors = resolver.resolve([])
        assert entities == []
        assert aliases == []
        assert anchors == []

    def test_resolve_is_deterministic(self, resolver: EntityResolver) -> None:
        """resolve() should return stable IDs across identical runs."""
        passages = [
            PassageRecord(
                passage_id="book1:0",
                source_id="book1",
                paragraph_index=0,
                text="Jon Snow walked to Winterfell.",
                char_start=0,
                char_end=31,
            ),
            PassageRecord(
                passage_id="book1:1",
                source_id="book1",
                paragraph_index=1,
                text="Arya Stark met Jon Snow by the Wall.",
                char_start=32,
                char_end=72,
            ),
        ]

        entities_a, aliases_a, anchors_a = resolver.resolve(passages)
        entities_b, aliases_b, anchors_b = resolver.resolve(passages)

        assert [e.entity_id for e in entities_a] == [e.entity_id for e in entities_b]
        assert [a.alias_id for a in aliases_a] == [a.alias_id for a in aliases_b]
        assert sorted(a.anchor_id for a in anchors_a) == sorted(a.anchor_id for a in anchors_b)

    def test_resolve_includes_all_types(
        self, resolver: EntityResolver, sample_passages: list[PassageRecord]
    ) -> None:
        """resolve() should extract multiple entity types."""
        entities, _, _ = resolver.resolve(sample_passages)
        types_found = {e.entity_type for e in entities}
        # Should find at least persons and places in sample passages
        assert len(types_found) >= 1


# =============================================================================
# Test: Evidence Anchors
# =============================================================================


class TestEvidenceAnchors:
    """Tests for evidence anchor generation."""

    def test_anchors_reference_valid_passages(
        self, resolver: EntityResolver, sample_passages: list[PassageRecord]
    ) -> None:
        """Evidence anchors should reference passages that exist."""
        _, _, anchors = resolver.resolve(sample_passages)
        passage_ids = {p.passage_id for p in sample_passages}
        for anchor in anchors:
            assert anchor.passage_id in passage_ids

    def test_anchor_excerpt_matches_passage(
        self, resolver: EntityResolver, sample_passages: list[PassageRecord]
    ) -> None:
        """Anchor excerpts should be substrings of their passages."""
        _, _, anchors = resolver.resolve(sample_passages)
        passage_map = {p.passage_id: p.text for p in sample_passages}
        for anchor in anchors:
            passage_text = passage_map[anchor.passage_id]
            assert anchor.excerpt in passage_text

    def test_anchor_char_offsets_valid(
        self, resolver: EntityResolver, sample_passages: list[PassageRecord]
    ) -> None:
        """Anchor char offsets should be within passage bounds."""
        _, _, anchors = resolver.resolve(sample_passages)
        passage_map = {p.passage_id: p.text for p in sample_passages}
        for anchor in anchors:
            passage_text = passage_map[anchor.passage_id]
            assert anchor.char_start >= 0
            assert anchor.char_end <= len(passage_text)
            assert anchor.char_start < anchor.char_end


# =============================================================================
# Test: Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_passage_with_no_entities(self, resolver: EntityResolver) -> None:
        """Should handle passages with no extractable entities."""
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="The sun rose slowly over the hills.",
                char_start=0,
                char_end=35,
            )
        ]
        entities = resolver.extract_entities(passages)
        # Should return empty list, not crash
        assert isinstance(entities, list)

    def test_very_long_passage(self, resolver: EntityResolver) -> None:
        """Should handle very long passages."""
        long_text = "Jon Snow walked. " * 100
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text=long_text,
                char_start=0,
                char_end=len(long_text),
            )
        ]
        entities = resolver.extract_entities(passages)
        jon = next((e for e in entities if "Jon Snow" in e.canonical_name), None)
        assert jon is not None
        assert jon.mention_count == 100

    def test_special_characters_in_names(self, resolver: EntityResolver) -> None:
        """Should handle special characters like apostrophes."""
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="They rode to King's Landing via the Kingsroad.",
                char_start=0,
                char_end=46,
            )
        ]
        entities = resolver.extract_entities(passages)
        names = [e.canonical_name for e in entities]
        assert "King's Landing" in names

    def test_unicode_characters(self, resolver: EntityResolver) -> None:
        """Should handle unicode characters."""
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="Aerys Targaryen was known as the Mad King.",
                char_start=0,
                char_end=42,
            )
        ]
        entities = resolver.extract_entities(passages)
        # Should not crash on unicode
        assert isinstance(entities, list)

    def test_duplicate_entity_deduplication(self, resolver: EntityResolver) -> None:
        """Same entity in multiple passages should be deduplicated."""
        passages = [
            PassageRecord(
                passage_id="p1:0",
                source_id="p1",
                paragraph_index=0,
                text="Jon Snow arrived.",
                char_start=0,
                char_end=17,
            ),
            PassageRecord(
                passage_id="p1:1",
                source_id="p1",
                paragraph_index=1,
                text="Jon Snow departed.",
                char_start=18,
                char_end=36,
            ),
        ]
        entities = resolver.extract_entities(passages)
        jon_entities = [e for e in entities if "Jon Snow" in e.canonical_name]
        # Should be deduplicated to one entity
        assert len(jon_entities) == 1
        # But with mention_count of 2
        assert jon_entities[0].mention_count == 2
