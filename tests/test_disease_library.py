from medical_drug_agent.app.symptom.disease_library import DiseaseLibrary
from medical_drug_agent.app.symptom.disease_matcher import DiseaseMatcher


def test_disease_library_loads_entries() -> None:
    entries = DiseaseLibrary().load_entries()
    assert len(entries) >= 20
    assert any(item.disease_id == "common_cold" for item in entries)


def test_fever_headache_sore_throat_matches_common_cold_or_flu_like() -> None:
    result = DiseaseMatcher().match("发热、头痛、咽痛，两天了")
    ids = {item.disease_id for item in result["disease_candidates"]}
    assert {"common_cold", "influenza_like"} & ids
    assert result["referral_required"] is False


def test_headache_matches_headache_candidate() -> None:
    result = DiseaseMatcher().match("头疼，一天了")
    assert any(item.disease_id == "headache" for item in result["disease_candidates"])


def test_acid_reflux_matches_reflux_candidate() -> None:
    result = DiseaseMatcher().match("反酸、烧心，胃部不适")
    assert any(item.disease_id == "acid_reflux" for item in result["disease_candidates"])


def test_allergic_rhinitis_matches_nose_keywords() -> None:
    result = DiseaseMatcher().match("鼻痒、流涕、打喷嚏")
    assert any(item.disease_id == "allergic_rhinitis" for item in result["disease_candidates"])


def test_lung_cancer_requires_referral() -> None:
    result = DiseaseMatcher().match("肺癌")
    assert result["referral_required"] is True
    assert any(item.disease_id == "lung_cancer" for item in result["disease_candidates"])
