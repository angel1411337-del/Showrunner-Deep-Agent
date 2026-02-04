from __future__ import annotations

from datetime import datetime

from showrunner.contracts import (
    Entity,
    EntityType,
    EvidenceAnchor,
    Obligation,
    ObligationCategory,
    PassageRecord,
)
from showrunner.contracts.wiki import EventType
from showrunner.extractors.event_extractor import EventExtractor


def _sample_passages() -> list[PassageRecord]:
    return [
        PassageRecord(
            passage_id="book1:0",
            source_id="book1",
            paragraph_index=0,
            text="The battle of Winterfell erupted as Arya fought the Night King.",
            char_start=0,
            char_end=67,
        )
    ]


def _sample_entities() -> list[Entity]:
    return [
        Entity(
            entity_id="ent_arya",
            canonical_name="Arya",
            entity_type=EntityType.PERSON,
            first_seen_passage="book1:0",
            mention_count=3,
        ),
        Entity(
            entity_id="ent_nk",
            canonical_name="Night King",
            entity_type=EntityType.PERSON,
            first_seen_passage="book1:0",
            mention_count=2,
        ),
        Entity(
            entity_id="ent_winterfell",
            canonical_name="Winterfell",
            entity_type=EntityType.PLACE,
            first_seen_passage="book1:0",
            mention_count=5,
        ),
    ]


def _sample_anchors() -> list[EvidenceAnchor]:
    return [
        EvidenceAnchor(
            anchor_id="ev_battle_001",
            passage_id="book1:0",
            char_start=0,
            char_end=67,
            excerpt="The battle of Winterfell erupted as Arya fought the Night King.",
        )
    ]


def _sample_obligations() -> list[Obligation]:
    return [
        Obligation(
            obligation_id="obl_001",
            category=ObligationCategory.PLOT_THREAD,
            description="Arya must defeat the Night King",
            evidence_anchor_ids=["ev_battle_001"],
            last_seen_passage_id="book1:0",
            confidence=0.9,
        )
    ]


def test_extract_battle_event_includes_provenance_and_time_fields() -> None:
    passages = _sample_passages()
    entities = _sample_entities()
    anchors = _sample_anchors()
    obligations = _sample_obligations()

    extractor = EventExtractor()
    events = extractor.extract(passages, entities, obligations, anchors)

    assert len(events) == 1
    event = events[0]

    assert event.event_type == EventType.BATTLE
    assert event.title
    assert event.description
    assert set(event.participant_entity_ids) >= {"ent_arya", "ent_nk"}
    assert event.location_entity_id == "ent_winterfell"
    assert event.evidence_anchor_ids == ["ev_battle_001"]
    assert event.related_obligation_ids == ["obl_001"]
    assert event.story_order.order_index == 0
    assert event.story_order.order_label == "book1:0"
    assert event.story_order.passage_id == "book1:0"
    assert event.story_time.time_label is not None
    assert isinstance(event.created_at, datetime)


def test_extract_returns_no_events_when_no_keywords() -> None:
    passages = [
        PassageRecord(
            passage_id="book1:1",
            source_id="book1",
            paragraph_index=1,
            text="The wind was cold and the night was quiet.",
            char_start=70,
            char_end=115,
        )
    ]
    extractor = EventExtractor()
    events = extractor.extract(passages, _sample_entities(), _sample_obligations(), _sample_anchors())
    assert events == []


def test_event_ids_are_deterministic() -> None:
    passages = _sample_passages()
    entities = _sample_entities()
    anchors = _sample_anchors()
    obligations = _sample_obligations()

    extractor = EventExtractor()
    first = extractor.extract(passages, entities, obligations, anchors)
    second = extractor.extract(passages, entities, obligations, anchors)

    assert [event.event_id for event in first] == [event.event_id for event in second]
