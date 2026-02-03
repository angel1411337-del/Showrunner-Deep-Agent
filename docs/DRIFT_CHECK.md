# Drift Check - Claude Kickoff Documentation

Source: `docs/claude_kickoff_documentation.txt` (imported from Downloads on 2026-02-03)

Purpose: keep the repo aligned with the kickoff scope, ordering, and non-negotiables.

**Scope Locks**
- Deliverable order is locked: v0.1 Dossier -> v0.2 Master Outline -> v0.3 Reveal Ledger -> v0.4 Twist Bank -> Passive Mode (git hooks)
- No obligations or canon claims without at least one evidence anchor
- Exports must render only from validated stores (no direct LLM-written exports)
- Determinism is required (stable IDs, ordering, and golden fixtures)

**MVP v0.1 Dossier Deliverables**
- Export: `exports/Unresolved_Threads_Dossier.md`
- Stores: `canon/passages.jsonl`, `canon/evidence_index.jsonl`, `canon/index.sqlite`, `kb/entities.json`, `kb/aliases.json`, `obligations/obligations.json`
- QA: `qa/findings.jsonl`, `qa/metrics.json`
- Manifests and audit logs: `run_manifest.json`, dataset manifests, tool call audit log

**Non-Negotiable Gates**
- Run manifest gate: no run without `run_manifest.json` (input hashes, model IDs, prompt hashes, tool versions)
- Evidence gate: every obligation has >= 1 evidence anchor
- Schema gate: all outputs validate against Pydantic v2 schemas
- Referential integrity gate: all IDs resolve
- Export gate: render only from validated stores
- Contradiction checks are WARN-only in MVP

**Tech Stack Constraints**
- Python 3.14.x baseline, uv with committed `uv.lock`
- LangGraph v1 for orchestration
- Pydantic v2 for contracts and schema snapshots in `schemas/`
- Ruff (lint + format) and Pyright (type check) required in CI
- Storage formats: JSONL (append-only), JSON (registries), SQLite (index)

**v0.2 Master Outline Acceptance Focus**
- Outline derived from obligations and entity/state substrate
- Convergence points and bridging beats included
- Coverage mapping: obligations -> outline beats (even if coarse)

**v0.3 Reveal Ledger Acceptance Focus**
- Output: `exports/mysteries_reveals_table.csv`
- Every reveal entry links to a mystery/obligation and evidence anchors

**v0.4 Twist Bank Acceptance Focus**
- Output: `exports/twist_bank.md`
- Twists constrained by obligations and evidence congruence
- Each twist includes setup/backfill suggestions and risk notes

**Passive Mode (V1 Direction)**
- Git hooks trigger micro-runs on changed text
- Review queue entries are non-blocking and logged
- Optional stages can be skipped only by user approval, logged

**Sci-Fi Mode (Future)**
- Separate mode with WorldSpec, constraints, and canonization loops
- Shares the same control plane (loops, gates, audit, user-only skips)

**Drift Signals to Watch**
- New exports bypass validated stores
- Obligations without evidence anchors
- CI missing Ruff or Pyright gates
- Pipeline skipping non-skippable gates
- Roadmap order changed without explicit decision
