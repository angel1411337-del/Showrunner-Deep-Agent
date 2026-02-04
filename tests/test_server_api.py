
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from showrunner.server.main import app

client = TestClient(app)

def test_get_aliases():
    """Test retrieving aliases."""
    mock_aliases = [{"alias_id": "a1", "alias": "Bond", "entity_id": "e1"}]
    
    with patch("showrunner.server.api.read_json_file") as mock_read:
        mock_read.return_value = mock_aliases
        response = client.get("/api/aliases")
        
        assert response.status_code == 200
        assert response.json() == mock_aliases
        mock_read.assert_called_with("kb/aliases.json")

def test_get_passage_by_id():
    """Test retrieving a single passage by ID."""
    mock_passages = [
        {"passage_id": "p1", "text": "Hello world"},
        {"passage_id": "p2", "text": "Foo bar"}
    ]
    
    with patch("showrunner.server.api.get_passages_data") as mock_get:
        mock_get.return_value = mock_passages
        
        # Test success
        response = client.get("/api/passages/p1")
        assert response.status_code == 200
        assert response.json() == {"passage_id": "p1", "text": "Hello world"}
        
        # Test Not Found
        response = client.get("/api/passages/p999")
        assert response.status_code == 404
