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
from showrunner.graph.neo4j_loader import Neo4jGraphLoader


class _FakeSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    def run(self, query: str, parameters: dict[str, object] | None = None) -> None:
        self.calls.append((query, parameters or {}))


def _sample_data() -> tuple[
    list[Entity],
    list[Event],
    list[Relationship],
    list[Obligation],
    list[PassageRecord],
    list[EvidenceAnchor],
]:
    entities = [
        Entity(
            entity_id="ent_arya",
            canonical_name="Arya Stark",
            entity_type=EntityType.PERSON,
            first_seen_passage="book1:0",
            mention_count=3,
        ),
        Entity(
            entity_id="ent_winterfell",
            canonical_name="Winterfell",
            entity_type=EntityType.PLACE,
            first_seen_passage="book1:0",
            mention_count=2,
        ),
    ]

    passages = [
        PassageRecord(
            passage_id="book1:0",
            source_id="book1",
            paragraph_index=0,
            text="Arya fought at Winterfell.",
            char_start=0,
            char_end=27,
        )
    ]

    anchors = [
        EvidenceAnchor(
            anchor_id="ev_001",
            passage_id="book1:0",
            char_start=0,
            char_end=27,
            excerpt="Arya fought at Winterfell.",
        )
    ]

    obligations = [
        Obligation(
            obligation_id="obl_001",
            category=ObligationCategory.PLOT_THREAD,
            description="Arya must survive the war.",
            evidence_anchor_ids=["ev_001"],
            last_seen_passage_id="book1:0",
            confidence=0.8,
            related_entity_ids=["ent_arya"],
        )
    ]

    events = [
        Event(
            event_id="evt_001",
            event_type=EventType.BATTLE,
            title="Battle of Winterfell",
            description="Arya fought at Winterfell.",
            participant_entity_ids=["ent_arya"],
            location_entity_id="ent_winterfell",
            related_obligation_ids=["obl_001"],
            evidence_anchor_ids=["ev_001"],
            story_time=StoryTime(time_label="unknown"),
            story_order=StoryOrder(
                order_index=0,
                order_label="book1:0",
                source_id="book1",
                passage_id="book1:0",
            ),
            created_at=datetime(2026, 2, 5, 12, 0, 0),
        )
    ]

    relationships = [
        Relationship(
            relationship_id="rel_001",
            relation_type=RelationshipType.ALLIANCE,
            source_entity_id="ent_arya",
            target_entity_id="ent_winterfell",
            description="Arya defends Winterfell.",
            evidence_anchor_ids=["ev_001"],
            story_time=StoryTime(time_label="unknown"),
            story_order=StoryOrder(
                order_index=0,
                order_label="book1:0",
                source_id="book1",
                passage_id="book1:0",
            ),
            created_at=datetime(2026, 2, 5, 12, 0, 0),
        )
    ]
    return entities, events, relationships, obligations, passages, anchors


def test_schema_queries_cover_required_nodes_and_edges() -> None:
    queries = Neo4jGraphLoader.schema_queries()

    for node_label in (
        "Entity",
        "Event",
        "Relationship",
        "Obligation",
        "Passage",
        "EvidenceAnchor",
    ):
        assert any(node_label in query for query in queries)

    for edge_type in (
        "PARTICIPATES_IN",
        "LOCATED_AT",
        "RELATES_TO",
        "SUPPORTED_BY",
        "APPEARS_IN",
        "RESOLVES",
    ):
        assert any(edge_type in query for query in queries)


def test_build_graph_contains_required_nodes_edges_and_provenance_fields() -> None:
    loader = Neo4jGraphLoader()
    entities, events, relationships, obligations, passages, anchors = _sample_data()

    nodes, edges = loader.build_graph(
        entities=entities,
        events=events,
        relationships=relationships,
        obligations=obligations,
        passages=passages,
        anchors=anchors,
    )

    assert {"Entity", "Event", "Relationship", "Obligation", "Passage", "EvidenceAnchor"} <= {
        node.label for node in nodes
    }
    assert {
        "PARTICIPATES_IN",
        "LOCATED_AT",
        "RELATES_TO",
        "SUPPORTED_BY",
        "APPEARS_IN",
        "RESOLVES",
    } <= {edge.rel_type for edge in edges}

    event_node = next(node for node in nodes if node.label == "Event")
    assert "story_time" in event_node.properties
    assert "story_order" in event_node.properties
    assert "created_at" in event_node.properties


def test_edge_ids_are_deterministic_for_same_inputs() -> None:
    loader = Neo4jGraphLoader()
    entities, events, relationships, obligations, passages, anchors = _sample_data()

    first_nodes, first_edges = loader.build_graph(
        entities=entities,
        events=events,
        relationships=relationships,
        obligations=obligations,
        passages=passages,
        anchors=anchors,
    )
    second_nodes, second_edges = loader.build_graph(
        entities=entities,
        events=events,
        relationships=relationships,
        obligations=obligations,
        passages=passages,
        anchors=anchors,
    )

    assert [(n.label, n.node_id) for n in first_nodes] == [
        (n.label, n.node_id) for n in second_nodes
    ]
    assert sorted(edge.edge_id for edge in first_edges) == sorted(
        edge.edge_id for edge in second_edges
    )


def test_loader_uses_merge_for_idempotent_upserts() -> None:
    loader = Neo4jGraphLoader()
    entities, events, relationships, obligations, passages, anchors = _sample_data()
    nodes, edges = loader.build_graph(
        entities=entities,
        events=events,
        relationships=relationships,
        obligations=obligations,
        passages=passages,
        anchors=anchors,
    )

    session = _FakeSession()
    loader.load(session=session, nodes=nodes, edges=edges, apply_schema=True)
    first_call_count = len(session.calls)

    loader.load(session=session, nodes=nodes, edges=edges, apply_schema=True)
    assert len(session.calls) == first_call_count * 2

    node_upserts = [query for query, _ in session.calls if "MERGE (n:" in query]
    edge_upserts = [query for query, _ in session.calls if "MERGE (s)-[r:" in query]

    assert node_upserts
    assert edge_upserts
    assert all("MERGE" in query for query in node_upserts + edge_upserts)
    assert any("PARTICIPATES_IN" in query for query in edge_upserts)

    edge_params = [params for query, params in session.calls if "MERGE (s)-[r:" in query]
    assert all("edge_id" in params for params in edge_params)
