from medical_drug_agent.app.evidence.retriever import EvidenceRetriever
from medical_drug_agent.app.schemas import DoseCheckResult, RiskFinding, RuleMatch


def test_retrieve_for_rule_match_returns_evidence() -> None:
    retriever = EvidenceRetriever()
    results = retriever.retrieve_for_rule_match(
        RuleMatch("R001", "medium", "可能影响血压控制", "NSAID可能影响血压", "建议监测", "本地规则", "布洛芬用于高血压患者")
    )
    assert results


def test_retrieve_for_dose_result_returns_evidence() -> None:
    retriever = EvidenceRetriever()
    results = retriever.retrieve_for_dose_result(
        DoseCheckResult("Ibuprofen", "missing_dose", "unknown", "需要补充剂量信息", {})
    )
    assert results


def test_retrieve_for_risk_finding_returns_evidence() -> None:
    retriever = EvidenceRetriever()
    results = retriever.retrieve_for_risk_finding(
        RiskFinding(
            source="rule_match",
            risk_level="high",
            title="出血风险",
            description="华法林与布洛芬合用需关注出血风险",
            mechanism="NSAID与抗凝药合用",
            recommendation="建议咨询药师",
            evidence_note="本地规则",
            related_drugs=["Ibuprofen", "Warfarin"],
            related_diseases=[],
        )
    )
    assert results


def test_no_hit_returns_empty_list() -> None:
    retriever = EvidenceRetriever()
    results = retriever.retrieve_for_risk_finding(
        RiskFinding(
            source="rule_match",
            risk_level="low",
            title="完全无关主题",
            description="完全无关描述",
            mechanism="无关机制",
            recommendation="无关建议",
            evidence_note="无关",
            related_drugs=["XYZUnmatchedDrug"],
            related_diseases=["UnknownDisease"],
        )
    )
    assert results == []
