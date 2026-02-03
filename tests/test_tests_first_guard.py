"""Tests for the tests-first guard hook."""

from __future__ import annotations

from showrunner.guards import tests_first


def test_blocks_src_without_tests() -> None:
    assert tests_first.should_block(["src/showrunner/foo.py"]) is True


def test_allows_src_with_tests() -> None:
    assert (
        tests_first.should_block(
            ["src/showrunner/foo.py", "tests/test_foo.py"]
        )
        is False
    )


def test_allows_tests_only() -> None:
    assert tests_first.should_block(["tests/test_foo.py"]) is False


def test_allows_non_src_changes() -> None:
    assert tests_first.should_block(["README.md", "docs/notes.md"]) is False
