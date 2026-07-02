from __future__ import annotations

from medical_drug_agent.app.agents.base import BaseAgent
from medical_drug_agent.app.evidence.retriever import EvidenceRetriever


class EvidenceAgent(BaseAgent):
    agent_name = "evidence-agent"

    def __init__(self, retriever: EvidenceRetriever | None = None) -> None:
        self.retriever = retriever or EvidenceRetriever()

    def _run_impl(self, state: dict) -> dict:
        evidence_items = []
        for rule_match in list(state.get("rule_matches", []) or []):
            evidence_items.extend(self.retriever.retrieve_for_rule_match(rule_match))
        for dose_result in list(state.get("dose_results", []) or []):
            evidence_items.extend(self.retriever.retrieve_for_dose_result(dose_result))
        return {
            "evidence_summary": {
                "evidence_item_count": len(evidence_items),
            },
            "evidence_items": evidence_items,
        }
