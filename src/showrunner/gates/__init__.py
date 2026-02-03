"""Quality gates for the Showrunner Orchestrator.

Provides DataOps-grade validation including:
- Schema validation
- Referential integrity checks
- Evidence gate (hard gate)
- Contradiction detection (soft gate)
"""

from showrunner.gates.quality_gates import QualityGates

__all__ = ["QualityGates"]
