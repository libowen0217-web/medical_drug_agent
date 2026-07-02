from __future__ import annotations

from medical_drug_agent.app.symptom.rule_store import SymptomRuleStore
from medical_drug_agent.app.symptom.schemas import OTCCandidate, ParsedSymptom


class OTCCandidateFinder:
    def __init__(self, rule_store: SymptomRuleStore | None = None) -> None:
        self.rule_store = rule_store or SymptomRuleStore()

    def find_candidates(
        self,
        symptom_text: str,
        parsed_symptoms: list[ParsedSymptom],
        diseases: list[str] | None = None,
        patient_factors: list[str] | None = None,
        allergies: list[str] | None = None,
    ) -> list[OTCCandidate]:
        text = str(symptom_text or "").strip().lower()
        disease_list = [str(item).strip() for item in list(diseases or []) if str(item).strip()]
        factor_list = [str(item).strip() for item in list(patient_factors or []) if str(item).strip()]
        allergy_list = [str(item).strip() for item in list(allergies or []) if str(item).strip()]
        matched_symptoms = {item.symptom_name for item in parsed_symptoms}

        results: list[OTCCandidate] = []
        seen: set[str] = set()
        for row in self.rule_store.load_otc_candidate_rules():
            if str(row.get("is_otc", "")).lower() != "true":
                continue
            keywords = list(row.get("keywords", []) or [])
            if not any(keyword.lower() in text for keyword in keywords):
                if not self._match_by_parsed_symptoms(keywords, matched_symptoms):
                    continue

            candidate_id = str(row.get("candidate_id", ""))
            if candidate_id in seen:
                continue
            seen.add(candidate_id)
            caution_parts = [str(row.get("caution", ""))]
            candidate_drugs = list(row.get("candidate_drugs", []) or [])
            caution_parts.extend(self._disease_cautions(candidate_drugs, disease_list))
            caution_parts.extend(self._allergy_cautions(candidate_drugs, allergy_list))
            caution_parts.extend(self._factor_cautions(candidate_drugs, factor_list))

            results.append(
                OTCCandidate(
                    candidate_id=candidate_id,
                    symptom_group=str(row.get("symptom_group", "")),
                    drug_class=str(row.get("drug_class", "")),
                    candidate_drugs=candidate_drugs,
                    is_otc=True,
                    requires_doctor_confirmation=str(row.get("requires_doctor_confirmation", "")).lower() == "true",
                    caution="；".join(part for part in caution_parts if part),
                    reason=str(row.get("reason", "")),
                )
            )
        return results

    @staticmethod
    def _match_by_parsed_symptoms(keywords: list[str], matched_symptoms: set[str]) -> bool:
        symptom_text = " ".join(matched_symptoms).lower()
        return any(keyword.lower() in symptom_text for keyword in keywords)

    @staticmethod
    def _disease_cautions(candidate_drugs: list[str], diseases: list[str]) -> list[str]:
        cautions: list[str] = []
        if "布洛芬" in candidate_drugs and "高血压" in diseases:
            cautions.append("合并高血压时，布洛芬使用需谨慎。")
        if "布洛芬" in candidate_drugs and "胃溃疡" in diseases:
            cautions.append("合并胃溃疡时，布洛芬使用需谨慎。")
        if "对乙酰氨基酚" in candidate_drugs and "肝功能异常" in diseases:
            cautions.append("合并肝功能异常时，对乙酰氨基酚使用需谨慎。")
        if "布洛芬" in candidate_drugs and "肾功能不全" in diseases:
            cautions.append("合并肾功能不全时，布洛芬使用需谨慎。")
        return cautions

    @staticmethod
    def _allergy_cautions(candidate_drugs: list[str], allergies: list[str]) -> list[str]:
        cautions: list[str] = []
        for drug in candidate_drugs:
            if any(drug in allergy or allergy in drug for allergy in allergies):
                cautions.append(f"过敏史中提到 {drug}，需谨慎。")
        return cautions

    @staticmethod
    def _factor_cautions(candidate_drugs: list[str], patient_factors: list[str]) -> list[str]:
        cautions: list[str] = []
        if any(factor in {"老年人", "高龄"} for factor in patient_factors) and "布洛芬" in candidate_drugs:
            cautions.append("老年人使用布洛芬需谨慎。")
        if any(factor in {"驾驶", "需要驾驶"} for factor in patient_factors) and (
            "氯雷他定" in candidate_drugs or "西替利嗪" in candidate_drugs
        ):
            cautions.append("涉及驾驶时，抗过敏类药物可能影响警觉性，需谨慎。")
        return cautions

