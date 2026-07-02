from medical_drug_agent.app.evidence.citation import EvidenceCitationBuilder
from medical_drug_agent.app.schemas import EvidenceItem


def _item(evidence_id: str, score: float, text: str) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        topic="topic",
        source_type="local",
        source_name="source",
        evidence_text=text,
        matched_reason="reason",
        score=score,
    )


def test_sorted_by_score_descending() -> None:
    items = [_item("a", 1.0, "a"), _item("b", 5.0, "b")]
    results = EvidenceCitationBuilder().assign_citations(items)
    assert results[0].evidence_id == "b"


def test_citation_label_is_generated() -> None:
    result = EvidenceCitationBuilder().assign_citations([_item("a", 1.0, "a")])[0]
    assert result.citation_label == "[证据1]"


def test_rank_is_generated() -> None:
    result = EvidenceCitationBuilder().assign_citations([_item("a", 1.0, "a")])[0]
    assert result.rank == 1


def test_duplicate_evidence_id_is_removed() -> None:
    results = EvidenceCitationBuilder().assign_citations([_item("a", 3.0, "x"), _item("a", 2.0, "y")])
    assert len(results) == 1


def test_duplicate_evidence_text_is_removed() -> None:
    results = EvidenceCitationBuilder().assign_citations([_item("a", 3.0, "x"), _item("b", 2.0, "x")])
    assert len(results) == 1


def test_top_k_is_effective() -> None:
    items = [_item("a", 5.0, "a"), _item("b", 4.0, "b"), _item("c", 3.0, "c"), _item("d", 2.0, "d")]
    results = EvidenceCitationBuilder().assign_citations(items, top_k=3)
    assert len(results) == 3
