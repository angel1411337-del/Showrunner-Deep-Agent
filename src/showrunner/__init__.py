"""Showrunner Orchestrator - Contract-driven deep agent for narrative analysis.

A Deep Agents harness on LangGraph v1 runtime that:
- Ingests long narrative corpus as stable, evidence-addressable passages
- Builds a living canon substrate (entities, obligations, state) with provenance
- Produces writer-ready planning docs (dossier first)
- Supports passive, incremental structuring via git hooks

MVP (v0.1): Unresolved Threads Dossier with evidence anchors.
"""

__version__ = "0.1.0"

# Re-export contracts for public API
from showrunner.contracts import (
    # Document
    DocumentUnit,
    PassageRecord,
    # Evidence
    EvidenceAnchor,
    EvidenceIndex,
    # Entity
    Entity,
    EntityType,
    AliasEntry,
    OverrideRule,
    OverrideAction,
    # Obligation
    Obligation,
    ObligationCategory,
    ObligationGraphEdge,
    EdgeType,
    # Quality
    Finding,
    FindingSeverity,
    MetricsReport,
    # Manifest
    RunManifest,
    DatasetManifest,
)

__all__ = [
    "__version__",
    # Document
    "DocumentUnit",
    "PassageRecord",
    # Evidence
    "EvidenceAnchor",
    "EvidenceIndex",
    # Entity
    "Entity",
    "EntityType",
    "AliasEntry",
    "OverrideRule",
    "OverrideAction",
    # Obligation
    "Obligation",
    "ObligationCategory",
    "ObligationGraphEdge",
    "EdgeType",
    # Quality
    "Finding",
    "FindingSeverity",
    "MetricsReport",
    # Manifest
    "RunManifest",
    "DatasetManifest",
]
