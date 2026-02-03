#!/usr/bin/env python3
"""Check referential integrity across all artifact stores.

This script validates that all cross-references between artifact types
are valid (i.e., referenced IDs actually exist in their respective stores).

Integrity checks:
    - Every obligation.evidence_anchor_ids exists in anchors
    - Every obligation.related_entity_ids exists in entities
    - Every obligation.last_seen_passage_id exists in passages
    - Every obligation.resolution_passage_id exists in passages (if set)
    - Every alias.entity_id exists in entities
    - Every anchor.passage_id exists in passages
    - Every entity.first_seen_passage exists in passages
    - Every obligation_edge source/target exists in obligations

Exit codes:
    0: All references valid
    1: Integrity violations found
    2: Required files missing or unreadable
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class IntegrityReport:
    """Accumulates integrity check results."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks_passed: int = 0
    checks_failed: int = 0

    def error(self, msg: str) -> None:
        """Record an integrity error."""
        self.errors.append(msg)
        self.checks_failed += 1

    def warn(self, msg: str) -> None:
        """Record a warning (non-fatal)."""
        self.warnings.append(msg)

    def passed(self) -> None:
        """Record a passed check."""
        self.checks_passed += 1

    @property
    def success(self) -> bool:
        """Return True if no errors."""
        return len(self.errors) == 0


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load records from a JSONL file."""
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_json_or_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load records from JSON or JSONL file.

    Tries .jsonl first, then .json.
    """
    jsonl_path = path.with_suffix(".jsonl")
    json_path = path.with_suffix(".json")

    if jsonl_path.exists():
        return load_jsonl(jsonl_path)

    if json_path.exists():
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else [data]

    return []


def extract_ids(records: list[dict[str, Any]], id_field: str) -> set[str]:
    """Extract a set of IDs from records."""
    return {r[id_field] for r in records if id_field in r}


def check_references(
    report: IntegrityReport,
    source_records: list[dict[str, Any]],
    source_name: str,
    ref_field: str,
    target_ids: set[str],
    target_name: str,
    id_field: str = "id",
    is_array: bool = False,
    optional: bool = False,
) -> None:
    """Check that all references from source to target are valid.

    Args:
        report: Report to accumulate results
        source_records: Records containing references
        source_name: Name of source type (for messages)
        ref_field: Field containing the reference(s)
        target_ids: Valid target IDs
        target_name: Name of target type (for messages)
        id_field: Field containing source record ID (for messages)
        is_array: True if ref_field contains array of IDs
        optional: True if field can be null/missing
    """
    for record in source_records:
        record_id = record.get(id_field, "<unknown>")
        ref_value = record.get(ref_field)

        if ref_value is None:
            if not optional:
                report.error(f"{source_name} {record_id}: missing required field '{ref_field}'")
            continue

        refs = ref_value if is_array else [ref_value]

        for ref in refs:
            if ref not in target_ids:
                report.error(
                    f"{source_name} {record_id}: {ref_field} references "
                    f"non-existent {target_name} '{ref}'"
                )
            else:
                report.passed()


def main() -> int:
    """Main integrity check routine."""
    project_root = Path(__file__).parent.parent
    artifacts_dir = project_root / "artifacts"

    report = IntegrityReport()

    print("=" * 60)
    print("Referential Integrity Check")
    print("=" * 60)

    # Check artifacts directory exists
    if not artifacts_dir.exists():
        print(f"INFO: No artifacts directory found at {artifacts_dir}")
        print("Skipping integrity checks (no artifacts to check)")
        return 0

    # Load all stores
    print("\nLoading artifact stores...")

    passages = load_json_or_jsonl(artifacts_dir / "passages")
    passage_ids = extract_ids(passages, "passage_id")
    print(f"  Passages: {len(passages)} records")

    anchors = load_json_or_jsonl(artifacts_dir / "anchors")
    anchor_ids = extract_ids(anchors, "anchor_id")
    print(f"  Anchors: {len(anchors)} records")

    entities = load_json_or_jsonl(artifacts_dir / "entities")
    entity_ids = extract_ids(entities, "entity_id")
    print(f"  Entities: {len(entities)} records")

    aliases = load_json_or_jsonl(artifacts_dir / "aliases")
    print(f"  Aliases: {len(aliases)} records")

    obligations = load_json_or_jsonl(artifacts_dir / "obligations")
    obligation_ids = extract_ids(obligations, "obligation_id")
    print(f"  Obligations: {len(obligations)} records")

    obligation_edges = load_json_or_jsonl(artifacts_dir / "obligation_edges")
    print(f"  Obligation edges: {len(obligation_edges)} records")

    # Skip if no artifacts
    total_records = (
        len(passages)
        + len(anchors)
        + len(entities)
        + len(aliases)
        + len(obligations)
        + len(obligation_edges)
    )

    if total_records == 0:
        print("\nNo artifacts found to check.")
        return 0

    print("\nRunning integrity checks...")

    # Check: anchor.passage_id -> passages
    if anchors:
        print("  Checking anchor -> passage references...")
        check_references(
            report,
            anchors,
            "Anchor",
            "passage_id",
            passage_ids,
            "passage",
            id_field="anchor_id",
        )

    # Check: alias.entity_id -> entities
    if aliases:
        print("  Checking alias -> entity references...")
        check_references(
            report,
            aliases,
            "Alias",
            "entity_id",
            entity_ids,
            "entity",
            id_field="alias_id",
        )

    # Check: entity.first_seen_passage -> passages
    if entities:
        print("  Checking entity -> passage references...")
        check_references(
            report,
            entities,
            "Entity",
            "first_seen_passage",
            passage_ids,
            "passage",
            id_field="entity_id",
        )

    # Check: obligation.evidence_anchor_ids -> anchors
    if obligations:
        print("  Checking obligation -> anchor references...")
        check_references(
            report,
            obligations,
            "Obligation",
            "evidence_anchor_ids",
            anchor_ids,
            "anchor",
            id_field="obligation_id",
            is_array=True,
        )

        # Check: obligation.last_seen_passage_id -> passages
        print("  Checking obligation -> last_seen_passage references...")
        check_references(
            report,
            obligations,
            "Obligation",
            "last_seen_passage_id",
            passage_ids,
            "passage",
            id_field="obligation_id",
        )

        # Check: obligation.resolution_passage_id -> passages (optional)
        print("  Checking obligation -> resolution_passage references...")
        check_references(
            report,
            obligations,
            "Obligation",
            "resolution_passage_id",
            passage_ids,
            "passage",
            id_field="obligation_id",
            optional=True,
        )

        # Check: obligation.related_entity_ids -> entities (optional, array)
        print("  Checking obligation -> entity references...")
        for obl in obligations:
            related_ids = obl.get("related_entity_ids", [])
            if related_ids:
                for eid in related_ids:
                    if eid not in entity_ids:
                        report.error(
                            f"Obligation {obl.get('obligation_id', '<unknown>')}: "
                            f"related_entity_ids references non-existent entity '{eid}'"
                        )
                    else:
                        report.passed()

    # Check: obligation_edge source/target -> obligations
    if obligation_edges:
        print("  Checking obligation_edge -> obligation references...")
        for edge in obligation_edges:
            edge_id = edge.get("edge_id", "<unknown>")

            source_id = edge.get("source_obligation_id")
            if source_id and source_id not in obligation_ids:
                report.error(
                    f"ObligationEdge {edge_id}: source_obligation_id references "
                    f"non-existent obligation '{source_id}'"
                )
            elif source_id:
                report.passed()

            target_id = edge.get("target_obligation_id")
            if target_id and target_id not in obligation_ids:
                report.error(
                    f"ObligationEdge {edge_id}: target_obligation_id references "
                    f"non-existent obligation '{target_id}'"
                )
            elif target_id:
                report.passed()

    # Summary
    print("\n" + "=" * 60)
    print(f"Checks passed: {report.checks_passed}")
    print(f"Checks failed: {report.checks_failed}")

    if report.warnings:
        print(f"\nWarnings ({len(report.warnings)}):")
        for warn in report.warnings:
            print(f"  - {warn}")

    if report.errors:
        print(f"\nERRORS ({len(report.errors)}):")
        for error in report.errors:
            print(f"  - {error}")
        return 1

    print("\nAll integrity checks passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
