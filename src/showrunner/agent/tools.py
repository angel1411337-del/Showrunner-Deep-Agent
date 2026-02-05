"""Tool wrappers for agent runtimes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from showrunner.agent.harness import AgentHarness, AgentRunResult
from showrunner.graph.queries import Neo4jQueryLayer, Neo4jSessionProtocol

if TYPE_CHECKING:
    from pathlib import Path


def run_pipeline(*, input_source: Path, output_dir: Path) -> AgentRunResult:
    harness = AgentHarness()
    return harness.run_pipeline(input_source=input_source, output_dir=output_dir)


def list_artifacts(*, output_dir: Path) -> list[str]:
    harness = AgentHarness()
    return harness.list_artifacts(output_dir=output_dir)


def read_artifact(*, output_dir: Path, relative_path: str) -> str:
    harness = AgentHarness()
    return harness.read_artifact(output_dir=output_dir, relative_path=relative_path)


def query_graph(
    *,
    query: str,
    parameters: dict[str, Any] | None,
    session: Neo4jSessionProtocol,
    query_layer: Neo4jQueryLayer | None = None,
) -> list[dict[str, Any]]:
    layer = query_layer or Neo4jQueryLayer()
    params = parameters or {}

    def require(name: str) -> Any:
        if name not in params:
            raise ValueError(f"Missing required parameter: {name}")
        return params[name]

    if query == "events_for_entity":
        return layer.events_for_entity(session=session, entity_id=require("entity_id"))
    if query == "relationships_active_during":
        return layer.relationships_active_during(session=session, time_value=require("time_value"))
    if query == "obligations_resolved_by_event":
        return layer.obligations_resolved_by_event(session=session, event_id=require("event_id"))
    if query == "evidence_for_relationship":
        return layer.evidence_for_relationship(
            session=session, relationship_id=require("relationship_id")
        )
    if query == "timeline_for_entity":
        return layer.timeline_for_entity(session=session, entity_id=require("entity_id"))
    raise ValueError(f"Unsupported graph query: {query}")
