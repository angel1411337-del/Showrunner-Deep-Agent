**LangChain/LangGraph Upgrade Checklist**

**Scope**
This is a repo-specific checklist to upgrade LangChain/LangGraph usage for Showrunner and stage deep-agent capabilities in two phases.

**V1 Checklist (Minimal, Safe)**
1. Pin versions in `pyproject.toml` for `langchain`, `langchain-core`, `langgraph`, and `deepagents`.
2. Ensure `langchain-core` is at a patched version (>=1.2.5) to avoid serialization vulnerabilities.
3. Add a minimal agent entrypoint in `src/showrunner/agent/` that wraps `create_agent` or a small LangGraph graph.
4. Implement a minimal tool surface.
5. Tool: `run_pipeline` to execute the existing pipeline with config.
6. Tool: `read_artifacts` to read artifacts from `exports/`, `qa/`, and manifests.
7. Tool: `list_artifacts` to enumerate outputs for a run.
8. Add middleware that enforces schema validation and evidence gates before writing outputs.
9. Constrain filesystem access to the repo root with a safe backend configuration.
10. Add tests first.
11. Unit tests for tool wrappers.
12. Integration test: agent runs the pipeline and produces the dossier artifacts.
13. Add `docs/AGENT_V1.md` describing capabilities and limits.

**V2 Checklist (Deep Agent + Research Layer)**
1. Enable planning with `write_todos` and `read_todos`.
2. Add subagents for events, relationships, obligations, and QA.
3. Add persistent memory with a composite backend.
4. Route `/memories/` to a store backend.
5. Route `/workspace/` to state or filesystem backend with safe access.
6. Integrate a graph backend (Neo4j or GraphRAG).
7. Add temporal memory for timeline evolution across runs.
8. Add multi-agent evaluation with scoring for canon, continuity, theme, and plausibility.
9. Add HITL interruptions for canon updates and high-risk edits.
10. Enable node caching and summarization middleware for performance.

**V1 vs V2 Feature Mapping**
1. Planning loop: V1 no, V2 yes.
2. Subagents: V1 no, V2 yes.
3. Persistent memory: V1 no, V2 yes.
4. Graph retrieval: V1 no, V2 yes.
5. Temporal memory: V1 no, V2 yes.
6. Multi-agent evaluation: V1 no, V2 yes.
7. HITL interrupts: V1 optional, V2 required.

**Acceptance Targets**
1. V1: agent can run pipeline end-to-end, gates pass, dossier generated, no persistent memory required.
2. V2: agent can generate multi-outline variants, pass gates, and recover via repair loop with review queue items.
