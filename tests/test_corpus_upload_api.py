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


def test_upload_rejects_unsupported_extensions(tmp_path: Path, monkeypatch) -> None:
    _configure_env(tmp_path, monkeypatch)

    files = [("files", ("bad.exe", b"nope", "application/octet-stream"))]
    response = client.post("/api/corpus/upload", files=files)

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["error"] == "unsupported_files"
    assert ".pdf" in detail["allowed_extensions"]
    assert detail["unsupported_files"] == ["bad.exe"]


def test_upload_collision_requires_choice(tmp_path: Path, monkeypatch) -> None:
    _configure_env(tmp_path, monkeypatch)

    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir(parents=True)
    (corpus_root / "chapter1.md").write_text("old", encoding="utf-8")

    files = [("files", ("chapter1.md", b"new", "text/markdown"))]
    response = client.post("/api/corpus/upload", files=files)

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["error"] == "file_conflict"
    assert "chapter1.md" in detail["conflicts"]
    assert detail["options"] == ["overwrite", "rename"]


def test_upload_collision_rename(tmp_path: Path, monkeypatch) -> None:
    _configure_env(tmp_path, monkeypatch)

    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir(parents=True)
    (corpus_root / "chapter1.md").write_text("old", encoding="utf-8")

    files = [("files", ("chapter1.md", b"new", "text/markdown"))]
    response = client.post(
        "/api/corpus/upload",
        data={"collision_mode": "rename"},
        files=files,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["collision_mode"] == "rename"
    assert payload["saved"] == ["chapter1 (2).md"]
    assert (corpus_root / "chapter1 (2).md").read_text(encoding="utf-8") == "new"
    assert (corpus_root / "chapter1.md").read_text(encoding="utf-8") == "old"


def test_upload_collision_overwrite(tmp_path: Path, monkeypatch) -> None:
    _configure_env(tmp_path, monkeypatch)

    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir(parents=True)
    (corpus_root / "chapter1.md").write_text("old", encoding="utf-8")

    files = [("files", ("chapter1.md", b"new", "text/markdown"))]
    response = client.post(
        "/api/corpus/upload",
        data={"collision_mode": "overwrite"},
        files=files,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["collision_mode"] == "overwrite"
    assert payload["saved"] == ["chapter1.md"]
    assert (corpus_root / "chapter1.md").read_text(encoding="utf-8") == "new"


def test_upload_preserves_subfolders_and_environment(tmp_path: Path, monkeypatch) -> None:
    _configure_env(tmp_path, monkeypatch)

    from showrunner.server import api

    api.ENV_FILE.write_text(
        json.dumps({"global_default_id": "winterfell"}),
        encoding="utf-8",
    )

    files = [("files", ("book1/chapter1.md", b"text", "text/markdown"))]
    response = client.post("/api/corpus/upload", files=files)

    assert response.status_code == 200
    payload = response.json()
    assert payload["environment_id"] == "winterfell"
    assert payload["saved"] == ["book1/chapter1.md"]

    target = tmp_path / "environments" / "winterfell" / "corpus" / "book1" / "chapter1.md"
    assert target.exists()


def test_upload_rejects_path_traversal(tmp_path: Path, monkeypatch) -> None:
    _configure_env(tmp_path, monkeypatch)

    files = [("files", ("../evil.md", b"nope", "text/markdown"))]
    response = client.post("/api/corpus/upload", files=files)

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["error"] == "invalid_path"
