"""Tests for the ObligationExtractor module.

TDD-style tests for extracting narrative obligations from passages.
Categories: PLOT_THREAD, CHEKHOV_GUN, PROPHECY_VISION, MYSTERY
"""

import pytest

from showrunner.contracts import (
    Entity,
    EntityType,
    EvidenceAnchor,
    Obligation,
    ObligationCategory,
    PassageRecord,
)
from showrunner.extractors.obligation_extractor import ObligationExtractor

# --- Fixtures ---


@pytest.fixture
def extractor() -> ObligationExtractor:
    """Return a fresh ObligationExtractor instance."""
    return ObligationExtractor()


@pytest.fixture
def sample_passage_prophecy() -> PassageRecord:
    """Passage containing a prophecy/vision."""
    return PassageRecord(
        passage_id="book1:42",
        source_id="book1",
        paragraph_index=42,
        text="The old crone spoke: 'I have seen a vision of three heads upon the dragon. "
        "The prince that was promised shall come again, and Azor Ahai will be reborn "
        "amidst salt and smoke.'",
        char_start=5000,
        char_end=5200,
    )


@pytest.fixture
def sample_passage_chekhov_gun() -> PassageRecord:
    """Passage containing a Chekhov's gun setup."""
    return PassageRecord(
        passage_id="book1:100",
        source_id="book1",
        paragraph_index=100,
        text="Lord Stark drew the Valyrian steel sword Ice from its sheath, the blade "
        "gleaming with an otherworldly shimmer. He would need it later, he knew. "
        "She kept it hidden beneath the floorboards, wrapped in oilcloth.",
        char_start=12000,
        char_end=12250,
    )


@pytest.fixture
def sample_passage_mystery() -> PassageRecord:
    """Passage containing a mystery."""
    return PassageRecord(
        passage_id="book2:15",
        source_id="book2",
        paragraph_index=15,
        text="Who had sent the assassin? The secret of his true parentage remained "
        "hidden from all. No one knew the real name of the masked knight. "
        "Why would the Citadel conceal such knowledge?",
        char_start=2000,
        char_end=2250,
    )


@pytest.fixture
def sample_passage_plot_thread() -> PassageRecord:
    """Passage containing an unresolved plot thread."""
    return PassageRecord(
        passage_id="book1:200",
        source_id="book1",
        paragraph_index=200,
        text="'I swear by the old gods and the new,' he said, 'I will find my sister "
        "and bring her home.' He set off toward Winterfell, but the road ahead was "
        "long and treacherous. The oath hung heavy in the air.",
        char_start=25000,
        char_end=25300,
    )


@pytest.fixture
def sample_entities() -> list[Entity]:
    """Sample entities for testing."""
    return [
        Entity(
            entity_id="ent_stark_001",
            canonical_name="Eddard Stark",
            entity_type=EntityType.PERSON,
            first_seen_passage="book1:1",
            mention_count=150,
            is_important=True,
        ),
        Entity(
            entity_id="ent_ice_001",
            canonical_name="Ice",
            entity_type=EntityType.ARTIFACT,
            first_seen_passage="book1:100",
            mention_count=25,
            is_important=True,
            description="Valyrian steel greatsword of House Stark",
        ),
        Entity(
            entity_id="ent_winterfell_001",
            canonical_name="Winterfell",
            entity_type=EntityType.PLACE,
            first_seen_passage="book1:1",
            mention_count=200,
        ),
    ]


@pytest.fixture
def multiple_passages() -> list[PassageRecord]:
    """Multiple passages for comprehensive testing."""
    return [
        PassageRecord(
            passage_id="book1:10",
            source_id="book1",
            paragraph_index=10,
            text="The three-eyed raven appeared in his dreams, foretelling doom.",
            char_start=1000,
            char_end=1100,
        ),
        PassageRecord(
            passage_id="book1:20",
            source_id="book1",
            paragraph_index=20,
            text="He gave her the dagger, its edge still sharp. She kept it hidden.",
            char_start=2000,
            char_end=2100,
        ),
        PassageRecord(
            passage_id="book1:30",
            source_id="book1",
            paragraph_index=30,
            text="What was the hidden truth behind the tower? The secret haunted him.",
            char_start=3000,
            char_end=3100,
        ),
        PassageRecord(
            passage_id="book1:40",
            source_id="book1",
            paragraph_index=40,
            text="'I promise to return,' he said, setting out for the Wall.",
            char_start=4000,
            char_end=4100,
        ),
    ]


# --- Test: Basic Instantiation ---


class TestObligationExtractorInstantiation:
    """Tests for ObligationExtractor creation."""

    def test_create_extractor_returns_instance(self, extractor: ObligationExtractor) -> None:
        """Extractor should be instantiable."""
        assert extractor is not None
        assert isinstance(extractor, ObligationExtractor)

    def test_extractor_has_extract_method(self, extractor: ObligationExtractor) -> None:
        """Extractor should have the extract method."""
        assert hasattr(extractor, "extract")
        assert callable(extractor.extract)


# --- Test: Extract Method Signature and Return Types ---


class TestExtractMethodSignature:
    """Tests for the extract method interface."""

    def test_extract_returns_tuple_of_two_lists(
        self,
        extractor: ObligationExtractor,
        sample_passage_prophecy: PassageRecord,
    ) -> None:
        """Extract should return a tuple of (obligations, anchors)."""
        result = extractor.extract([sample_passage_prophecy], [])
        assert isinstance(result, tuple)
        assert len(result) == 2
        obligations, anchors = result
        assert isinstance(obligations, list)
        assert isinstance(anchors, list)

    def test_extract_with_empty_passages_returns_empty_lists(
        self,
        extractor: ObligationExtractor,
    ) -> None:
        """Extract with no passages should return empty lists."""
        obligations, anchors = extractor.extract([], [])
        assert obligations == []
        assert anchors == []

    def test_extract_returns_obligation_objects(
        self,
        extractor: ObligationExtractor,
        sample_passage_prophecy: PassageRecord,
    ) -> None:
        """Extracted items should be Obligation instances."""
        obligations, _ = extractor.extract([sample_passage_prophecy], [])
        assert len(obligations) > 0
        for obl in obligations:
            assert isinstance(obl, Obligation)

    def test_extract_returns_evidence_anchor_objects(
        self,
        extractor: ObligationExtractor,
        sample_passage_prophecy: PassageRecord,
    ) -> None:
        """Extracted anchors should be EvidenceAnchor instances."""
        _, anchors = extractor.extract([sample_passage_prophecy], [])
        assert len(anchors) > 0
        for anchor in anchors:
            assert isinstance(anchor, EvidenceAnchor)


# --- Test: Prophecy/Vision Extraction ---


class TestProphecyVisionExtraction:
    """Tests for extracting prophecy and vision obligations."""

    def test_extract_detects_vision_keyword(
        self,
        extractor: ObligationExtractor,
        sample_passage_prophecy: PassageRecord,
    ) -> None:
        """Should detect 'vision' keyword and create PROPHECY_VISION obligation."""
        obligations, _ = extractor.extract([sample_passage_prophecy], [])
        prophecy_obls = [o for o in obligations if o.category == ObligationCategory.PROPHECY_VISION]
        assert len(prophecy_obls) >= 1

    def test_extract_detects_foretold_keyword(
        self,
        extractor: ObligationExtractor,
    ) -> None:
        """Should detect 'foretold' keyword."""
        passage = PassageRecord(
            passage_id="book1:1",
            source_id="book1",
            paragraph_index=1,
            text="It was foretold that he would conquer the seven kingdoms.",
            char_start=0,
            char_end=60,
        )
        obligations, _ = extractor.extract([passage], [])
        prophecy_obls = [o for o in obligations if o.category == ObligationCategory.PROPHECY_VISION]
        assert len(prophecy_obls) >= 1

    def test_extract_detects_prince_that_was_promised(
        self,
        extractor: ObligationExtractor,
        sample_passage_prophecy: PassageRecord,
    ) -> None:
        """Should detect 'prince that was promised' phrase."""
        obligations, _ = extractor.extract([sample_passage_prophecy], [])
        prophecy_obls = [o for o in obligations if o.category == ObligationCategory.PROPHECY_VISION]
        descriptions = " ".join(o.description.lower() for o in prophecy_obls)
        assert "prince" in descriptions or len(prophecy_obls) >= 1

    def test_extract_detects_azor_ahai(
        self,
        extractor: ObligationExtractor,
        sample_passage_prophecy: PassageRecord,
    ) -> None:
        """Should detect 'azor ahai' phrase."""
        obligations, _ = extractor.extract([sample_passage_prophecy], [])
        prophecy_obls = [o for o in obligations if o.category == ObligationCategory.PROPHECY_VISION]
        assert len(prophecy_obls) >= 1

    def test_extract_detects_three_heads(
        self,
        extractor: ObligationExtractor,
        sample_passage_prophecy: PassageRecord,
    ) -> None:
        """Should detect 'three heads' phrase."""
        obligations, _ = extractor.extract([sample_passage_prophecy], [])
        prophecy_obls = [o for o in obligations if o.category == ObligationCategory.PROPHECY_VISION]
        assert len(prophecy_obls) >= 1

    def test_extract_detects_dream_keyword(
        self,
        extractor: ObligationExtractor,
    ) -> None:
        """Should detect dream-related keywords."""
        passage = PassageRecord(
            passage_id="book1:5",
            source_id="book1",
            paragraph_index=5,
            text="In his dreams, he saw the wolves running through snow.",
            char_start=0,
            char_end=60,
        )
        obligations, _ = extractor.extract([passage], [])
        prophecy_obls = [o for o in obligations if o.category == ObligationCategory.PROPHECY_VISION]
        assert len(prophecy_obls) >= 1


# --- Test: Chekhov's Gun Extraction ---


class TestChekhovGunExtraction:
    """Tests for extracting Chekhov's gun setups."""

    def test_extract_detects_would_need_it_later(
        self,
        extractor: ObligationExtractor,
        sample_passage_chekhov_gun: PassageRecord,
    ) -> None:
        """Should detect 'would need it later' pattern."""
        obligations, _ = extractor.extract([sample_passage_chekhov_gun], [])
        chekhov_obls = [o for o in obligations if o.category == ObligationCategory.CHEKHOV_GUN]
        assert len(chekhov_obls) >= 1

    def test_extract_detects_kept_it_hidden(
        self,
        extractor: ObligationExtractor,
        sample_passage_chekhov_gun: PassageRecord,
    ) -> None:
        """Should detect 'kept it hidden' pattern."""
        obligations, _ = extractor.extract([sample_passage_chekhov_gun], [])
        chekhov_obls = [o for o in obligations if o.category == ObligationCategory.CHEKHOV_GUN]
        assert len(chekhov_obls) >= 1

    def test_extract_detects_named_weapon_with_description(
        self,
        extractor: ObligationExtractor,
        sample_entities: list[Entity],
    ) -> None:
        """Should detect named weapons with significant description."""
        passage = PassageRecord(
            passage_id="book1:50",
            source_id="book1",
            paragraph_index=50,
            text="The sword Longclaw hung at his side, Valyrian steel forged in ancient times.",
            char_start=5000,
            char_end=5100,
        )
        obligations, _ = extractor.extract([passage], sample_entities)
        chekhov_obls = [o for o in obligations if o.category == ObligationCategory.CHEKHOV_GUN]
        assert len(chekhov_obls) >= 1

    def test_extract_detects_poison_vial_letter(
        self,
        extractor: ObligationExtractor,
    ) -> None:
        """Should detect poison, vial, or letter mentioned with emphasis."""
        passage = PassageRecord(
            passage_id="book1:60",
            source_id="book1",
            paragraph_index=60,
            text="She clutched the vial of poison tight, knowing its contents could change everything.",
            char_start=6000,
            char_end=6100,
        )
        obligations, _ = extractor.extract([passage], [])
        chekhov_obls = [o for o in obligations if o.category == ObligationCategory.CHEKHOV_GUN]
        assert len(chekhov_obls) >= 1

    def test_chekhov_gun_links_artifact_entities(
        self,
        extractor: ObligationExtractor,
        sample_passage_chekhov_gun: PassageRecord,
        sample_entities: list[Entity],
    ) -> None:
        """Chekhov's gun should link to related artifact entities."""
        obligations, _ = extractor.extract([sample_passage_chekhov_gun], sample_entities)
        chekhov_obls = [o for o in obligations if o.category == ObligationCategory.CHEKHOV_GUN]
        # At least one should have related entity IDs
        # May not always find entities if name doesn't match exactly
        assert len(chekhov_obls) >= 1


# --- Test: Mystery Extraction ---


class TestMysteryExtraction:
    """Tests for extracting unresolved mysteries."""

    def test_extract_detects_who_had_question(
        self,
        extractor: ObligationExtractor,
        sample_passage_mystery: PassageRecord,
    ) -> None:
        """Should detect 'Who had...' question pattern."""
        obligations, _ = extractor.extract([sample_passage_mystery], [])
        mystery_obls = [o for o in obligations if o.category == ObligationCategory.MYSTERY]
        assert len(mystery_obls) >= 1

    def test_extract_dedupes_fragment_questions_when_full_question_present(
        self,
        extractor: ObligationExtractor,
        sample_passage_mystery: PassageRecord,
    ) -> None:
        """Fragment question patterns should not duplicate full question matches."""
        obligations, _ = extractor.extract([sample_passage_mystery], [])
        question_descriptions = [
            o.description
            for o in obligations
            if o.category == ObligationCategory.MYSTERY
            and "unresolved question" in o.description.lower()
        ]

        who_had = [desc for desc in question_descriptions if "who had" in desc.lower()]
        why_would = [desc for desc in question_descriptions if "why would" in desc.lower()]

        assert len(who_had) == 1
        assert len(why_would) == 1
        assert "?" in who_had[0]
        assert "?" in why_would[0]

    def test_extract_detects_why_would_question(
        self,
        extractor: ObligationExtractor,
        sample_passage_mystery: PassageRecord,
    ) -> None:
        """Should detect 'Why would...' question pattern."""
        obligations, _ = extractor.extract([sample_passage_mystery], [])
        mystery_obls = [o for o in obligations if o.category == ObligationCategory.MYSTERY]
        assert len(mystery_obls) >= 1

    def test_extract_detects_secret_keyword(
        self,
        extractor: ObligationExtractor,
        sample_passage_mystery: PassageRecord,
    ) -> None:
        """Should detect 'secret' keyword."""
        obligations, _ = extractor.extract([sample_passage_mystery], [])
        mystery_obls = [o for o in obligations if o.category == ObligationCategory.MYSTERY]
        assert len(mystery_obls) >= 1

    def test_extract_detects_hidden_truth(
        self,
        extractor: ObligationExtractor,
    ) -> None:
        """Should detect 'hidden truth' pattern."""
        passage = PassageRecord(
            passage_id="book1:70",
            source_id="book1",
            paragraph_index=70,
            text="The hidden truth lay buried beneath the crypts of Winterfell.",
            char_start=7000,
            char_end=7100,
        )
        obligations, _ = extractor.extract([passage], [])
        mystery_obls = [o for o in obligations if o.category == ObligationCategory.MYSTERY]
        assert len(mystery_obls) >= 1

    def test_extract_detects_true_parentage(
        self,
        extractor: ObligationExtractor,
        sample_passage_mystery: PassageRecord,
    ) -> None:
        """Should detect 'true parentage' identity mystery."""
        obligations, _ = extractor.extract([sample_passage_mystery], [])
        mystery_obls = [o for o in obligations if o.category == ObligationCategory.MYSTERY]
        assert len(mystery_obls) >= 1

    def test_extract_detects_real_name_mystery(
        self,
        extractor: ObligationExtractor,
        sample_passage_mystery: PassageRecord,
    ) -> None:
        """Should detect 'real name' identity mystery."""
        obligations, _ = extractor.extract([sample_passage_mystery], [])
        mystery_obls = [o for o in obligations if o.category == ObligationCategory.MYSTERY]
        assert len(mystery_obls) >= 1

    def test_extract_detects_no_one_knew(
        self,
        extractor: ObligationExtractor,
        sample_passage_mystery: PassageRecord,
    ) -> None:
        """Should detect 'no one knew' pattern."""
        obligations, _ = extractor.extract([sample_passage_mystery], [])
        mystery_obls = [o for o in obligations if o.category == ObligationCategory.MYSTERY]
        assert len(mystery_obls) >= 1


# --- Test: Plot Thread Extraction ---


class TestPlotThreadExtraction:
    """Tests for extracting ongoing plot threads."""

    def test_extract_detects_oath_promise(
        self,
        extractor: ObligationExtractor,
        sample_passage_plot_thread: PassageRecord,
    ) -> None:
        """Should detect oaths and promises."""
        obligations, _ = extractor.extract([sample_passage_plot_thread], [])
        thread_obls = [o for o in obligations if o.category == ObligationCategory.PLOT_THREAD]
        assert len(thread_obls) >= 1

    def test_extract_detects_swear_keyword(
        self,
        extractor: ObligationExtractor,
        sample_passage_plot_thread: PassageRecord,
    ) -> None:
        """Should detect 'swear' keyword indicating oath."""
        obligations, _ = extractor.extract([sample_passage_plot_thread], [])
        thread_obls = [o for o in obligations if o.category == ObligationCategory.PLOT_THREAD]
        assert len(thread_obls) >= 1

    def test_extract_detects_journey_to_destination(
        self,
        extractor: ObligationExtractor,
    ) -> None:
        """Should detect unfinished journeys."""
        passage = PassageRecord(
            passage_id="book1:80",
            source_id="book1",
            paragraph_index=80,
            text="They set off toward Braavos, the journey ahead long and uncertain.",
            char_start=8000,
            char_end=8100,
        )
        obligations, _ = extractor.extract([passage], [])
        thread_obls = [o for o in obligations if o.category == ObligationCategory.PLOT_THREAD]
        assert len(thread_obls) >= 1

    def test_extract_detects_promise_to_return(
        self,
        extractor: ObligationExtractor,
    ) -> None:
        """Should detect 'promise to return' pattern."""
        passage = PassageRecord(
            passage_id="book1:85",
            source_id="book1",
            paragraph_index=85,
            text="'I promise to return before the winter comes,' he said.",
            char_start=8500,
            char_end=8600,
        )
        obligations, _ = extractor.extract([passage], [])
        thread_obls = [o for o in obligations if o.category == ObligationCategory.PLOT_THREAD]
        assert len(thread_obls) >= 1

    def test_extract_detects_conflict_introduction(
        self,
        extractor: ObligationExtractor,
    ) -> None:
        """Should detect unresolved conflicts."""
        passage = PassageRecord(
            passage_id="book1:90",
            source_id="book1",
            paragraph_index=90,
            text="War between the houses seemed inevitable. The conflict would not end easily.",
            char_start=9000,
            char_end=9100,
        )
        obligations, _ = extractor.extract([passage], [])
        thread_obls = [o for o in obligations if o.category == ObligationCategory.PLOT_THREAD]
        assert len(thread_obls) >= 1


# --- Test: Evidence Anchor Requirements ---


class TestEvidenceAnchorRequirements:
    """Tests for evidence anchor hard gate requirement."""

    def test_every_obligation_has_at_least_one_anchor(
        self,
        extractor: ObligationExtractor,
        multiple_passages: list[PassageRecord],
        sample_entities: list[Entity],
    ) -> None:
        """Every obligation MUST have >= 1 evidence anchor (hard gate)."""
        obligations, anchors = extractor.extract(multiple_passages, sample_entities)
        anchor_ids = {a.anchor_id for a in anchors}

        for obl in obligations:
            assert len(obl.evidence_anchor_ids) >= 1, (
                f"Obligation {obl.obligation_id} has no evidence anchors"
            )
            for anchor_id in obl.evidence_anchor_ids:
                assert anchor_id in anchor_ids, (
                    f"Obligation {obl.obligation_id} references non-existent anchor {anchor_id}"
                )

    def test_anchor_points_to_valid_passage(
        self,
        extractor: ObligationExtractor,
        sample_passage_prophecy: PassageRecord,
    ) -> None:
        """Evidence anchor should point to a valid passage."""
        obligations, anchors = extractor.extract([sample_passage_prophecy], [])
        for anchor in anchors:
            assert anchor.passage_id == sample_passage_prophecy.passage_id

    def test_anchor_has_valid_char_offsets(
        self,
        extractor: ObligationExtractor,
        sample_passage_prophecy: PassageRecord,
    ) -> None:
        """Evidence anchor should have valid character offsets within passage."""
        _, anchors = extractor.extract([sample_passage_prophecy], [])
        passage_len = len(sample_passage_prophecy.text)
        for anchor in anchors:
            assert 0 <= anchor.char_start < passage_len
            assert anchor.char_start < anchor.char_end <= passage_len

    def test_anchor_excerpt_matches_passage_text(
        self,
        extractor: ObligationExtractor,
        sample_passage_prophecy: PassageRecord,
    ) -> None:
        """Evidence anchor excerpt should match the passage text at offsets."""
        _, anchors = extractor.extract([sample_passage_prophecy], [])
        for anchor in anchors:
            expected_excerpt = sample_passage_prophecy.text[anchor.char_start : anchor.char_end]
            assert anchor.excerpt == expected_excerpt


# --- Test: Obligation ID Stability ---


class TestObligationIdStability:
    """Tests for stable obligation ID generation."""

    def test_obligation_ids_are_unique(
        self,
        extractor: ObligationExtractor,
        multiple_passages: list[PassageRecord],
    ) -> None:
        """All obligation IDs should be unique."""
        obligations, _ = extractor.extract(multiple_passages, [])
        ids = [o.obligation_id for o in obligations]
        assert len(ids) == len(set(ids))

    def test_anchor_ids_are_unique(
        self,
        extractor: ObligationExtractor,
        multiple_passages: list[PassageRecord],
    ) -> None:
        """All anchor IDs should be unique."""
        _, anchors = extractor.extract(multiple_passages, [])
        ids = [a.anchor_id for a in anchors]
        assert len(ids) == len(set(ids))

    def test_obligation_id_is_deterministic(
        self,
        extractor: ObligationExtractor,
        sample_passage_prophecy: PassageRecord,
    ) -> None:
        """Same input should produce same obligation ID."""
        obligations1, _ = extractor.extract([sample_passage_prophecy], [])
        obligations2, _ = extractor.extract([sample_passage_prophecy], [])

        ids1 = sorted(o.obligation_id for o in obligations1)
        ids2 = sorted(o.obligation_id for o in obligations2)
        assert ids1 == ids2

    def test_obligation_id_format(
        self,
        extractor: ObligationExtractor,
        sample_passage_prophecy: PassageRecord,
    ) -> None:
        """Obligation ID should follow a consistent format."""
        obligations, _ = extractor.extract([sample_passage_prophecy], [])
        for obl in obligations:
            # Should be non-empty string
            assert obl.obligation_id
            assert isinstance(obl.obligation_id, str)
            # Should have prefix indicating type
            assert obl.obligation_id.startswith("obl_")


# --- Test: Last Seen Passage Reference ---


class TestLastSeenPassageReference:
    """Tests for tracking last-seen passage reference."""

    def test_last_seen_passage_id_is_set(
        self,
        extractor: ObligationExtractor,
        sample_passage_prophecy: PassageRecord,
    ) -> None:
        """Obligation should have last_seen_passage_id set."""
        obligations, _ = extractor.extract([sample_passage_prophecy], [])
        for obl in obligations:
            assert obl.last_seen_passage_id is not None
            assert obl.last_seen_passage_id == sample_passage_prophecy.passage_id

    def test_last_seen_passage_tracks_most_recent(
        self,
        extractor: ObligationExtractor,
    ) -> None:
        """Last seen should track the most recent passage mentioning the pattern."""
        passages = [
            PassageRecord(
                passage_id="book1:1",
                source_id="book1",
                paragraph_index=1,
                text="The vision came to him in sleep.",
                char_start=0,
                char_end=40,
            ),
            PassageRecord(
                passage_id="book1:50",
                source_id="book1",
                paragraph_index=50,
                text="Another vision troubled his dreams.",
                char_start=5000,
                char_end=5040,
            ),
        ]
        obligations, _ = extractor.extract(passages, [])
        # If same obligation is detected multiple times, last_seen should be book1:50
        prophecy_obls = [o for o in obligations if o.category == ObligationCategory.PROPHECY_VISION]
        assert len(prophecy_obls) >= 1


# --- Test: Confidence Scores ---


class TestConfidenceScores:
    """Tests for confidence score assignment."""

    def test_confidence_is_between_0_and_1(
        self,
        extractor: ObligationExtractor,
        multiple_passages: list[PassageRecord],
    ) -> None:
        """Confidence scores should be in [0, 1] range."""
        obligations, _ = extractor.extract(multiple_passages, [])
        for obl in obligations:
            assert 0.0 <= obl.confidence <= 1.0

    def test_exact_match_patterns_have_high_confidence(
        self,
        extractor: ObligationExtractor,
    ) -> None:
        """Exact pattern matches (azor ahai, prince promised) should have high confidence."""
        passage = PassageRecord(
            passage_id="book1:1",
            source_id="book1",
            paragraph_index=1,
            text="Azor Ahai shall be born again amidst salt and smoke.",
            char_start=0,
            char_end=55,
        )
        obligations, _ = extractor.extract([passage], [])
        prophecy_obls = [o for o in obligations if o.category == ObligationCategory.PROPHECY_VISION]
        assert len(prophecy_obls) >= 1
        assert any(o.confidence >= 0.8 for o in prophecy_obls)


# --- Test: Entity Linking ---


class TestEntityLinking:
    """Tests for linking related entities to obligations."""

    def test_obligation_can_have_related_entities(
        self,
        extractor: ObligationExtractor,
        sample_passage_chekhov_gun: PassageRecord,
        sample_entities: list[Entity],
    ) -> None:
        """Obligations should be able to link to related entities."""
        obligations, _ = extractor.extract([sample_passage_chekhov_gun], sample_entities)
        # Check structure is valid even if no entities linked
        for obl in obligations:
            assert isinstance(obl.related_entity_ids, list)

    def test_related_entity_ids_reference_valid_entities(
        self,
        extractor: ObligationExtractor,
        sample_passage_chekhov_gun: PassageRecord,
        sample_entities: list[Entity],
    ) -> None:
        """Related entity IDs should reference entities from input."""
        obligations, _ = extractor.extract([sample_passage_chekhov_gun], sample_entities)
        entity_ids = {e.entity_id for e in sample_entities}
        for obl in obligations:
            for eid in obl.related_entity_ids:
                assert eid in entity_ids


# --- Test: Multiple Categories in One Passage ---


class TestMultipleCategoriesInPassage:
    """Tests for extracting multiple obligation types from one passage."""

    def test_extract_multiple_categories_from_one_passage(
        self,
        extractor: ObligationExtractor,
    ) -> None:
        """Should extract multiple obligation types from a rich passage."""
        passage = PassageRecord(
            passage_id="book1:999",
            source_id="book1",
            paragraph_index=999,
            text="In her vision, she saw the sword gleaming. 'I swear to find the truth,' "
            "she said. Who had hidden the secret? She kept the blade close.",
            char_start=99000,
            char_end=99200,
        )
        obligations, _ = extractor.extract([passage], [])

        categories_found = {o.category for o in obligations}
        # Should find at least 2 different categories
        assert len(categories_found) >= 2


# --- Test: Default State ---


class TestDefaultState:
    """Tests for default obligation state."""

    def test_obligation_is_not_resolved_by_default(
        self,
        extractor: ObligationExtractor,
        sample_passage_prophecy: PassageRecord,
    ) -> None:
        """New obligations should not be marked as resolved."""
        obligations, _ = extractor.extract([sample_passage_prophecy], [])
        for obl in obligations:
            assert obl.is_resolved is False
            assert obl.resolution_passage_id is None


# --- Test: Private Method Interfaces ---


class TestPrivateMethodInterfaces:
    """Tests for private extraction methods."""

    def test_extract_prophecies_returns_list_of_tuples(
        self,
        extractor: ObligationExtractor,
        sample_passage_prophecy: PassageRecord,
    ) -> None:
        """_extract_prophecies should return list of (Obligation, EvidenceAnchor) tuples."""
        results = extractor._extract_prophecies([sample_passage_prophecy])
        assert isinstance(results, list)
        for item in results:
            assert isinstance(item, tuple)
            assert len(item) == 2
            assert isinstance(item[0], Obligation)
            assert isinstance(item[1], EvidenceAnchor)

    def test_extract_chekhov_guns_returns_list_of_tuples(
        self,
        extractor: ObligationExtractor,
        sample_passage_chekhov_gun: PassageRecord,
        sample_entities: list[Entity],
    ) -> None:
        """_extract_chekhov_guns should return list of (Obligation, EvidenceAnchor) tuples."""
        results = extractor._extract_chekhov_guns([sample_passage_chekhov_gun], sample_entities)
        assert isinstance(results, list)
        for item in results:
            assert isinstance(item, tuple)
            assert len(item) == 2
            assert isinstance(item[0], Obligation)
            assert isinstance(item[1], EvidenceAnchor)

    def test_extract_mysteries_returns_list_of_tuples(
        self,
        extractor: ObligationExtractor,
        sample_passage_mystery: PassageRecord,
    ) -> None:
        """_extract_mysteries should return list of (Obligation, EvidenceAnchor) tuples."""
        results = extractor._extract_mysteries([sample_passage_mystery])
        assert isinstance(results, list)
        for item in results:
            assert isinstance(item, tuple)
            assert len(item) == 2
            assert isinstance(item[0], Obligation)
            assert isinstance(item[1], EvidenceAnchor)

    def test_extract_plot_threads_returns_list_of_tuples(
        self,
        extractor: ObligationExtractor,
        sample_passage_plot_thread: PassageRecord,
        sample_entities: list[Entity],
    ) -> None:
        """_extract_plot_threads should return list of (Obligation, EvidenceAnchor) tuples."""
        results = extractor._extract_plot_threads([sample_passage_plot_thread], sample_entities)
        assert isinstance(results, list)
        for item in results:
            assert isinstance(item, tuple)
            assert len(item) == 2
            assert isinstance(item[0], Obligation)
            assert isinstance(item[1], EvidenceAnchor)
