"""Detect changed corpus files for passive hook execution."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

DEFAULT_EXTENSIONS = {".txt", ".md", ".markdown", ".docx", ".pdf"}


def normalize_repo_paths(paths: Iterable[str | Path], repo_root: Path) -> list[Path]:
    """Normalize repo-relative paths into absolute Paths."""
    normalized: list[Path] = []
    for path in paths:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = (repo_root / candidate).resolve()
        normalized.append(candidate)
    return normalized


def filter_corpus_files(
    paths: Iterable[Path],
    *,
    corpus_root: Path,
    allowed_extensions: Iterable[str] | None = None,
) -> list[Path]:
    """Filter paths to only corpus files with supported extensions."""
    allowed = {ext.lower() for ext in (allowed_extensions or DEFAULT_EXTENSIONS)}
    corpus_root = corpus_root.resolve()
    filtered: list[Path] = []

    for path in paths:
        candidate = path.resolve()
        if candidate == corpus_root or corpus_root not in candidate.parents:
            continue
        if candidate.suffix.lower() not in allowed:
            continue
        filtered.append(candidate)

    return filtered


def _git_changed_paths(
    repo_root: Path,
    *,
    base: str | None = None,
    head: str | None = None,
    staged: bool = False,
) -> list[Path]:
    args = ["git", "-C", str(repo_root), "diff", "--name-only"]
    if staged:
        args.append("--cached")
    if base and head:
        args.extend([base, head])
    elif base:
        args.append(base)

    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return []
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return normalize_repo_paths(lines, repo_root)


def detect_changed_text_files(
    repo_root: Path,
    *,
    corpus_root: Path | None = None,
    base: str | None = None,
    head: str | None = None,
    staged: bool = False,
    allowed_extensions: Iterable[str] | None = None,
) -> list[Path]:
    """Detect changed corpus files using git diff."""
    actual_corpus_root = corpus_root or (repo_root / "corpus")
    changed_paths = _git_changed_paths(repo_root, base=base, head=head, staged=staged)
    return filter_corpus_files(
        changed_paths,
        corpus_root=actual_corpus_root,
        allowed_extensions=allowed_extensions,
    )
