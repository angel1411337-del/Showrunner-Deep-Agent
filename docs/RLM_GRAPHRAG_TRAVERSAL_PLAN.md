# RLM + GraphRAG + Agentic Traversal Integration Plan

**Purpose**
Define how REPL/RLM, GraphRAG, and agentic traversal work together as one retrieval-and-reasoning system for Showrunner V2.

---

## Unified Architecture (How They Work Together)

**Knowledge Sources**
- **GraphRAG**: structured knowledge (entities, events, relationships, obligations, timelines).
- **REPL/RLM**: full corpus as a REPL variable for precise slicing and targeted sub-LLM calls.

**Retrieval Policy (Dual-Channel)**
- **Graph channel**: traverse graph neighbors, communities, multi-hop paths.
- **REPL channel**: slice text snippets to confirm evidence or fill gaps.

**Agentic Traversal Loop**
1. **Anchor selection**
   - Identify candidate entities/obligations from query.
   - If uncertain, explore multiple anchors in parallel.
2. **Graph expansion**
   - Expand neighbors and events.
   - Capture candidate evidence anchor IDs.
3. **REPL verification**
   - For each candidate edge or claim, pull exact slices via REPL.
   - Use sub-LLM calls only on those slices.
4. **Evidence gate**
   - If no evidence anchor, discard or queue for review.
5. **Stop condition**
   - Stop on evidence saturation, hop budget, or confidence threshold.
6. **Synthesis**
   - Merge paths across anchors, dedupe, and write updates.

---

## V2 Components

**REPL/RLM**
- `rlm/repl_executor.py`
  - Executes safe queries over the corpus variable.
- `rlm/corpus_variable.py`
  - Exposes helpers: `search()`, `slice()`, `get_passage()`.
- `rlm/sub_llm_delegator.py`
  - Runs focused sub-LLM calls on selected slices.

**GraphRAG**
- `graph/query_engine.py`
  - Local / global / drift search over graph.
- `graph/temporal_edges.py`
  - Time-bounded traversal support.

**Traversal Orchestration**
- `traversal/planner.py`
  - Chooses next hop and retrieval mode.
- `traversal/worker.py`
  - Executes traversal for a given anchor.
- `traversal/supervisor.py`
  - Merges results and resolves conflicts.

---

## Decision & Budget Policies

- Max hops per traversal.
- Max REPL queries per run.
- Max sub-LLM calls per run.
- Stop when no new evidence is found after N steps.

---

## Outputs

- `traces/traversal_trace.jsonl`
  - Each step recorded with anchor, graph query, REPL slice, evidence IDs.
- `wiki/events.json` and `wiki/relationships.json`
  - Updated with evidence-anchored outputs.
- `review/queue.jsonl`
  - Ambiguous or low-confidence edges queued for review.

---

## Gates

- Schema validation
- Evidence gate
- Referential integrity
- Contradiction warning (WARN in MVP; optional hard fail in V2)

---

## Implementation Order

1. **REPL corpus interface**
   - Safe slice + search helpers.
2. **Graph traversal API**
   - Local + multi-hop traversal.
3. **Dual-channel worker**
   - Graph expansion + REPL verification.
4. **Supervisor merge + evidence gate**
5. **Trace + audit logging**

---

## Integration Notes

- Use evidence anchors as the universal bridge between graph edges and corpus text.
- Keep traversal trace logs in JSONL for replayability and audit.
- Never write to canon stores without passing gates.
