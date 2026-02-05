from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from showrunner.server.main import app

client = TestClient(app)


def test_get_events_empty():
    """Test retrieving events when file is missing (graceful fallback)."""
    with patch("showrunner.server.api.read_json_file") as mock_read:
        # Mocking HTTPException(404) as raised by read_json_file
        mock_read.side_effect = HTTPException(status_code=404, detail="File not found")

        response = client.get("/api/wiki/events")
        assert response.status_code == 200
        assert response.json() == []


def test_get_events_success():
    """Test retrieving events successfully."""
    mock_events = [
        {"event_id": "ev1", "title": "Battle of X", "story_time": {"time_label": "298 AC"}}
    ]
    with patch("showrunner.server.api.read_json_file") as mock_read:
        mock_read.return_value = mock_events
        response = client.get("/api/wiki/events")

        assert response.status_code == 200
        assert response.json() == mock_events
    mock_read.assert_called_with("events/events.json", environment_id=None)


def test_get_relationships_success():
    """Test retrieving relationships successfully."""
    mock_rels = [{"relationship_id": "r1", "source_entity_id": "e1", "relation_type": "alliance"}]
    with patch("showrunner.server.api.read_json_file") as mock_read:
        mock_read.return_value = mock_rels
        response = client.get("/api/wiki/relationships")

        assert response.status_code == 200
        assert response.json() == mock_rels
    mock_read.assert_called_with("relationships/relationships.json", environment_id=None)
