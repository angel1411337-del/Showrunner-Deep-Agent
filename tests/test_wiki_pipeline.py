from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import Mock

from showrunner.contracts.wiki import (
    Event,
    EventType,
    Relationship,
    RelationshipType,
    StoryOrder,
    StoryTime,
)
from showrunner.pipeline.orchestrator import ComponentFactory, PipelineConfig, ShowrunnerPipeline


def test_pipeline_writes_wiki_outputs(tmp_path) -> None:
    input_dir = tmp_path / "corpus"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    output_dir.mkdir()

    config = PipelineConfig(input_source=input_dir, output_dir=output_dir)

    sample_event = Event(
        event_id="evt_001",
        event_type=EventType.BATTLE,
        title="Battle of Winterfell",
        description="A battle erupts at Winterfell.",
        participant_entity_ids=["ent_arya"],
        location_entity_id="ent_winterfell",
        related_obligation_ids=[],
        evidence_anchor_ids=["ev_001"],
        story_time=StoryTime(time_label="unknown"),
        story_order=StoryOrder(
            order_index=0,
            order_label="book1:0",
            source_id="book1",
            passage_id="book1:0",
        ),
        created_at=datetime(2026, 2, 4, 12, 0, 0),
    )

    sample_relationship = Relationship(
        relationship_id="rel_001",
        relation_type=RelationshipType.ALLIANCE,
        source_entity_id="ent_arya",
        target_entity_id="ent_jon",
        description="Arya allied with Jon Snow.",
        evidence_anchor_ids=["ev_001"],
        story_time=StoryTime(time_label="unknown"),
        story_order=StoryOrder(
            order_index=0,
            order_label="book1:0",
            source_id="book1",
            passage_id="book1:0",
        ),
        created_at=datetime(2026, 2, 4, 12, 0, 0),
    )

    mock_factory = Mock(spec=ComponentFactory)
    mock_factory.config = config

    mock_adapter = Mock()
    mock_adapter.load.return_value = []
    mock_factory.create_input_adapter.return_value = mock_adapter

    mock_indexer = Mock()
    mock_indexer.index.return_value = ([], [])
    mock_indexer.segment_paragraphs.return_value = []
    mock_factory.create_canon_indexer.return_value = mock_indexer

    mock_resolver = Mock()
    mock_resolver.resolve.return_value = ([], [], [])
    mock_factory.create_entity_resolver.return_value = mock_resolver

    mock_obligation_extractor = Mock()
    mock_obligation_extractor.extract.return_value = ([], [])
    mock_factory.create_obligation_extractor.return_value = mock_obligation_extractor

    mock_merger = Mock()
    mock_merger.merge.return_value = ([], [], 0.0)
    mock_factory.create_dedupe_merger.return_value = mock_merger

    mock_gates = Mock()
    mock_gates.validate.return_value = (True, [])
    mock_factory.create_quality_gates.return_value = mock_gates

    mock_event_extractor = Mock()
    mock_event_extractor.extract.return_value = [sample_event]
    mock_factory.create_event_extractor.return_value = mock_event_extractor

    mock_relationship_extractor = Mock()
    mock_relationship_extractor.extract.return_value = [sample_relationship]
    mock_factory.create_relationship_extractor.return_value = mock_relationship_extractor

    mock_renderer = Mock()
    mock_renderer.render.return_value = output_dir / "exports" / "dossier.md"
    mock_factory.create_export_renderer.return_value = mock_renderer

    pipeline = ShowrunnerPipeline(config=config, factory=mock_factory)
    state, _manifest = pipeline.run()

    events_path = output_dir / "wiki" / "events.json"
    relationships_path = output_dir / "wiki" / "relationships.json"

    assert events_path.exists()
    assert relationships_path.exists()

    events_payload = json.loads(events_path.read_text())
    relationships_payload = json.loads(relationships_path.read_text())

    assert events_payload[0]["event_id"] == "evt_001"
    assert relationships_payload[0]["relationship_id"] == "rel_001"
    assert state["events"][0].event_id == "evt_001"
    assert state["relationships"][0].relationship_id == "rel_001"
