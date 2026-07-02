from __future__ import annotations

from medical_drug_agent.app.symptom.rule_store import SymptomRuleStore
from medical_drug_agent.app.symptom.schemas import RedFlagFinding


class RedFlagChecker:
    FEVER_KEYWORDS = ["发热", "发烧", "高热", "体温高"]
    ELDERLY_WORSENING_KEYWORDS = ["加重", "越来越严重", "更严重", "恶化"]
    SERIOUS_DISEASE_KEYWORDS = [
        "肺癌",
        "癌症",
        "肿瘤",
        "恶性肿瘤",
        "咯血",
        "胸痛",
        "呼吸困难",
        "意识模糊",
    ]

    def __init__(self, rule_store: SymptomRuleStore | None = None) -> None:
        self.rule_store = rule_store or SymptomRuleStore()
        self._red_flag_rows = self.rule_store.load_red_flags()

    def check(
        self,
        symptom_text: str,
        age: int | None = None,
        temperature_c: float | None = None,
        duration_days: int | None = None,
        patient_factors: list[str] | None = None,
    ) -> list[RedFlagFinding]:
        text = str(symptom_text or "").strip().lower()
        factors = [str(item).strip().lower() for item in list(patient_factors or []) if str(item).strip()]
        findings: dict[str, RedFlagFinding] = {}

        for row in self._red_flag_rows:
            keywords = list(row.get("keywords", []) or [])
            condition_hint = str(row.get("condition_hint", "") or "")
            if condition_hint == "keyword_combo":
                matched = [keyword for keyword in keywords if keyword.lower() in text]
                if len(matched) >= 2:
                    findings[row["red_flag_id"]] = self._build_finding(row, matched)
                continue
            matched = [keyword for keyword in keywords if keyword.lower() in text]
            if matched:
                findings[row["red_flag_id"]] = self._build_finding(row, matched)

        serious_hits = [keyword for keyword in self.SERIOUS_DISEASE_KEYWORDS if keyword.lower() in text]
        if serious_hits:
            findings["RF900"] = RedFlagFinding(
                red_flag_id="RF900",
                title="严重疾病或红旗风险",
                description="当前描述涉及严重疾病或红旗风险，不适合由本系统生成 OTC 候选药。",
                matched_keywords=list(dict.fromkeys(serious_hits)),
                action="请由医生进一步评估，必要时及时就医。",
                urgency_level="high",
            )

        if temperature_c is not None and temperature_c >= 40.0:
            self._add_by_id(findings, "RF007", [f"{temperature_c:.1f}℃"])

        if temperature_c is not None and duration_days is not None and temperature_c >= 39.0 and duration_days >= 3:
            self._add_by_id(findings, "RF006", [f"{temperature_c:.1f}℃", f"{duration_days}天"])

        if temperature_c is not None and age is not None and age <= 3 and temperature_c >= 38.5:
            self._add_by_id(findings, "RF009", [f"{age}岁", f"{temperature_c:.1f}℃"])

        has_fever = any(keyword in text for keyword in self.FEVER_KEYWORDS) or (
            temperature_c is not None and temperature_c >= 38.0
        )
        if has_fever and any(item in factors for item in ["孕妇", "怀孕"]):
            self._add_by_id(findings, "RF010", ["孕妇", "发热"])

        if age is not None and age >= 65:
            worsening_hits = [keyword for keyword in self.ELDERLY_WORSENING_KEYWORDS if keyword in text]
            if worsening_hits:
                self._add_by_id(findings, "RF011", worsening_hits)

        return list(findings.values())

    def _add_by_id(self, findings: dict[str, RedFlagFinding], red_flag_id: str, matched_keywords: list[str]) -> None:
        if red_flag_id in findings:
            existing = findings[red_flag_id]
            for item in matched_keywords:
                if item not in existing.matched_keywords:
                    existing.matched_keywords.append(item)
            return
        row = next((item for item in self._red_flag_rows if item.get("red_flag_id") == red_flag_id), None)
        if row is not None:
            findings[red_flag_id] = self._build_finding(row, matched_keywords)

    @staticmethod
    def _build_finding(row: dict, matched_keywords: list[str]) -> RedFlagFinding:
        return RedFlagFinding(
            red_flag_id=str(row.get("red_flag_id", "")),
            title=str(row.get("category", "")),
            description=str(row.get("description", "")),
            matched_keywords=list(dict.fromkeys(matched_keywords)),
            action=str(row.get("action", "")),
            urgency_level=str(row.get("urgency_level", "")),
        )
