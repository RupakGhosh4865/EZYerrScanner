from langgraph.graph import StateGraph, END, START
from graph_ezyerr.state import GraphState
from graph_ezyerr.nodes import (
    parse_file_node, schema_node, supervisor_node,
    duplicate_node, quality_node, logic_node,
    anomaly_node, stale_node, aggregate_node, synthesizer_node
)

def build_graph():
    workflow = StateGraph(GraphState)
    
    # Add all nodes
    workflow.add_node("parse_file", parse_file_node)
    workflow.add_node("schema_intelligence", schema_node)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("duplicate_hunter", duplicate_node)
    workflow.add_node("data_quality", quality_node)
    workflow.add_node("business_logic", logic_node)
    workflow.add_node("anomaly_detector", anomaly_node)
    workflow.add_node("stale_records", stale_node)
    workflow.add_node("aggregator", aggregate_node)
    workflow.add_node("synthesizer", synthesizer_node)
    
    # Linear flow
    workflow.add_edge(START, "parse_file")
    workflow.add_edge("parse_file", "schema_intelligence")
    workflow.add_edge("schema_intelligence", "supervisor")
    
    # Fan-out
    workflow.add_edge("supervisor", "duplicate_hunter")
    workflow.add_edge("supervisor", "data_quality")
    workflow.add_edge("supervisor", "business_logic")
    workflow.add_edge("supervisor", "anomaly_detector")
    workflow.add_edge("supervisor", "stale_records")
    
    # Fan-in
    workflow.add_edge("duplicate_hunter", "aggregator")
    workflow.add_edge("data_quality", "aggregator")
    workflow.add_edge("business_logic", "aggregator")
    workflow.add_edge("anomaly_detector", "aggregator")
    workflow.add_edge("stale_records", "aggregator")
    
    # Final
    workflow.add_edge("aggregator", "synthesizer")
    workflow.add_edge("synthesizer", END)
    
    return workflow.compile()

ezyerr_graph = build_graph()
