from __future__ import annotations


class EvidenceScorer:
    """Field-weighted keyword scorer for local evidence rows."""

    FIELD_WEIGHTS = {
        "topic": 3.0,
        "drug_or_class": 3.0,
        "disease_or_factor": 3.0,
        "risk": 2.0,
        "evidence_text": 1.0,
    }

    def score(self, evidence_row: dict, keywords: list[str]) -> dict:
        normalized_keywords = self._normalize_keywords(keywords)
        if not normalized_keywords:
            return {
                "score": 0.0,
                "matched_keywords": [],
                "matched_fields": [],
            }

        total_score = 0.0
        matched_keywords: list[str] = []
        matched_fields: list[str] = []

        for keyword in normalized_keywords:
            keyword_lower = keyword.lower()
            keyword_hit = False
            for field_name, weight in self.FIELD_WEIGHTS.items():
                field_text = str(evidence_row.get(field_name, ""))
                if keyword_lower in field_text.lower():
                    total_score += float(weight)
                    if field_name not in matched_fields:
                        matched_fields.append(field_name)
                    keyword_hit = True
            if keyword_hit and keyword not in matched_keywords:
                matched_keywords.append(keyword)

        return {
            "score": float(total_score),
            "matched_keywords": matched_keywords,
            "matched_fields": matched_fields,
        }

    @staticmethod
    def _normalize_keywords(keywords: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for keyword in keywords:
            cleaned = str(keyword).strip()
            if not cleaned:
                continue
            lowered = cleaned.lower()
            if lowered not in seen:
                seen.add(lowered)
                normalized.append(cleaned)
        return normalized
