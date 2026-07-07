from __future__ import annotations

from medical_drug_agent.app.agents.base import BaseAgent
from medical_drug_agent.app.rag.context import retrieve_drug_safety_evidences


class RAGEvidenceAgent(BaseAgent):
    agent_name = "rag-evidence-agent"

    def _run_impl(self, state: dict) -> dict:
        payload = dict(state.get("input_payload", {}) or {})
        evidences = retrieve_drug_safety_evidences(payload=payload, state=state, top_k=5)
        return {"rag_evidences": evidences}
