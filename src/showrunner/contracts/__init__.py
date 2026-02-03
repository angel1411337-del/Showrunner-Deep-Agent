"""Pydantic v2 contracts for the Showrunner Orchestrator.

All formal artifacts and tool I/O use these contracts for:
- Schema enforcement at runtime
- JSON Schema generation for CI validation
- Referential integrity checking
"""

from showrunner.contracts.document import DocumentUnit, PassageRecord
from showrunner.contracts.entity import (
    AliasEntry,
    Entity,
    EntityType,
    OverrideAction,
    OverrideRule,
)
from showrunner.contracts.evidence import EvidenceAnchor, EvidenceIndex
from showrunner.contracts.manifest import DatasetManifest, RunManifest
from showrunner.contracts.obligation import (
    EdgeType,
    Obligation,
    ObligationCategory,
    ObligationGraphEdge,
)
from showrunner.contracts.outline import Beat, ConvergencePoint, OutlineSection
from showrunner.contracts.quality import Finding, FindingSeverity, MetricsReport

__all__ = [
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
    # Outline
    "Beat",
    "ConvergencePoint",
    "OutlineSection",
]
