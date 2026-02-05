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
from showrunner.contracts.wiki import (
    Event,
    EventType,
    Relationship,
    RelationshipType,
    StoryOrder,
    StoryTime,
)
from showrunner.graph.incremental_sync import build_incremental_graph_payload, source_ids_from_paths


def _state_fixture() -> dict[str, object]:
    return {
        "entities": [
            Entity(
                entity_id="ent_arya",
                canonical_name="Arya Stark",
                entity_type=EntityType.PERSON,
                first_seen_passage="book1:0",
                mention_count=3,
            ),
            Entity(
                entity_id="ent_jon",
                canonical_name="Jon Snow",
                entity_type=EntityType.PERSON,
                first_seen_passage="book2:0",
                mention_count=2,
            ),
        ],
        "passages": [
            PassageRecord(
                passage_id="book1:0",
                source_id="book1",
                paragraph_index=0,
                text="Arya fought.",
                char_start=0,
                char_end=12,
            ),
            PassageRecord(
                passage_id="book2:0",
                source_id="book2",
                paragraph_index=0,
                text="Jon marched.",
                char_start=0,
                char_end=12,
            ),
        ],
        "evidence_anchors": [
            EvidenceAnchor(
                anchor_id="ev_1",
                passage_id="book1:0",
                char_start=0,
                char_end=12,
                excerpt="Arya fought.",
            ),
            EvidenceAnchor(
                anchor_id="ev_2",
                passage_id="book2:0",
                char_start=0,
                char_end=12,
                excerpt="Jon marched.",
            ),
        ],
        "obligations": [
            Obligation(
                obligation_id="obl_1",
                category=ObligationCategory.PLOT_THREAD,
                description="Arya survives",
                evidence_anchor_ids=["ev_1"],
                last_seen_passage_id="book1:0",
                confidence=0.8,
                related_entity_ids=["ent_arya"],
            ),
            Obligation(
                obligation_id="obl_2",
                category=ObligationCategory.PLOT_THREAD,
                description="Jon survives",
                evidence_anchor_ids=["ev_2"],
                last_seen_passage_id="book2:0",
                confidence=0.8,
                related_entity_ids=["ent_jon"],
            ),
        ],
        "events": [
            Event(
                event_id="evt_1",
                event_type=EventType.BATTLE,
                title="Battle one",
                description="Arya fought.",
                participant_entity_ids=["ent_arya"],
                location_entity_id=None,
                related_obligation_ids=["obl_1"],
                evidence_anchor_ids=["ev_1"],
                story_time=StoryTime(time_label="book1"),
                story_order=StoryOrder(
                    order_index=0,
                    order_label="book1:0",
                    source_id="book1",
                    passage_id="book1:0",
                ),
                created_at=datetime(2026, 2, 5, 12, 0, 0),
            ),
            Event(
                event_id="evt_2",
                event_type=EventType.BATTLE,
                title="Battle two",
                description="Jon marched.",
                participant_entity_ids=["ent_jon"],
                location_entity_id=None,
                related_obligation_ids=["obl_2"],
                evidence_anchor_ids=["ev_2"],
                story_time=StoryTime(time_label="book2"),
                story_order=StoryOrder(
                    order_index=0,
                    order_label="book2:0",
                    source_id="book2",
                    passage_id="book2:0",
                ),
                created_at=datetime(2026, 2, 5, 12, 0, 0),
            ),
        ],
        "relationships": [
            Relationship(
                relationship_id="rel_1",
                relation_type=RelationshipType.ALLIANCE,
                source_entity_id="ent_arya",
                target_entity_id="ent_jon",
                description="temp",
                evidence_anchor_ids=["ev_1"],
                story_time=StoryTime(time_label="book1"),
                story_order=StoryOrder(
                    order_index=0,
                    order_label="book1:0",
                    source_id="book1",
                    passage_id="book1:0",
                ),
                created_at=datetime(2026, 2, 5, 12, 0, 0),
            )
        ],
    }


def test_source_ids_from_paths_uses_file_stem() -> None:
    source_ids = source_ids_from_paths(["C:/repo/corpus/book1.txt", "C:/repo/corpus/book2.md"])
    assert source_ids == {"book1", "book2"}


def test_build_incremental_graph_payload_filters_to_changed_sources() -> None:
    nodes, edges = build_incremental_graph_payload(
        state=_state_fixture(),
        changed_source_ids={"book1"},
    )

    assert any(node.node_id == "book1:0" for node in nodes)
    assert not any(node.node_id == "book2:0" for node in nodes)
    assert not any(node.node_id == "evt_2" for node in nodes)

    edge_ids = {edge.edge_id for edge in edges}
    assert edge_ids
