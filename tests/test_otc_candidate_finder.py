from medical_drug_agent.app.symptom.otc_candidate_finder import OTCCandidateFinder
from medical_drug_agent.app.symptom.symptom_parser import SymptomParser


def test_fever_returns_antipyretic_candidates() -> None:
    parsed = SymptomParser().parse("发热")
    results = OTCCandidateFinder().find_candidates("发热", parsed)
    assert any(item.drug_class == "退热镇痛类" for item in results)


def test_runny_nose_returns_antiallergy_candidates() -> None:
    parsed = SymptomParser().parse("流鼻涕")
    results = OTCCandidateFinder().find_candidates("流鼻涕", parsed)
    assert any(item.drug_class == "抗过敏类" for item in results)


def test_cough_with_sputum_returns_expectorant_candidates() -> None:
    parsed = SymptomParser().parse("咳嗽有痰")
    results = OTCCandidateFinder().find_candidates("咳嗽有痰", parsed)
    assert any("化痰/祛痰类" == item.drug_class for item in results)


def test_results_do_not_include_antibiotics() -> None:
    parsed = SymptomParser().parse("发热")
    results = OTCCandidateFinder().find_candidates("发热", parsed)
    all_drugs = [drug for item in results for drug in item.candidate_drugs]
    assert "阿莫西林" not in all_drugs


def test_allergy_hit_adds_caution() -> None:
    parsed = SymptomParser().parse("发热")
    results = OTCCandidateFinder().find_candidates("发热", parsed, allergies=["布洛芬"])
    assert any("过敏史" in item.caution for item in results)


def test_hypertension_adds_ibuprofen_caution() -> None:
    parsed = SymptomParser().parse("发热")
    results = OTCCandidateFinder().find_candidates("发热", parsed, diseases=["高血压"])
    assert any("高血压" in item.caution for item in results if "布洛芬" in item.candidate_drugs)
