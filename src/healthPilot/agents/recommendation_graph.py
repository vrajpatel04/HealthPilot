"""Recommendation LangGraph topology."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from healthPilot.agents.recommendation_nodes import (
    behavior_agent_node,
    evaluation_agent_node,
    load_context_node,
    memory_agent_node,
    persuasion_agent_node,
    recommendation_agent_node,
    retrieval_agent_node,
    store_recommendation_node,
)
from healthPilot.agents.recommendation_state import RecommendationState


def build_recommendation_graph():
    graph = StateGraph(RecommendationState)

    graph.add_node("load_context", load_context_node)
    graph.add_node("behavior_agent", behavior_agent_node)
    graph.add_node("memory_agent", memory_agent_node)
    graph.add_node("retrieval_agent", retrieval_agent_node)
    graph.add_node("evaluation_agent", evaluation_agent_node)
    graph.add_node("recommendation_agent", recommendation_agent_node)
    graph.add_node("persuasion_agent", persuasion_agent_node)
    graph.add_node("store_recommendation", store_recommendation_node)

    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "behavior_agent")
    graph.add_edge("behavior_agent", "memory_agent")
    graph.add_edge("memory_agent", "retrieval_agent")
    graph.add_edge("retrieval_agent", "evaluation_agent")
    graph.add_edge("evaluation_agent", "recommendation_agent")
    graph.add_edge("recommendation_agent", "persuasion_agent")
    graph.add_edge("persuasion_agent", "store_recommendation")
    graph.add_edge("store_recommendation", END)

    return graph.compile()


recommendation_graph = build_recommendation_graph()
