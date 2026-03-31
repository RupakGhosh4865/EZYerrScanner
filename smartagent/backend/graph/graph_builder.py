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
    anomaly_node,
    aggregate_node,
    synthesizer_node,
)


def build_smartagent_graph():
    workflow = StateGraph(GraphState)

    # Register all nodes
    workflow.add_node("sheet_loader",          load_sheet_node)
    workflow.add_node("schema_intelligence", schema_node)
    workflow.add_node("supervisor",          supervisor_node)
    workflow.add_node("duplicate_hunter",    duplicate_node)
    workflow.add_node("data_quality",        quality_node)
    workflow.add_node("business_logic",      logic_node)
    workflow.add_node("stale_records",       stale_node)
    workflow.add_node("anomaly_detector",    anomaly_node)
    workflow.add_node("aggregator",          aggregate_node)
    workflow.add_node("synthesizer",         synthesizer_node)

    # Main pipeline edges
    workflow.add_edge(START,                "sheet_loader")
    workflow.add_edge("sheet_loader",       "schema_intelligence")
    workflow.add_edge("schema_intelligence", "supervisor")

    # Sequential specialist agents (avoids concurrent write conflicts)
    workflow.add_edge("supervisor",       "duplicate_hunter")
    workflow.add_edge("duplicate_hunter", "data_quality")
    workflow.add_edge("data_quality",     "business_logic")
    workflow.add_edge("business_logic",   "stale_records")
    workflow.add_edge("stale_records",    "anomaly_detector")
    workflow.add_edge("anomaly_detector", "aggregator")

    workflow.add_edge("aggregator",  "synthesizer")
    workflow.add_edge("synthesizer", END)

    # NOTE: execute_actions_node is called SEPARATELY via /api/actions/execute
    # It is NOT part of this graph — it runs after human approval.
    return workflow.compile()


# Singleton — imported by FastAPI routers
smartagent_graph = build_smartagent_graph()
