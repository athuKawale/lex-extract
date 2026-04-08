from langgraph.graph import StateGraph, START, END
from src.nodes import (
    ingest_node,
    extract_node,
    validate_node,
    retry_node,
    output_node
)
from src.state import ExtractionState

workflow = StateGraph(ExtractionState)
workflow.add_node("ingest", ingest_node)
workflow.add_node("extract", extract_node)
workflow.add_node("validate", validate_node)
workflow.add_node("retry", retry_node)
workflow.add_node("output", output_node)

workflow.add_edge(START, "ingest")
workflow.add_edge("ingest", "extract")
workflow.add_edge("extract", "validate")
workflow.add_conditional_edges("validate", 
    lambda s: "retry" if s.get("fields_to_retry") and s.get("retry_count", 0) < 2 else "output")
workflow.add_edge("retry", "validate")
workflow.add_edge("output", END)

graph = workflow.compile()