from __future__ import annotations

from medical_drug_agent.app.agents.base import AgentResult, BaseAgent
from medical_drug_agent.app.symptom.otc_candidate_finder import OTCCandidateFinder
from medical_drug_agent.app.symptom.schemas import OTCCandidate


class OTCCandidateAgent(BaseAgent):
    agent_name = "otc-candidate-agent"

    def __init__(self, finder: OTCCandidateFinder | None = None) -> None:
        self.finder = finder or OTCCandidateFinder()

    def run(self, state: dict) -> AgentResult:
        if bool(state.get("stop_candidate_recommendation")):
            return AgentResult(agent_name=self.agent_name, status="skipped", output={"otc_candidates": []})
        return super().run(state)

    def _run_impl(self, state: dict) -> dict:
        payload = dict(state.get("input_payload", {}) or {})
        disease_candidates = list(state.get("disease_candidates", []) or [])
        candidates_from_diseases = self._build_candidates_from_disease_library(disease_candidates)
        if candidates_from_diseases:
            return {"otc_candidates": candidates_from_diseases}

        return {
            "otc_candidates": self.finder.find_candidates(
                symptom_text=str(payload.get("symptom_text", "") or ""),
                parsed_symptoms=list(state.get("parsed_symptoms", []) or []),
                diseases=list(payload.get("diseases", []) or []),
                patient_factors=list(payload.get("patient_factors", []) or []),
                allergies=list(payload.get("allergies", []) or []),
            )
        }

    @staticmethod
    def _build_candidates_from_disease_library(disease_candidates: list[object]) -> list[OTCCandidate]:
        candidates: list[OTCCandidate] = []
        seen_drugs: set[str] = set()

        for disease in disease_candidates:
            scope = str(getattr(disease, "scope", "") or "")
            if scope not in {"otc_allowed", "otc_caution"}:
                continue

            candidate_drugs = [
                str(drug).strip()
                for drug in list(getattr(disease, "candidate_drugs", []) or [])
                if str(drug).strip()
            ]
            unique_drugs = [drug for drug in candidate_drugs if drug not in seen_drugs]
            if not unique_drugs:
                continue

            seen_drugs.update(unique_drugs)
            disease_name = str(getattr(disease, "disease_name_cn", "") or "")
            disease_id = str(getattr(disease, "disease_id", "") or "")
            drug_classes = list(getattr(disease, "candidate_drug_classes", []) or [])
            advice = str(getattr(disease, "advice", "") or "")
            caution_parts = [advice]
            if scope == "otc_caution":
                caution_parts.insert(0, "该常见疾病候选需要谨慎评估。")

            candidates.append(
                OTCCandidate(
                    candidate_id=f"disease-{disease_id}",
                    symptom_group=disease_name,
                    drug_class="；".join(str(item) for item in drug_classes if str(item).strip())
                    or "OTC 候选药",
                    candidate_drugs=unique_drugs,
                    is_otc=True,
                    requires_doctor_confirmation=scope == "otc_caution",
                    caution="；".join(part for part in caution_parts if part),
                    reason=f"来源于常见疾病候选：{disease_name}。仅用于问诊辅助，不构成诊断。",
                    source="disease_library",
                    source_disease=disease_name,
                    source_disease_id=disease_id,
                )
            )

        return candidates
