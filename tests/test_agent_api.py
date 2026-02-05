from unittest.mock import patch

from fastapi.testclient import TestClient

from showrunner.server.main import app

client = TestClient(app)


def test_agent_run_aliases_pipeline_run():
    with patch("showrunner.server.api.run_pipeline_task") as mock_task:
        response = client.post("/api/agent/run")
    assert response.status_code == 202
    assert response.json()["status"] == "starting"
    assert mock_task.called


def test_agent_status_aliases_pipeline_status():
    from showrunner.server import api

    api.PIPELINE_STATE["is_running"] = True
    api.PIPELINE_STATE["progress"] = 0.25
    api.PIPELINE_STATE["message"] = "Working..."

    response = client.get("/api/agent/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["is_running"] is True
    assert payload["progress"] == 0.25
    assert payload["message"] == "Working..."

    api.PIPELINE_STATE["is_running"] = False


def test_agent_artifacts_lists_relative_paths():
    mock_paths = ["exports/Unresolved_Threads_Dossier.md", "exports/twist_bank.md"]

    with patch("showrunner.server.api.list_artifacts") as mock_list:
        mock_list.return_value = mock_paths
        response = client.get("/api/agent/artifacts")

    assert response.status_code == 200
    assert response.json() == {"artifacts": mock_paths}
