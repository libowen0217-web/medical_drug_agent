from medical_drug_agent.app.evidence.scoring import EvidenceScorer


def _row() -> dict:
    return {
        "topic": "NSAID高血压风险",
        "drug_or_class": "NSAID",
        "disease_or_factor": "高血压",
        "risk": "血压控制风险",
        "evidence_text": "NSAID类药物在部分患者中可能影响血压控制。",
    }


def test_topic_hit_adds_score() -> None:
    result = EvidenceScorer().score(_row(), ["NSAID高血压风险"])
    assert result["score"] >= 3.0


def test_drug_or_class_hit_adds_score() -> None:
    result = EvidenceScorer().score(_row(), ["NSAID"])
    assert result["score"] >= 3.0


def test_disease_or_factor_hit_adds_score() -> None:
    result = EvidenceScorer().score(_row(), ["高血压"])
    assert result["score"] >= 3.0


def test_evidence_text_hit_adds_score() -> None:
    result = EvidenceScorer().score(_row(), ["影响血压控制"])
    assert result["score"] >= 1.0


def test_case_insensitive_for_english_keywords() -> None:
    result = EvidenceScorer().score(_row(), ["nsaid"])
    assert result["score"] >= 3.0


def test_no_match_returns_zero() -> None:
    result = EvidenceScorer().score(_row(), ["Warfarin"])
    assert result["score"] == 0.0


def test_matched_keywords_are_deduplicated() -> None:
    result = EvidenceScorer().score(_row(), ["NSAID", "nsaid"])
    assert len(result["matched_keywords"]) == 1
