from __future__ import annotations

from dataclasses import replace

from medical_drug_agent.app.schemas import EvidenceItem


class EvidenceCitationBuilder:
    """Deduplicate, sort, and assign citation labels to evidence items."""

    def assign_citations(self, evidence_items: list[EvidenceItem], top_k: int = 3) -> list[EvidenceItem]:
        deduped = self._dedupe(evidence_items)
        ordered = sorted(
            enumerate(deduped),
            key=lambda pair: (-pair[1].score, pair[0]),
        )

        results: list[EvidenceItem] = []
        for rank, (_, item) in enumerate(ordered[:top_k], start=1):
            results.append(
                replace(
                    item,
                    rank=rank,
                    citation_label=f"[证据{rank}]",
                )
            )
        return results

    @staticmethod
    def _dedupe(evidence_items: list[EvidenceItem]) -> list[EvidenceItem]:
        deduped: list[EvidenceItem] = []
        seen_ids: set[str] = set()
        seen_texts: set[str] = set()
        for item in evidence_items:
            text_key = item.evidence_text.strip()
            if item.evidence_id in seen_ids or text_key in seen_texts:
                continue
            deduped.append(item)
            seen_ids.add(item.evidence_id)
            seen_texts.add(text_key)
        return deduped
