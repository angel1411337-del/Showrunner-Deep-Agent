# Showrunner Outputs Contract

This document lists the agreed filesystem outputs by release. It is intended to keep all contributors aligned on the exact artifact names, locations, and purposes. Local-first, artifact-driven, paragraph-level evidence, hard evidence gate, and soft contradiction WARN are assumed.

## v0.1 - Dossier (MVP)

### Writer-facing export
1. `exports/Unresolved_Threads_Dossier.md`

### Canonical stores (data artifacts)
1. `canon/passages.jsonl`
2. `canon/evidence_index.jsonl`
3. `canon/index.sqlite`
4. `kb/entities.json`
5. `kb/aliases.json`
6. `obligations/obligations.json`

### QA + run bookkeeping
1. `qa/findings.jsonl`
2. `qa/metrics.json`
3. `run_manifest.json`
4. `dataset_manifest.json`
5. `tool_call_audit.jsonl`

## v0.2 - Master Outline

### Writer-facing export
1. `exports/master_outline_books_6_7.md`

### Supporting structured store
1. `plans/outline.json`

### QA + run bookkeeping
1. `qa/findings.jsonl` (adds outline coverage checks)
2. `qa/metrics.json`
3. `run_manifest.json`
4. `dataset_manifest.json`
5. `tool_call_audit.jsonl`

## v0.3 - Reveal Ledger

### Writer-facing export
1. `exports/mysteries_reveals_table.csv`

### Supporting structured store
1. `plans/reveals.json`

### QA + run bookkeeping
1. `qa/findings.jsonl` (adds reveal validity checks)
2. `qa/metrics.json`
3. `run_manifest.json`
4. `dataset_manifest.json`
5. `tool_call_audit.jsonl`

## v0.4 - Twist Bank

### Writer-facing export
1. `exports/twist_bank.md`

### Supporting structured store
1. `plans/twists.json`

### QA + run bookkeeping
1. `qa/findings.jsonl` (adds twist plausibility checks)
2. `qa/metrics.json`
3. `run_manifest.json`
4. `dataset_manifest.json`
5. `tool_call_audit.jsonl`

## Passive Mode (Git Hooks)

Passive mode does not add new writer-facing exports by itself. It updates existing stores and adds a review queue:

1. `review/queue.jsonl`

Updated continuously:
1. `canon/*`
2. `kb/*`
3. `obligations/*`
4. `qa/*`
5. manifests and audit logs
