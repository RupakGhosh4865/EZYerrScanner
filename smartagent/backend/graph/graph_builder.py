"""
SmartAgent LangGraph Pipeline Builder
"""
from langgraph.graph import StateGraph, END, START

from graph.state import GraphState
from graph.nodes import (
    load_sheet_node,
    schema_node,
    supervisor_node,
    duplicate_node,
    quality_node,
    logic_node,
    stale_node,
    aggregate_node,
    synthesizer_node,
)


def build_smartagent_graph():
    workflow = StateGraph(GraphState)

    # Register all nodes
    workflow.add_node("load_sheet",          load_sheet_node)
    workflow.add_node("schema_intelligence", schema_node)
    workflow.add_node("supervisor",          supervisor_node)
    workflow.add_node("duplicate_hunter",    duplicate_node)
    workflow.add_node("quality_auditor",     quality_node)
    workflow.add_node("logic_validator",     logic_node)
    workflow.add_node("stale_detector",      stale_node)
    workflow.add_node("aggregator",          aggregate_node)
    workflow.add_node("synthesizer",         synthesizer_node)

    # Main pipeline edges
    workflow.add_edge(START,                "load_sheet")
    workflow.add_edge("load_sheet",         "schema_intelligence")
    workflow.add_edge("schema_intelligence", "supervisor")

    # Sequential specialist agents (avoids concurrent write conflicts)
    workflow.add_edge("supervisor",       "duplicate_hunter")
    workflow.add_edge("duplicate_hunter", "quality_auditor")
    workflow.add_edge("quality_auditor",  "logic_validator")
    workflow.add_edge("logic_validator",  "stale_detector")
    workflow.add_edge("stale_detector",   "aggregator")

    workflow.add_edge("aggregator",  "synthesizer")
    workflow.add_edge("synthesizer", END)

    # NOTE: execute_actions_node is called SEPARATELY via /api/actions/execute
    # It is NOT part of this graph — it runs after human approval.
    return workflow.compile()


# Singleton — imported by FastAPI routers
smartagent_graph = build_smartagent_graph()
