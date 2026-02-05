"""Deepagents runtime integration using the deepagents library."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from showrunner.agent import tools
from showrunner.agent.harness import AgentRunResult
from showrunner.agent.loop import AgentLoop, AgentLoopResult
from showrunner.rlm.memory_store import MemoryStore
from showrunner.rlm.rlm_runner import RLMRunner

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel

    from showrunner.agent.harness import AgentRunResult
    from showrunner.graph.queries import Neo4jQueryLayer, Neo4jSessionProtocol
    from showrunner.rlm.repl_executor import RLMRunResult
    from langgraph.graph.state import CompiledStateGraph


class DeepagentsRuntime:
    """Scaffolded deepagents runtime that delegates to pipeline tools for now."""

    def __init__(
        self,
        *,
        graph_session: Neo4jSessionProtocol | None = None,
        query_layer: Neo4jQueryLayer | None = None,
        memory_store: MemoryStore | None = None,
        loop: AgentLoop | None = None,
        environment_root: Path | None = None,
        model: str | BaseChatModel | None = None,
        system_prompt: str | None = None,
    ) -> None:
        self._available = _deepagents_available()
        self._graph_session = graph_session
        self._query_layer = query_layer
        self._memory_store = memory_store or MemoryStore()
        self._loop = loop or AgentLoop(environment_root=environment_root)
        self._environment_root = environment_root
        self._model = model or os.getenv("SHOWRUNNER_LLM_MODEL")
        self._system_prompt = system_prompt
        self._agent: CompiledStateGraph | None = None
        self._rlm_runner = RLMRunner(
            tools=self._build_tools(),
            memory_store=self._memory_store,
        )

    @property
    def available(self) -> bool:
        return self._available

    def run(self, *, input_source: Path, output_dir: Path) -> AgentRunResult:
        if not self._available or self._model is None:
            return tools.run_pipeline(input_source=input_source, output_dir=output_dir)
        if self._environment_root is None:
            raise RuntimeError("Deepagents runtime requires environment_root to be set")

        self._assert_within_environment(self._environment_root, input_source)
        self._assert_within_environment(self._environment_root, output_dir)

        agent = self._agent or self._build_agent()
        prompt = self._build_run_prompt(input_source=input_source, output_dir=output_dir)
        agent.invoke({"messages": [{"role": "user", "content": prompt}]})
        return self._result_from_output_dir(output_dir)

    def run_loop(self, *, input_source: Path, output_dir: Path) -> AgentLoopResult:
        return self._loop.run(input_source=input_source, output_dir=output_dir)

    def list_artifacts(self, *, output_dir: Path) -> list[str]:
        return tools.list_artifacts(output_dir=output_dir)

    def read_artifact(self, *, output_dir: Path, relative_path: str) -> str:
        return tools.read_artifact(output_dir=output_dir, relative_path=relative_path)

    def query_graph(
        self, *, query: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        if self._graph_session is None:
            raise RuntimeError("Graph session is not configured for deepagents runtime")
        return tools.query_graph(
            query=query,
            parameters=parameters,
            session=self._graph_session,
            query_layer=self._query_layer,
        )

    def run_repl_program(self, *, prompt: str, code: str) -> RLMRunResult:
        return self._rlm_runner.run_program(prompt=prompt, code=code)

    def _build_tools(self) -> dict[str, Any]:
        return {
            "run_pipeline": tools.run_pipeline,
            "list_artifacts": tools.list_artifacts,
            "read_artifact": tools.read_artifact,
            "query_graph": self.query_graph,
        }

    def _build_agent(self) -> CompiledStateGraph:
        if self._environment_root is None:
            raise RuntimeError("Deepagents runtime requires environment_root to be set")
        if self._model is None:
            raise RuntimeError("Deepagents runtime requires SHOWRUNNER_LLM_MODEL or model")

        from deepagents import create_deep_agent
        from deepagents.backends import FilesystemBackend

        backend = FilesystemBackend(
            root_dir=self._environment_root,
            virtual_mode=True,
        )
        system_prompt = self._system_prompt or _default_system_prompt()
        self._agent = create_deep_agent(
            model=self._model,
            tools=[
                self._tool_run_pipeline,
                self._tool_list_artifacts,
                self._tool_read_artifact,
                self._tool_query_graph,
            ],
            system_prompt=system_prompt,
            backend=backend,
        )
        return self._agent

    def _build_run_prompt(self, *, input_source: Path, output_dir: Path) -> str:
        return (
            "Run the Showrunner pipeline for the provided input and output paths. "
            "Then list the artifacts and confirm completion.\n\n"
            f"input_source: {input_source}\n"
            f"output_dir: {output_dir}\n"
        )

    def _result_from_output_dir(self, output_dir: Path) -> AgentRunResult:
        run_manifest = output_dir / "run_manifest.json"
        export_dir = output_dir / "exports"
        export_paths = sorted(path for path in export_dir.glob("*") if path.is_file())
        if not run_manifest.exists():
            return AgentRunResult(
                status="failed",
                error="run_manifest.json not found after deepagents run",
                output_dir=output_dir,
                run_manifest_path=run_manifest,
                export_paths=export_paths,
            )
        return AgentRunResult(
            status="completed",
            error=None,
            output_dir=output_dir,
            run_manifest_path=run_manifest,
            export_paths=export_paths,
        )

    def _tool_run_pipeline(self, input_source: str, output_dir: str) -> dict[str, Any]:
        input_path = Path(input_source)
        output_path = Path(output_dir)
        if self._environment_root is not None:
            self._assert_within_environment(self._environment_root, input_path)
            self._assert_within_environment(self._environment_root, output_path)
        result = tools.run_pipeline(input_source=input_path, output_dir=output_path)
        return {
            "status": result.status,
            "error": result.error,
            "output_dir": str(result.output_dir),
            "run_manifest_path": str(result.run_manifest_path),
            "export_paths": [str(path) for path in result.export_paths],
        }

    def _tool_list_artifacts(self, output_dir: str) -> list[str]:
        output_path = Path(output_dir)
        if self._environment_root is not None:
            self._assert_within_environment(self._environment_root, output_path)
        return tools.list_artifacts(output_dir=output_path)

    def _tool_read_artifact(self, output_dir: str, relative_path: str) -> str:
        output_path = Path(output_dir)
        if self._environment_root is not None:
            self._assert_within_environment(self._environment_root, output_path)
        return tools.read_artifact(output_dir=output_path, relative_path=relative_path)

    def _tool_query_graph(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return self.query_graph(query=query, parameters=parameters)

    def _assert_within_environment(self, env_root: Path, path: Path) -> None:
        resolved_root = env_root.resolve()
        resolved_path = path.resolve()
        try:
            resolved_path.relative_to(resolved_root)
        except ValueError as exc:
            raise ValueError(
                f"Path '{resolved_path}' is outside environment root '{resolved_root}'"
            ) from exc


def _deepagents_available() -> bool:
    import importlib.util

    return importlib.util.find_spec("deepagents") is not None


def _default_system_prompt() -> str:
    return (
        "You are the Showrunner deep agent. Your job is to orchestrate the pipeline "
        "using the provided tools, validate outputs, and report completion. "
        "Do not access files outside the configured environment root."
    )
