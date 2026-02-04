"""Tests for wiki-oriented contracts (events, relationships, temporal metadata)."""

from datetime import datetime

import pytest

from showrunner.contracts import Event, Relationship, StoryOrder, StoryTime


def test_story_time_requires_at_least_label_or_bounds() -> None:
    with pytest.raises(ValueError):
        StoryTime(time_label=None, time_start=None, time_end=None)

    story_time = StoryTime(time_label="297 AC, late summer", time_start=None, time_end=None)
    assert story_time.time_label == "297 AC, late summer"


def test_story_order_requires_index() -> None:
    story_order = StoryOrder(order_index=5, order_label="book2:3", passage_id="book2:3")
    assert story_order.order_index == 5


def test_event_requires_provenance_and_time_fields() -> None:
    now = datetime(2026, 2, 4, 12, 0, 0)
    story_time = StoryTime(time_label="298 AC", time_start=None, time_end=None)
    story_order = StoryOrder(order_index=10, order_label="book3:1", passage_id="book3:1")

    event = Event(
        event_id="evt_001",
        event_type="battle",
        title="Battle of Blackwater",
        description="A decisive naval battle in King's Landing.",
        participant_entity_ids=["ent_stannis", "ent_tyrion"],
        location_entity_id="ent_kings_landing",
        evidence_anchor_ids=["anc_001"],
        story_time=story_time,
        story_order=story_order,
        created_at=now,
    )

    assert event.evidence_anchor_ids == ["anc_001"]
    assert event.story_time.time_label == "298 AC"


def test_relationship_requires_provenance_and_time_fields() -> None:
    now = datetime(2026, 2, 4, 12, 0, 0)
    story_time = StoryTime(time_label="299 AC", time_start=None, time_end=None)
    story_order = StoryOrder(order_index=22, order_label="book4:5", passage_id="book4:5")

    relation = Relationship(
        relationship_id="rel_001",
        relation_type="alliance",
        source_entity_id="ent_stark",
        target_entity_id="ent_tully",
        description="Alliance through marriage and shared goals.",
        evidence_anchor_ids=["anc_010"],
        story_time=story_time,
        story_order=story_order,
        created_at=now,
    )

    assert relation.relation_type == "alliance"
    assert relation.evidence_anchor_ids == ["anc_010"]
