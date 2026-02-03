"""QualityGates module for DataOps-grade quality validation.

Implements quality gates for the Showrunner Orchestrator:
- Schema validation against JSON schemas
- Referential integrity checks
- Evidence gate (hard gate)
- Contradiction detection (soft gate in MVP)
"""

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel

from showrunner.contracts import (
    AliasEntry,
    Entity,
    EvidenceAnchor,
    Finding,
    FindingSeverity,
    Obligation,
    PassageRecord,
)


class QualityGates:
    """DataOps-grade quality gates for pipeline validation.

    Provides comprehensive validation including:
    - JSON schema validation for artifacts
    - Referential integrity across all entities
    - Evidence gate (ERROR if obligation has no evidence)
    - Contradiction detection (WARN only in MVP)
    """

    def validate_schema(
        self,
        artifact: BaseModel,
        schema_path: Path,
    ) -> list[Finding]:
        """Validate an artifact against a JSON schema.

        Args:
            artifact: Pydantic model instance to validate.
            schema_path: Path to JSON schema file.

        Returns:
            List of Finding objects for any validation errors.
        """
        findings: list[Finding] = []

        # Check if schema file exists
        if not schema_path.exists():
            findings.append(
                Finding(
                    finding_id=f"schema-{uuid4().hex[:8]}",
                    severity=FindingSeverity.ERROR,
                    category="schema",
                    message=f"Schema file not found: {schema_path}",
                    related_ids=[],
                )
            )
            return findings

        # Try to load and parse the schema
        try:
            schema_content = schema_path.read_text()
            schema = json.loads(schema_content)
        except json.JSONDecodeError as e:
            findings.append(
                Finding(
                    finding_id=f"schema-{uuid4().hex[:8]}",
                    severity=FindingSeverity.ERROR,
                    category="schema",
                    message=f"Invalid JSON schema file: {e}",
                    related_ids=[],
                )
            )
            return findings

        # Convert artifact to dict for validation
        artifact_dict = artifact.model_dump(mode="json")

        # Validate against schema
        schema_errors = self._validate_against_schema(artifact_dict, schema)
        for error in schema_errors:
            findings.append(
                Finding(
                    finding_id=f"schema-{uuid4().hex[:8]}",
                    severity=FindingSeverity.ERROR,
                    category="schema",
                    message=error,
                    related_ids=[],
                )
            )

        return findings

    def _validate_against_schema(
        self,
        data: dict,
        schema: dict,
    ) -> list[str]:
        """Validate data against a JSON schema.

        Args:
            data: Dictionary representation of the artifact.
            schema: Parsed JSON schema.

        Returns:
            List of error messages.
        """
        errors: list[str] = []

        # Check required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Check property types
        properties = schema.get("properties", {})
        for field_name, field_schema in properties.items():
            if field_name in data:
                value = data[field_name]
                expected_type = field_schema.get("type")
                if expected_type and not self._check_type(value, expected_type):
                    errors.append(
                        f"Field '{field_name}' has wrong type: "
                        f"expected {expected_type}, got {type(value).__name__}"
                    )

        return errors

    def _check_type(self, value: object, expected_type: str) -> bool:
        """Check if a value matches the expected JSON schema type.

        Args:
            value: The value to check.
            expected_type: Expected JSON schema type string.

        Returns:
            True if type matches, False otherwise.
        """
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None),
        }

        expected_python_type = type_map.get(expected_type)
        if expected_python_type is None:
            return True  # Unknown type, assume valid

        return isinstance(value, expected_python_type)

    def check_referential_integrity(
        self,
        passages: list[PassageRecord],
        anchors: list[EvidenceAnchor],
        entities: list[Entity],
        aliases: list[AliasEntry],
        obligations: list[Obligation],
    ) -> list[Finding]:
        """Check referential integrity across all artifacts.

        Validates:
        - Every obligation.evidence_anchor_ids references existing anchors
        - Every alias.entity_id exists in entities
        - Every anchor.passage_id exists in passages

        Args:
            passages: List of passage records.
            anchors: List of evidence anchors.
            entities: List of entities.
            aliases: List of alias entries.
            obligations: List of obligations.

        Returns:
            List of Finding objects for integrity violations.
        """
        findings: list[Finding] = []

        # Build lookup sets for fast membership testing
        passage_ids = {p.passage_id for p in passages}
        anchor_ids = {a.anchor_id for a in anchors}
        entity_ids = {e.entity_id for e in entities}

        # Check: obligation.evidence_anchor_ids must exist in anchors
        for obligation in obligations:
            for anchor_id in obligation.evidence_anchor_ids:
                if anchor_id not in anchor_ids:
                    findings.append(
                        Finding(
                            finding_id=f"ref-{uuid4().hex[:8]}",
                            severity=FindingSeverity.ERROR,
                            category="referential_integrity",
                            message=(
                                f"Obligation '{obligation.obligation_id}' references "
                                f"non-existent anchor: {anchor_id}"
                            ),
                            related_ids=[obligation.obligation_id, anchor_id],
                        )
                    )

        # Check: alias.entity_id must exist in entities
        for alias in aliases:
            if alias.entity_id not in entity_ids:
                findings.append(
                    Finding(
                        finding_id=f"ref-{uuid4().hex[:8]}",
                        severity=FindingSeverity.ERROR,
                        category="referential_integrity",
                        message=(
                            f"Alias '{alias.alias_id}' references "
                            f"non-existent entity: {alias.entity_id}"
                        ),
                        related_ids=[alias.alias_id, alias.entity_id],
                    )
                )

        # Check: anchor.passage_id must exist in passages
        for anchor in anchors:
            if anchor.passage_id not in passage_ids:
                findings.append(
                    Finding(
                        finding_id=f"ref-{uuid4().hex[:8]}",
                        severity=FindingSeverity.ERROR,
                        category="referential_integrity",
                        message=(
                            f"Anchor '{anchor.anchor_id}' references "
                            f"non-existent passage: {anchor.passage_id}"
                        ),
                        related_ids=[anchor.anchor_id, anchor.passage_id],
                    )
                )

        return findings

    def check_evidence_gate(
        self,
        obligations: list[Obligation],
    ) -> list[Finding]:
        """Check that all obligations have at least one evidence anchor.

        This is a hard gate - ERROR if any obligation has 0 evidence anchors.

        Args:
            obligations: List of obligations to check.

        Returns:
            List of Finding objects for obligations without evidence.
        """
        findings: list[Finding] = []

        for obligation in obligations:
            if not obligation.evidence_anchor_ids:
                findings.append(
                    Finding(
                        finding_id=f"evidence-{uuid4().hex[:8]}",
                        severity=FindingSeverity.ERROR,
                        category="evidence_gate",
                        message=(
                            f"Obligation '{obligation.obligation_id}' has no "
                            f"evidence anchors (minimum 1 required)"
                        ),
                        related_ids=[obligation.obligation_id],
                    )
                )

        return findings

    def detect_contradictions(
        self,
        obligations: list[Obligation],
    ) -> list[Finding]:
        """Detect potential contradictions between obligations.

        MVP implementation: Returns WARN severity (soft gate).
        This is a placeholder for more sophisticated contradiction
        detection in future versions.

        Args:
            obligations: List of obligations to analyze.

        Returns:
            List of Finding objects for detected contradictions (WARN only).
        """
        findings: list[Finding] = []

        # MVP: Simple heuristic-based contradiction detection
        # Future: Use semantic similarity and NLP for better detection

        if len(obligations) < 2:
            return findings

        # Group obligations by category for comparison
        by_category: dict[str, list[Obligation]] = {}
        for obl in obligations:
            cat = obl.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(obl)

        # Check for potential contradictions within same category
        # MVP: Simple keyword-based heuristic
        contradiction_keywords = [
            ("will live", "will die"),
            ("will succeed", "will fail"),
            ("will return", "will never return"),
            ("is alive", "is dead"),
            ("will win", "will lose"),
            ("is good", "is evil"),
            ("is true", "is false"),
        ]

        for category, obls in by_category.items():
            for i, obl1 in enumerate(obls):
                for obl2 in obls[i + 1:]:
                    for positive, negative in contradiction_keywords:
                        desc1_lower = obl1.description.lower()
                        desc2_lower = obl2.description.lower()

                        if (
                            (positive in desc1_lower and negative in desc2_lower) or
                            (negative in desc1_lower and positive in desc2_lower)
                        ):
                            findings.append(
                                Finding(
                                    finding_id=f"contradiction-{uuid4().hex[:8]}",
                                    severity=FindingSeverity.WARN,
                                    category="contradiction",
                                    message=(
                                        f"Potential contradiction between "
                                        f"'{obl1.obligation_id}' and '{obl2.obligation_id}': "
                                        f"'{obl1.description}' vs '{obl2.description}'"
                                    ),
                                    related_ids=[obl1.obligation_id, obl2.obligation_id],
                                )
                            )

        return findings

    def run_all_gates(
        self,
        passages: list[PassageRecord],
        anchors: list[EvidenceAnchor],
        entities: list[Entity],
        aliases: list[AliasEntry],
        obligations: list[Obligation],
    ) -> tuple[list[Finding], bool]:
        """Run all quality gates and return aggregated results.

        Runs:
        1. Referential integrity checks
        2. Evidence gate
        3. Contradiction detection

        Args:
            passages: List of passage records.
            anchors: List of evidence anchors.
            entities: List of entities.
            aliases: List of alias entries.
            obligations: List of obligations.

        Returns:
            Tuple of (all findings, passed: bool).
            passed is True only if no ERROR-level findings exist.
        """
        all_findings: list[Finding] = []

        # Run referential integrity checks
        integrity_findings = self.check_referential_integrity(
            passages=passages,
            anchors=anchors,
            entities=entities,
            aliases=aliases,
            obligations=obligations,
        )
        all_findings.extend(integrity_findings)

        # Run evidence gate
        evidence_findings = self.check_evidence_gate(obligations)
        all_findings.extend(evidence_findings)

        # Run contradiction detection (soft gate in MVP)
        contradiction_findings = self.detect_contradictions(obligations)
        all_findings.extend(contradiction_findings)

        # Determine pass/fail: ERROR findings fail the gate
        has_errors = any(f.severity == FindingSeverity.ERROR for f in all_findings)
        passed = not has_errors

        return all_findings, passed

    def validate(
        self,
        passages: list[PassageRecord],
        anchors: list[EvidenceAnchor],
        entities: list[Entity],
        aliases: list[AliasEntry],
        obligations: list[Obligation],
    ) -> tuple[bool, list[Finding]]:
        """Compatibility wrapper returning (passed, findings)."""
        findings, passed = self.run_all_gates(
            passages=passages,
            anchors=anchors,
            entities=entities,
            aliases=aliases,
            obligations=obligations,
        )
        return passed, findings
