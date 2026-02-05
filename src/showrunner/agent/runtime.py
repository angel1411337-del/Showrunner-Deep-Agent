"""Runtime facade over pipeline, LangChain, and deepagents modes."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from showrunner.agent.deepagents_runtime import DeepagentsRuntime
from showrunner.agent.harness import AgentHarness, AgentRunResult, runtime_capabilities
from showrunner.agent.langchain_runtime import LangChainRuntime

if TYPE_CHECKING:
    from pathlib import Path


class RuntimeMode(str, Enum):
    PIPELINE = "pipeline"
    LANGCHAIN = "langchain"
    DEEPAGENTS = "deepagents"


def parse_runtime_mode(value: str | RuntimeMode) -> RuntimeMode:
    if isinstance(value, RuntimeMode):
        return value
    try:
        return RuntimeMode(value)
    except ValueError as exc:
        raise ValueError(f"Unsupported runtime mode: {value}") from exc


class AgentRuntime:
    """Facade that routes runtime calls by mode."""

    def __init__(
        self,
        mode: RuntimeMode | str = RuntimeMode.PIPELINE,
        harness: AgentHarness | None = None,
        langchain_runtime: LangChainRuntime | None = None,
        deepagents_runtime: DeepagentsRuntime | None = None,
    ) -> None:
        self._mode = parse_runtime_mode(mode)
        self._harness = harness or AgentHarness()
        self._langchain = langchain_runtime or LangChainRuntime()
        self._deepagents = deepagents_runtime or DeepagentsRuntime()

    @property
    def mode(self) -> RuntimeMode:
        return self._mode

    def run(self, *, input_source: Path, output_dir: Path) -> AgentRunResult:
        if self._mode is RuntimeMode.PIPELINE:
            return self._harness.run_pipeline(input_source=input_source, output_dir=output_dir)
        if self._mode is RuntimeMode.LANGCHAIN:
            return self._langchain.run(input_source=input_source, output_dir=output_dir)
        if self._mode is RuntimeMode.DEEPAGENTS:
            return self._deepagents.run(input_source=input_source, output_dir=output_dir)
        raise NotImplementedError(f"{self._mode.value} runtime is not integrated yet")

    def list_artifacts(self, *, output_dir: Path) -> list[str]:
        if self._mode is RuntimeMode.LANGCHAIN:
            return self._langchain.list_artifacts(output_dir=output_dir)
        if self._mode is RuntimeMode.DEEPAGENTS:
            return self._deepagents.list_artifacts(output_dir=output_dir)
        return self._harness.list_artifacts(output_dir=output_dir)

    def read_artifact(self, *, output_dir: Path, relative_path: str) -> str:
        if self._mode is RuntimeMode.LANGCHAIN:
            return self._langchain.read_artifact(output_dir=output_dir, relative_path=relative_path)
        if self._mode is RuntimeMode.DEEPAGENTS:
            return self._deepagents.read_artifact(
                output_dir=output_dir, relative_path=relative_path
            )
        return self._harness.read_artifact(output_dir=output_dir, relative_path=relative_path)

    def capabilities(self) -> dict[str, bool]:
        return runtime_capabilities()
