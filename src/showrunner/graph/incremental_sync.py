"""Incremental graph payload and hook sync helpers for Neo4j ingestion."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, cast

from showrunner.graph.neo4j_loader import GraphEdge, GraphNode, Neo4jGraphLoader

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from contextlib import AbstractContextManager

    from showrunner.contracts import Entity, EvidenceAnchor, Obligation, PassageRecord
    from showrunner.contracts.wiki import Event, Relationship


class Neo4jSessionProtocol(Protocol):
    """Minimal Neo4j session protocol required by the loader."""

    def run(self, query: str, parameters: dict[str, Any] | None = None) -> Any:
        """Execute a Cypher statement."""
        ...


class Neo4jDriverProtocol(Protocol):
    """Minimal Neo4j driver protocol for runtime loading."""

    def session(self) -> AbstractContextManager[Neo4jSessionProtocol]:
        """Create a new session context manager."""
        ...

    def close(self) -> None:
        """Close the driver."""
        ...


def source_ids_from_paths(paths: Iterable[str | Path]) -> set[str]:
    """Map changed file paths to source IDs using file stems."""
    source_ids: set[str] = set()
    for path in paths:
        stem = Path(path).stem.strip()
        if stem:
            source_ids.add(stem)
    return source_ids


def build_incremental_graph_payload(
    *,
    state: Mapping[str, object],
    changed_source_ids: set[str],
) -> tuple[list[GraphNode], list[GraphEdge]]:
    """Build a smallest-possible graph payload for changed source IDs."""
    if not changed_source_ids:
        return [], []

    passages = _passages_for_sources(_state_list(state, "passages"), changed_source_ids)
    changed_passage_ids = {passage.passage_id for passage in passages}

    anchors = _anchors_for_passages(_state_list(state, "evidence_anchors"), changed_passage_ids)
    changed_anchor_ids = {anchor.anchor_id for anchor in anchors}

    obligations = _obligations_for_changes(
        _state_list(state, "obligations"),
        changed_passage_ids=changed_passage_ids,
        changed_anchor_ids=changed_anchor_ids,
    )
    changed_obligation_ids = {obligation.obligation_id for obligation in obligations}

    events = _events_for_changes(
        _state_list(state, "events"),
        changed_source_ids=changed_source_ids,
        changed_passage_ids=changed_passage_ids,
        changed_anchor_ids=changed_anchor_ids,
        changed_obligation_ids=changed_obligation_ids,
    )
    relationships = _relationships_for_changes(
        _state_list(state, "relationships"),
        changed_source_ids=changed_source_ids,
        changed_passage_ids=changed_passage_ids,
        changed_anchor_ids=changed_anchor_ids,
    )

    entities = _entities_for_changes(
        _state_list(state, "entities"),
        changed_passage_ids=changed_passage_ids,
        obligations=obligations,
        events=events,
        relationships=relationships,
    )

    loader = Neo4jGraphLoader()
    return loader.build_graph(
        entities=entities,
        events=events,
        relationships=relationships,
        obligations=obligations,
        passages=passages,
        anchors=anchors,
    )


def sync_incremental_graph_update(
    *,
    state: Mapping[str, object],
    changed_files: list[Path],
) -> None:
    """Incrementally upsert affected nodes/edges into Neo4j when configured."""
    source_ids = source_ids_from_paths(changed_files)
    nodes, edges = build_incremental_graph_payload(state=state, changed_source_ids=source_ids)
    if not nodes and not edges:
        return

    uri = os.getenv("SHOWRUNNER_NEO4J_URI")
    password = os.getenv("SHOWRUNNER_NEO4J_PASSWORD")
    if not uri or not password:
        return
    username = os.getenv("SHOWRUNNER_NEO4J_USER", "neo4j")

    try:
        from neo4j import GraphDatabase  # type: ignore[import-untyped]
    except Exception:
        return

    graph_database = cast("Any", GraphDatabase)
    driver = cast("Neo4jDriverProtocol", graph_database.driver(uri, auth=(username, password)))
    try:
        with driver.session() as session:
            Neo4jGraphLoader().load(session=session, nodes=nodes, edges=edges, apply_schema=True)
    finally:
        driver.close()


def _state_list(state: Mapping[str, object], key: str) -> list[Any]:
    value = state.get(key, [])
    if isinstance(value, list):
        return cast("list[Any]", value)
    return []


def _passages_for_sources(
    passages: list[PassageRecord],
    source_ids: set[str],
) -> list[PassageRecord]:
    return [passage for passage in passages if passage.source_id in source_ids]


def _anchors_for_passages(
    anchors: list[EvidenceAnchor],
    passage_ids: set[str],
) -> list[EvidenceAnchor]:
    return [anchor for anchor in anchors if anchor.passage_id in passage_ids]


def _obligations_for_changes(
    obligations: list[Obligation],
    *,
    changed_passage_ids: set[str],
    changed_anchor_ids: set[str],
) -> list[Obligation]:
    selected: list[Obligation] = []
    for obligation in obligations:
        if obligation.last_seen_passage_id in changed_passage_ids or (
            set(obligation.evidence_anchor_ids) & changed_anchor_ids
        ):
            selected.append(obligation)
    return selected


def _events_for_changes(
    events: list[Event],
    *,
    changed_source_ids: set[str],
    changed_passage_ids: set[str],
    changed_anchor_ids: set[str],
    changed_obligation_ids: set[str],
) -> list[Event]:
    selected: list[Event] = []
    for event in events:
        source_match = (
            event.story_order.source_id in changed_source_ids
            or event.story_order.passage_id in changed_passage_ids
        )
        evidence_match = bool(set(event.evidence_anchor_ids) & changed_anchor_ids)
        obligation_match = bool(set(event.related_obligation_ids) & changed_obligation_ids)
        if source_match or evidence_match or obligation_match:
            selected.append(event)
    return selected


def _relationships_for_changes(
    relationships: list[Relationship],
    *,
    changed_source_ids: set[str],
    changed_passage_ids: set[str],
    changed_anchor_ids: set[str],
) -> list[Relationship]:
    selected: list[Relationship] = []
    for relationship in relationships:
        source_match = (
            relationship.story_order.source_id in changed_source_ids
            or relationship.story_order.passage_id in changed_passage_ids
        )
        evidence_match = bool(set(relationship.evidence_anchor_ids) & changed_anchor_ids)
        if source_match or evidence_match:
            selected.append(relationship)
    return selected


def _entities_for_changes(
    entities: list[Entity],
    *,
    changed_passage_ids: set[str],
    obligations: list[Obligation],
    events: list[Event],
    relationships: list[Relationship],
) -> list[Entity]:
    related_ids = {
        entity_id for obligation in obligations for entity_id in obligation.related_entity_ids
    }
    related_ids.update(entity_id for event in events for entity_id in event.participant_entity_ids)
    related_ids.update(relationship.source_entity_id for relationship in relationships)
    related_ids.update(relationship.target_entity_id for relationship in relationships)
    related_ids.update(
        event.location_entity_id for event in events if event.location_entity_id is not None
    )

    selected: list[Entity] = []
    for entity in entities:
        if entity.entity_id in related_ids or entity.first_seen_passage in changed_passage_ids:
            selected.append(entity)
    return selected
