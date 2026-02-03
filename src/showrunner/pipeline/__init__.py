"""Pipeline module for Showrunner orchestration.

Exports the main pipeline components and protocols for dependency injection.
"""

from showrunner.pipeline.orchestrator import (
    ComponentFactory,
    PipelineConfig,
    PipelineState,
    ShowrunnerPipeline,
)
from showrunner.pipeline.protocols import (
    CanonIndexerProtocol,
    DedupeMergerProtocol,
    DossierFormatterProtocol,
    EntityResolverProtocol,
    ExportRendererProtocol,
    InputAdapterProtocol,
    ObligationExtractorProtocol,
    QualityGatesProtocol,
)

__all__ = [
    # Orchestrator
    "ComponentFactory",
    "PipelineConfig",
    "PipelineState",
    "ShowrunnerPipeline",
    # Protocols
    "CanonIndexerProtocol",
    "DedupeMergerProtocol",
    "DossierFormatterProtocol",
    "EntityResolverProtocol",
    "ExportRendererProtocol",
    "InputAdapterProtocol",
    "ObligationExtractorProtocol",
    "QualityGatesProtocol",
]
