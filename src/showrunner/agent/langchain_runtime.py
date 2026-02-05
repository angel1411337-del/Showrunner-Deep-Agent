"""LangChain-backed runtime adapter using safe tool wrappers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from showrunner.agent import tools

if TYPE_CHECKING:
    from pathlib import Path

    from langchain_core.runnables import RunnableLambda

    from showrunner.agent.harness import AgentRunResult
    from showrunner.graph.queries import Neo4jQueryLayer, Neo4jSessionProtocol


class LangChainRuntime:
    """LangChain runtime wrapper that delegates to safe tool wrappers."""

    def __init__(
        self,
        *,
        graph_session: Neo4jSessionProtocol | None = None,
        query_layer: Neo4jQueryLayer | None = None,
    ) -> None:
        self._graph_session = graph_session
        self._query_layer = query_layer
        self._runner: RunnableLambda[dict[str, Path], AgentRunResult] = self._build_runner()

    def _build_runner(self) -> RunnableLambda[dict[str, Path], AgentRunResult]:
        from langchain_core.runnables import RunnableLambda

        def _run(payload: dict[str, Path]) -> AgentRunResult:
            return tools.run_pipeline(
                input_source=payload["input_source"],
                output_dir=payload["output_dir"],
            )

        return RunnableLambda(_run)

    def run(self, *, input_source: Path, output_dir: Path) -> AgentRunResult:
        return self._runner.invoke({"input_source": input_source, "output_dir": output_dir})

    def list_artifacts(self, *, output_dir: Path) -> list[str]:
        return tools.list_artifacts(output_dir=output_dir)

    def read_artifact(self, *, output_dir: Path, relative_path: str) -> str:
        return tools.read_artifact(output_dir=output_dir, relative_path=relative_path)

    def query_graph(
        self, *, query: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        if self._graph_session is None:
            raise RuntimeError("Graph session is not configured for LangChain runtime")
        return tools.query_graph(
            query=query,
            parameters=parameters,
            session=self._graph_session,
            query_layer=self._query_layer,
        )
