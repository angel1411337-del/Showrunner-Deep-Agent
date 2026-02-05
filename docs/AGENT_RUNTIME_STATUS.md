# Agent Runtime Status (LangGraph + LangChain + Deepagents)

## Purpose
Track what is implemented today versus what is still pending for the planned
deep-agent runtime.

## Current Status (as of 2026-02-05)

| Layer | Status | Evidence |
|------|--------|----------|
| LangGraph pipeline orchestration | Implemented | `src/showrunner/pipeline/orchestrator.py` |
| LangChain provider integrations | Partial | `src/showrunner/providers/anthropic.py`, `src/showrunner/providers/__init__.py` |
| Minimal agent harness wrapper | Implemented | `src/showrunner/agent/harness.py` |
| Deepagents runtime entrypoint | Not implemented | `runtime_capabilities()` reports availability only; no deepagents execution loop |
| v0.1-v0.4 artifact production | Implemented | `tests/test_pipeline_planning_exports.py` |
| Wiki extraction | Implemented | `src/showrunner/extractors/event_extractor.py`, `src/showrunner/extractors/relationship_extractor.py` |
| Graph baseline (Neo4j schema/loader/queries) | Implemented | `src/showrunner/graph/` |

## What "Partial" Means for LangChain

LangChain is currently used as an adapter layer for model providers. The main
control loop still runs through `ShowrunnerPipeline` instead of a LangChain
agent runtime.

## Target End State

1. Keep LangGraph as the deterministic artifact pipeline.
2. Add a minimal agent harness that calls the pipeline and reads artifacts.
3. Add deepagents runtime as an optional execution mode for V2 planning loops.
4. Keep evidence gates and schema checks mandatory across all runtimes.

## Immediate Refactor Direction

1. Add `src/showrunner/agent/` with a minimal harness interface.
2. Keep deepagents import optional to avoid breaking V1 environments.
3. Add integration tests proving:
   - the harness can execute pipeline runs,
   - the harness can read writer-facing artifacts safely.
