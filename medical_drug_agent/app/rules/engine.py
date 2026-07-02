from __future__ import annotations

import pandas as pd

from medical_drug_agent.app.constants import PHARMACY_RULES_PATH
from medical_drug_agent.app.schemas import DrugInfo, PatientInfo, RuleMatch


class SafetyRuleEngine:
    """Deterministic safety rule matcher based on local CSV rules."""

    def __init__(self, rules_path=PHARMACY_RULES_PATH) -> None:
        self.rules_path = rules_path
        self._rules_df: pd.DataFrame | None = None

    @staticmethod
    def _normalize_text(value: str) -> str:
        return value.strip().lower()

    @staticmethod
    def _split_classes(drug_class: str) -> list[str]:
        return [part.strip() for part in str(drug_class).split("/") if part.strip()]

    def _get_rules(self) -> pd.DataFrame:
        if self._rules_df is None:
            if not self.rules_path.exists():
                raise FileNotFoundError(f"安全规则表不存在：{self.rules_path}")
            self._rules_df = pd.read_csv(self.rules_path).fillna("")
        return self._rules_df

    def _normalize_patient(self, patient: PatientInfo) -> PatientInfo:
        diseases = [d.strip() for d in patient.diseases if d and d.strip()]
        patient_factors = [f.strip() for f in patient.patient_factors if f and f.strip()]
        if patient.age is not None and patient.age >= 65 and "老年人" not in patient_factors:
            patient_factors.append("老年人")
        return PatientInfo(age=patient.age, diseases=diseases, patient_factors=patient_factors)

    def _match_class(self, drug: DrugInfo, target_class: str) -> bool:
        normalized_target = self._normalize_text(target_class)
        return any(
            self._normalize_text(class_name) == normalized_target
            for class_name in self._split_classes(drug.drug_class)
        )

    def _match_drug_pair(
        self,
        current_drug: DrugInfo,
        new_drug: DrugInfo,
        rule_drug: str,
        rule_pair: str,
    ) -> bool:
        current_name = self._normalize_text(current_drug.en_name)
        new_name = self._normalize_text(new_drug.en_name)
        rule_drug_name = self._normalize_text(rule_drug)
        rule_pair_name = self._normalize_text(rule_pair)
        return (
            current_name == rule_drug_name and new_name == rule_pair_name
        ) or (
            current_name == rule_pair_name and new_name == rule_drug_name
        )

    def match_rules(
        self,
        current_drugs: list[DrugInfo],
        new_drug: DrugInfo,
        patient: PatientInfo,
    ) -> list[RuleMatch]:
        normalized_patient = self._normalize_patient(patient)
        rules_df = self._get_rules()
        matches: list[RuleMatch] = []
        seen_rule_ids: set[str] = set()

        for row in rules_df.to_dict(orient="records"):
            rule_id = str(row["rule_id"]).strip()
            trigger_type = str(row["trigger_type"]).strip()
            matched_reason: str | None = None

            if trigger_type == "class_disease":
                disease = str(row["disease"]).strip()
                if self._match_class(new_drug, str(row["drug_or_class"])) and any(
                    self._normalize_text(item) == self._normalize_text(disease)
                    for item in normalized_patient.diseases
                ):
                    matched_reason = f"新增药物{new_drug.zh_name}属于{row['drug_or_class']}，患者存在{disease}"

            elif trigger_type == "class_patient_factor":
                factor = str(row["patient_factor"]).strip()
                if self._match_class(new_drug, str(row["drug_or_class"])) and any(
                    self._normalize_text(item) == self._normalize_text(factor)
                    for item in normalized_patient.patient_factors
                ):
                    if factor == "老年人" and normalized_patient.age is not None:
                        matched_reason = (
                            f"新增药物{new_drug.zh_name}属于{row['drug_or_class']}，"
                            f"患者年龄{normalized_patient.age}岁，命中老年人用药风险"
                        )
                    else:
                        matched_reason = (
                            f"新增药物{new_drug.zh_name}属于{row['drug_or_class']}，"
                            f"患者因素包含{factor}"
                        )

            elif trigger_type == "class_class":
                pair_class = str(row["paired_drug_or_class"]).strip()
                if self._match_class(new_drug, str(row["drug_or_class"])):
                    paired_drug = next(
                        (drug for drug in current_drugs if self._match_class(drug, pair_class)),
                        None,
                    )
                    if paired_drug is not None:
                        matched_reason = (
                            f"当前药物{paired_drug.zh_name}属于{pair_class}，"
                            f"新增药物{new_drug.zh_name}属于{row['drug_or_class']}"
                        )

            elif trigger_type == "drug_pair":
                paired_drug = next(
                    (
                        drug
                        for drug in current_drugs
                        if self._match_drug_pair(
                            drug,
                            new_drug,
                            str(row["drug_or_class"]),
                            str(row["paired_drug_or_class"]),
                        )
                    ),
                    None,
                )
                if paired_drug is not None:
                    matched_reason = (
                        f"当前药物{paired_drug.zh_name}与新增药物{new_drug.zh_name}"
                        "命中特定药物对风险规则"
                    )

            elif trigger_type == "drug_disease":
                disease = str(row["disease"]).strip()
                if (
                    self._normalize_text(new_drug.en_name)
                    == self._normalize_text(str(row["drug_or_class"]))
                    and any(
                        self._normalize_text(item) == self._normalize_text(disease)
                        for item in normalized_patient.diseases
                    )
                ):
                    matched_reason = f"新增药物{new_drug.zh_name}与患者疾病{disease}命中特定用药风险规则"

            if matched_reason is None or rule_id in seen_rule_ids:
                continue

            seen_rule_ids.add(rule_id)
            matches.append(
                RuleMatch(
                    rule_id=rule_id,
                    risk_level=str(row["risk_level"]).strip(),
                    risk=str(row["risk"]).strip(),
                    mechanism=str(row["mechanism"]).strip(),
                    recommendation=str(row["recommendation"]).strip(),
                    evidence_note=str(row["evidence_note"]).strip(),
                    matched_reason=matched_reason,
                )
            )

        return matches

