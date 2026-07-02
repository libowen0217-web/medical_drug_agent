from __future__ import annotations

from typing import Any

from medical_drug_agent.app.graph.nodes import (
    aggregate_risk_node,
    build_response_node,
    dose_check_node,
    generate_report_node,
    normalize_drugs_node,
    query_kg_node,
    rule_check_node,
    safety_filter_node,
    validate_input_node,
)
from medical_drug_agent.app.graph.state import DrugSafetyGraphState

try:
    from langgraph.graph import END, START, StateGraph

    LANGGRAPH_AVAILABLE = True
except Exception:
    END = "__end__"
    START = "__start__"
    StateGraph = None
    LANGGRAPH_AVAILABLE = False


def _route_on_error(state: DrugSafetyGraphState) -> str:
    return "build_response" if state.get("error") else "next"


class DrugSafetyLangGraph:
    """Wrap the existing deterministic workflow as a LangGraph-style execution graph."""

    def __init__(self) -> None:
        self._app = self._build_app()

    def _build_app(self) -> Any:
        if not LANGGRAPH_AVAILABLE:
            return None

        graph = StateGraph(DrugSafetyGraphState)
        graph.add_node("validate_input", validate_input_node)
        graph.add_node("normalize_drugs", normalize_drugs_node)
        graph.add_node("query_kg", query_kg_node)
        graph.add_node("rule_check", rule_check_node)
        graph.add_node("dose_check", dose_check_node)
        graph.add_node("aggregate_risk", aggregate_risk_node)
        graph.add_node("generate_report", generate_report_node)
        graph.add_node("safety_filter", safety_filter_node)
        graph.add_node("build_response", build_response_node)

        graph.add_edge(START, "validate_input")
        graph.add_conditional_edges(
            "validate_input",
            _route_on_error,
            {"build_response": "build_response", "next": "normalize_drugs"},
        )
        graph.add_conditional_edges(
            "normalize_drugs",
            _route_on_error,
            {"build_response": "build_response", "next": "query_kg"},
        )
        graph.add_conditional_edges(
            "query_kg",
            _route_on_error,
            {"build_response": "build_response", "next": "rule_check"},
        )
        graph.add_conditional_edges(
            "rule_check",
            _route_on_error,
            {"build_response": "build_response", "next": "dose_check"},
        )
        graph.add_conditional_edges(
            "dose_check",
            _route_on_error,
            {"build_response": "build_response", "next": "aggregate_risk"},
        )
        graph.add_conditional_edges(
            "aggregate_risk",
            _route_on_error,
            {"build_response": "build_response", "next": "generate_report"},
        )
        graph.add_conditional_edges(
            "generate_report",
            _route_on_error,
            {"build_response": "build_response", "next": "safety_filter"},
        )
        graph.add_conditional_edges(
            "safety_filter",
            _route_on_error,
            {"build_response": "build_response", "next": "build_response"},
        )
        graph.add_edge("build_response", END)
        return graph.compile()

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        initial_state: DrugSafetyGraphState = {"input_payload": dict(payload or {}), "error": None}
        if self._app is not None:
            final_state = self._app.invoke(initial_state)
            return dict(final_state.get("response", {}) or {})

        state = initial_state
        for node in (
            validate_input_node,
            normalize_drugs_node,
            query_kg_node,
            rule_check_node,
            dose_check_node,
            aggregate_risk_node,
            generate_report_node,
            safety_filter_node,
            build_response_node,
        ):
            state = node(state)
            if node is not build_response_node and state.get("error"):
                continue
        return dict(state.get("response", {}) or {})
