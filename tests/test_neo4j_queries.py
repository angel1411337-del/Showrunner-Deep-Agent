from __future__ import annotations

from showrunner.graph.queries import Neo4jQueryLayer


class _FakeSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    def run(
        self, query: str, parameters: dict[str, object] | None = None
    ) -> list[dict[str, object]]:
        self.calls.append((query, parameters or {}))
        return [{"ok": True}]


def test_events_for_entity_uses_participates_in() -> None:
    query_layer = Neo4jQueryLayer()
    session = _FakeSession()

    result = query_layer.events_for_entity(session=session, entity_id="ent_arya")

    assert result == [{"ok": True}]
    query, params = session.calls[-1]
    assert "PARTICIPATES_IN" in query
    assert params["entity_id"] == "ent_arya"


def test_relationships_active_during_uses_story_time_range_filters() -> None:
    query_layer = Neo4jQueryLayer()
    session = _FakeSession()

    result = query_layer.relationships_active_during(
        session=session,
        time_value="298 AC",
    )

    assert result == [{"ok": True}]
    query, params = session.calls[-1]
    assert "Relationship" in query
    assert "story_time_start" in query
    assert "story_time_end" in query
    assert params["time_value"] == "298 AC"


def test_obligations_resolved_by_event_uses_resolves_edge() -> None:
    query_layer = Neo4jQueryLayer()
    session = _FakeSession()

    result = query_layer.obligations_resolved_by_event(session=session, event_id="evt_001")

    assert result == [{"ok": True}]
    query, params = session.calls[-1]
    assert "RESOLVES" in query
    assert params["event_id"] == "evt_001"


def test_evidence_for_relationship_uses_supported_by_and_appears_in() -> None:
    query_layer = Neo4jQueryLayer()
    session = _FakeSession()

    result = query_layer.evidence_for_relationship(session=session, relationship_id="rel_001")

    assert result == [{"ok": True}]
    query, params = session.calls[-1]
    assert "SUPPORTED_BY" in query
    assert "APPEARS_IN" in query
    assert params["relationship_id"] == "rel_001"


def test_timeline_for_entity_uses_events_and_relationships() -> None:
    query_layer = Neo4jQueryLayer()
    session = _FakeSession()

    result = query_layer.timeline_for_entity(session=session, entity_id="ent_arya")

    assert result == [{"ok": True}]
    query, params = session.calls[-1]
    assert "PARTICIPATES_IN" in query
    assert "RELATES_TO" in query
    assert "UNION ALL" in query
    assert params["entity_id"] == "ent_arya"
