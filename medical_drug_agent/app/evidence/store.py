from __future__ import annotations

import pandas as pd

from medical_drug_agent.app.constants import EVIDENCE_STORE_PATH
from medical_drug_agent.app.evidence.scoring import EvidenceScorer
from medical_drug_agent.app.schemas import EvidenceItem


class EvidenceStore:
    """Keyword-searchable local evidence store backed by CSV."""

    SEARCH_COLUMNS = ["topic", "drug_or_class", "disease_or_factor", "risk", "evidence_text"]

    def __init__(self, store_path=EVIDENCE_STORE_PATH) -> None:
        self.store_path = store_path
        self._dataframe: pd.DataFrame | None = None
        self.scorer = EvidenceScorer()

    def load(self) -> pd.DataFrame:
        if self._dataframe is None:
            if not self.store_path.exists():
                raise FileNotFoundError(f"本地证据库文件不存在：{self.store_path}")
            self._dataframe = pd.read_csv(self.store_path).fillna("")
        return self._dataframe

    def list_all(self) -> list[EvidenceItem]:
        return [
            self._row_to_item(row, matched_reason="")
            for row in self.load().to_dict(orient="records")
        ]

    def search_by_keywords(self, keywords: list[str], limit: int = 5) -> list[EvidenceItem]:
        normalized_keywords = self._normalize_keywords(keywords)
        if not normalized_keywords:
            return []

        scored_items: list[tuple[int, EvidenceItem]] = []
        for row in self.load().to_dict(orient="records"):
            score_result = self.scorer.score(row, normalized_keywords)
            score = float(score_result["score"])
            if score > 0:
                scored_items.append(
                    (
                        score,
                        self._row_to_item(
                            row,
                            matched_reason=(
                                f"命中关键词：{', '.join(score_result['matched_keywords'])}；评分：{score:.1f}"
                            ),
                            score=score,
                            matched_keywords=list(score_result["matched_keywords"]),
                        ),
                    )
                )

        scored_items.sort(key=lambda item: (-item[0], item[1].evidence_id))
        return [item for _, item in scored_items[:limit]]

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

    @staticmethod
    def _row_to_item(
        row: dict,
        matched_reason: str,
        score: float = 0.0,
        matched_keywords: list[str] | None = None,
    ) -> EvidenceItem:
        return EvidenceItem(
            evidence_id=str(row.get("evidence_id", "")),
            topic=str(row.get("topic", "")),
            source_type=str(row.get("source_type", "")),
            source_name=str(row.get("source_name", "")),
            evidence_text=str(row.get("evidence_text", "")),
            matched_reason=matched_reason,
            score=float(score),
            matched_keywords=list(matched_keywords or []),
        )
