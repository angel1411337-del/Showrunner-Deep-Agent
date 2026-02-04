# Showrunner Deep Agent — V2 Spec (Research-Layer Enabled)

**Purpose**
Evolve the V1 pipeline into a deep agent with planning, persistent memory, and multi-agent evaluation to generate trustworthy outlines, payoffs, and alternate paths grounded in canon.

**Goals**
- Replace simple harness with a multi-step deep agent loop.
- Add persistent memory, planning, and subagent specialization.
- Enable multi-outline + payoff + inflection generation.
- Introduce graph-aware retrieval and temporal memory.

**Non-Goals**
- Unbounded autonomy without evidence gates.
- Free-form outputs that bypass schema contracts.
- Replacing deterministic stores with opaque model state.

**Architecture Enhancements**
**Agent loop (full)**
1. Detect change / start run.
2. Retrieve relevant canon + memory.
3. Plan (structured tasks).
4. Propose candidates (events, relationships, payoffs, outlines).
5. Validate (gates).
6. Repair or re-plan if needed.
7. Persist artifacts + summaries.
8. Queue human review items.
9. Resume on next change.

**New layers**
- GraphRAG / Neo4j for multi-hop relationship queries.
- Temporal memory (Zep-style) for timeline evolution across runs.
- Multi-agent evaluation (canon, theme, continuity, plausibility).
- Hierarchical planning for outline expansion from coarse → detailed.

**New Artifacts**
**Writer-facing**
- `exports/master_outline.md`
- `exports/mysteries_reveals_table.csv`
- `exports/twist_bank.md`

**Structured stores**
- `plans/outline.json`
- `plans/reveals.json`
- `plans/twists.json`
- `plans/outline_variants.json` or `plans/multi_outline_pack.json`

**Safety & HITL**
- Approval gates for canon-store updates.
- Interruptions for high-risk edits and ambiguous evidence.
- Audit trail for all tool calls.

**Success Criteria**
- Consistent multi-outline generation grounded in evidence.
- Reduced human cleanup due to verification + repair loop.
- Long-running memory + timeline consistency across runs.

**Acceptance Criteria**
- Agent can generate multiple outline variants with payoffs and inflections that pass gates.
- Graph queries answer multi-hop questions with evidence anchors.
- Temporal memory reflects time-ordered changes across multiple runs.
- Multi-agent evaluation produces ranked candidates with traceable rationale.
- HITL interrupts occur before canon writes and are resumable.

**Test Matrix**
| Area | Test Type | Tests / Evidence |
| --- | --- | --- |
| Planning loop | Integration | Plan creation, execution order, and re-plan on failure |
| Graph retrieval | Integration | Multi-hop query tests with evidence anchors |
| Temporal memory | Integration | Timeline state persistence across runs |
| Multi-agent evaluation | Integration | Ranking output + rationale validation |
| Outline variants | Unit + schema snapshot | Contract tests + schema snapshots |
| HITL interrupts | Integration | Pause, approval, and resume flow tests |
| Repair loop | Integration | Gate failure triggers repair and re-validation |
