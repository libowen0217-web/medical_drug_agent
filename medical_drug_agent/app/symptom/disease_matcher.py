from __future__ import annotations

from medical_drug_agent.app.symptom.disease_library import DiseaseLibrary, DiseaseLibraryEntry
from medical_drug_agent.app.symptom.schemas import DiseaseCandidate, ParsedSymptom


REFERRAL_MESSAGE = (
    "当前描述涉及严重疾病或红旗风险，不适合由本系统生成 OTC 候选药，请由医生进一步评估。"
)
NO_MATCH_MESSAGE = "未匹配到明确常见病候选，仅基于症状规则进行初步辅助评估。"


class DiseaseMatcher:
    def __init__(self, library: DiseaseLibrary | None = None, max_candidates: int = 5) -> None:
        self.library = library or DiseaseLibrary()
        self.max_candidates = max_candidates

    def match(
        self,
        symptom_text: str,
        parsed_symptoms: list[ParsedSymptom] | None = None,
    ) -> dict:
        text = self._normalize_text(symptom_text)
        parsed_text = self._normalize_text(
            " ".join(
                [item.symptom_name for item in list(parsed_symptoms or [])]
                + [keyword for item in list(parsed_symptoms or []) for keyword in item.matched_keywords]
            )
        )
        searchable_text = f"{text} {parsed_text}".strip()

        candidates = [
            candidate
            for candidate in (
                self._match_entry(entry, searchable_text) for entry in self.library.load_entries()
            )
            if candidate is not None
        ]
        candidates.sort(key=lambda item: (self._scope_rank(item.scope), -item.score, item.disease_id))
        candidates = candidates[: self.max_candidates]

        referral_required = any(item.scope == "referral_required" for item in candidates)
        return {
            "disease_candidates": candidates,
            "referral_required": referral_required,
            "disease_match_summary": self._build_summary(candidates, referral_required),
        }

    def _match_entry(self, entry: DiseaseLibraryEntry, text: str) -> DiseaseCandidate | None:
        required_matches = self._matched(entry.required_keywords, text)
        optional_matches = self._matched(entry.optional_keywords, text)
        red_flag_matches = self._matched(entry.red_flag_keywords, text)

        if not required_matches and len(optional_matches) < 2 and not red_flag_matches:
            return None

        matched_keywords = self._dedupe(required_matches + optional_matches + red_flag_matches)
        score = len(required_matches) * 3 + len(optional_matches) + len(red_flag_matches) * 5
        if entry.scope == "referral_required":
            score += 10

        return DiseaseCandidate(
            disease_id=entry.disease_id,
            disease_name_cn=entry.disease_name_cn,
            disease_name_en=entry.disease_name_en,
            category=entry.category,
            scope=entry.scope,
            severity=entry.severity,
            typical_symptoms=entry.typical_symptoms,
            matched_keywords=matched_keywords,
            candidate_drug_classes=entry.candidate_drug_classes,
            candidate_drugs=entry.candidate_drugs,
            advice=entry.advice,
            score=score,
        )

    @staticmethod
    def _normalize_text(text: str) -> str:
        return str(text or "").strip().lower()

    @classmethod
    def _matched(cls, keywords: list[str], text: str) -> list[str]:
        normalized_text = cls._normalize_text(text)
        return [keyword for keyword in keywords if cls._normalize_text(keyword) in normalized_text]

    @staticmethod
    def _dedupe(items: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for item in items:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result

    @staticmethod
    def _scope_rank(scope: str) -> int:
        if scope == "referral_required":
            return 0
        if scope == "otc_caution":
            return 1
        return 2

    @staticmethod
    def _build_summary(candidates: list[DiseaseCandidate], referral_required: bool) -> str:
        if referral_required:
            return REFERRAL_MESSAGE
        if not candidates:
            return NO_MATCH_MESSAGE
        names = "、".join(item.disease_name_cn for item in candidates[:3] if item.disease_name_cn)
        return f"匹配到 {names} 等常见疾病候选，仅用于问诊辅助，不构成诊断。"
