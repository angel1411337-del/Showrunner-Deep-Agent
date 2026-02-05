from unittest.mock import patch

from fastapi.testclient import TestClient

from showrunner.server.main import app

client = TestClient(app)


def test_run_agent_starts_pipeline():
    """Test that POST /api/run triggers the pipeline."""
    with patch("showrunner.server.api.run_pipeline_task") as mock_task:
        response = client.post("/api/run")
    assert response.status_code == 202
    assert response.json()["status"] == "starting"
    assert mock_task.called


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


def test_run_agent_accepts_environment_id(tmp_path):
    """Test that POST /api/run can accept an environment id."""
    from showrunner.server import api

    corpus_root = tmp_path / "corpus"
    output_dir = tmp_path / "out"
    corpus_root.mkdir()
    output_dir.mkdir()

    with (
        patch("showrunner.server.api.resolve_corpus_root") as mock_corpus,
        patch("showrunner.server.api.resolve_output_dir") as mock_output,
        patch("showrunner.server.api.run_pipeline_task") as mock_task,
    ):
        mock_corpus.return_value = corpus_root
        mock_output.return_value = output_dir
        response = client.post("/api/run", json={"environment_id": "winterfell"})

    assert response.status_code == 202
    assert response.json()["status"] == "starting"
    mock_corpus.assert_called_once_with(api.BASE_DIR, environment_id="winterfell")
    mock_output.assert_called_once_with(api.BASE_DIR, environment_id="winterfell")
    mock_task.assert_called()
