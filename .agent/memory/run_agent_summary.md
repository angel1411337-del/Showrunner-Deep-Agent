# Run Agent Feature Implementation (v1.3)

**Date**: 2026-02-04
**Summary**: Implemented the "Run Agent" functionality which allows the user to trigger the pipeline via the UI.

## Status
- **Backend**: Implemented `POST /api/run` and `GET /api/run/status`.
    - **NOTE**: The backend implementation currently uses a **STUB** (`run_pipeline_stub` in `src/showrunner/server/api.py`) to simulate execution. This was done to unblock UI development.
    - Future work must replace this stub with the actual `ShowrunnerPipeline` execution logic once the pipeline is fully stable and configured.
- **Frontend**: `App.jsx` updated with polling logic and progress UI.
- **Verification**: Verified end-to-end flow with browser automation.

## Key Files
- `src/showrunner/server/api.py`: Contains endpoints and the stub function.
- `web/src/App.jsx`: Contains frontend logic for triggering and monitoring the run.
- `tests/test_run_api.py`: Tests for the API endpoints.

## Known Limitations
- The "Run Agent" button currently runs a simulation, not the real agent.
- Input/Output directories are hardcoded in the stub/plan to `sample_corpus` and `out`.

## Usage
To trigger a run, send a POST request to `http://localhost:8000/api/run`.
Monitor progress via `http://localhost:8000/api/run/status`.
