from __future__ import annotations

from medical_drug_agent.app.agents.base import BaseAgent
from medical_drug_agent.app.reporting.aggregator import RiskAggregator


class RiskAggregationAgent(BaseAgent):
    agent_name = "risk-aggregation-agent"

    def __init__(self, aggregator: RiskAggregator | None = None) -> None:
        self.aggregator = aggregator or RiskAggregator()

    def _run_impl(self, state: dict) -> dict:
        risk_summary = self.aggregator.aggregate(
            current_drugs=list(state.get("normalized_current_drugs", []) or []),
            new_drug=state.get("normalized_new_drug"),
            kg_pair_relations=list(state.get("kg_pair_relations", []) or []),
            rule_matches=list(state.get("rule_matches", []) or []),
            dose_results=list(state.get("dose_results", []) or []),
        )
        return {"risk_summary": risk_summary}
