# Agent V1 Capabilities and Limits

## Purpose
Define what the current V1 agent harness can do and what it does not yet do.

## Implemented

1. Run the existing pipeline end-to-end through a single harness API.
2. List generated artifacts from an output directory.
3. Read artifacts safely from a bounded output directory.
4. Report runtime capability flags for LangGraph, LangChain, and deepagents.

## Interfaces

- `showrunner.agent.harness.runtime_capabilities()`
- `showrunner.agent.harness.AgentHarness.run_pipeline(input_source, output_dir)`
- `showrunner.agent.harness.AgentHarness.list_artifacts(output_dir)`
- `showrunner.agent.harness.AgentHarness.read_artifact(output_dir, relative_path)`

## Non-Goals in V1

1. No deepagents execution loop yet.
2. No long-horizon autonomous planning runtime in the agent harness.
3. No persistent memory layer in the harness itself (pipeline artifacts are still
   the source of truth).
4. No subagent orchestration.

## Test Coverage

Harness behavior is covered by:
- `tests/test_agent_harness.py`

Pipeline export contract remains covered by:
- `tests/test_pipeline_planning_exports.py`
