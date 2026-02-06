import json
import os
from pathlib import Path
from typing import Any, cast

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel

from showrunner.adapters.input_adapter import SUPPORTED_EXTENSIONS
from showrunner.hooks.incremental_runner import resolve_corpus_root, resolve_output_dir
from showrunner.pipeline.orchestrator import PipelineConfig, ShowrunnerPipeline

router = APIRouter()

# Bugbear B008: avoid calling File() in argument defaults.
UPLOAD_FILES = File(...)

# Global state to track pipeline progress
PIPELINE_STATE = {
    "is_running": False,
    "progress": 0.0,
    "message": "Idle",
    "error": None,
}


class RunRequest(BaseModel):
    environment_id: str | None = None


def run_pipeline_task(*, corpus_root: Path, output_dir: Path) -> None:
    """Background task to run the real pipeline and update status."""
    global PIPELINE_STATE
    PIPELINE_STATE["is_running"] = True
    PIPELINE_STATE["progress"] = 0.0
    PIPELINE_STATE["message"] = "Initializing..."
    PIPELINE_STATE["error"] = None
    PIPELINE_STATE["output_dir"] = str(output_dir)

    def _progress(stage: str, progress: float) -> None:
        PIPELINE_STATE["message"] = stage
        PIPELINE_STATE["progress"] = progress

    try:
        config = PipelineConfig(input_source=corpus_root, output_dir=output_dir)
        state, manifest = ShowrunnerPipeline(config=config, on_progress=_progress).run()
        if manifest.status == "failed":
            PIPELINE_STATE["error"] = state.get("error") or "Pipeline failed"
            PIPELINE_STATE["message"] = "Failed"
            PIPELINE_STATE["progress"] = 1.0
        else:
            PIPELINE_STATE["message"] = "Completed"
            PIPELINE_STATE["progress"] = 1.0
    except Exception as exc:
        PIPELINE_STATE["error"] = str(exc)
        PIPELINE_STATE["message"] = "Failed"
        PIPELINE_STATE["progress"] = 1.0
    finally:
        PIPELINE_STATE["is_running"] = False


@router.post("/run", status_code=202)
async def run_agent(background_tasks: BackgroundTasks, request: RunRequest | None = None):
    """Trigger a new agent run."""
    if PIPELINE_STATE["is_running"]:
        return Response(
            status_code=409,
            content=json.dumps({"status": "already_running"}),
            media_type="application/json",
        )

    environment_id = request.environment_id if request else None
    corpus_root = resolve_corpus_root(BASE_DIR, environment_id=environment_id)
    output_dir = resolve_output_dir(BASE_DIR, environment_id=environment_id)
    if not corpus_root.exists():
        fallback = BASE_DIR / "sample_corpus"
        if fallback.exists():
            corpus_root = fallback
        else:
            raise HTTPException(status_code=404, detail=f"Corpus not found: {corpus_root}")
    PIPELINE_STATE["environment_id"] = environment_id
    background_tasks.add_task(run_pipeline_task, corpus_root=corpus_root, output_dir=output_dir)
    return Response(
        status_code=202, content=json.dumps({"status": "starting"}), media_type="application/json"
    )


@router.get("/run/status")
async def get_run_status():
    """Get the current status of the agent run."""
    return PIPELINE_STATE


@router.post("/agent/run", status_code=202)
async def run_agent_alias(background_tasks: BackgroundTasks):
    """Alias for /api/run to support external UI hooks."""
    return await run_agent(background_tasks)


@router.get("/agent/status")
async def get_agent_status_alias():
    """Alias for /api/run/status to support external UI hooks."""
    return await get_run_status()


BASE_DIR = Path(os.getcwd())


def get_latest_output_dir(*, environment_id: str | None = None) -> Path | None:
    out_base = resolve_output_dir(BASE_DIR, environment_id=environment_id)
    if out_base.exists():
        return out_base

    parent = out_base.parent
    out_dirs = sorted(
        [d for d in parent.glob("out_*") if d.is_dir()],
        key=lambda x: x.name,
        reverse=True,
    )
    if out_dirs:
        return out_dirs[0]
    return None


def read_json_file(subpath: str, *, environment_id: str | None = None) -> Any:
    out_dir = get_latest_output_dir(environment_id=environment_id)
    if not out_dir:
        raise HTTPException(status_code=404, detail="No output directory found")

    file_path = out_dir / subpath
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {subpath}")

    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def read_text_file(subpath: str, *, environment_id: str | None = None) -> str:
    out_dir = get_latest_output_dir(environment_id=environment_id)
    if not out_dir:
        raise HTTPException(status_code=404, detail="No output directory found")

    file_path = out_dir / subpath
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {subpath}")

    return file_path.read_text(encoding="utf-8")


def list_artifacts(*, environment_id: str | None = None) -> list[str]:
    out_dir = get_latest_output_dir(environment_id=environment_id)
    if not out_dir:
        return []
    files = [path for path in out_dir.rglob("*") if path.is_file()]
    root = out_dir.resolve()
    return sorted(path.resolve().relative_to(root).as_posix() for path in files)


@router.get("/agent/artifacts")
async def get_agent_artifacts(environment_id: str | None = None) -> dict[str, list[str]]:
    """List artifacts under the latest output directory."""
    return {"artifacts": list_artifacts(environment_id=environment_id)}


ENV_FILE = BASE_DIR / "environments.json"


def _load_env_data() -> dict[str, Any]:
    if not ENV_FILE.exists():
        return {}
    try:
        return json.loads(ENV_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_env_data(data: dict[str, Any]) -> None:
    ENV_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_environment_name(environment_id: str | None) -> str:
    data = _load_env_data()
    # If no ID provided, we consider it the "root" or "default" environment
    key = environment_id or "default"
    return data.get(key, {}).get("name", "Showrunner Project")


class SetNameRequest(BaseModel):
    name: str
    environment_id: str | None = None


def _resolve_request_environment_id(environment_id: str | None) -> str:
    if environment_id:
        return environment_id
    data = _load_env_data()
    return data.get("global_default_id", "default")


def _resolve_corpus_root_for_api(environment_id: str | None) -> Path:
    if environment_id:
        return BASE_DIR / "environments" / environment_id / "corpus"
    return BASE_DIR / "corpus"


def _normalize_upload_path(raw_path: str) -> Path:
    cleaned = raw_path.replace("\\", "/").strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail={"error": "invalid_path"})
    path = Path(cleaned)
    if path.is_absolute() or path.drive or ".." in path.parts:
        raise HTTPException(status_code=400, detail={"error": "invalid_path"})
    return path


def _resolve_unique_path(path: Path, reserved: set[Path]) -> Path:
    if path not in reserved and not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    index = 2
    while True:
        candidate = path.with_name(f"{stem} ({index}){suffix}")
        if candidate not in reserved and not candidate.exists():
            return candidate
        index += 1


@router.post("/env/name")
async def set_environment_name(request: SetNameRequest):
    data = _load_env_data()
    key = request.environment_id or "default"
    if key not in data:
        data[key] = {}
    data[key]["name"] = request.name
    _save_env_data(data)
    return {"status": "updated", "name": request.name}


@router.post("/corpus/upload")
async def upload_corpus_files(
    files: list[UploadFile] = UPLOAD_FILES,
    environment_id: str | None = Form(None),
    collision_mode: str | None = Form(None),
) -> dict[str, Any]:
    allowed_extensions = sorted(SUPPORTED_EXTENSIONS)
    if collision_mode not in (None, "overwrite", "rename"):
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_collision_mode", "options": ["overwrite", "rename"]},
        )

    effective_env_id = _resolve_request_environment_id(environment_id)
    resolve_id = None if effective_env_id == "default" else effective_env_id
    corpus_root = _resolve_corpus_root_for_api(resolve_id)
    corpus_root.mkdir(parents=True, exist_ok=True)

    normalized: list[tuple[UploadFile, Path]] = []
    unsupported: list[str] = []
    for upload in files:
        filename = upload.filename or ""
        rel_path = _normalize_upload_path(filename)
        if rel_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            unsupported.append(filename)
        normalized.append((upload, rel_path))

    if unsupported:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "unsupported_files",
                "allowed_extensions": allowed_extensions,
                "unsupported_files": unsupported,
            },
        )

    conflicts: list[str] = []
    seen: set[Path] = set()
    for _, rel_path in normalized:
        target = corpus_root / rel_path
        if target.exists() or target in seen:
            conflicts.append(rel_path.as_posix())
        seen.add(target)

    if conflicts and collision_mode is None:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "file_conflict",
                "conflicts": conflicts,
                "options": ["overwrite", "rename"],
            },
        )

    saved: list[str] = []
    reserved: set[Path] = {path for path in corpus_root.rglob("*") if path.is_file()}
    for upload, rel_path in normalized:
        target = corpus_root / rel_path
        if collision_mode == "rename":
            target = _resolve_unique_path(target, reserved)
        reserved.add(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        content = await upload.read()
        target.write_bytes(content)
        saved.append(target.relative_to(corpus_root).as_posix())
        await upload.close()

    return {
        "status": "saved",
        "environment_id": effective_env_id,
        "collision_mode": collision_mode,
        "saved": saved,
    }


@router.get("/environments")
async def list_environments() -> list[dict[str, Any]]:
    """List all available environments used for switching context."""
    data = _load_env_data()
    envs: list[dict[str, Any]] = []

    # 1. Add Default/Root
    root_name = data.get("default", {}).get("name", "Showrunner Project")
    envs.append({"id": "default", "name": root_name, "is_default": True})

    # 2. Scan environments/ directory
    env_dir = BASE_DIR / "environments"
    if env_dir.exists():
        for path in env_dir.iterdir():
            if path.is_dir():
                env_id = path.name
                name = data.get(env_id, {}).get("name", env_id.replace("_", " ").title())
                envs.append({"id": env_id, "name": name, "is_default": False})

    # 3. Mark global default
    global_default = data.get("global_default_id", "default")
    for env in envs:
        env["is_global_default"] = env["id"] == global_default

    return envs


class CreateEnvRequest(BaseModel):
    name: str


@router.post("/environments")
async def create_environment(request: CreateEnvRequest):
    """Create a new environment directory and save its name."""
    # Generate ID from name (slugify-ish)
    env_id = request.name.lower().replace(" ", "_")
    # Ensure it doesn't collide with "default" or reserved keywords if any
    if env_id == "default":
        raise HTTPException(status_code=400, detail="Cannot create environment with ID 'default'")

    env_dir = BASE_DIR / "environments" / env_id
    if env_dir.exists():
        raise HTTPException(status_code=409, detail=f"Environment '{env_id}' already exists")

    # Create directory
    env_dir.mkdir(parents=True, exist_ok=True)

    # Save name mapping
    data = _load_env_data()
    if env_id not in data:
        data[env_id] = {}
    data[env_id]["name"] = request.name
    _save_env_data(data)

    return {"status": "created", "id": env_id, "name": request.name}


class SetDefaultRequest(BaseModel):
    environment_id: str


@router.post("/environments/default")
async def set_global_default(request: SetDefaultRequest):
    data = _load_env_data()
    data["global_default_id"] = request.environment_id
    _save_env_data(data)
    return {"status": "updated", "global_default_id": request.environment_id}


@router.get("/status")
async def get_status(environment_id: str | None = None):
    # If no specific ID requested, use the global default
    if not environment_id:
        data = _load_env_data()
        environment_id = data.get("global_default_id", "default")

    # Access "default" (root) by either "default" ID or None in finding directory
    # But for directory resolution, None = Root.
    # So if ID is "default", we pass None to directory resolver.
    resolve_id = None if environment_id == "default" else environment_id

    out_dir = get_latest_output_dir(environment_id=resolve_id)

    # We return the resolved ID so frontend knows what context it's in effectively
    return {
        "status": "online",
        "agent": "showrunner",
        "current_corpus": str(out_dir) if out_dir else None,
        "environment_name": get_environment_name(environment_id),
        "active_environment_id": environment_id,
    }


@router.get("/obligations")
async def get_obligations(environment_id: str | None = None) -> Any:
    return read_json_file("obligations/obligations.json", environment_id=environment_id)


@router.get("/entities")
async def get_entities(environment_id: str | None = None) -> Any:
    return read_json_file("kb/entities.json", environment_id=environment_id)


@router.get("/stats")
async def get_stats(environment_id: str | None = None) -> dict[str, int]:
    # Aggregate some basic stats for the dashboard
    try:
        obligations = cast(
            "list[dict[str, Any]]",
            read_json_file("obligations/obligations.json", environment_id=environment_id),
        )
        entities = cast(
            "list[dict[str, Any]]",
            read_json_file("kb/entities.json", environment_id=environment_id),
        )

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


def read_jsonl_file(subpath: str, *, environment_id: str | None = None) -> list[dict[str, Any]]:
    out_dir = get_latest_output_dir(environment_id=environment_id)
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
async def get_aliases(environment_id: str | None = None) -> list[dict[str, Any]]:
    """Get all aliases from the knowledge base."""
    # Try kb/aliases.json or aliases.json
    try:
        return cast(
            "list[dict[str, Any]]",
            read_json_file("kb/aliases.json", environment_id=environment_id),
        )
    except HTTPException:
        return []


@router.get("/wiki/events")
async def get_events(environment_id: str | None = None) -> list[dict[str, Any]]:
    """Get all events from the wiki."""
    # Try events/events.json or wiki/events.json
    try:
        return cast(
            "list[dict[str, Any]]",
            read_json_file("events/events.json", environment_id=environment_id),
        )
    except HTTPException:
        try:
            return cast(
                "list[dict[str, Any]]",
                read_json_file("wiki/events.json", environment_id=environment_id),
            )
        except HTTPException:
            return []


@router.get("/wiki/relationships")
async def get_relationships(environment_id: str | None = None) -> list[dict[str, Any]]:
    """Get all relationships from the wiki."""
    try:
        return cast(
            "list[dict[str, Any]]",
            read_json_file("relationships/relationships.json", environment_id=environment_id),
        )
    except HTTPException:
        try:
            return cast(
                "list[dict[str, Any]]",
                read_json_file("wiki/relationships.json", environment_id=environment_id),
            )
        except HTTPException:
            return []


@router.get("/exports/outline")
async def get_outline_export(environment_id: str | None = None) -> Response:
    try:
        content = read_text_file(
            "exports/master_outline_books_6_7.md",
            environment_id=environment_id,
        )
    except HTTPException:
        try:
            content = read_text_file("exports/master_outline.md", environment_id=environment_id)
        except HTTPException:
            content = ""
    return Response(content=content, media_type="text/markdown")


@router.get("/exports/reveals")
async def get_reveals_export(environment_id: str | None = None) -> Response:
    try:
        content = read_text_file(
            "exports/mysteries_reveals_table.csv",
            environment_id=environment_id,
        )
    except HTTPException:
        content = ""
    return Response(content=content, media_type="text/csv")


@router.get("/exports/twists")
async def get_twists_export(environment_id: str | None = None) -> Response:
    try:
        content = read_text_file("exports/twist_bank.md", environment_id=environment_id)
    except HTTPException:
        content = ""
    return Response(content=content, media_type="text/markdown")


@router.get("/plans/outline")
async def get_outline_plan(environment_id: str | None = None) -> list[dict[str, Any]]:
    try:
        return cast(
            "list[dict[str, Any]]",
            read_json_file("plans/outline.json", environment_id=environment_id),
        )
    except HTTPException:
        return []


@router.get("/plans/reveals")
async def get_reveals_plan(environment_id: str | None = None) -> list[dict[str, Any]]:
    try:
        return cast(
            "list[dict[str, Any]]",
            read_json_file("plans/reveals.json", environment_id=environment_id),
        )
    except HTTPException:
        return []


@router.get("/plans/twists")
async def get_twists_plan(environment_id: str | None = None) -> list[dict[str, Any]]:
    try:
        return cast(
            "list[dict[str, Any]]",
            read_json_file("plans/twists.json", environment_id=environment_id),
        )
    except HTTPException:
        return []


def get_passages_data(*, environment_id: str | None = None) -> list[dict[str, Any]]:
    return read_jsonl_file("canon/passages.jsonl", environment_id=environment_id)


@router.get("/passages/{passage_id}")
async def get_passage(passage_id: str, environment_id: str | None = None) -> dict[str, Any]:
    passages = get_passages_data(environment_id=environment_id)
    for p in passages:
        if p.get("passage_id") == passage_id:
            return p
    raise HTTPException(status_code=404, detail="Passage not found")
