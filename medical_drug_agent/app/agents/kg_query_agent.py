from __future__ import annotations

from medical_drug_agent.app.agents.base import BaseAgent
from medical_drug_agent.app.knowledge.knowledge_router import KnowledgeBackendRouter


class KGQueryAgent(BaseAgent):
    agent_name = "kg-query-agent"

    def __init__(self, knowledge_backend: str | None = None, router: KnowledgeBackendRouter | None = None) -> None:
        self.router = router or KnowledgeBackendRouter(backend=knowledge_backend)

    def _run_impl(self, state: dict) -> dict:
        normalized_current = list(state.get("normalized_current_drugs", []) or [])
        normalized_new = state.get("normalized_new_drug")
        if normalized_new is None:
            raise ValueError("normalized_new_drug 缺失")

        pair_relations = []
        for current_drug in normalized_current:
            pair_relations.extend(
                self.router.query_pair_relations(current_drug.en_name, normalized_new.en_name)
            )

        new_drug_summary = self.router.query_drug_summary(normalized_new.en_name)
        backend_metadata = self.router.get_last_metadata()
        new_drug_summary.total_count = (
            len(new_drug_summary.drug_drug_relations)
            + len(new_drug_summary.drug_disease_relations)
            + len(new_drug_summary.drug_effect_relations)
        )
        kg_query_summary = {
            "pair_relation_count": len(pair_relations),
            "drug_drug_count": len(new_drug_summary.drug_drug_relations),
            "drug_disease_count": len(new_drug_summary.drug_disease_relations),
            "drug_effect_count": len(new_drug_summary.drug_effect_relations),
            "total_count": new_drug_summary.total_count,
            **backend_metadata,
        }
        return {
            "kg_pair_relations": pair_relations,
            "kg_query_summary": kg_query_summary,
            "kg_backend_metadata": backend_metadata,
        }
