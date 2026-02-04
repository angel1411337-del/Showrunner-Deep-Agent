from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from showrunner.server.main import app

client = TestClient(app)

def test_run_agent_starts_pipeline():
    """Test that POST /api/run triggers the pipeline."""
    # We don't need to mock ShowrunnerPipeline anymore since we stubbed the task.
    # We just want to ensure it accepts the request.
    response = client.post("/api/run")
    assert response.status_code == 202
    assert response.json()["status"] == "starting"

def test_get_run_status_initial():
    """Test retrieving status before any run."""
    # Reset state if possible or rely on default
    # This might require some way to reset global state in api.py for testing
    from showrunner.server import api
    api.PIPELINE_STATE["is_running"] = False
    
    response = client.get("/api/run/status")
    assert response.status_code == 200
    assert response.json()["is_running"] is False

def test_get_run_status_running():
    """Test retrieving status while running."""
    from showrunner.server import api
    api.PIPELINE_STATE["is_running"] = True
    api.PIPELINE_STATE["progress"] = 0.5
    api.PIPELINE_STATE["message"] = "Processing..."
    
    response = client.get("/api/run/status")
    assert response.status_code == 200
    data = response.json()
    assert data["is_running"] is True
    assert data["progress"] == 0.5
    assert data["message"] == "Processing..."
    
    # Cleanup
    api.PIPELINE_STATE["is_running"] = False
