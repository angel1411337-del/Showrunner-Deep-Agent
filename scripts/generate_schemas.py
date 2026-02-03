#!/usr/bin/env python
"""Generate JSON Schema snapshots from Pydantic contracts.

DataOps requirement: Schema snapshots are versioned into schemas/ and
validated against in CI for artifact integrity.
"""

import json
from pathlib import Path

from showrunner.contracts import (
    AliasEntry,
    Beat,
    ConvergencePoint,
    DatasetManifest,
    DocumentUnit,
    Entity,
    EvidenceAnchor,
    EvidenceIndex,
    Finding,
    MetricsReport,
    Obligation,
    ObligationGraphEdge,
    OutlineSection,
    OverrideRule,
    PassageRecord,
    RunManifest,
)

SCHEMA_DIR = Path(__file__).parent.parent / "schemas"


def generate_schemas() -> None:
    """Generate JSON Schema for all contract models."""
    SCHEMA_DIR.mkdir(exist_ok=True)

    models = [
        DocumentUnit,
        PassageRecord,
        EvidenceAnchor,
        EvidenceIndex,
        Entity,
        AliasEntry,
        OverrideRule,
        Obligation,
        ObligationGraphEdge,
        Finding,
        MetricsReport,
        RunManifest,
        DatasetManifest,
        Beat,
        ConvergencePoint,
        OutlineSection,
    ]

    for model in models:
        schema = model.model_json_schema()
        schema_path = SCHEMA_DIR / f"{model.__name__}.json"
        with open(schema_path, "w") as f:
            json.dump(schema, f, indent=2)
        print(f"Generated: {schema_path}")

    print(f"\n[OK] Generated {len(models)} schemas in {SCHEMA_DIR}")


if __name__ == "__main__":
    generate_schemas()
