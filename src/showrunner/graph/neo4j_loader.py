"""Neo4j graph model + idempotent loader for Showrunner artifacts.

This module maps canonical stores into a property graph with provenance-first
relationships and uses MERGE-based upserts so the loader is safe to rerun.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from datetime import datetime

    from showrunner.contracts import Entity, EvidenceAnchor, Obligation, PassageRecord
    from showrunner.contracts.wiki import Event, Relationship

_NODE_LABELS = (
    "Entity",
    "Event",
    "Relationship",
    "Obligation",
    "Passage",
    "EvidenceAnchor",
)

_EDGE_TYPES = (
    "PARTICIPATES_IN",
    "LOCATED_AT",
    "RELATES_TO",
    "SUPPORTED_BY",
    "APPEARS_IN",
    "RESOLVES",
)


class Neo4jSessionProtocol(Protocol):
    """Minimal session protocol required by the loader."""

    def run(self, query: str, parameters: dict[str, Any] | None = None) -> Any:
        """Execute a Cypher statement."""


@dataclass(frozen=True)
class GraphNode:
    """Canonical node representation before DB upsert."""

    label: str
    node_id: str
    properties: dict[str, Any]


@dataclass(frozen=True)
class GraphEdge:
    """Canonical relationship representation before DB upsert."""

    rel_type: str
    source_label: str
    source_id: str
    target_label: str
    target_id: str
    edge_id: str
    properties: dict[str, Any]


class Neo4jGraphLoader:
    """Builds and loads a provenance-first graph model into Neo4j."""

    @staticmethod
    def schema_queries() -> list[str]:
        """Return Neo4j constraints for idempotent upserts."""
        node_queries = [
            (
                f"CREATE CONSTRAINT {label.lower()}_id_unique IF NOT EXISTS "
                f"FOR (n:{label}) REQUIRE n.id IS UNIQUE"
            )
            for label in _NODE_LABELS
        ]
        edge_queries = [
            (
                f"CREATE CONSTRAINT {edge_type.lower()}_edge_id_unique IF NOT EXISTS "
                f"FOR ()-[r:{edge_type}]-() REQUIRE r.edge_id IS UNIQUE"
            )
            for edge_type in _EDGE_TYPES
        ]
        index_queries = [
            (
                "CREATE INDEX event_story_order_index IF NOT EXISTS "
                "FOR (n:Event) ON (n.story_order_index)"
            ),
            (
                "CREATE INDEX relationship_story_order_index IF NOT EXISTS "
                "FOR (n:Relationship) ON (n.story_order_index)"
            ),
            (
                "CREATE INDEX obligation_last_seen_passage_index IF NOT EXISTS "
                "FOR (n:Obligation) ON (n.last_seen_passage_id)"
            ),
            ("CREATE INDEX passage_source_id_index IF NOT EXISTS FOR (n:Passage) ON (n.source_id)"),
            (
                "CREATE INDEX anchor_passage_id_index IF NOT EXISTS "
                "FOR (n:EvidenceAnchor) ON (n.passage_id)"
            ),
        ]
        return node_queries + edge_queries + index_queries

    def build_graph(
        self,
        *,
        entities: list[Entity],
        events: list[Event],
        relationships: list[Relationship],
        obligations: list[Obligation],
        passages: list[PassageRecord],
        anchors: list[EvidenceAnchor],
    ) -> tuple[list[GraphNode], list[GraphEdge]]:
        """Build deterministic nodes and edges from pipeline artifacts."""
        node_map: dict[tuple[str, str], GraphNode] = {}
        edge_map: dict[str, GraphEdge] = {}

        for passage in passages:
            passage_story_order = {
                "order_index": passage.paragraph_index,
                "passage_id": passage.passage_id,
                "source_id": passage.source_id,
            }
            self._put_node(
                node_map,
                GraphNode(
                    label="Passage",
                    node_id=passage.passage_id,
                    properties={
                        "source_id": passage.source_id,
                        "paragraph_index": passage.paragraph_index,
                        "text": passage.text,
                        "char_start": passage.char_start,
                        "char_end": passage.char_end,
                        "story_time": None,
                        "story_order": self._serialize_json(passage_story_order),
                        "story_time_label": None,
                        "story_time_start": None,
                        "story_time_end": None,
                        "story_order_index": passage.paragraph_index,
                        "story_order_label": None,
                        "story_order_source_id": passage.source_id,
                        "story_order_passage_id": passage.passage_id,
                        "created_at": None,
                    },
                ),
            )

        for anchor in anchors:
            self._put_node(
                node_map,
                GraphNode(
                    label="EvidenceAnchor",
                    node_id=anchor.anchor_id,
                    properties={
                        "passage_id": anchor.passage_id,
                        "char_start": anchor.char_start,
                        "char_end": anchor.char_end,
                        "excerpt": anchor.excerpt,
                        "story_time": None,
                        "story_order": None,
                        "story_time_label": None,
                        "story_time_start": None,
                        "story_time_end": None,
                        "story_order_index": None,
                        "story_order_label": None,
                        "story_order_source_id": None,
                        "story_order_passage_id": None,
                        "created_at": None,
                    },
                ),
            )
            self._put_edge(
                edge_map,
                self._edge(
                    rel_type="APPEARS_IN",
                    source_label="EvidenceAnchor",
                    source_id=anchor.anchor_id,
                    target_label="Passage",
                    target_id=anchor.passage_id,
                ),
            )

        for entity in entities:
            self._put_node(
                node_map,
                GraphNode(
                    label="Entity",
                    node_id=entity.entity_id,
                    properties={
                        "canonical_name": entity.canonical_name,
                        "entity_type": entity.entity_type.value,
                        "first_seen_passage": entity.first_seen_passage,
                        "mention_count": entity.mention_count,
                        "is_important": entity.is_important,
                        "description": entity.description,
                        "story_time": None,
                        "story_order": None,
                        "story_time_label": None,
                        "story_time_start": None,
                        "story_time_end": None,
                        "story_order_index": None,
                        "story_order_label": None,
                        "story_order_source_id": None,
                        "story_order_passage_id": None,
                        "created_at": None,
                    },
                ),
            )
            self._put_edge(
                edge_map,
                self._edge(
                    rel_type="APPEARS_IN",
                    source_label="Entity",
                    source_id=entity.entity_id,
                    target_label="Passage",
                    target_id=entity.first_seen_passage,
                ),
            )

        for obligation in obligations:
            self._put_node(
                node_map,
                GraphNode(
                    label="Obligation",
                    node_id=obligation.obligation_id,
                    properties={
                        "category": obligation.category.value,
                        "description": obligation.description,
                        "last_seen_passage_id": obligation.last_seen_passage_id,
                        "confidence": obligation.confidence,
                        "is_resolved": obligation.is_resolved,
                        "resolution_passage_id": obligation.resolution_passage_id,
                        "story_time": None,
                        "story_order": None,
                        "story_time_label": None,
                        "story_time_start": None,
                        "story_time_end": None,
                        "story_order_index": None,
                        "story_order_label": None,
                        "story_order_source_id": None,
                        "story_order_passage_id": None,
                        "created_at": None,
                    },
                ),
            )
            self._put_edge(
                edge_map,
                self._edge(
                    rel_type="APPEARS_IN",
                    source_label="Obligation",
                    source_id=obligation.obligation_id,
                    target_label="Passage",
                    target_id=obligation.last_seen_passage_id,
                ),
            )
            for entity_id in obligation.related_entity_ids:
                self._put_edge(
                    edge_map,
                    self._edge(
                        rel_type="RELATES_TO",
                        source_label="Obligation",
                        source_id=obligation.obligation_id,
                        target_label="Entity",
                        target_id=entity_id,
                    ),
                )
            for anchor_id in obligation.evidence_anchor_ids:
                self._put_edge(
                    edge_map,
                    self._edge(
                        rel_type="SUPPORTED_BY",
                        source_label="Obligation",
                        source_id=obligation.obligation_id,
                        target_label="EvidenceAnchor",
                        target_id=anchor_id,
                    ),
                )

        for event in events:
            event_story_time = event.story_time.model_dump()
            event_story_order = event.story_order.model_dump()
            event_created_at = self._datetime_to_iso(event.created_at)
            self._put_node(
                node_map,
                GraphNode(
                    label="Event",
                    node_id=event.event_id,
                    properties={
                        "event_type": event.event_type.value,
                        "title": event.title,
                        "description": event.description,
                        "location_entity_id": event.location_entity_id,
                        "story_time": self._serialize_json(event_story_time),
                        "story_order": self._serialize_json(event_story_order),
                        "story_time_label": event.story_time.time_label,
                        "story_time_start": event.story_time.time_start,
                        "story_time_end": event.story_time.time_end,
                        "story_order_index": event.story_order.order_index,
                        "story_order_label": event.story_order.order_label,
                        "story_order_source_id": event.story_order.source_id,
                        "story_order_passage_id": event.story_order.passage_id,
                        "created_at": event_created_at,
                    },
                ),
            )
            if event.story_order.passage_id is not None:
                self._put_edge(
                    edge_map,
                    self._edge(
                        rel_type="APPEARS_IN",
                        source_label="Event",
                        source_id=event.event_id,
                        target_label="Passage",
                        target_id=event.story_order.passage_id,
                        story_time=event_story_time,
                        story_order=event_story_order,
                        created_at=event_created_at,
                    ),
                )
            for entity_id in event.participant_entity_ids:
                self._put_edge(
                    edge_map,
                    self._edge(
                        rel_type="PARTICIPATES_IN",
                        source_label="Entity",
                        source_id=entity_id,
                        target_label="Event",
                        target_id=event.event_id,
                        story_time=event_story_time,
                        story_order=event_story_order,
                        created_at=event_created_at,
                    ),
                )
            if event.location_entity_id is not None:
                self._put_edge(
                    edge_map,
                    self._edge(
                        rel_type="LOCATED_AT",
                        source_label="Event",
                        source_id=event.event_id,
                        target_label="Entity",
                        target_id=event.location_entity_id,
                        story_time=event_story_time,
                        story_order=event_story_order,
                        created_at=event_created_at,
                    ),
                )
            for obligation_id in event.related_obligation_ids:
                self._put_edge(
                    edge_map,
                    self._edge(
                        rel_type="RESOLVES",
                        source_label="Event",
                        source_id=event.event_id,
                        target_label="Obligation",
                        target_id=obligation_id,
                        story_time=event_story_time,
                        story_order=event_story_order,
                        created_at=event_created_at,
                    ),
                )
            for anchor_id in event.evidence_anchor_ids:
                self._put_edge(
                    edge_map,
                    self._edge(
                        rel_type="SUPPORTED_BY",
                        source_label="Event",
                        source_id=event.event_id,
                        target_label="EvidenceAnchor",
                        target_id=anchor_id,
                        story_time=event_story_time,
                        story_order=event_story_order,
                        created_at=event_created_at,
                    ),
                )

        for relationship in relationships:
            rel_story_time = relationship.story_time.model_dump()
            rel_story_order = relationship.story_order.model_dump()
            rel_created_at = self._datetime_to_iso(relationship.created_at)
            self._put_node(
                node_map,
                GraphNode(
                    label="Relationship",
                    node_id=relationship.relationship_id,
                    properties={
                        "relation_type": relationship.relation_type.value,
                        "source_entity_id": relationship.source_entity_id,
                        "target_entity_id": relationship.target_entity_id,
                        "description": relationship.description,
                        "story_time": self._serialize_json(rel_story_time),
                        "story_order": self._serialize_json(rel_story_order),
                        "story_time_label": relationship.story_time.time_label,
                        "story_time_start": relationship.story_time.time_start,
                        "story_time_end": relationship.story_time.time_end,
                        "story_order_index": relationship.story_order.order_index,
                        "story_order_label": relationship.story_order.order_label,
                        "story_order_source_id": relationship.story_order.source_id,
                        "story_order_passage_id": relationship.story_order.passage_id,
                        "created_at": rel_created_at,
                    },
                ),
            )
            if relationship.story_order.passage_id is not None:
                self._put_edge(
                    edge_map,
                    self._edge(
                        rel_type="APPEARS_IN",
                        source_label="Relationship",
                        source_id=relationship.relationship_id,
                        target_label="Passage",
                        target_id=relationship.story_order.passage_id,
                        story_time=rel_story_time,
                        story_order=rel_story_order,
                        created_at=rel_created_at,
                    ),
                )
            self._put_edge(
                edge_map,
                self._edge(
                    rel_type="RELATES_TO",
                    source_label="Relationship",
                    source_id=relationship.relationship_id,
                    target_label="Entity",
                    target_id=relationship.source_entity_id,
                    story_time=rel_story_time,
                    story_order=rel_story_order,
                    created_at=rel_created_at,
                ),
            )
            self._put_edge(
                edge_map,
                self._edge(
                    rel_type="RELATES_TO",
                    source_label="Relationship",
                    source_id=relationship.relationship_id,
                    target_label="Entity",
                    target_id=relationship.target_entity_id,
                    story_time=rel_story_time,
                    story_order=rel_story_order,
                    created_at=rel_created_at,
                ),
            )
            for anchor_id in relationship.evidence_anchor_ids:
                self._put_edge(
                    edge_map,
                    self._edge(
                        rel_type="SUPPORTED_BY",
                        source_label="Relationship",
                        source_id=relationship.relationship_id,
                        target_label="EvidenceAnchor",
                        target_id=anchor_id,
                        story_time=rel_story_time,
                        story_order=rel_story_order,
                        created_at=rel_created_at,
                    ),
                )

        nodes = sorted(node_map.values(), key=lambda item: (item.label, item.node_id))
        edges = sorted(edge_map.values(), key=lambda item: item.edge_id)
        return nodes, edges

    def load(
        self,
        *,
        session: Neo4jSessionProtocol,
        nodes: list[GraphNode],
        edges: list[GraphEdge],
        apply_schema: bool = True,
    ) -> None:
        """Upsert graph data into Neo4j with idempotent MERGE statements."""
        if apply_schema:
            for query in self.schema_queries():
                session.run(query)

        for node in nodes:
            query = (
                f"MERGE (n:{self._safe_node_label(node.label)} {{id: $id}}) SET n += $properties"
            )
            session.run(query, {"id": node.node_id, "properties": node.properties})

        for edge in edges:
            rel_type = self._safe_rel_type(edge.rel_type)
            source_label = self._safe_node_label(edge.source_label)
            target_label = self._safe_node_label(edge.target_label)
            query = (
                f"MATCH (s:{source_label} {{id: $source_id}}) "
                f"MATCH (t:{target_label} {{id: $target_id}}) "
                f"MERGE (s)-[r:{rel_type} {{edge_id: $edge_id}}]->(t) "
                "SET r += $properties"
            )
            session.run(
                query,
                {
                    "source_id": edge.source_id,
                    "target_id": edge.target_id,
                    "edge_id": edge.edge_id,
                    "properties": edge.properties,
                },
            )

    def _put_node(self, node_map: dict[tuple[str, str], GraphNode], node: GraphNode) -> None:
        node_map[(node.label, node.node_id)] = node

    def _put_edge(self, edge_map: dict[str, GraphEdge], edge: GraphEdge) -> None:
        edge_map[edge.edge_id] = edge

    def _edge(
        self,
        *,
        rel_type: str,
        source_label: str,
        source_id: str,
        target_label: str,
        target_id: str,
        story_time: dict[str, Any] | None = None,
        story_order: dict[str, Any] | None = None,
        created_at: str | None = None,
    ) -> GraphEdge:
        edge_id = self._stable_id(
            "edge",
            rel_type,
            source_label,
            source_id,
            target_label,
            target_id,
        )
        return GraphEdge(
            rel_type=rel_type,
            source_label=source_label,
            source_id=source_id,
            target_label=target_label,
            target_id=target_id,
            edge_id=edge_id,
            properties={
                "story_time": self._serialize_json(story_time),
                "story_order": self._serialize_json(story_order),
                "story_time_label": self._nested_value(story_time, "time_label"),
                "story_time_start": self._nested_value(story_time, "time_start"),
                "story_time_end": self._nested_value(story_time, "time_end"),
                "story_order_index": self._nested_value(story_order, "order_index"),
                "story_order_label": self._nested_value(story_order, "order_label"),
                "story_order_source_id": self._nested_value(story_order, "source_id"),
                "story_order_passage_id": self._nested_value(story_order, "passage_id"),
                "created_at": created_at,
            },
        )

    def _stable_id(self, prefix: str, *parts: str) -> str:
        payload = "|".join(parts)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
        return f"{prefix}_{digest}"

    def _safe_node_label(self, label: str) -> str:
        if label not in _NODE_LABELS:
            raise ValueError(f"Unsupported node label: {label}")
        return label

    def _safe_rel_type(self, rel_type: str) -> str:
        if rel_type not in _EDGE_TYPES:
            raise ValueError(f"Unsupported relationship type: {rel_type}")
        return rel_type

    def _datetime_to_iso(self, value: datetime) -> str:
        return value.isoformat()

    def _nested_value(self, payload: dict[str, Any] | None, key: str) -> Any:
        if payload is None:
            return None
        return payload.get(key)

    def _serialize_json(self, payload: dict[str, Any] | None) -> str | None:
        if payload is None:
            return None
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))
