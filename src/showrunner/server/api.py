import json
import os
from pathlib import Path
from typing import Any, cast

from fastapi import APIRouter, HTTPException

router = APIRouter()

BASE_DIR = Path(os.getcwd())


def get_latest_output_dir() -> Path | None:
    # Try generic 'out' first
    if (BASE_DIR / "out").exists():
        return BASE_DIR / "out"

    # Logic to find latest out_YYYYMMDD_HHMMSS
    out_dirs = sorted(
        [d for d in BASE_DIR.glob("out_*") if d.is_dir()], key=lambda x: x.name, reverse=True
    )
    if out_dirs:
        return out_dirs[0]
    return None


def read_json_file(subpath: str) -> Any:
    out_dir = get_latest_output_dir()
    if not out_dir:
        raise HTTPException(status_code=404, detail="No output directory found")

    file_path = out_dir / subpath
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {subpath}")

    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


@router.get("/status")
async def get_status():
    out_dir = get_latest_output_dir()
    return {
        "status": "online",
        "agent": "showrunner",
        "current_corpus": str(out_dir) if out_dir else None,
    }


@router.get("/obligations")
async def get_obligations() -> Any:
    return read_json_file("obligations/obligations.json")


@router.get("/entities")
async def get_entities() -> Any:
    return read_json_file("kb/entities.json")


@router.get("/stats")
async def get_stats() -> dict[str, int]:
    # Aggregate some basic stats for the dashboard
    try:
        obligations = cast(
            "list[dict[str, Any]]",
            read_json_file("obligations/obligations.json"),
        )
        entities = cast("list[dict[str, Any]]", read_json_file("kb/entities.json"))

        unresolved = [o for o in obligations if not o.get("is_resolved", False)]
        high_confidence = [o for o in obligations if o.get("confidence", 0) > 0.8]

        return {
            "total_obligations": len(obligations),
            "open_threads": len(unresolved),
            "key_entities": len(entities),
            "high_confidence_events": len(high_confidence),
        }
    except Exception:
        return {
            "total_obligations": 0,
            "open_threads": 0,
            "key_entities": 0,
            "high_confidence_events": 0,
        }


def read_jsonl_file(subpath: str) -> list[dict[str, Any]]:
    out_dir = get_latest_output_dir()
    if not out_dir:
        raise HTTPException(status_code=404, detail="No output directory found")

    file_path = out_dir / subpath
    if not file_path.exists():
        # Fallback empty list if optional files missing?
        # But passages and aliases should be present.
        raise HTTPException(status_code=404, detail=f"File not found: {subpath}")

    data: list[dict[str, Any]] = []
    with open(file_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


@router.get("/aliases")
async def get_aliases():
    return read_json_file("kb/aliases.json")


def get_passages_data() -> list[dict[str, Any]]:
    return read_jsonl_file("canon/passages.jsonl")


@router.get("/passages/{passage_id}")
async def get_passage(passage_id: str) -> dict[str, Any]:
    passages = get_passages_data()
    for p in passages:
        if p.get("passage_id") == passage_id:
            return p
    raise HTTPException(status_code=404, detail="Passage not found")
