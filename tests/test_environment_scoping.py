from __future__ import annotations

from typing import TYPE_CHECKING

from showrunner.hooks.incremental_runner import resolve_corpus_root, resolve_output_dir

if TYPE_CHECKING:
    from pathlib import Path


def test_resolve_paths_default_repo_root(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("SHOWRUNNER_ENV", raising=False)
    monkeypatch.delenv("SHOWRUNNER_CORPUS_DIR", raising=False)
    monkeypatch.delenv("SHOWRUNNER_OUTPUT_DIR", raising=False)

    assert resolve_corpus_root(tmp_path) == tmp_path / "corpus"
    assert resolve_output_dir(tmp_path) == tmp_path / "out"


def test_resolve_paths_with_environment_id(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("SHOWRUNNER_ENV", raising=False)
    monkeypatch.delenv("SHOWRUNNER_CORPUS_DIR", raising=False)
    monkeypatch.delenv("SHOWRUNNER_OUTPUT_DIR", raising=False)

    env_id = "winterfell"
    assert resolve_corpus_root(tmp_path, environment_id=env_id) == (
        tmp_path / "environments" / env_id / "corpus"
    )
    assert resolve_output_dir(tmp_path, environment_id=env_id) == (
        tmp_path / "environments" / env_id / "out"
    )


def test_resolve_paths_with_environment_var(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SHOWRUNNER_ENV", "dragonstone")
    monkeypatch.delenv("SHOWRUNNER_CORPUS_DIR", raising=False)
    monkeypatch.delenv("SHOWRUNNER_OUTPUT_DIR", raising=False)

    assert resolve_corpus_root(tmp_path) == tmp_path / "environments" / "dragonstone" / "corpus"
    assert resolve_output_dir(tmp_path) == tmp_path / "environments" / "dragonstone" / "out"


def test_resolve_paths_with_overrides(tmp_path: Path, monkeypatch):
    custom_corpus = tmp_path / "custom_corpus"
    custom_out = tmp_path / "custom_out"
    monkeypatch.setenv("SHOWRUNNER_CORPUS_DIR", str(custom_corpus))
    monkeypatch.setenv("SHOWRUNNER_OUTPUT_DIR", str(custom_out))

    assert resolve_corpus_root(tmp_path) == custom_corpus
    assert resolve_output_dir(tmp_path) == custom_out
