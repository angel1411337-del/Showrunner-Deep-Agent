import asyncio
import json
import os
from pathlib import Path
from typing import Any, cast

from fastapi import APIRouter, BackgroundTasks, HTTPException, Response

router = APIRouter()

# Global state to track pipeline progress
PIPELINE_STATE = {
    "is_running": False,
    "progress": 0.0,
    "message": "Idle",
    "error": None,
}


async def run_pipeline_stub():
    """Stub background task to simulate pipeline steps."""
    global PIPELINE_STATE
    PIPELINE_STATE["is_running"] = True
    PIPELINE_STATE["progress"] = 0.0
    PIPELINE_STATE["message"] = "Initializing..."
    PIPELINE_STATE["error"] = None

    try:
        steps = [
            ("Loading corpus...", 0.1),
            ("Indexing canon...", 0.3),
            ("Resolving entities...", 0.5),
            ("Extracting obligations...", 0.7),
            ("Merging duplicates...", 0.8),
            ("Validating gates...", 0.9),
            ("Finalizing export...", 1.0),
        ]

        for msg, prog in steps:
            await asyncio.sleep(1)  # Simulate work
            PIPELINE_STATE["message"] = msg
            PIPELINE_STATE["progress"] = prog

        PIPELINE_STATE["message"] = "Completed"
        PIPELINE_STATE["progress"] = 1.0

    except Exception as e:
        PIPELINE_STATE["error"] = str(e)
        PIPELINE_STATE["message"] = "Failed"
    finally:
        PIPELINE_STATE["is_running"] = False


@router.post("/run", status_code=202)
async def run_agent(background_tasks: BackgroundTasks):
    """Trigger a new agent run (simulated)."""
    if PIPELINE_STATE["is_running"]:
        return Response(
            status_code=409,
            content=json.dumps({"status": "already_running"}),
            media_type="application/json",
        )

    background_tasks.add_task(run_pipeline_stub)
    return Response(
        status_code=202, content=json.dumps({"status": "starting"}), media_type="application/json"
    )


@router.get("/run/status")
async def get_run_status():
    """Get the current status of the agent run."""
    return PIPELINE_STATE


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
async def get_aliases() -> list[dict[str, Any]]:
    """Get all aliases from the knowledge base."""
    # Try kb/aliases.json or aliases.json
    try:
        return cast("list[dict[str, Any]]", read_json_file("kb/aliases.json"))
    except HTTPException:
        return []


@router.get("/wiki/events")
async def get_events() -> list[dict[str, Any]]:
    """Get all events from the wiki."""
    # Try events/events.json or wiki/events.json
    try:
        return cast("list[dict[str, Any]]", read_json_file("events/events.json"))
    except HTTPException:
        try:
            return cast("list[dict[str, Any]]", read_json_file("wiki/events.json"))
        except HTTPException:
            return []


@router.get("/wiki/relationships")
async def get_relationships() -> list[dict[str, Any]]:
    """Get all relationships from the wiki."""
    try:
        return cast("list[dict[str, Any]]", read_json_file("relationships/relationships.json"))
    except HTTPException:
        try:
            return cast("list[dict[str, Any]]", read_json_file("wiki/relationships.json"))
        except HTTPException:
            return []


def get_passages_data() -> list[dict[str, Any]]:
    return read_jsonl_file("canon/passages.jsonl")


@router.get("/passages/{passage_id}")
async def get_passage(passage_id: str) -> dict[str, Any]:
    passages = get_passages_data()
    for p in passages:
        if p.get("passage_id") == passage_id:
            return p
    raise HTTPException(status_code=404, detail="Passage not found")
