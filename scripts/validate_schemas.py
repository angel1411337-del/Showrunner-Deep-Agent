#!/usr/bin/env python3
"""Validate artifacts against JSON Schema snapshots.

This script validates all artifact files in the artifacts/ directory against
their corresponding JSON schemas in the schemas/ directory.

Exit codes:
    0: All artifacts valid
    1: Validation errors found
    2: Schema or artifact files missing
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft7Validator
except ImportError:
    print("ERROR: jsonschema package not installed. Run: uv add jsonschema")
    sys.exit(2)


# Map artifact file patterns to their schema files
ARTIFACT_SCHEMA_MAP: dict[str, str] = {
    "passages.json": "PassageRecord.json",
    "passages.jsonl": "PassageRecord.json",
    "anchors.json": "EvidenceAnchor.json",
    "anchors.jsonl": "EvidenceAnchor.json",
    "evidence_index.json": "EvidenceIndex.json",
    "entities.json": "Entity.json",
    "entities.jsonl": "Entity.json",
    "aliases.json": "AliasEntry.json",
    "aliases.jsonl": "AliasEntry.json",
    "obligations.json": "Obligation.json",
    "obligations.jsonl": "Obligation.json",
    "obligation_edges.json": "ObligationGraphEdge.json",
    "obligation_edges.jsonl": "ObligationGraphEdge.json",
    "findings.json": "Finding.json",
    "findings.jsonl": "Finding.json",
    "metrics.json": "MetricsReport.json",
    "run_manifest.json": "RunManifest.json",
    "dataset_manifest.json": "DatasetManifest.json",
    "events.json": "Event.json",
    "events.jsonl": "Event.json",
    "relationships.json": "Relationship.json",
    "relationships.jsonl": "Relationship.json",
    "queue.jsonl": "ReviewQueueItem.json",
    "queue.json": "ReviewQueueItem.json",
    "documents.json": "DocumentUnit.json",
    "documents.jsonl": "DocumentUnit.json",
    "overrides.json": "OverrideRule.json",
    "overrides.jsonl": "OverrideRule.json",
}


def load_schema(schema_path: Path) -> dict[str, Any]:
    """Load a JSON schema from file."""
    with open(schema_path, encoding="utf-8") as f:
        return json.load(f)


def load_artifacts(artifact_path: Path) -> list[dict[str, Any]]:
    """Load artifacts from JSON or JSONL file.

    Returns a list of artifact objects for validation.
    """
    with open(artifact_path, encoding="utf-8") as f:
        if artifact_path.suffix == ".jsonl":
            # JSONL: one object per line
            return [json.loads(line) for line in f if line.strip()]
        else:
            # JSON: could be array or single object
            data = json.load(f)
            if isinstance(data, list):
                return data
            return [data]


def validate_artifact(
    artifact: dict[str, Any],
    schema: dict[str, Any],
    validator: Draft7Validator,
) -> list[str]:
    """Validate a single artifact against schema.

    Returns list of error messages (empty if valid).
    """
    errors = []
    for error in validator.iter_errors(artifact):
        path = ".".join(str(p) for p in error.absolute_path) or "(root)"
        errors.append(f"  - {path}: {error.message}")
    return errors


def main() -> int:
    """Main validation routine.

    Returns exit code.
    """
    project_root = Path(__file__).parent.parent
    schemas_dir = project_root / "schemas"
    artifacts_dir = project_root / "artifacts"

    # Check schemas directory exists
    if not schemas_dir.exists():
        print(f"ERROR: Schemas directory not found: {schemas_dir}")
        return 2

    # Check artifacts directory exists (optional - may not exist yet)
    if not artifacts_dir.exists():
        print(f"INFO: No artifacts directory found at {artifacts_dir}")
        print("Skipping artifact validation (no artifacts to validate)")
        return 0

    # Track validation results
    total_files = 0
    total_records = 0
    failed_files: list[str] = []
    all_errors: list[str] = []

    print("=" * 60)
    print("Schema Validation Report")
    print("=" * 60)

    # Find and validate all artifact files
    for artifact_file in sorted(artifacts_dir.rglob("*")):
        if not artifact_file.is_file():
            continue
        if artifact_file.suffix not in (".json", ".jsonl"):
            continue

        # Find matching schema
        schema_name = ARTIFACT_SCHEMA_MAP.get(artifact_file.name)
        if not schema_name:
            print(f"WARN: No schema mapping for {artifact_file.name}, skipping")
            continue

        schema_path = schemas_dir / schema_name
        if not schema_path.exists():
            print(f"ERROR: Schema not found: {schema_path}")
            failed_files.append(str(artifact_file))
            continue

        total_files += 1

        # Load schema and create validator
        try:
            schema = load_schema(schema_path)
            validator = Draft7Validator(schema)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in schema {schema_path}: {e}")
            failed_files.append(str(artifact_file))
            continue

        # Load and validate artifacts
        try:
            artifacts = load_artifacts(artifact_file)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in {artifact_file}: {e}")
            failed_files.append(str(artifact_file))
            continue

        file_errors: list[str] = []
        for i, artifact in enumerate(artifacts):
            total_records += 1
            errors = validate_artifact(artifact, schema, validator)
            if errors:
                file_errors.append(f"Record {i}:")
                file_errors.extend(errors)

        if file_errors:
            print(f"FAIL: {artifact_file.name} ({len(file_errors)} errors)")
            all_errors.append(f"\n{artifact_file.name}:")
            all_errors.extend(file_errors)
            failed_files.append(str(artifact_file))
        else:
            print(f"OK: {artifact_file.name} ({len(artifacts)} records)")

    # Summary
    print("\n" + "=" * 60)
    print(f"Validated {total_files} files, {total_records} records")

    if failed_files:
        print(f"\nFAILED ({len(failed_files)} files):")
        for f in failed_files:
            print(f"  - {f}")
        print("\nErrors:")
        for error in all_errors:
            print(error)
        return 1

    print("All validations passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
