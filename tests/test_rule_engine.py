from medical_drug_agent.app.normalization.mapper import DrugNameMapper
from medical_drug_agent.app.rules.engine import SafetyRuleEngine
from medical_drug_agent.app.schemas import PatientInfo


def test_ibuprofen_and_hypertension_match_nsaid_hypertension_rule() -> None:
    mapper = DrugNameMapper()
    engine = SafetyRuleEngine()
    matches = engine.match_rules(
        current_drugs=[mapper.normalize("硝苯地平")],
        new_drug=mapper.normalize("布洛芬"),
        patient=PatientInfo(age=40, diseases=["高血压"]),
    )
    assert any(match.rule_id == "R001" for match in matches)


def test_ibuprofen_and_elderly_match_nsaid_elderly_rule() -> None:
    mapper = DrugNameMapper()
    engine = SafetyRuleEngine()
    matches = engine.match_rules(
        current_drugs=[mapper.normalize("硝苯地平")],
        new_drug=mapper.normalize("布洛芬"),
        patient=PatientInfo(age=68, diseases=[]),
    )
    assert any(match.rule_id == "R002" for match in matches)


def test_warfarin_and_ibuprofen_match_nsaid_anticoagulant_rule() -> None:
    mapper = DrugNameMapper()
    engine = SafetyRuleEngine()
    matches = engine.match_rules(
        current_drugs=[mapper.normalize("华法林")],
        new_drug=mapper.normalize("布洛芬"),
        patient=PatientInfo(age=40, diseases=[]),
    )
    assert any(match.rule_id == "R003" for match in matches)


def test_aspirin_and_warfarin_match_specific_drug_pair_rule() -> None:
    mapper = DrugNameMapper()
    engine = SafetyRuleEngine()
    matches = engine.match_rules(
        current_drugs=[mapper.normalize("华法林")],
        new_drug=mapper.normalize("阿司匹林"),
        patient=PatientInfo(age=40, diseases=[]),
    )
    assert any(match.rule_id == "R004" for match in matches)


def test_no_rule_match_returns_empty_list() -> None:
    mapper = DrugNameMapper()
    engine = SafetyRuleEngine()
    matches = engine.match_rules(
        current_drugs=[mapper.normalize("奥美拉唑")],
        new_drug=mapper.normalize("氨氯地平"),
        patient=PatientInfo(age=30, diseases=[]),
    )
    assert matches == []

