"""Pytest configuration for golden tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add --update-golden option to pytest."""
    parser.addoption(
        "--update-golden",
        action="store_true",
        default=False,
        help="Update golden files with current output",
    )


@pytest.fixture
def update_golden(request: pytest.FixtureRequest) -> bool:
    """Return True if --update-golden flag was passed."""
    return bool(request.config.getoption("--update-golden"))


@pytest.fixture
def golden_dir() -> Path:
    """Return path to golden files directory."""
    return Path(__file__).parent / "fixtures"


def load_golden(path: Path) -> dict[str, Any] | list[Any]:
    """Load a golden file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_golden(path: Path, data: dict[str, Any] | list[Any]) -> None:
    """Save data to a golden file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")


@pytest.fixture
def assert_golden(
    golden_dir: Path, update_golden: bool
) -> Any:  # Returns callable, using Any for simplicity
    """Fixture that compares output against golden files.

    Usage:
        def test_something(assert_golden):
            result = my_function()
            assert_golden("test_something.json", result)
    """

    def _assert_golden(name: str, actual: dict[str, Any] | list[Any]) -> None:
        golden_path = golden_dir / name

        if update_golden:
            save_golden(golden_path, actual)
            pytest.skip(f"Updated golden file: {golden_path}")

        if not golden_path.exists():
            save_golden(golden_path, actual)
            pytest.fail(
                f"Golden file created: {golden_path}\n"
                "Re-run tests to verify, or use --update-golden to accept."
            )

        expected = load_golden(golden_path)
        assert actual == expected, (
            f"Output differs from golden file: {golden_path}\n"
            "Run with --update-golden to update if change is intentional."
        )

    return _assert_golden
