# Agentic Traversal for GraphRAG (Research Summary + Showrunner Policy)

**Purpose**
Summarize recent arXiv research on agentic graph traversal and translate it into a practical traversal policy for Showrunner’s V2 graph layer.

---

## Research Snapshot (arXiv)

### 1) Graph-R1 (arXiv:2507.21892)
**Key idea:** Treat GraphRAG retrieval as a multi-turn agent–environment loop optimized with reinforcement learning.  
**Relevant concepts:** multi-step retrieval, adaptive traversal, and lightweight hypergraph construction.

### 2) GraphSearch (arXiv:2509.22009)
**Key idea:** Agentic deep-search workflow with **dual-channel retrieval**: semantic text retrieval + relational graph retrieval.  
**Relevant concepts:** multi-turn modular retrieval and iterative reasoning with both modalities.

### 3) BYOKG-RAG (arXiv:2507.04127)
**Key idea:** LLMs generate graph artifacts (entities, reasoning paths, OpenCypher), while graph tools ground and retrieve context; iterative refinement addresses entity-linking failures.  
**Relevant concepts:** tool-assisted traversal + iterative correction for custom KGs.

### 4) AnchorRAG (arXiv:2509.01238)
**Key idea:** Multi-agent collaboration for **open-world KG RAG** when anchor entities are uncertain. Predictor proposes candidate anchors, retrievers expand in parallel, supervisor synthesizes.  
**Relevant concepts:** anchor uncertainty, parallel multi-hop exploration, supervisor synthesis.

### 5) Agent-as-a-Graph (arXiv:2511.18194)
**Key idea:** Graph-based tool/agent retrieval. Tools and agents are graph nodes; retrieval uses vector search, weighted RRF rerank, and graph traversal.  
**Relevant concepts:** graph-based routing for tool/agent selection.

### 6) KG-R1 (arXiv:2509.26383) — **Withdrawn**
**Status:** Withdrawn; paper notes incorrect main results.  
**Key idea (treat as conceptual only):** single-agent RL traversal over KGs for retrieval.

---

## Common Patterns Across the Literature

1. **Multi-turn traversal** beats one-shot retrieval for multi-hop reasoning.
2. **Dual-channel retrieval** (graph + text) yields better recall and answer quality.
3. **Anchor uncertainty handling** (candidate anchors + parallel exploration) improves robustness.
4. **Tool-grounded graph querying** is more reliable than free-form LLM traversal.
5. **Supervisor synthesis** is needed to merge paths and resolve conflicts.

---

## Showrunner Agentic Traversal Policy (V2)

**Objective:** produce evidence-anchored, multi-hop story reasoning while keeping provenance first-class.

### Step 1: Anchor Candidates
- Use entity linker to generate top-K anchor entities for the query.
- If entity confidence is low, generate multiple anchor candidates.

### Step 2: Parallel Traversal Workers
- Spawn one traversal worker per anchor candidate.
- Each worker performs multi-turn expansions over relationships and events.

### Step 3: Dual-Channel Retrieval
- At each hop, run:
- Graph expansion: neighbors, relations, events.
- Text retrieval: canon passages supporting those nodes/edges.
- Merge and rank evidence (e.g., weighted RRF or similar).

### Step 4: Tool-Grounded Queries
- Workers propose candidate edges and paths.
- Graph tooling executes and returns subgraph context.
- Workers refine traversal based on returned evidence.

### Step 5: Evidence Gate
- Retain only nodes/edges with at least one evidence anchor.

### Step 6: Stop Rules
- Stop if no new evidence is found for N steps.
- Stop if hop budget reached.
- Stop when confidence exceeds threshold.

### Step 7: Supervisor Synthesis
- Merge subgraphs across workers.
- Deduplicate and resolve contradictions.
- Output graph updates + provenance for canon stores.

### Step 8: Routing & Specialization
- Use graph-based routing to assign specialized agents:
  - events, relationships, obligations, QA.

---

## How This Integrates with Showrunner

**Inputs**
- Entities + relationships + obligations (from canonical stores)
- Evidence anchors (canon passages)

**Outputs**
- Updated graph stores (events/relationships)
- Review queue items for ambiguous anchors
- Evidence-backed traversal traces for QA

**Gates**
- Schema validation
- Evidence gate
- Referential integrity
- Contradiction detection (WARN in MVP)

---

## Implementation Notes

1. Start with **AnchorRAG-style anchor expansion** + **GraphSearch dual-channel retrieval**.
2. Add **BYOKG-RAG style tooling** to ground traversal in graph queries.
3. Add **Graph-R1 style multi-turn loop** once traversal stability is proven.
4. Use **Agent-as-a-Graph routing** to assign specialist workers.

---

## Risks & Mitigations

- **Entity linking errors:** Use multiple anchors and keep a review queue for low-confidence cases.
- **Traversal explosion:** Use hop limits and evidence saturation thresholds.
- **Hallucinated edges:** Enforce evidence gate at every hop.
- **Conflicting paths:** Supervisor synthesis resolves conflicts and raises review items.

---

## References (arXiv IDs)
- Graph-R1: arXiv:2507.21892
- GraphSearch: arXiv:2509.22009
- BYOKG-RAG: arXiv:2507.04127
- AnchorRAG: arXiv:2509.01238
- Agent-as-a-Graph: arXiv:2511.18194
- KG-R1 (withdrawn): arXiv:2509.26383
