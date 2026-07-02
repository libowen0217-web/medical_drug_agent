from __future__ import annotations

from medical_drug_agent.app.agents.base import BaseAgent
from medical_drug_agent.app.rules.engine import SafetyRuleEngine


class RuleCheckAgent(BaseAgent):
    agent_name = "rule-check-agent"

    def __init__(self, rule_engine: SafetyRuleEngine | None = None) -> None:
        self.rule_engine = rule_engine or SafetyRuleEngine()

    def _run_impl(self, state: dict) -> dict:
        return {
            "rule_matches": self.rule_engine.match_rules(
                current_drugs=list(state.get("normalized_current_drugs", []) or []),
                new_drug=state.get("normalized_new_drug"),
                patient=state.get("patient_info"),
            )
        }
