# GUI Input Contract (V1)

## Purpose
Define the file-based inputs the GUI should read in V1. This keeps the GUI
decoupled from backend implementation details and lets it operate on exported
artifacts.

## Related Docs
- `docs/V1_SPEC.md`
- `docs/V2_SPEC.md`
- `docs/OUTPUTS_CONTRACT.md`
- `docs/LANGCHAIN_LANGGRAPH_UPGRADE.md`

## Expected Input Root
The GUI should accept a path to an output directory produced by the pipeline.
Example:
```
out/
  canon/
  kb/
  obligations/
  qa/
  exports/
  review/
  run_manifest.json
```

## Required Inputs (V1)
The GUI should function with the following files present. If any are missing,
show a clear error state with a remediation hint.

1. `obligations/obligations.json`
   - Array of Obligation objects.
   - Used for dossier sections, filtering, and obligation detail pages.
2. `kb/entities.json`
   - Array of Entity objects.
   - Used for entity explorer and linking obligations to entities.
3. `kb/aliases.json`
   - Array of AliasEntry objects.
   - Used for search and entity mapping.
4. `canon/passages.jsonl`
   - JSONL of PassageRecord objects.
   - Used to render evidence excerpts in context.
5. `exports/Unresolved_Threads_Dossier.md`
   - Rendered dossier for a read-only view and export.

## Optional Inputs (Nice-to-have)
If present, the GUI should show additional sections. If absent, hide the
corresponding UI without error.

1. `exports/mysteries_reveals_table.csv`
   - Reveal ledger view.
2. `exports/twist_bank.md`
   - Twist bank view.
3. `review/queue.jsonl`
   - Review queue viewer.
4. `qa/findings.jsonl`
   - Optional diagnostics.
5. `run_manifest.json`
   - Run metadata (timestamp, git sha, config hash).
6. `events/events.json` or `events.json`
   - Event records for wiki views.
7. `relationships/relationships.json` or `relationships.json`
   - Relationship records for wiki views.

## File Schemas (High-Level)
Refer to contracts in `src/showrunner/contracts/` for canonical fields.

### Obligation (obligations.json)
- `obligation_id`: string
- `category`: "plot_thread" | "chekhov_gun" | "prophecy_vision" | "mystery"
- `description`: string
- `evidence_anchor_ids`: string[]
- `last_seen_passage_id`: string
- `confidence`: number (0-1)
- `is_resolved`: boolean
- `resolution_passage_id`: string | null
- `related_entity_ids`: string[]

### Entity (entities.json)
- `entity_id`: string
- `canonical_name`: string
- `entity_type`: "person" | "place" | "artifact" | "group" | "vehicle"
- `first_seen_passage`: string
- `mention_count`: number
- `is_important`: boolean
- `description`: string | null

### AliasEntry (aliases.json)
- `alias_id`: string
- `alias`: string
- `entity_id`: string
- `confidence`: number (0-1)

### PassageRecord (passages.jsonl)
- `passage_id`: string
- `source_id`: string
- `source_path`: string
- `paragraph_index`: number
- `text`: string
- `char_start`: number
- `char_end`: number

### EvidenceAnchor (anchors in pipeline state)
Evidence anchors are referenced by `obligations.evidence_anchor_ids` and are
stored in pipeline state. The GUI should resolve anchors using the anchor IDs
embedded in the pipeline outputs (if a separate anchors file is added later).

### ReviewQueueItem (review/queue.jsonl)
- `item_id`: string
- `created_at`: ISO timestamp
- `category`: "ambiguous_entity" | "low_confidence_obligation" | "potential_contradiction"
- `severity`: "high" | "medium" | "low"
- `description`: string
- `related_ids`: string[]
- `suggested_actions`: string[]
- `status`: "pending" | "reviewed" | "dismissed"

### Event (events.json)
- `event_id`: string
- `event_type`: "battle" | "death" | "treaty" | "betrayal" | "marriage" | "coronation" | "travel" | "discovery" | "other"
- `title`: string
- `description`: string
- `participant_entity_ids`: string[]
- `location_entity_id`: string | null
- `related_obligation_ids`: string[]
- `evidence_anchor_ids`: string[]
- `story_time`: StoryTime
- `story_order`: StoryOrder
- `created_at`: ISO timestamp

### Relationship (relationships.json)
- `relationship_id`: string
- `relation_type`: "alliance" | "enmity" | "kinship" | "oath" | "debt" | "command" | "membership" | "ownership" | "other"
- `source_entity_id`: string
- `target_entity_id`: string
- `description`: string
- `evidence_anchor_ids`: string[]
- `story_time`: StoryTime
- `story_order`: StoryOrder
- `created_at`: ISO timestamp

### StoryTime (embedded)
- `time_label`: string | null
- `time_start`: string | null
- `time_end`: string | null

### StoryOrder (embedded)
- `order_index`: number
- `order_label`: string | null
- `source_id`: string | null
- `passage_id`: string | null

## Required Behaviors
1. Graceful fallback if optional files are missing.
2. Clear error if required files are missing.
3. No mutation of source files; GUI is read-only in V1.

## Path Compatibility
Paths may be Windows-style or POSIX-style. Use robust path joins and avoid
string concatenation.
