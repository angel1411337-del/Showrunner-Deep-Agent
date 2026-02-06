from __future__ import annotations

import json
from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from showrunner.server.main import app

if TYPE_CHECKING:
    from pathlib import Path

client = TestClient(app)


def _configure_env(tmp_path: Path, monkeypatch) -> None:
    from showrunner.server import api

    monkeypatch.setattr(api, "BASE_DIR", tmp_path)
    monkeypatch.setattr(api, "ENV_FILE", tmp_path / "environments.json")


def test_list_environments_includes_default(tmp_path: Path, monkeypatch) -> None:
    _configure_env(tmp_path, monkeypatch)

    response = client.get("/api/environments")
    assert response.status_code == 200
    data = response.json()

    assert data[0]["id"] == "default"
    assert data[0]["is_default"] is True
    assert data[0]["is_global_default"] is True


def test_create_environment_persists_name(tmp_path: Path, monkeypatch) -> None:
    _configure_env(tmp_path, monkeypatch)

    response = client.post("/api/environments", json={"name": "Winterfell"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "winterfell"

    env_file = tmp_path / "environments.json"
    data = json.loads(env_file.read_text(encoding="utf-8"))
    assert data["winterfell"]["name"] == "Winterfell"


def test_set_global_default_updates_file(tmp_path: Path, monkeypatch) -> None:
    _configure_env(tmp_path, monkeypatch)

    response = client.post("/api/environments/default", json={"environment_id": "winterfell"})
    assert response.status_code == 200

    env_file = tmp_path / "environments.json"
    data = json.loads(env_file.read_text(encoding="utf-8"))
    assert data["global_default_id"] == "winterfell"
