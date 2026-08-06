"""LangGraph coaching graph with Presidio → NeMo → LLM privacy pipeline."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from healthPilot.agents.nodes import (
    guardrail_input_node,
    guardrail_output_node,
    llm_call_node,
    presidio_deanonymize_node,
    presidio_deidentify_node,
    route_on_error,
)
from healthPilot.agents.state import CoachState


def _error_node(state: CoachState) -> dict:
    return {"messages": []}


def build_coach_graph():
    """
    Graph topology:
      START → presidio_deidentify → guardrail_input → llm_call
            → guardrail_output → presidio_deanonymize → END
    """
    graph = StateGraph(CoachState)

    graph.add_node("presidio_deidentify", presidio_deidentify_node)
    graph.add_node("guardrail_input", guardrail_input_node)
    graph.add_node("llm_call", llm_call_node)
    graph.add_node("guardrail_output", guardrail_output_node)
    graph.add_node("presidio_deanonymize", presidio_deanonymize_node)
    graph.add_node("error", _error_node)

    graph.add_edge(START, "presidio_deidentify")
    graph.add_conditional_edges(
        "presidio_deidentify",
        route_on_error,
        {"error": "error", "continue": "guardrail_input"},
    )
    graph.add_conditional_edges(
        "guardrail_input",
        route_on_error,
        {"error": "error", "continue": "llm_call"},
    )
    graph.add_edge("llm_call", "guardrail_output")
    graph.add_conditional_edges(
        "guardrail_output",
        route_on_error,
        {"error": "error", "continue": "presidio_deanonymize"},
    )
    graph.add_edge("presidio_deanonymize", END)
    graph.add_edge("error", END)

    return graph.compile()


coach_graph = build_coach_graph()
