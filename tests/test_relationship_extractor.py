from __future__ import annotations

from datetime import datetime

from showrunner.contracts import Entity, EntityType, EvidenceAnchor, Obligation, PassageRecord
from showrunner.contracts.wiki import RelationshipType
from showrunner.extractors.relationship_extractor import RelationshipExtractor


def _sample_passages() -> list[PassageRecord]:
    return [
        PassageRecord(
            passage_id="book2:0",
            source_id="book2",
            paragraph_index=0,
            text="Arya allied with Jon Snow to defend Winterfell.",
            char_start=0,
            char_end=52,
        )
    ]


def _sample_entities() -> list[Entity]:
    return [
        Entity(
            entity_id="ent_arya",
            canonical_name="Arya",
            entity_type=EntityType.PERSON,
            first_seen_passage="book2:0",
            mention_count=3,
        ),
        Entity(
            entity_id="ent_jon",
            canonical_name="Jon Snow",
            entity_type=EntityType.PERSON,
            first_seen_passage="book2:0",
            mention_count=4,
        ),
        Entity(
            entity_id="ent_winterfell",
            canonical_name="Winterfell",
            entity_type=EntityType.PLACE,
            first_seen_passage="book2:0",
            mention_count=5,
        ),
    ]


def _sample_anchors() -> list[EvidenceAnchor]:
    return [
        EvidenceAnchor(
            anchor_id="ev_rel_001",
            passage_id="book2:0",
            char_start=0,
            char_end=52,
            excerpt="Arya allied with Jon Snow to defend Winterfell.",
        )
    ]


def test_extract_alliance_relationship_with_provenance() -> None:
    passages = _sample_passages()
    entities = _sample_entities()
    anchors = _sample_anchors()
    obligations: list[Obligation] = []

    extractor = RelationshipExtractor()
    relationships = extractor.extract(passages, entities, obligations, anchors)

    assert len(relationships) == 1
    relationship = relationships[0]

    assert relationship.relation_type == RelationshipType.ALLIANCE
    assert relationship.source_entity_id == "ent_arya"
    assert relationship.target_entity_id == "ent_jon"
    assert relationship.evidence_anchor_ids == ["ev_rel_001"]
    assert relationship.story_order.order_index == 0
    assert relationship.story_order.order_label == "book2:0"
    assert relationship.story_order.passage_id == "book2:0"
    assert relationship.story_time.time_label is not None
    assert isinstance(relationship.created_at, datetime)


def test_relationship_ids_are_deterministic() -> None:
    passages = _sample_passages()
    entities = _sample_entities()
    anchors = _sample_anchors()
    obligations: list[Obligation] = []

    extractor = RelationshipExtractor()
    first = extractor.extract(passages, entities, obligations, anchors)
    second = extractor.extract(passages, entities, obligations, anchors)

    assert [rel.relationship_id for rel in first] == [rel.relationship_id for rel in second]
