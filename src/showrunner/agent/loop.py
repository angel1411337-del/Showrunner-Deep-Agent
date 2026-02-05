"""Deep-agent loop orchestration for V2 scaffolding."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Literal

from showrunner.contracts import Finding, FindingSeverity
from showrunner.gates.quality_gates import QualityGates
from showrunner.pipeline.orchestrator import ComponentFactory, PipelineConfig, ShowrunnerPipeline

if TYPE_CHECKING:
    from pathlib import Path

    from showrunner.providers.base import LLMProviderProtocol


@dataclass(frozen=True)
class LoopStep:
    name: str
    status: Literal["completed", "failed", "skipped"]
    started_at: datetime
    finished_at: datetime
    details: dict[str, Any]


@dataclass(frozen=True)
class AgentLoopResult:
    status: Literal["completed", "failed"]
    steps: list[LoopStep]
    findings: list[Finding]
    report_path: Path | None


class AgentLoop:
    """Minimal deep-agent loop scaffold (plan -> propose -> validate -> repair -> persist)."""

    def __init__(
        self,
        *,
        schema_dir: Path | None = None,
        environment_root: Path | None = None,
        provider: LLMProviderProtocol | None = None,
    ) -> None:
        self._schema_dir = schema_dir
        self._environment_root = environment_root
        self._provider = provider

    def run(self, *, input_source: Path, output_dir: Path) -> AgentLoopResult:
        env_root = self._environment_root
        if env_root is not None:
            self._assert_within_environment(env_root, input_source)
            self._assert_within_environment(env_root, output_dir)

        steps: list[LoopStep] = []
        findings: list[Finding] = []
        report_path: Path | None = None

        plan_start = datetime.now(tz=UTC)
        plan_details = {
            "tasks": [
                "run_pipeline",
                "validate_outputs",
                "persist_report",
            ],
            "input_source": str(input_source),
            "output_dir": str(output_dir),
        }
        steps.append(
            LoopStep(
                name="plan",
                status="completed",
                started_at=plan_start,
                finished_at=datetime.now(tz=UTC),
                details=plan_details,
            )
        )

        propose_start = datetime.now(tz=UTC)
        pipeline_state = None
        try:
            config = PipelineConfig(input_source=input_source, output_dir=output_dir)
            factory = ComponentFactory(config=config, provider=self._provider)
            pipeline_state, _manifest = ShowrunnerPipeline(
                config=config,
                factory=factory,
            ).run()
            propose_status: Literal["completed", "failed"] = (
                "failed" if pipeline_state.get("error") else "completed"
            )
            propose_details = {
                "error": pipeline_state.get("error"),
            }
        except Exception as exc:
            propose_status = "failed"
            propose_details = {"error": str(exc)}
        steps.append(
            LoopStep(
                name="propose",
                status=propose_status,
                started_at=propose_start,
                finished_at=datetime.now(tz=UTC),
                details=propose_details,
            )
        )

        validate_start = datetime.now(tz=UTC)
        validate_status: Literal["completed", "failed", "skipped"] = "completed"
        validate_details: dict[str, Any] = {}
        if pipeline_state is None or pipeline_state.get("error"):
            validate_status = "skipped"
            validate_details["reason"] = "pipeline_failed"
        else:
            gates = QualityGates(schema_dir=self._schema_dir)
            gate_findings, passed = gates.run_all_gates(
                passages=pipeline_state.get("passages", []),
                anchors=pipeline_state.get("evidence_anchors", []),
                entities=pipeline_state.get("entities", []),
                aliases=pipeline_state.get("aliases", []),
                obligations=pipeline_state.get("obligations", []),
            )
            findings.extend(gate_findings)
            validate_details = {
                "passed": passed,
                "finding_count": len(gate_findings),
            }
            if not passed:
                validate_status = "failed"
        steps.append(
            LoopStep(
                name="validate",
                status=validate_status,
                started_at=validate_start,
                finished_at=datetime.now(tz=UTC),
                details=validate_details,
            )
        )

        repair_start = datetime.now(tz=UTC)
        repair_status: Literal["completed", "failed", "skipped"] = "skipped"
        repair_details: dict[str, Any] = {"reason": "no_repair_strategy"}
        if any(f.severity == FindingSeverity.ERROR for f in findings):
            repair_status = "failed"
            repair_details = {"reason": "manual_intervention_required"}
        steps.append(
            LoopStep(
                name="repair",
                status=repair_status,
                started_at=repair_start,
                finished_at=datetime.now(tz=UTC),
                details=repair_details,
            )
        )

        persist_start = datetime.now(tz=UTC)
        report_path = self._write_report(
            output_dir=output_dir,
            steps=steps,
            findings=findings,
        )
        steps.append(
            LoopStep(
                name="persist",
                status="completed",
                started_at=persist_start,
                finished_at=datetime.now(tz=UTC),
                details={"report_path": str(report_path)},
            )
        )

        status: Literal["completed", "failed"] = "completed"
        if any(step.status == "failed" for step in steps):
            status = "failed"

        return AgentLoopResult(
            status=status,
            steps=steps,
            findings=findings,
            report_path=report_path,
        )

    def _write_report(
        self,
        *,
        output_dir: Path,
        steps: list[LoopStep],
        findings: list[Finding],
    ) -> Path:
        qa_dir = output_dir / "qa"
        qa_dir.mkdir(parents=True, exist_ok=True)
        report_path = qa_dir / "agent_loop.json"
        report = {
            "generated_at": datetime.now(tz=UTC).isoformat(),
            "status": "failed" if any(step.status == "failed" for step in steps) else "completed",
            "steps": [
                {
                    "name": step.name,
                    "status": step.status,
                    "started_at": step.started_at.isoformat(),
                    "finished_at": step.finished_at.isoformat(),
                    "details": step.details,
                }
                for step in steps
            ],
            "findings": [finding.model_dump() for finding in findings],
        }
        report_path.write_text(json_dumps(report), encoding="utf-8")
        return report_path

    def _assert_within_environment(self, env_root: Path, path: Path) -> None:
        resolved_root = env_root.resolve()
        resolved_path = path.resolve()
        try:
            resolved_path.relative_to(resolved_root)
        except ValueError as exc:
            raise ValueError(
                f"Path '{resolved_path}' is outside environment root '{resolved_root}'"
            ) from exc


def json_dumps(payload: dict[str, Any]) -> str:
    import json

    return json.dumps(payload, indent=2, default=str)
