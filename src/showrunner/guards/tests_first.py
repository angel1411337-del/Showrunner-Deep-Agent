"""Guard to enforce tests-first changes.

Blocks commits/CI when src/ changes occur without corresponding tests/ updates.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


def _normalize(paths: Iterable[str]) -> list[Path]:
    normalized: list[Path] = []
    for raw in paths:
        cleaned = raw.strip()
        if cleaned:
            normalized.append(Path(cleaned))
    return normalized


def classify_changed(paths: Iterable[str]) -> tuple[list[Path], list[Path]]:
    """Return (src_changes, test_changes) from a list of paths."""
    src_changes: list[Path] = []
    test_changes: list[Path] = []
    for path in _normalize(paths):
        if path.parts and path.parts[0] == "src":
            src_changes.append(path)
        if path.parts and path.parts[0] == "tests":
            test_changes.append(path)
    return src_changes, test_changes


def should_block(paths: Iterable[str]) -> bool:
    """Return True if src/ changed without any tests/ changes."""
    src_changes, test_changes = classify_changed(paths)
    if not src_changes:
        return False
    return not test_changes


def _git_diff_name_only(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _get_changed_files(base: str | None, head: str | None, staged: bool) -> list[str]:
    if staged:
        return _git_diff_name_only("--cached")
    if base and head:
        return _git_diff_name_only(base, head)
    return _git_diff_name_only("HEAD")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tests-first guard")
    parser.add_argument("--base", help="Base git ref for diff")
    parser.add_argument("--head", help="Head git ref for diff")
    parser.add_argument("--staged", action="store_true", help="Use staged diff")
    args = parser.parse_args(argv)

    changed = _get_changed_files(args.base, args.head, args.staged)
    if should_block(changed):
        print("Tests-first guard: src/ changed without tests/.")
        print("Add/modify tests in tests/ for any src/ changes.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
