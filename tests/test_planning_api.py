from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from showrunner.server.main import app

client = TestClient(app)


def test_get_master_outline_success() -> None:
    with patch("showrunner.server.api.read_text_file") as mock_read:
        mock_read.return_value = "# Master Outline\n"
        response = client.get("/api/exports/outline")

        assert response.status_code == 200
        assert response.text == "# Master Outline\n"
    mock_read.assert_called_once_with(
        "exports/master_outline_books_6_7.md",
        environment_id=None,
    )


def test_get_master_outline_falls_back_to_generic_name() -> None:
    with patch("showrunner.server.api.read_text_file") as mock_read:
        mock_read.side_effect = [
            HTTPException(status_code=404, detail="missing"),
            "# Master Outline\n",
        ]
        response = client.get("/api/exports/outline")

        assert response.status_code == 200
        assert response.text == "# Master Outline\n"
        assert mock_read.call_count == 2
        assert mock_read.call_args_list[0].args[0] == "exports/master_outline_books_6_7.md"
        assert mock_read.call_args_list[1].args[0] == "exports/master_outline.md"


def test_get_reveal_ledger_csv_success() -> None:
    with patch("showrunner.server.api.read_text_file") as mock_read:
        mock_read.return_value = "reveal_id,mystery_obligation_id\n"
        response = client.get("/api/exports/reveals")

        assert response.status_code == 200
        assert response.text == "reveal_id,mystery_obligation_id\n"
    mock_read.assert_called_once_with(
        "exports/mysteries_reveals_table.csv",
        environment_id=None,
    )


def test_get_twist_bank_returns_empty_when_missing() -> None:
    with patch("showrunner.server.api.read_text_file") as mock_read:
        mock_read.side_effect = HTTPException(status_code=404, detail="missing")
        response = client.get("/api/exports/twists")

        assert response.status_code == 200
        assert response.text == ""


def test_get_outline_plan_json_success() -> None:
    plan = [{"section_id": "book_6"}]
    with patch("showrunner.server.api.read_json_file") as mock_read:
        mock_read.return_value = plan
        response = client.get("/api/plans/outline")

        assert response.status_code == 200
        assert response.json() == plan
    mock_read.assert_called_once_with(
        "plans/outline.json",
        environment_id=None,
    )


def test_get_reveals_plan_json_returns_empty_when_missing() -> None:
    with patch("showrunner.server.api.read_json_file") as mock_read:
        mock_read.side_effect = HTTPException(status_code=404, detail="missing")
        response = client.get("/api/plans/reveals")

        assert response.status_code == 200
        assert response.json() == []
