from __future__ import annotations

import re

from medical_drug_agent.app.evidence.citation import EvidenceCitationBuilder
from medical_drug_agent.app.evidence.store import EvidenceStore
from medical_drug_agent.app.schemas import DoseCheckResult, EvidenceItem, RiskFinding, RuleMatch


class EvidenceRetriever:
    """Retrieve local evidence snippets for rules, dose checks, and findings."""

    def __init__(self, store: EvidenceStore | None = None) -> None:
        self.store = store or EvidenceStore()
        self.citation_builder = EvidenceCitationBuilder()

    def retrieve_for_rule_match(self, rule_match: RuleMatch, limit: int = 3) -> list[EvidenceItem]:
        keywords = self._extract_keywords(
            rule_match.risk,
            rule_match.mechanism,
            rule_match.evidence_note,
            rule_match.matched_reason,
        )
        return self._retrieve(keywords, limit=limit)

    def retrieve_for_dose_result(self, dose_result: DoseCheckResult, limit: int = 3) -> list[EvidenceItem]:
        keywords = self._extract_keywords(
            dose_result.drug_name,
            dose_result.status,
            dose_result.message,
            "剂量",
        )
        return self._retrieve(keywords, limit=limit)

    def retrieve_for_risk_finding(self, finding: RiskFinding, limit: int = 3) -> list[EvidenceItem]:
        keywords = self._extract_keywords(
            finding.title,
            finding.description,
            finding.mechanism,
            *finding.related_drugs,
            *finding.related_diseases,
        )
        return self._retrieve(keywords, limit=limit)

    def _retrieve(self, keywords: list[str], limit: int) -> list[EvidenceItem]:
        try:
            items = self.store.search_by_keywords(keywords, limit=max(limit * 2, limit))
            return self.citation_builder.assign_citations(items, top_k=limit)
        except Exception:
            return []

    @staticmethod
    def _extract_keywords(*values: str) -> list[str]:
        keywords: list[str] = []
        seen: set[str] = set()
        for value in values:
            text = str(value or "").strip()
            if not text:
                continue
            candidates = [text]
            candidates.extend(re.findall(r"[A-Za-z][A-Za-z0-9\-]+|[\u4e00-\u9fff]{2,}", text))
            for candidate in candidates:
                cleaned = candidate.strip(" ,.;:[]()")
                if len(cleaned) < 2:
                    continue
                lowered = cleaned.lower()
                if lowered not in seen:
                    seen.add(lowered)
                    keywords.append(cleaned)
        return keywords
