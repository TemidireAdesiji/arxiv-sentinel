"""Tests for sentinel.agent.graph — workflow execution."""

from __future__ import annotations

import pytest

from sentinel.agent.graph import END, WorkflowGraph


class TestWorkflowGraph:
    async def test_static_edge_linear_flow(self):
        log: list[str] = []

        async def node_a(state, ctx):
            log.append("a")
            return state

        async def node_b(state, ctx):
            log.append("b")
            return state

        g = WorkflowGraph()
        g.add_node("a", node_a)
        g.add_node("b", node_b)
        g.add_edge("a", "b")
        g.add_edge("b", END)

        await g.execute("a", {}, None)
        assert log == ["a", "b"]

    async def test_conditional_edge_routing(self):
        async def node_check(state, ctx):
            return state

        async def node_yes(state, ctx):
            state["went"] = "yes"
            return state

        async def node_no(state, ctx):
            state["went"] = "no"
            return state

        def router(state):
            return "yes" if state.get("flag") else "no"

        g = WorkflowGraph()
        g.add_node("check", node_check)
        g.add_node("yes", node_yes)
        g.add_node("no", node_no)
        g.add_conditional_edge("check", router)
        g.add_edge("yes", END)
        g.add_edge("no", END)

        result = await g.execute("check", {"flag": True}, None)
        assert result["went"] == "yes"

        result = await g.execute("check", {"flag": False}, None)
        assert result["went"] == "no"

    async def test_unknown_node_raises(self):
        g = WorkflowGraph()
        with pytest.raises(ValueError, match="Unknown"):
            await g.execute("missing", {}, None)

    async def test_missing_edge_raises(self):
        async def noop(state, ctx):
            return state

        g = WorkflowGraph()
        g.add_node("a", noop)
        with pytest.raises(ValueError, match="No edge"):
            await g.execute("a", {}, None)
