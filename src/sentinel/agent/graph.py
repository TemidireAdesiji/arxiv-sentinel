"""Minimal directed-graph executor for agent workflows.

Replaces LangGraph with ~60 lines of plain Python.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import structlog

log = structlog.get_logger(__name__)

END = "__end__"

NodeFn = Callable[..., Awaitable[Any]]
RouterFn = Callable[[Any], str]


class WorkflowGraph:
    """Async state-machine that runs named node functions.

    Edges can be static (always go to node *X*) or
    conditional (call a router function that returns the
    next node name based on current state).
    """

    def __init__(self) -> None:
        self._nodes: dict[str, NodeFn] = {}
        self._edges: dict[str, str | RouterFn] = {}

    def add_node(self, name: str, fn: NodeFn) -> None:
        self._nodes[name] = fn

    def add_edge(self, src: str, dst: str) -> None:
        """Static transition: *src* always goes to *dst*."""
        self._edges[src] = dst

    def add_conditional_edge(
        self,
        src: str,
        router: RouterFn,
    ) -> None:
        """Dynamic transition driven by *router(state)*."""
        self._edges[src] = router

    async def execute(
        self,
        entry: str,
        state: Any,
        ctx: Any,
    ) -> Any:
        """Run the graph starting from *entry* node.

        Stops when the current node resolves to ``END``.
        """
        current = entry
        while current != END:
            fn = self._nodes.get(current)
            if fn is None:
                raise ValueError(f"Unknown node: {current!r}")
            log.debug("node_enter", node=current)
            state = await fn(state, ctx)
            edge = self._edges.get(current)
            if edge is None:
                raise ValueError(f"No edge from node: {current!r}")
            if callable(edge):
                current = edge(state)
            else:
                current = edge
            log.debug(
                "node_exit",
                node=current,
            )
        return state
