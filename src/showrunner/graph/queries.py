"""Core Neo4j query layer for writer-facing graph retrievals."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, cast


class Neo4jSessionProtocol(Protocol):
    """Minimal query protocol used by the graph query layer."""

    def run(self, query: str, parameters: dict[str, Any] | None = None) -> Any:
        """Execute a Cypher query."""


class Neo4jQueryLayer:
    """Reusable Cypher queries that prove graph value before UI wiring."""

    def events_for_entity(
        self,
        *,
        session: Neo4jSessionProtocol,
        entity_id: str,
    ) -> list[dict[str, Any]]:
        """Return events connected to an entity through PARTICIPATES_IN."""
        query = """
            MATCH (e:Entity {id: $entity_id})-[:PARTICIPATES_IN]->(event:Event)
            OPTIONAL MATCH (event)-[:LOCATED_AT]->(location:Entity)
            RETURN
              event.id AS event_id,
              event.title AS title,
              event.event_type AS event_type,
              event.story_time_label AS story_time_label,
              event.story_order_index AS story_order_index,
              location.id AS location_entity_id
            ORDER BY event.story_order_index ASC, event.id ASC
        """
        return self._run(session=session, query=query, parameters={"entity_id": entity_id})

    def relationships_active_during(
        self,
        *,
        session: Neo4jSessionProtocol,
        time_value: str,
    ) -> list[dict[str, Any]]:
        """Return relationships whose story-time range includes the given value."""
        query = """
            MATCH (r:Relationship)
            WHERE
              r.story_time_label = $time_value
              OR (
                r.story_time_start IS NOT NULL
                AND r.story_time_end IS NOT NULL
                AND r.story_time_start <= $time_value
                AND r.story_time_end >= $time_value
              )
              OR (
                r.story_time_start IS NOT NULL
                AND r.story_time_end IS NULL
                AND r.story_time_start <= $time_value
              )
            RETURN
              r.id AS relationship_id,
              r.relation_type AS relation_type,
              r.source_entity_id AS source_entity_id,
              r.target_entity_id AS target_entity_id,
              r.story_time_label AS story_time_label,
              r.story_time_start AS story_time_start,
              r.story_time_end AS story_time_end,
              r.story_order_index AS story_order_index
            ORDER BY r.story_order_index ASC, r.id ASC
        """
        return self._run(session=session, query=query, parameters={"time_value": time_value})

    def obligations_resolved_by_event(
        self,
        *,
        session: Neo4jSessionProtocol,
        event_id: str,
    ) -> list[dict[str, Any]]:
        """Return obligations linked to an event through RESOLVES."""
        query = """
            MATCH (event:Event {id: $event_id})-[:RESOLVES]->(ob:Obligation)
            RETURN
              ob.id AS obligation_id,
              ob.category AS category,
              ob.description AS description,
              ob.confidence AS confidence,
              ob.is_resolved AS is_resolved
            ORDER BY ob.id ASC
        """
        return self._run(session=session, query=query, parameters={"event_id": event_id})

    def evidence_for_relationship(
        self,
        *,
        session: Neo4jSessionProtocol,
        relationship_id: str,
    ) -> list[dict[str, Any]]:
        """Return evidence anchors and passages for a relationship."""
        query = """
            MATCH (r:Relationship {id: $relationship_id})-[:SUPPORTED_BY]->(a:EvidenceAnchor)
            MATCH (a)-[:APPEARS_IN]->(p:Passage)
            RETURN
              a.id AS anchor_id,
              a.excerpt AS excerpt,
              p.id AS passage_id,
              p.source_id AS source_id,
              p.paragraph_index AS paragraph_index
            ORDER BY p.source_id ASC, p.paragraph_index ASC, a.id ASC
        """
        return self._run(
            session=session, query=query, parameters={"relationship_id": relationship_id}
        )

    def timeline_for_entity(
        self,
        *,
        session: Neo4jSessionProtocol,
        entity_id: str,
    ) -> list[dict[str, Any]]:
        """Return an entity timeline across events and direct relationships."""
        query = """
            MATCH (:Entity {id: $entity_id})-[:PARTICIPATES_IN]->(event:Event)
            RETURN
              "event" AS item_type,
              event.id AS item_id,
              event.title AS label,
              event.story_time_label AS story_time_label,
              event.story_order_index AS story_order_index
            UNION ALL
            MATCH (r:Relationship)-[:RELATES_TO]->(:Entity {id: $entity_id})
            RETURN
              "relationship" AS item_type,
              r.id AS item_id,
              r.description AS label,
              r.story_time_label AS story_time_label,
              r.story_order_index AS story_order_index
            ORDER BY story_order_index ASC, item_id ASC
        """
        return self._run(session=session, query=query, parameters={"entity_id": entity_id})

    def _run(
        self,
        *,
        session: Neo4jSessionProtocol,
        query: str,
        parameters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        result = session.run(query, parameters)
        if isinstance(result, list):
            return self._normalize_rows(cast("list[Any]", result))
        if hasattr(result, "data"):
            data = result.data()
            if isinstance(data, list):
                return self._normalize_rows(cast("list[Any]", data))
        return []

    def _normalize_rows(self, rows: list[Any]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for row in rows:
            if isinstance(row, Mapping):
                typed_row = cast("Mapping[str, Any]", row)
                normalized.append(dict(typed_row))
        return normalized
