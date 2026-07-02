from __future__ import annotations

from medical_drug_agent.app.symptom.rule_store import SymptomRuleStore
from medical_drug_agent.app.symptom.schemas import ParsedSymptom


class SymptomParser:
    def __init__(self, rule_store: SymptomRuleStore | None = None) -> None:
        self.rule_store = rule_store or SymptomRuleStore()

    def parse(self, symptom_text: str) -> list[ParsedSymptom]:
        text = str(symptom_text or "").strip().lower()
        if not text:
            return []

        parsed: list[ParsedSymptom] = []
        seen: set[str] = set()
        for rule in self.rule_store.load_symptom_rules():
            matched_keywords = [
                keyword for keyword in list(rule.get("keywords", []) or []) if keyword.lower() in text
            ]
            symptom_name = str(rule.get("symptom_name", "") or "")
            if matched_keywords and symptom_name not in seen:
                seen.add(symptom_name)
                parsed.append(
                    ParsedSymptom(
                        symptom_name=symptom_name,
                        matched_keywords=matched_keywords,
                        severity=(rule.get("severity") or None),
                    )
                )
        return parsed

