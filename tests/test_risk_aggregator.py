from medical_drug_agent.app.reporting.aggregator import RiskAggregator
from medical_drug_agent.app.schemas import DoseCheckResult, DrugInfo, DrugRelation, RuleMatch


def _current_drug() -> DrugInfo:
    return DrugInfo(input_name="硝苯地平", zh_name="硝苯地平", en_name="Nifedipine", drug_class="钙通道阻滞剂/降压药")


def _new_drug() -> DrugInfo:
    return DrugInfo(input_name="布洛芬", zh_name="布洛芬", en_name="Ibuprofen", drug_class="NSAID/非甾体抗炎药")


def test_high_rule_sets_overall_risk_to_high() -> None:
    aggregator = RiskAggregator()
    summary = aggregator.aggregate(
        current_drugs=[_current_drug()],
        new_drug=_new_drug(),
        kg_pair_relations=[],
        rule_matches=[RuleMatch("R", "high", "出血风险增加", "机制", "建议", "证据", "原因")],
        dose_results=[],
    )
    assert summary.overall_risk_level == "high"


def test_medium_rule_sets_overall_risk_to_medium() -> None:
    aggregator = RiskAggregator()
    summary = aggregator.aggregate(
        current_drugs=[_current_drug()],
        new_drug=_new_drug(),
        kg_pair_relations=[],
        rule_matches=[RuleMatch("R", "medium", "可能影响血压控制", "机制", "建议", "证据", "原因")],
        dose_results=[],
    )
    assert summary.overall_risk_level == "medium"


def test_kg_pair_relations_create_kg_finding() -> None:
    aggregator = RiskAggregator()
    summary = aggregator.aggregate(
        current_drugs=[_current_drug()],
        new_drug=_new_drug(),
        kg_pair_relations=[DrugRelation("Nifedipine", "drug", "Ibuprofen", "drug", "x", "synergistic interaction", "drug_drug", "Nifedipine;Ibuprofen", {})],
        rule_matches=[],
        dose_results=[],
    )
    assert any(finding.source == "kg_relation" for finding in summary.findings)


def test_missing_dose_creates_dose_finding() -> None:
    aggregator = RiskAggregator()
    summary = aggregator.aggregate(
        current_drugs=[_current_drug()],
        new_drug=_new_drug(),
        kg_pair_relations=[],
        rule_matches=[],
        dose_results=[DoseCheckResult("布洛芬", "missing_dose", "unknown", "缺失", {})],
    )
    assert any(finding.source == "dose_check" and finding.title == "剂量信息缺失" for finding in summary.findings)


def test_findings_are_deduplicated() -> None:
    aggregator = RiskAggregator()
    match = RuleMatch("R", "medium", "同一风险", "机制", "建议", "证据", "原因")
    summary = aggregator.aggregate(
        current_drugs=[_current_drug()],
        new_drug=_new_drug(),
        kg_pair_relations=[],
        rule_matches=[match, match],
        dose_results=[],
    )
    assert len(summary.findings) == 1

